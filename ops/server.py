#!/usr/bin/env python3
"""
Ops console for the Elastic x Hopsworks hackathon clusters.

Self-hosted, stdlib HTTP server + one static page. Lets you:
  - connect to the primary cluster (from .env) or any other cluster
  - run ingest.py against a cluster and watch its log
  - mint read-only API keys for remote reindexing, and revoke them
  - delete indices / tear a cluster down

Usage:  python ops/server.py [--host 127.0.0.1] [--port 8787]

Credentials entered in the UI are kept in memory only.
"""

import argparse, json, os, re, signal, subprocess, sys, threading, time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dotenv import dotenv_values
from elasticsearch import Elasticsearch, NotFoundError

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
KEY_PREFIX = "hackathon-ro-"
DATA_PATTERN = "f1-*"
INDEX_NAMES = ["f1-sessions", "f1-results", "f1-laps", "f1-weather", "f1-telemetry"]

clusters = {}            # name -> {url, api_key, username, password}
clusters_lock = threading.Lock()


class Bad(Exception):
    pass


# ── Clusters ──────────────────────────────────────────────────────────────────

def load_primary():
    env = {**dotenv_values(ROOT / ".env"), **{k: v for k, v in os.environ.items() if k.startswith("ELASTICSEARCH_")}}
    if env.get("ELASTICSEARCH_URL"):
        clusters["primary"] = dict(
            url=env["ELASTICSEARCH_URL"],
            api_key=env.get("ELASTICSEARCH_API_KEY") or "",
            username=env.get("ELASTICSEARCH_USERNAME") or "",
            password=env.get("ELASTICSEARCH_PASSWORD") or "",
        )


def profile(name):
    with clusters_lock:
        p = clusters.get(name)
    if not p:
        raise Bad("unknown cluster %r" % name)
    return p


def client(name):
    p = profile(name)
    kw = dict(request_timeout=30)
    if p["api_key"]:
        kw["api_key"] = p["api_key"]
    elif p["username"]:
        kw["basic_auth"] = (p["username"], p["password"])
    return Elasticsearch(p["url"], **kw)


def auth_kind(p):
    return "api_key" if p["api_key"] else "basic" if p["username"] else "none"


def remote_host(url):
    """Host string for reindex source.remote.host (needs scheme + port)."""
    u = urlparse(url)
    port = u.port or (443 if u.scheme == "https" else 9200)
    return "%s://%s:%d" % (u.scheme, u.hostname, port)


def es_error(e):
    """Short message from an elasticsearch exception."""
    body = getattr(e, "body", None)
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):
            return "%s: %s" % (getattr(e, "status_code", ""), err.get("reason") or err.get("type"))
    return str(e)[:400]


# ── Ingest process ────────────────────────────────────────────────────────────

class Ingest:
    def __init__(self):
        self.lock = threading.Lock()
        self.proc = None
        self.cluster = None
        self.started = None
        self.ended = None
        self.log = deque(maxlen=1000)
        self.total = 0

    def _add(self, line):
        line = line.rstrip()
        if not line or "%|" in line:     # drop tqdm bars
            return
        with self.lock:
            self.log.append(line)
            self.total += 1

    def _pump(self, proc):
        buf = ""
        while True:
            chunk = proc.stdout.read1(4096) if hasattr(proc.stdout, "read1") else proc.stdout.read(4096)
            if not chunk:
                break
            buf += chunk.decode("utf-8", "replace").replace("\r", "\n")
            *lines, buf = buf.split("\n")
            for ln in lines:
                self._add(ln)
        if buf:
            self._add(buf)
        code = proc.wait()
        self._add("— ingest exited with code %s —" % code)
        self.ended = time.time()

    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def start(self, cluster, seasons):
        if self.running():
            raise Bad("ingest already running against %r" % self.cluster)
        p = profile(cluster)
        env = dict(os.environ)
        env.update(
            ELASTICSEARCH_URL=p["url"], ELASTICSEARCH_API_KEY=p["api_key"],
            ELASTICSEARCH_USERNAME=p["username"], ELASTICSEARCH_PASSWORD=p["password"],
            F1_SEASONS=",".join(str(s) for s in seasons),
            PYTHONUNBUFFERED="1", TQDM_DISABLE="1",
        )
        with self.lock:
            self.log.clear()
            self.total = 0
        self.proc = subprocess.Popen(
            [sys.executable, "-u", str(ROOT / "ingest.py")], cwd=str(ROOT), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True,
        )
        self.cluster, self.started, self.ended = cluster, time.time(), None
        self._add("— started ingest: cluster=%s seasons=%s —" % (cluster, seasons))
        threading.Thread(target=self._pump, args=(self.proc,), daemon=True).start()

    def stop(self):
        if not self.running():
            raise Bad("no ingest running")
        os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)

    def snapshot(self, since=0):
        with self.lock:
            n = min(max(self.total - since, 0), len(self.log))
            lines = list(self.log)[len(self.log) - n:] if n else []
            return dict(running=self.running(), cluster=self.cluster, started=self.started,
                        ended=self.ended, total=self.total, lines=lines)


ingest = Ingest()


# ── Operations ────────────────────────────────────────────────────────────────

def valid_pattern(pat):
    if not isinstance(pat, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._*-]*", pat) or len(pat.replace("*", "")) < 2:
        raise Bad("pattern must be lowercase, not start with . or _, and not be only wildcards")
    return pat


def cat_indices(es, pattern):
    try:
        rows = es.cat.indices(index=pattern, format="json", h="index,health,docs.count,store.size",
                              expand_wildcards="open", s="index")
    except NotFoundError:
        return []
    return [dict(index=r["index"], health=r.get("health"), docs=int(r.get("docs.count") or 0),
                 size=r.get("store.size")) for r in rows]


def delete_indices(es, pattern):
    names = [r["index"] for r in cat_indices(es, valid_pattern(pattern))]
    for i in range(0, len(names), 50):
        es.indices.delete(index=",".join(names[i:i + 50]), ignore_unavailable=True)
    return names


def list_keys(es):
    res = es.security.get_api_key(name=KEY_PREFIX + "*", active_only=True)
    return [dict(id=k["id"], name=k["name"], created=k.get("creation"), expiration=k.get("expiration"),
                 username=k.get("username")) for k in res.get("api_keys", [])]


def op_status(name):
    es, p = client(name), profile(name)
    out = dict(name=name, url=p["url"], auth=auth_kind(p), errors=[])
    for key, fn in (
        ("info", lambda: es.info().body),
        ("whoami", lambda: es.security.authenticate().body),
        ("indices", lambda: cat_indices(es, DATA_PATTERN)),
    ):
        try:
            out[key] = fn()
        except Exception as e:
            out["errors"].append("%s: %s" % (key, es_error(e)))
    if "info" in out:
        out["info"] = dict(version=out["info"]["version"]["number"], cluster_name=out["info"]["cluster_name"])
    if "whoami" in out:
        w = out["whoami"]
        out["whoami"] = dict(user=w.get("username"), type=w.get("authentication_type"), roles=w.get("roles"))
    return out


def op_create_key(name, label, days, patterns):
    label = re.sub(r"[^a-z0-9-]", "-", (label or "event").lower()).strip("-") or "event"
    days = int(days)
    if not 1 <= days <= 365:
        raise Bad("expiry must be 1–365 days")
    patterns = [valid_pattern(x.strip()) for x in patterns if x.strip()] or [DATA_PATTERN]
    es = client(name)
    if auth_kind(profile(name)) == "api_key":
        raise Bad("This connection authenticates with an API key, and Elasticsearch won't let an API key "
                  "mint a key with privileges. Connect the same URL with username/password "
                  "(Overview → Connect another cluster), select that cluster, and retry.")
    res = es.security.create_api_key(
        name=KEY_PREFIX + label, expiration="%dd" % days,
        role_descriptors={"f1_reader": {"indices": [{"names": patterns, "privileges": ["read", "view_index_metadata"]}]}},
        metadata={"created_by": "hackathon-ops-console", "purpose": "remote reindex"},
    )
    host = remote_host(profile(name)["url"])
    snippets = "\n\n".join(
        'POST _reindex?wait_for_completion=false\n'
        '{\n  "source": {\n    "remote": {\n      "host": "%s",\n      "api_key": "%s"\n    },\n'
        '    "index": "%s",\n    "size": 2000\n  },\n  "dest": { "index": "%s" }\n}' % (host, res["encoded"], i, i)
        for i in INDEX_NAMES)
    return dict(id=res["id"], name=res["name"], encoded=res["encoded"], host=host, snippets=snippets)


def op_teardown(name):
    es = client(name)
    out = dict(deleted_indices=delete_indices(es, DATA_PATTERN), invalidated_keys=[], errors=[])
    try:
        ids = [k["id"] for k in list_keys(es)]
        if ids:
            es.security.invalidate_api_key(ids=ids)
        out["invalidated_keys"] = ids
    except Exception as e:
        out["errors"].append("keys: " + es_error(e))
    return out


def need_confirm(body):
    if body.get("confirm") != body.get("cluster"):
        raise Bad("type the cluster name to confirm")


# ── HTTP ──────────────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    loopback_only = True

    def log_message(self, *a):
        pass

    def send_json(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def guard(self, mutating):
        # Block DNS-rebinding and cross-site POSTs against the local server.
        if self.loopback_only:
            host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
            if host not in ("localhost", "127.0.0.1", "::1"):
                raise Bad("bad Host header")
        if mutating and (self.headers.get("X-Ops-Console") != "1"
                         or "application/json" not in (self.headers.get("Content-Type") or "")):
            raise Bad("missing X-Ops-Console header / JSON content type")

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def handle_any(self, method):
        try:
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            self.guard(method != "GET")
            if method == "GET" and u.path in ("/", "/index.html"):
                data = (HERE / "index.html").read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            body = self.body() if method != "GET" else {}
            self.send_json(self.route(method, u.path, q, body))
        except Bad as e:
            self.send_json(dict(error=str(e)), 400)
        except Exception as e:
            self.send_json(dict(error=es_error(e)), 500)

    def route(self, method, path, q, b):
        key = (method, path)
        if key == ("GET", "/api/clusters"):
            with clusters_lock:
                return [dict(name=n, url=p["url"], auth=auth_kind(p)) for n, p in clusters.items()]
        if key == ("POST", "/api/clusters"):
            name = re.sub(r"[^A-Za-z0-9_-]", "", b.get("name", ""))[:32]
            if not name or not b.get("url", "").startswith(("http://", "https://")):
                raise Bad("need a name and an http(s) URL")
            if not (b.get("api_key") or b.get("username")):
                raise Bad("need an API key or username/password")
            with clusters_lock:
                clusters[name] = dict(url=b["url"].rstrip("/"), api_key=b.get("api_key", ""),
                                      username=b.get("username", ""), password=b.get("password", ""))
            return op_status(name)
        if method == "DELETE" and path.startswith("/api/clusters/"):
            name = path.rsplit("/", 1)[1]
            if ingest.running() and ingest.cluster == name:
                raise Bad("ingest is running against this cluster")
            with clusters_lock:
                clusters.pop(name, None)
            return dict(ok=True)
        if key == ("GET", "/api/status"):
            return op_status(q.get("cluster", "primary"))
        if key == ("GET", "/api/indices"):
            return cat_indices(client(q["cluster"]), valid_pattern(q.get("pattern", DATA_PATTERN)))
        if key == ("GET", "/api/ingest"):
            return ingest.snapshot(int(q.get("since", 0)))
        if key == ("POST", "/api/ingest/start"):
            seasons = sorted({int(s) for s in b.get("seasons", [])})
            if not seasons or not all(2018 <= s <= 2030 for s in seasons):
                raise Bad("seasons must be years between 2018 and 2030")
            if not b.get("confirm_wipe"):
                raise Bad("ingest recreates f1-* indices; confirm_wipe required")
            ingest.start(b["cluster"], seasons)
            return ingest.snapshot()
        if key == ("POST", "/api/ingest/stop"):
            ingest.stop()
            return dict(ok=True)
        if key == ("GET", "/api/keys"):
            return list_keys(client(q["cluster"]))
        if key == ("POST", "/api/keys"):
            return op_create_key(b["cluster"], b.get("label"), b.get("days", 3), b.get("patterns", []))
        if key == ("POST", "/api/keys/invalidate"):
            ids = b.get("ids") or []
            if not ids:
                raise Bad("no key ids")
            return client(b["cluster"]).security.invalidate_api_key(ids=ids).body
        if key == ("POST", "/api/indices/delete"):
            need_confirm(b)
            if ingest.running() and ingest.cluster == b["cluster"]:
                raise Bad("ingest is running against this cluster")
            return dict(deleted=delete_indices(client(b["cluster"]), b["pattern"]))
        if key == ("POST", "/api/teardown"):
            need_confirm(b)
            if ingest.running() and ingest.cluster == b["cluster"]:
                raise Bad("ingest is running against this cluster")
            return op_teardown(b["cluster"])
        raise Bad("not found")

    def do_GET(self): self.handle_any("GET")
    def do_POST(self): self.handle_any("POST")
    def do_DELETE(self): self.handle_any("DELETE")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8787)
    a = ap.parse_args()
    load_primary()
    Handler.loopback_only = a.host in ("127.0.0.1", "localhost", "::1")
    if not Handler.loopback_only:
        print("WARNING: bound to %s — this console has no login. Keep it on a trusted network." % a.host)
    print("Ops console: http://%s:%d   (primary cluster %s)" % (
        a.host, a.port, "loaded from .env" if "primary" in clusters else "not configured — add one in the UI"))
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
