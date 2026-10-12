"""
Cluster selection shared by ingest.py and ops/server.py.

CLUSTER=local|remote picks the LOCAL_* or REMOTE_* variable set:
    <PREFIX>_ELASTICSEARCH_URL, _API_KEY, _USERNAME, _PASSWORD
If CLUSTER is unset, the legacy ELASTICSEARCH_* variables are used.
"""
import os


def resolve(env=None):
    env = os.environ if env is None else env
    cluster = (env.get("CLUSTER") or "").strip().lower()
    if not cluster:
        if not env.get("ELASTICSEARCH_URL"):
            raise SystemExit("Set CLUSTER=local|remote (or legacy ELASTICSEARCH_URL) in .env")
        prefix = "ELASTICSEARCH_"
        cluster = "default"
    elif cluster in ("local", "remote"):
        prefix = cluster.upper() + "_ELASTICSEARCH_"
    else:
        raise SystemExit('CLUSTER must be "local" or "remote", got %r' % cluster)

    url = env.get(prefix + "URL")
    if not url:
        raise SystemExit("%sURL is required when CLUSTER=%s" % (prefix, cluster))
    cfg = dict(
        name=cluster, url=url,
        api_key=env.get(prefix + "API_KEY") or "",
        username=env.get(prefix + "USERNAME") or "",
        password=env.get(prefix + "PASSWORD") or "",
    )
    if cluster == "remote" and not cfg["api_key"] and not cfg["username"]:
        raise SystemExit("REMOTE_ELASTICSEARCH_API_KEY is required when CLUSTER=remote")
    return cfg
