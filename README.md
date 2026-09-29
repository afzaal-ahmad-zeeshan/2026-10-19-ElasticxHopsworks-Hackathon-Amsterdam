# 🏎️ Hack Night — Elastic x Hopsworks | Amsterdam

**Build an ML-powered F1 application using real race telemetry, the Elastic Stack, and the Hopsworks Feature Store.**

- 📅 **19 October 2026**
- 📍 **Amsterdam**
- ⏰ **18:00 – 21:00**
- 🎟️ **Free** — limited seats

---

## 👋 Welcome

During this Hack Night you will work with **real Formula 1 telemetry data** — every throttle input, braking point, tyre compound, and pit stop from the 2024 season — and combine it with **Elastic** for search and dashboards, and **Hopsworks** for ML feature engineering and model serving.

Build a tyre strategy advisor, a lap-time predictor, a race outcome simulator, a driver comparison tool — the limit is your creativity.

No prior experience with Elastic or Hopsworks is required. Mentors will be on hand throughout.

---

## 📊 The Dataset — F1 2024 Season

Data is sourced from [FastF1](https://github.com/theOehrly/Fast-F1), an open-source Python library that pulls from the official F1 timing feed. **No API key required.**

The data covers all 24 races of the 2024 Formula 1 season, including **Round 15 — Dutch Grand Prix at Zandvoort**.

### Index Structure

| Index | Granularity | Size |
|---|---|---|
| `f1-sessions` | 1 doc = 1 session (Race / Qualifying / Practice) | ~120 docs |
| `f1-results` | 1 doc = 1 driver × 1 session result | ~500 docs |
| `f1-laps` | 1 doc = 1 lap per driver | ~26 000 docs |
| `f1-weather` | 1 doc = 1 weather sample per session | ~5 000 docs |
| `f1-telemetry` | 1 doc = 1 telemetry sample (~4 Hz per driver) | ~10 000 000 docs |

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
| `fastest_lap_time` | float | `75.318` (seconds) |

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
| `lap_time_s` | float | `75.318` |
| `sector_1_s` | float | `19.4` |
| `sector_2_s` | float | `31.1` |
| `sector_3_s` | float | `24.8` |
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
| `speed_kmh` | integer | `287` |
| `rpm` | integer | `11200` |
| `throttle` | integer | `100` (0–100%) |
| `brake` | boolean | `false` |
| `drs` | integer | `12` (0=off, 12=open) |
| `gear` | integer | `7` |
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
| `air_temp` | float | `22.3` |
| `track_temp` | float | `38.1` |
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

### Option 2 — Self-ingest via TypeScript (slow — telemetry takes ~30–60 min)

1. Install [Node.js 20+](https://nodejs.org/).
2. Copy `.env.example` to `.env` and fill in your cluster credentials:
   ```
   ELASTICSEARCH_URL=<your-cluster-url>
   ELASTICSEARCH_API_KEY=<your-api-key>
   ```
3. Install dependencies and run:
   ```bash
   npm install
   npm run ingest
   ```
   You can also ingest individual indices:
   ```bash
   npm run ingest:sessions   # fast (~seconds)
   npm run ingest:laps       # medium (~5 min)
   npm run ingest:weather    # fast (~seconds)
   npm run ingest:telemetry  # slow (~30-60 min)
   ```
4. Verify the data loaded correctly:
   ```bash
   npm run verify
   ```

---

## 🔍 Example Queries

All queries run in **Kibana Dev Tools** or via the ES|QL tab in **Discover**.

### Top 10 drivers by average lap time at Zandvoort 2024

```esql
FROM f1-laps
| WHERE event_name == "Dutch Grand Prix" AND session_name == "Race"
| WHERE lap_time_s IS NOT NULL AND is_pit_out_lap == false AND is_pit_in_lap == false
| STATS avg_lap = AVG(lap_time_s), laps = COUNT() BY driver_code
| SORT avg_lap ASC
| LIMIT 10
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
| STATS top_speed = MAX(speed_kmh) BY driver_code
| SORT top_speed DESC
```

### Track temperature vs. fastest lap time (all 2024 races)

```esql
FROM f1-laps
| WHERE session_name == "Race" AND lap_time_s IS NOT NULL
| STATS best_lap = MIN(lap_time_s) BY round_number
```

### Throttle vs. brake profile for Verstappen at Zandvoort

```esql
FROM f1-telemetry
| WHERE event_name == "Dutch Grand Prix" AND driver_code == "VER" AND lap_number == 10
| KEEP session_time_s, speed_kmh, throttle, brake, gear, drs
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
| ✅ **Required** | Use the **F1 2024 dataset** (can combine with others) |
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
- [OpenF1 API](https://openf1.org/) — free, no-auth REST API for F1 telemetry and timing data
- [OpenF1 docs](https://openf1.org/#introduction)
- [Jolpica API](https://api.jolpi.ca/) — free F1 historical results (Ergast replacement)

### Community
- [Elastic discuss forum](https://discuss.elastic.co/)
- [Hopsworks community Slack](https://community.hopsworks.ai/)
