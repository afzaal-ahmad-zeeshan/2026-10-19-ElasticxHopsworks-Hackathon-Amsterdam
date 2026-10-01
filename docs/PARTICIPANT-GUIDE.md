# 🏎️ Hack Night — Elastic x Hopsworks | Amsterdam

**Build an ML-powered F1 application using real race telemetry, the Elastic Stack, and the Hopsworks Feature Store.**

- 📅 **19 October 2026**
- 📍 **Amsterdam**
- ⏰ **18:00 – 21:00**
- 🎟️ **Free** — limited seats

---

## 👋 Welcome

During this Hack Night you will work with **real Formula 1 telemetry data** — every throttle input, braking point, tyre compound, and pit stop from the 2023 and 2024 seasons — and combine it with **Elastic** for search and dashboards, and **Hopsworks** for ML feature engineering and model serving.

Build a tyre strategy advisor, a lap-time predictor, a race outcome simulator, a driver comparison tool — the limit is your creativity.

No prior experience with Elastic or Hopsworks is required. Mentors will be on hand throughout.

---

## 📊 The Dataset — F1 2023 & 2024 Seasons

Data is sourced from [FastF1](https://github.com/theOehrly/Fast-F1), an open-source Python library that pulls from the official F1 timing feed. **No API key required.**

The data covers all Race and Qualifying sessions across the **2023 season (22 rounds)** and **2024 season (24 rounds)**, including **Round 15 of 2024 — Dutch Grand Prix at Zandvoort**.

### Index Structure

Data covers the **2023 and 2024 F1 seasons** (46 rounds total), **Race and Qualifying** sessions — 92 sessions, 20 drivers each.

| Index | Granularity | Actual docs (fully ingested) |
|---|---|---|
| `f1-sessions` | 1 doc = 1 session | **93** |
| `f1-results` | 1 doc = 1 driver × 1 session | **1,858** |
| `f1-laps` | 1 doc = 1 lap per driver | **67,110** |
| `f1-weather` | 1 doc = 1 weather sample (~1 per min) | **11,391** |
| `f1-telemetry` | 1 doc = 1 telemetry sample (~10 Hz per driver) | **57,353,359** |

> **Tyre data** (compound, tyre life, pit in/out lap flags) is embedded in `f1-laps`, not a separate index.
> FastF1 samples telemetry at up to **10 Hz** per driver — higher than the advertised 4 Hz — which is why the telemetry volume is ~57M rows rather than the ~18M initially estimated.

#### Verify your setup

**Step 1 — Check total document counts**

Run this in **Kibana Dev Tools** (`/app/dev_tools`):

```
GET _cat/indices/f1-*?v&h=index,docs.count&s=index
```

Expected output (fully ingested):

```
index           docs.count
f1-laps              67110
f1-results            1858
f1-sessions             93
f1-telemetry      57353359
f1-weather           11391
```

**Step 2 — Confirm all rounds are present per season**

Run each query separately in Dev Tools. 2023 should have 22 rounds, 2024 should have 24:

```esql
FROM f1-sessions
| STATS rounds = COUNT_DISTINCT(round_number) BY season
| SORT season
```

Expected:

```
season | rounds
2023   | 22
2024   | 24
```

**Step 3 — Confirm both session types per round**

```esql
FROM f1-sessions
| STATS session_count = COUNT() BY season, session_name
| SORT season, session_name
```

Expected:

```
season | session_name | session_count
2023   | Qualifying   | 22
2023   | Race         | 22
2024   | Qualifying   | 24
2024   | Race         | 24
```

**Step 4 — Spot-check telemetry coverage**

Confirms the Dutch GP (the key race for this event) is fully present:

```esql
FROM f1-telemetry
| WHERE event_name == "Dutch Grand Prix"
| STATS samples = COUNT(), drivers = COUNT_DISTINCT(driver_code) BY season, session_name
| SORT season, session_name
```

Expected: 20 drivers and 150,000–350,000 samples per session.

#### `f1-sessions` — Race calendar & session metadata

| Field | Type | Example |
|---|---|---|
| `season` | integer | `2024` |
| `round_number` | integer | `15` |
| `country` | keyword | `Netherlands` |
| `location` | keyword | `Zandvoort` |
| `event_name` | keyword | `Dutch Grand Prix` |
| `session_name` | keyword | `Race` |
| `session_date` | date | `2024-08-25` |

#### `f1-results` — Driver session results

| Field | Type | Example |
|---|---|---|
| `season` | integer | `2024` |
| `round_number` | integer | `15` |
| `event_name` | keyword | `Dutch Grand Prix` |
| `session_name` | keyword | `Race` |
| `driver_number` | integer | `1` |
| `driver_code` | keyword | `VER` |
| `full_name` | keyword | `Max Verstappen` |
| `team_name` | keyword | `Red Bull Racing` |
| `position` | integer | `1` |
| `points` | float | `25.0` |
| `grid_position` | integer | `1` |
| `status` | keyword | `Finished` |
| `fastest_lap_ms` | integer | `75318` (milliseconds) |

#### `f1-laps` — Per-driver lap data

| Field | Type | Example |
|---|---|---|
| `season` | integer | `2024` |
| `round_number` | integer | `15` |
| `event_name` | keyword | `Dutch Grand Prix` |
| `session_name` | keyword | `Race` |
| `driver_code` | keyword | `VER` |
| `team_name` | keyword | `Red Bull Racing` |
| `lap_number` | integer | `32` |
| `lap_duration_ms` | integer | `75318` (milliseconds) |
| `duration_sector_1` | integer | `19400` |
| `duration_sector_2` | integer | `31100` |
| `duration_sector_3` | integer | `24800` |
| `compound` | keyword | `SOFT` |
| `tyre_life` | integer | `8` |
| `is_pit_out_lap` | boolean | `false` |
| `is_pit_in_lap` | boolean | `false` |
| `track_status` | keyword | `1` |
| `position` | integer | `1` |

#### `f1-telemetry` — High-frequency car data (the big one)

| Field | Type | Example |
|---|---|---|
| `season` | integer | `2024` |
| `round_number` | integer | `15` |
| `event_name` | keyword | `Dutch Grand Prix` |
| `session_name` | keyword | `Race` |
| `driver_code` | keyword | `VER` |
| `team_name` | keyword | `Red Bull Racing` |
| `lap_number` | integer | `32` |
| `session_time_s` | float | `4521.3` |
| `speed` | integer | `287` (km/h) |
| `rpm` | integer | `11200` |
| `throttle` | integer | `100` (0–100%) |
| `brake` | boolean | `false` |
| `drs` | integer | `12` (0=off, 12=open) |
| `n_gear` | integer | `7` |
| `x` | float | `123.4` (track coordinates) |
| `y` | float | `-56.7` |
| `z` | float | `0.2` |

#### `f1-weather` — Weather conditions

| Field | Type | Example |
|---|---|---|
| `season` | integer | `2024` |
| `round_number` | integer | `15` |
| `event_name` | keyword | `Dutch Grand Prix` |
| `session_name` | keyword | `Race` |
| `session_time_s` | float | `1800.0` |
| `air_temperature` | float | `22.3` |
| `track_temperature` | float | `38.1` |
| `humidity` | float | `61.0` |
| `pressure` | float | `1012.3` |
| `wind_speed` | float | `3.1` |
| `wind_direction` | integer | `220` |
| `rainfall` | boolean | `false` |

---

## 🚀 Get the Data

### Option 1 — Reindex from pre-filled cluster (recommended, ~minutes)

Open the **Kibana Dev Tools** console (`/app/dev_tools`) of your deployment and run the following for each index. Replace `<READONLY_API_KEY>` with the key displayed during the session.

```js
POST _reindex?wait_for_completion=false
{
  "source": {
    "remote": {
      "host": "https://<SOURCE_CLUSTER>.es.<region>.elastic.cloud:443",
      "api_key": "<READONLY_API_KEY>"
    },
    "index": "f1-sessions"
  },
  "dest": { "index": "f1-sessions" }
}
```

Repeat for `f1-results`, `f1-laps`, `f1-weather`, and `f1-telemetry`.

### Option 2 — Self-ingest via Python + FastF1 (slow — telemetry takes ~1–2 hours)

1. Install Python 3.9+.
2. Copy `.env.example` to `.env` and fill in your cluster credentials:
   ```
   ELASTICSEARCH_URL=<your-cluster-url>
   ELASTICSEARCH_API_KEY=<your-api-key>
   ```
3. Install dependencies and run the ingest:
   ```bash
   pip install -r requirements.txt
   python ingest.py
   ```

Approximate ingest times per season:
- Sessions + results: < 1 minute
- Laps: ~5 minutes
- Weather: ~1 minute
- Telemetry: ~1–2 hours (the big one — ~10M docs per season)

---

## 🗂️ Kibana Data Views

Before using **Lens**, **Discover**, or **Dashboards** in Kibana, you need to create a Data View for each index.

### Why most indices have no time field

Only `f1-sessions` has a true calendar date (`session_date`). The other indices store **relative session time** (`session_time_s` — seconds elapsed since session start), not absolute timestamps. This is how FastF1 exposes the data — absolute timestamps are not available per lap or per telemetry sample without a custom join against session start times.

**Practical consequence:** For `f1-laps`, `f1-weather`, `f1-telemetry`, and `f1-results`, the Kibana time filter does nothing useful. Filter by `season`, `round_number`, `event_name`, or `session_name` instead.

### Create data views via Dev Tools

Open **Kibana Dev Tools** (`/app/dev_tools`) and run each block separately:

```
POST kbn:/api/data_views/data_view
{"data_view": {"title": "f1-sessions", "name": "f1-sessions", "timeFieldName": "session_date"}}
```

```
POST kbn:/api/data_views/data_view
{"data_view": {"title": "f1-results", "name": "f1-results"}}
```

```
POST kbn:/api/data_views/data_view
{"data_view": {"title": "f1-laps", "name": "f1-laps"}}
```

```
POST kbn:/api/data_views/data_view
{"data_view": {"title": "f1-weather", "name": "f1-weather"}}
```

```
POST kbn:/api/data_views/data_view
{"data_view": {"title": "f1-telemetry", "name": "f1-telemetry"}}
```

### Or create them manually

Go to **Stack Management → Data Views → Create data view**:

| Data view | Index pattern | Time field |
|---|---|---|
| `f1-sessions` | `f1-sessions` | `session_date` |
| `f1-results` | `f1-results` | *(none)* |
| `f1-laps` | `f1-laps` | *(none)* |
| `f1-weather` | `f1-weather` | *(none)* |
| `f1-telemetry` | `f1-telemetry` | *(none)* |

### Set the Kibana time range

`f1-sessions` uses `session_date` so the global time picker applies to it. The data is from **2023–2024**, which is outside Kibana's default "Last 15 minutes" window — this is why the index appears empty on first load.

**Fix:** In the top-right time picker, click **Absolute**, and set:
- Start: `2023-01-01T00:00:00.000Z`
- End: `2024-12-31T23:59:59.999Z`

> This covers all 46 race weekends. A narrower range like `2023-09-29` → `2024-09-29` will show data but will miss early-season 2023 rounds (Bahrain GP is in March).

Or paste this into Dev Tools to set it as the Kibana-wide default for all sessions:

```
PUT kbn:/api/saved_objects/config/9.5.4
{
  "attributes": {
    "timepicker:timeDefaults": "{\"from\":\"2023-01-01T00:00:00.000Z\",\"to\":\"2024-12-31T23:59:59.999Z\"}"
  }
}
```

> **If fields still appear empty** after setting the time range, confirm the ingest has completed for that index (`GET _cat/indices/f1-*?v`) and refresh the data view in **Stack Management → Data Views**.

Once set up, all five indices will appear in **Lens** (`/app/lens`), **Discover** (`/app/discover`), and the **Dashboard** editor.

---

## 🔍 Example Queries

All queries run in **Kibana Dev Tools** or via the ES|QL tab in **Discover**.

### Top 10 drivers by average lap time at Zandvoort 2024

```esql
FROM f1-laps
| WHERE event_name == "Dutch Grand Prix" AND session_name == "Race"
| WHERE lap_duration_ms IS NOT NULL AND is_pit_out_lap == false AND is_pit_in_lap == false
| STATS avg_lap_ms = AVG(lap_duration_ms), laps = COUNT() BY driver_code
| EVAL avg_lap_s = ROUND(avg_lap_ms / 1000.0, 3)
| SORT avg_lap_ms ASC
| LIMIT 10
| KEEP driver_code, avg_lap_s, laps
```

### Tyre compound strategy across the 2024 season

```esql
FROM f1-laps
| WHERE session_name == "Race"
| STATS laps = COUNT() BY compound, round_number
| SORT round_number, compound
```

### Max speed per driver in the Dutch GP race

```esql
FROM f1-telemetry
| WHERE event_name == "Dutch Grand Prix" AND session_name == "Race"
| STATS top_speed = MAX(speed) BY driver_code
| SORT top_speed DESC
```

### Track temperature vs. fastest lap time (all races)

```esql
FROM f1-laps
| WHERE season == 2024 AND session_name == "Race" AND lap_duration_ms IS NOT NULL
| STATS best_lap_ms = MIN(lap_duration_ms) BY round_number
| EVAL best_lap_s = ROUND(best_lap_ms / 1000.0, 3)
| SORT round_number
| KEEP round_number, best_lap_s
```

### Throttle vs. brake profile for Verstappen at Zandvoort

```esql
FROM f1-telemetry
| WHERE event_name == "Dutch Grand Prix" AND session_name == "Race"
  AND driver_code == "VER" AND lap_number == 10
| KEEP session_time_s, speed, throttle, brake, n_gear, drs
| SORT session_time_s
```

---

## 🧠 The Hopsworks Angle

[Hopsworks](https://www.hopsworks.ai/) is an open-source Feature Store and MLOps platform. In this hackathon it is **mandatory to use at least one Hopsworks Feature Group**.

### Suggested workflow

```
FastF1 raw data
      │
      ├─► Elasticsearch ──► Kibana dashboards + search
      │
      └─► Hopsworks Feature Pipeline
              │
              ├─ Feature Group: tyre_degradation_features
              │    (compound, tyre_life, lap_delta, track_temp per lap)
              │
              ├─ Feature Group: driver_form_features
              │    (rolling avg lap time, sector consistency, position trend)
              │
              └─► Feature View (point-in-time join)
                        │
                        ├─► Train model (pit stop prediction / lap time regression)
                        │
                        └─► Hopsworks Model Registry → Deploy → serve predictions
                                    │
                                    └─► Push results back to Elasticsearch
```

### Ideas for feature groups

| Feature Group | Key Features | ML Task |
|---|---|---|
| `tyre_degradation` | tyre_life, compound, lap_delta, track_temp | Predict optimal pit lap |
| `driver_form` | rolling_avg_lap, sector_consistency, gap_to_leader | Race outcome prediction |
| `weather_risk` | track_temp_delta, rainfall_prob, wind_speed | Safety car probability |
| `sector_performance` | sector_1/2/3 split vs. driver average | Qualifying position prediction |

---

## 🗓️ Schedule

| Time | Activity |
|---|---|
| 18:00 – 18:15 | Intro + live demo |
| 18:15 – 20:15 | Hack time + food |
| 20:15 – 20:45 | Team demos + vote |
| 20:45 – 21:00 | Prizes + close |

---

## 📋 Rules

### Teams
- 1 to 4 people. Form on the day or come ready.

### What's required / not allowed

| | |
|---|---|
| ✅ **Required** | Use **Elastic** (search, dashboards, or Agent Builder) |
| ✅ **Required** | Use **Hopsworks** — at least one Feature Group |
| ✅ **Required** | Use the **F1 2023/2024 dataset** (can combine with others) |
| ✅ Allowed | LangChain, Streamlit, Plotly, other open-source tools |
| ✅ Allowed | Research and ideas prepared before the event |
| ❌ Not allowed | Pre-written code repos — code on the day only |

### Final demo
- 5 minutes per team: live demo + explanation
- Show what you built, how it works, and how you used Elastic + Hopsworks

### Judging criteria

| Criterion | What judges look for |
|---|---|
| 🎨 Creativity | Originality of the idea |
| ⚙️ Functionality | Does it actually work? |
| 🔍 Elastic use | How well did you exploit search, dashboards, or AI features? |
| 🧠 Hopsworks use | Quality of feature engineering and ML pipeline |
| 📊 Data depth | How well did you explore the F1 dataset? |
| 🎬 Presentation | Clarity and quality of the demo |

---

## 🛠️ Resources

### Elastic
- [Agent Builder docs](https://www.elastic.co/docs/explore-analyze/ai-features/agent-builder)
- [ES|QL reference](https://www.elastic.co/guide/en/elasticsearch/reference/current/esql.html)
- [Elasticsearch Labs](https://www.elastic.co/search-labs)

### Hopsworks
- [Hopsworks docs](https://docs.hopsworks.ai/)
- [Feature Store quickstart](https://docs.hopsworks.ai/latest/tutorials/)
- [Python SDK (hsfs)](https://pypi.org/project/hsfs/)

### Data
- [FastF1 Python library](https://github.com/theOehrly/Fast-F1) — free, no-auth, covers 2018–present
- [FastF1 docs](https://docs.fastf1.dev/)

### Community
- [Elastic discuss forum](https://discuss.elastic.co/)
- [Hopsworks community Slack](https://community.hopsworks.ai/)
