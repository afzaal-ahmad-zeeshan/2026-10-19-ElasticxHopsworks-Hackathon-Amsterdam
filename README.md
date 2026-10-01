# 🏎️ Hack Night — Elastic x Hopsworks | Amsterdam

> **This repo exists only for the hackathon:** [Hack Night Amsterdam, 19 October 2026](https://www.meetup.com/elastic-nl/events/316709910/).

Build an ML-powered F1 application using real race telemetry (FastF1, 2023–2024 seasons), the Elastic Stack, and the Hopsworks Feature Store.

## Contents

| Path | Purpose |
|---|---|
| `ingest.py` | Loads FastF1 data into Elasticsearch (`pip install -r requirements.txt && python ingest.py`) |
| `ops/` | Self-hosted ops console: prime clusters, mint read-only reindex keys, clean up / tear down (`python ops/server.py`, then open http://127.0.0.1:8787) |
| `requirements.txt` | Python dependencies for the ingest script |
| `docs/` | All documentation (see below) |

## Docs

| Document | What's in it |
|---|---|
| [`docs/PARTICIPANT-GUIDE.md`](docs/PARTICIPANT-GUIDE.md) | Dataset schema, getting the data, Kibana setup, example ES\|QL queries, Hopsworks ideas, schedule, rules, judging |
| [`docs/EVENT-BRIEF.md`](docs/EVENT-BRIEF.md) | Event brief |
| [`docs/SCHIPHOL-BRIEF.md`](docs/SCHIPHOL-BRIEF.md) | Schiphol brief |
| [`docs/DATASET-COMPARISON.md`](docs/DATASET-COMPARISON.md) | Dataset comparison |
