# 🏎️ Hack Night Elastic x Hopsworks — Formula 1 Edition

**Build an ML-powered F1 application using real race telemetry, the Elastic Stack, and the Hopsworks Feature Store!**

* 📅 **19 October 2026**
* 📍 **Amsterdam** — [event page](https://www.meetup.com/elastic-nl/events/316709910/)
* ⏰ **18:00 – 21:00**
* 🎟️ **Free** — limited seats

> **This repo exists only for the hackathon.**

## 👋 Welcome

During this Hack Night you will work with **real Formula 1 data** from the Dutch Grand Prix at Zandvoort in 2023 and 2024 ([FastF1](https://github.com/theOehrly/Fast-F1)): every throttle input, braking point, tyre compound and pit stop. You will combine it with the **Elastic Stack** (search, ES|QL, Kibana, Agent Builder) and the **Hopsworks Feature Store** (feature engineering, model training and serving) to build something great in a few hours.

It could be a tyre strategy advisor, a lap-time predictor, a race outcome simulator, a driver comparison tool. The limit is your creativity!

**No prior experience with Elastic or Hopsworks is required.** Mentors will be around throughout the event to help you.

## 🚀 Set up your environment

1. [Create a free Elastic Cloud account](https://ela.st/hack-night-elastic-hopsworks-2026) or log in to your existing one.
2. Create an **Elasticsearch Serverless** project (or a hosted deployment).
3. Once it is created, open **Kibana** from the project page.
4. [Create a free Hopsworks account](https://run.hopsworks.ai/) and create a project for the hackathon. Generate an API key for the Python SDK.
5. Install **Python 3.10+** on your laptop. It is required: the Hopsworks Python SDK (`hopsworks`) runs on it, and you need it to build your feature pipelines.

**Note:** if you do not want to create an account, we can provide temporary credentials to access a shared Elastic Cloud deployment and Hopsworks cluster.

## 🚀 Get the data

### Use our pre-filled cluster (recommended, a few minutes)

Open **Kibana Dev Tools** (`/app/dev_tools`) of your deployment and run the commands below to create the indices and copy the data from our public Elastic Cloud deployment.

The public **READONLY** API key and the source cluster URL will be shared during the session. In the commands below, replace `<SOURCE_CLUSTER_URL>` and `<ELASTICSEARCH_API_KEY>` with those values.

To get you started quickly, the pre-filled cluster holds a **lite** version of the dataset: the **Dutch Grand Prix at Zandvoort in 2023 and 2024** (Race and Qualifying), about **2.9 million documents** in total. The source indices are called `f1-*-lite`, and the commands below copy them into indices called `f1-*` in your deployment, so all queries and examples in this guide use the plain `f1-*` names.

> **Shortcut:** all the commands for the five indices are also in [`docs/reindex-all.kibana.txt`](docs/reindex-all.kibana.txt). Paste the whole file into Kibana Dev Tools, replace the two placeholders, select everything and click Run.

#### f1-sessions (4 documents)

```js
DELETE f1-sessions
PUT f1-sessions
{
  "mappings": {"properties": {
    "season":       {"type": "integer"},
    "round_number": {"type": "integer"},
    "session_key":  {"type": "integer"},
    "event_name":   {"type": "keyword"},
    "country":      {"type": "keyword"},
    "location":     {"type": "keyword"},
    "circuit_name": {"type": "keyword"},
    "session_name": {"type": "keyword"},
    "session_type": {"type": "keyword"},
    "session_date": {"type": "date", "format": "strict_date_optional_time"}
  }}
}
POST _reindex?wait_for_completion=false
{
  "source": {
    "remote": {
      "host": "<SOURCE_CLUSTER_URL>",
      "api_key": "<ELASTICSEARCH_API_KEY>"
    },
    "index": "f1-sessions-lite"
  },
  "dest": { "index": "f1-sessions" }
}
```

#### f1-results (80 documents)

```js
DELETE f1-results
PUT f1-results
{
  "mappings": {"properties": {
    "season":         {"type": "integer"},
    "round_number":   {"type": "integer"},
    "event_name":     {"type": "keyword"},
    "session_name":   {"type": "keyword"},
    "driver_number":  {"type": "integer"},
    "driver_code":    {"type": "keyword"},
    "full_name":      {"type": "keyword"},
    "team_name":      {"type": "keyword"},
    "position":       {"type": "integer"},
    "points":         {"type": "float"},
    "grid_position":  {"type": "integer"},
    "status":         {"type": "keyword"},
    "fastest_lap_ms": {"type": "integer"}
  }}
}
POST _reindex?wait_for_completion=false
{
  "source": {
    "remote": {
      "host": "<SOURCE_CLUSTER_URL>",
      "api_key": "<ELASTICSEARCH_API_KEY>"
    },
    "index": "f1-results-lite"
  },
  "dest": { "index": "f1-results" }
}
```

#### f1-laps (3,531 documents)

```js
DELETE f1-laps
PUT f1-laps
{
  "mappings": {"properties": {
    "season":            {"type": "integer"},
    "round_number":      {"type": "integer"},
    "session_key":       {"type": "integer"},
    "event_name":        {"type": "keyword"},
    "session_name":      {"type": "keyword"},
    "driver_number":     {"type": "integer"},
    "driver_code":       {"type": "keyword"},
    "team_name":         {"type": "keyword"},
    "lap_number":        {"type": "integer"},
    "lap_duration_ms":   {"type": "integer"},
    "duration_sector_1": {"type": "integer"},
    "duration_sector_2": {"type": "integer"},
    "duration_sector_3": {"type": "integer"},
    "compound":          {"type": "keyword"},
    "tyre_life":         {"type": "integer"},
    "is_pit_out_lap":    {"type": "boolean"},
    "is_pit_in_lap":     {"type": "boolean"},
    "track_status":      {"type": "keyword"},
    "position":          {"type": "integer"}
  }}
}
POST _reindex?wait_for_completion=false
{
  "source": {
    "remote": {
      "host": "<SOURCE_CLUSTER_URL>",
      "api_key": "<ELASTICSEARCH_API_KEY>"
    },
    "index": "f1-laps-lite"
  },
  "dest": { "index": "f1-laps" }
}
```

#### f1-weather (541 documents)

```js
DELETE f1-weather
PUT f1-weather
{
  "mappings": {"properties": {
    "season":            {"type": "integer"},
    "round_number":      {"type": "integer"},
    "session_key":       {"type": "integer"},
    "event_name":        {"type": "keyword"},
    "session_name":      {"type": "keyword"},
    "session_time_s":    {"type": "float"},
    "air_temperature":   {"type": "float"},
    "track_temperature": {"type": "float"},
    "humidity":          {"type": "float"},
    "pressure":          {"type": "float"},
    "wind_speed":        {"type": "float"},
    "wind_direction":    {"type": "integer"},
    "rainfall":          {"type": "boolean"}
  }}
}
POST _reindex?wait_for_completion=false
{
  "source": {
    "remote": {
      "host": "<SOURCE_CLUSTER_URL>",
      "api_key": "<ELASTICSEARCH_API_KEY>"
    },
    "index": "f1-weather-lite"
  },
  "dest": { "index": "f1-weather" }
}
```

#### f1-telemetry (2,869,213 documents)

```js
DELETE f1-telemetry
PUT f1-telemetry
{
  "mappings": {"properties": {
    "season":         {"type": "integer"},
    "round_number":   {"type": "integer"},
    "session_key":    {"type": "integer"},
    "event_name":     {"type": "keyword"},
    "session_name":   {"type": "keyword"},
    "driver_number":  {"type": "integer"},
    "driver_code":    {"type": "keyword"},
    "team_name":      {"type": "keyword"},
    "lap_number":     {"type": "integer"},
    "session_time_s": {"type": "float"},
    "speed":          {"type": "integer"},
    "rpm":            {"type": "integer"},
    "throttle":       {"type": "integer"},
    "brake":          {"type": "boolean"},
    "drs":            {"type": "integer"},
    "n_gear":         {"type": "integer"},
    "x":              {"type": "float"},
    "y":              {"type": "float"},
    "z":              {"type": "float"}
  }}
}
POST _reindex?wait_for_completion=false
{
  "source": {
    "remote": {
      "host": "<SOURCE_CLUSTER_URL>",
      "api_key": "<ELASTICSEARCH_API_KEY>"
    },
    "index": "f1-telemetry-lite"
  },
  "dest": { "index": "f1-telemetry" }
}
```

Telemetry is the biggest one (2.9 million documents). Follow the progress of each reindex with `GET _tasks/<task_id>` and check the counts when it is done:

```
GET _cat/indices/f1-*?v&h=index,docs.count&s=index
```

### Index the full dataset yourself (very long!)

Create a `.env` file at the root of the project (start from `.env.example`) with your deployment details:

```bash
ELASTICSEARCH_URL=<ELASTICSEARCH_URL>
ELASTICSEARCH_API_KEY=<ELASTICSEARCH_API_KEY>
```

1. **Install Python 3.10+** on your computer.
2. Install the dependencies: `pip install -r requirements.txt`
3. Run `python ingest.py` to fetch the data from FastF1 and index it into your deployment.

This loads the **full** dataset (every Race and Qualifying session of 2023 and 2024, about 57 million telemetry documents), not the lite version above. Approximate times:

* sessions + results: < 1 minute
* laps: ~5 minutes
* weather: ~1 minute
* telemetry: ~2 hours per season (~28M docs per season); the full 2023 + 2024 load took about 4 hours

### Description of the data

The pre-filled lite dataset covers the **Race and Qualifying** sessions of the **Dutch Grand Prix at Zandvoort** in **2023 (round 13)** and **2024 (round 15)**, 4 sessions in total. The data comes from FastF1, and no API key is required for it. If you want other circuits, run `ingest.py` yourself (see above) to load the full 2023 and 2024 seasons.

| Index | Documents in the lite set |
| --- | --- |
| `f1-sessions` | 4 |
| `f1-results` | 80 |
| `f1-laps` | 3,531 |
| `f1-weather` | 541 |
| `f1-telemetry` | 2,869,213 |

Every lap in `f1-laps` has matching telemetry in `f1-telemetry`. Join on `season`, `round_number`, `session_name`, `driver_code` and `lap_number`. Laps with `lap_duration_ms` empty (out laps, in laps, aborted laps) still have telemetry.

| Index | Granularity | Content |
| --- | --- | --- |
| `f1-sessions` | 1 doc = 1 session | Race calendar and session metadata |
| `f1-results` | 1 doc = 1 driver × 1 session | Final classification, grid, points, status |
| `f1-laps` | 1 doc = 1 lap per driver | Lap and sector times, tyre compound, tyre life, pit flags |
| `f1-weather` | 1 doc = 1 weather sample (~1 per minute) | Air and track temperature, humidity, wind, rain |
| `f1-telemetry` | 1 doc = 1 telemetry sample (~10 Hz per driver) | Speed, RPM, throttle, brake, DRS, gear, track coordinates |

> Tyre data (compound, tyre life, pit in/out flags) lives in `f1-laps`, not in a separate index.

Only `f1-sessions` has a real calendar date (`session_date`). The other indices store the **relative session time** (`session_time_s`), so the Kibana time filter is not useful for them. Filter by `season`, `round_number`, `event_name` or `session_name` instead.

The full field reference for every index is in [`docs/PARTICIPANT-GUIDE.md`](docs/PARTICIPANT-GUIDE.md).

#### `f1-laps`: sample document

| Field | Value |
| --- | --- |
| `event_name` | Dutch Grand Prix |
| `session_name` | Race |
| `driver_code` | VER |
| `team_name` | Red Bull Racing |
| `lap_number` | 32 |
| `lap_duration_ms` | 75318 |
| `compound` | SOFT |
| `tyre_life` | 8 |
| `is_pit_out_lap` | false |
| `position` | 1 |

### Use the data

Here are a few ideas to get you started. Run them in **Kibana Dev Tools** or in the ES|QL tab of **Discover**.

Check that all four sessions are there (2023 and 2024, Race and Qualifying):

```json
POST _query?format=txt
{
  "query": """
    FROM f1-sessions
    | STATS sessions = COUNT() BY season
    | SORT season
  """
}
```

```txt
season | sessions
-------+---------
2023   | 2
2024   | 2
```

Top 10 drivers by average clean-lap time in the 2024 Dutch GP:

```esql
FROM f1-laps
| WHERE season == 2024 AND session_name == "Race"
| WHERE lap_duration_ms IS NOT NULL AND is_pit_out_lap == false AND is_pit_in_lap == false
| STATS avg_lap_ms = AVG(lap_duration_ms), laps = COUNT() BY driver_code
| EVAL avg_lap_s = ROUND(avg_lap_ms / 1000.0, 3)
| SORT avg_lap_ms ASC
| LIMIT 10
| KEEP driver_code, avg_lap_s, laps
```

Tyre compound usage in the Dutch GP races of 2023 and 2024:

```esql
FROM f1-laps
| WHERE session_name == "Race"
| STATS laps = COUNT() BY compound, season
| SORT season, compound
```

Top speed per driver in the 2024 Dutch GP race:

```esql
FROM f1-telemetry
| WHERE season == 2024 AND session_name == "Race"
| STATS top_speed = MAX(speed) BY driver_code
| SORT top_speed DESC
```

Throttle and brake profile of Verstappen on lap 10 at Zandvoort:

```esql
FROM f1-telemetry
| WHERE season == 2024 AND session_name == "Race"
  AND driver_code == "VER" AND lap_number == 10
| KEEP session_time_s, speed, throttle, brake, n_gear, drs
| SORT session_time_s
```

### Kibana data views

Before using **Lens**, **Discover** or **Dashboards**, create a data view for each index. In Dev Tools:

```
POST kbn:/api/data_views/data_view
{"data_view": {"title": "f1-sessions", "name": "f1-sessions", "timeFieldName": "session_date"}}
```

Repeat with `f1-results`, `f1-laps`, `f1-weather` and `f1-telemetry` (without `timeFieldName`).

The data is from 2023–2024, so set the time picker to **Absolute**, from `2023-01-01` to `2024-12-31`, otherwise `f1-sessions` looks empty.

## 🧠 The Hopsworks angle

[Hopsworks](https://www.hopsworks.ai/) is an open-source Feature Store and MLOps platform. In this hackathon you **must use at least one Hopsworks Feature Group**.

```
FastF1 raw data
      │
      ├─► Elasticsearch ──► Kibana dashboards + search + Agent Builder
      │
      └─► Hopsworks Feature Pipeline
              │
              ├─ Feature Group: tyre_degradation_features
              ├─ Feature Group: driver_form_features
              │
              └─► Feature View (point-in-time join)
                        │
                        ├─► Train a model (pit stop prediction / lap time regression)
                        │
                        └─► Model Registry → Deploy → serve predictions
                                    │
                                    └─► Push results back to Elasticsearch
```

| Feature Group | Key features | ML task |
| --- | --- | --- |
| `tyre_degradation` | tyre_life, compound, lap_delta, track_temp | Predict the optimal pit lap |
| `driver_form` | rolling_avg_lap, sector_consistency, gap_to_leader | Race outcome prediction |
| `weather_risk` | track_temp_delta, rainfall_prob, wind_speed | Safety car probability |
| `sector_performance` | sector 1/2/3 split vs. driver average | Qualifying position prediction |

We will provide you with access to the F1 2023/2024 dataset in Hopsworks by us sharing the tables with your Hopsworks project. The easiest way to start with Hopsworks is if you have a Claude/Codex/Copilot, you can use the hops CLI. If you don't have a coding agent subscription, we can provide credits to DeepSeek for the evening. You can also build an App (Python/Javascript) on Hopsworks to visualize your ML predictions or anything else. 


## 🗓️ Agenda

| Time | Activity |
| --------- | ----------- |
| 18:00 – 18:15 | 🎤 Introduction + demo |
| 18:15 – 20:15 | 💻🍕 Hack time and pizza |
| 20:15 – 20:45 | 🎬 Project presentations + vote |
| 20:45 – 21:00 | 🏆 Awards + closing |

## 📋 Challenge rules

### Teams

* **1 to 4 people** per team (individual registrations are also welcome).
* Form your team on site or come with a ready-made team.

### What is allowed / not allowed

* ✅ **Required**: use **Elastic** (search, ES|QL, dashboards or **Agent Builder**).
* ✅ **Required**: use **Hopsworks**, with at least one Feature Group.
* ✅ **Required**: use the **F1 2023/2024 dataset**. You can combine it with other datasets.
* ✅ You can combine with other tools and libraries (LangChain, Streamlit, Plotly, etc.).
* ✅ Research and ideas can be prepared before the event.
* ❌ **Code on the day only**: no ready-to-use repository.

### Final presentation

* **5 minutes** per team (live demo + explanation).
* Show what you built, how it works, and how you used Elastic and Hopsworks.

### Judging criteria

| Criterion | What the judges look for |
| --------- | -------------------------------- |
| 🎨 **Creativity** | Originality of the idea |
| ⚙️ **Functionality** | Does it actually work? |
| 🔍 **Elastic use** | How well did you use search, dashboards or AI features? |
| 🧠 **Hopsworks use** | Quality of the feature engineering and ML pipeline |
| 📊 **Data depth** | How well did you explore the F1 dataset? |
| 🎬 **Presentation** | Clarity and quality of the demo |

### Jury

* **Elastic**
* **Hopsworks**
* **Popular vote** from the participants

## 🛠️ Useful resources

### Elastic

* 📖 [Agent Builder documentation](https://www.elastic.co/docs/explore-analyze/ai-features/agent-builder)
* 📊 [ES|QL guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/esql.html)
* 🔬 [Elasticsearch Labs](https://www.elastic.co/search-labs): tutorials, examples and technical articles

### Hopsworks

* 📖 [Hopsworks documentation](https://docs.hopsworks.ai/)
* 🧪 [Feature Store tutorials](https://docs.hopsworks.ai/latest/tutorials/)
* 🐍 [Python SDK (hopsworks)](https://pypi.org/project/hopsworks/)

### Data

* 🏎️ [FastF1 Python library](https://github.com/theOehrly/Fast-F1)
* 📚 [FastF1 documentation](https://docs.fastf1.dev/)

### Community

* 💬 [Elastic Discuss forum](https://discuss.elastic.co/)
* 💬 [Hopsworks community](https://community.hopsworks.ai/)

## 📁 Repository contents

| Path | Purpose |
|---|---|
| `ingest.py` | Loads FastF1 data into Elasticsearch (`pip install -r requirements.txt && python ingest.py`) |
| `ops/` | Self-hosted ops console for the organizers: prime clusters, mint read-only reindex keys, clean up / tear down (`python ops/server.py`, then open http://127.0.0.1:8787) |
| `requirements.txt` | Python dependencies for the ingest script |
| `docs/` | Detailed documentation, see below |

| Document | What's in it |
|---|---|
| [`docs/PARTICIPANT-GUIDE.md`](docs/PARTICIPANT-GUIDE.md) | Full dataset schema, Kibana setup, more ES\|QL queries, Hopsworks ideas, schedule, rules, judging |
| [`docs/EVENT-BRIEF.md`](docs/EVENT-BRIEF.md) | Event brief |
