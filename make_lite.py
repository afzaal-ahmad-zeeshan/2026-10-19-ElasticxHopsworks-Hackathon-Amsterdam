"""
Build the *-lite indices (Dutch GP 2023 + 2024, Race + Qualifying) from the full f1-* indices
on the same cluster. Drops and recreates the -lite indices only; full indices are never touched.

Usage: CLUSTER=remote python make_lite.py   (uses the same .env as ingest.py)
"""
import time
from dotenv import load_dotenv
load_dotenv()
from elasticsearch import Elasticsearch
from es_config import resolve

cfg = resolve()
es = (Elasticsearch(cfg["url"], api_key=cfg["api_key"]) if cfg["api_key"]
      else Elasticsearch(cfg["url"], basic_auth=(cfg["username"], cfg["password"])))

INDICES = ["f1-sessions", "f1-results", "f1-laps", "f1-weather", "f1-telemetry"]
QUERY = {"bool": {"filter": [
    {"term": {"event_name": "Dutch Grand Prix"}},
    {"terms": {"season": [2023, 2024]}},
    {"terms": {"session_name": ["Race", "Qualifying"]}},
]}}

for src in INDICES:
    lite = src + "-lite"
    if es.indices.exists(index=lite):
        es.indices.delete(index=lite)
    mappings = es.indices.get_mapping(index=src)[src]["mappings"]
    es.indices.create(index=lite, mappings=mappings)
    task = es.reindex(source={"index": src, "query": QUERY, "size": 5000},
                      dest={"index": lite}, wait_for_completion=False)["task"]
    while not es.tasks.get(task_id=task)["completed"]:
        time.sleep(5)
    es.indices.refresh(index=lite)
    print(f"{lite}: {es.count(index=lite)['count']:,}")
