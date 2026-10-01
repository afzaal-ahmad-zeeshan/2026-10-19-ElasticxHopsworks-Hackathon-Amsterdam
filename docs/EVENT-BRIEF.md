# Hack Night: Elastic × Hopsworks — Amsterdam
### 19 October 2026 · Amsterdam

---

## The Pitch

Formula 1 generates more data per race than most companies produce in a year. Every corner, every gear change, every tyre degradation curve is captured at 4 Hz across 20 cars for the full race distance.

On October 19 we hand that data to developers in Amsterdam and ask a simple question: **what can you build in two hours?**

---

## The Data

We're using the **official F1 timing feed** via [FastF1](https://github.com/theOehrly/Fast-F1) — the same source the teams themselves use. Two full seasons (2023 + 2024), Race and Qualifying sessions, pre-loaded into Elasticsearch and ready to query from minute one.

| What | Scale |
|---|---|
| Seasons | 2023 + 2024 (46 race weekends) |
| Sessions | 92 (Race + Qualifying per round) |
| Lap records | ~60,000 |
| Telemetry samples | **~18 million** (speed, throttle, brake, DRS, gear, X/Y coordinates) |
| Weather samples | ~9,000 (air temp, track temp, wind, rainfall) |

The Dutch Grand Prix at **Zandvoort** — home turf — is in there. Round 15 of 2024. Every lap Verstappen drove. Every braking point. Every overtake attempt.

---

## The Stack

### Elastic — Search, Explore, Visualise

Elasticsearch stores all 18 million telemetry rows and makes them queryable in milliseconds using **ES|QL** — Elastic's SQL-like query language built for time-series and analytics workloads.

Kibana Lens, Discover, and Dashboards give participants a visual playground from the moment they arrive. No setup friction — data views are pre-configured, the cluster is live.

```esql
FROM f1-telemetry
| WHERE event_name == "Dutch Grand Prix" AND driver_code == "VER"
| STATS top_speed = MAX(speed) BY lap_number
| SORT top_speed DESC
| LIMIT 5
```

### Hopsworks — Feature Engineering, ML, Model Serving

[Hopsworks](https://www.hopsworks.ai/) is an open-source Feature Store and MLOps platform. It bridges the gap between raw data and production ML: participants define **feature pipelines** that read from Elasticsearch, compute derived features (tyre degradation curves, sector-level driver consistency, rolling lap deltas), and store them in a **Feature Store** that is consistent between training and serving.

The result: models that don't break when they hit real data.

```
Raw telemetry (Elasticsearch)
        │
        ▼
Feature Pipeline (Python)
        │
        ├── tyre_degradation_features
        │     compound · tyre_life · lap_delta · track_temp
        │
        └── driver_form_features
              rolling_avg_lap · sector_consistency · position_trend
        │
        ▼
Feature View → Train model → Hopsworks Model Registry
        │
        ▼
Serve predictions → push results back to Kibana dashboard
```

**Together**, Elastic and Hopsworks cover the full arc from raw event data to a deployed, explainable ML application — something that normally takes weeks, compressed into a two-hour hack.

---

## The Challenge

Teams of up to four people build an F1 application that uses:

- **Elastic** — for search, dashboards, or AI features
- **Hopsworks** — at least one Feature Group with meaningful feature engineering
- **The F1 dataset** — telemetry, laps, weather, or results

Ideas to get started:

- **Pit stop strategy advisor** — predict the optimal lap to pit based on tyre degradation and gap to traffic
- **Driver fingerprinting** — build a model that identifies a driver from their throttle and braking style alone
- **Safety car predictor** — use weather and incident data to estimate safety car probability per lap
- **Race replay with ML overlay** — Kibana dashboard showing live-style race progression with model predictions overlaid

---

## Why Amsterdam

Amsterdam is a natural home for this event. The Dutch Grand Prix at Zandvoort — 30 km from the city — is one of the most passionate crowds on the F1 calendar. The Netherlands has produced the current world champion. And the Amsterdam tech community has the engineering depth to do the data justice.

---

## The Collaboration

This event is jointly designed and run by **Elastic** and **Hopsworks**. Both companies contribute:

| | Elastic | Hopsworks |
|---|---|---|
| **Infrastructure** | Pre-loaded Elasticsearch cluster, Kibana environment | Hosted Feature Store sandbox accounts for all participants |
| **Mentors on the night** | Elastic engineers on hand for ES|QL, Lens, Agent Builder | Hopsworks engineers for Feature Store, training pipelines, model serving |
| **Dataset** | F1 telemetry pre-ingested and queryable | Feature pipeline examples and starter code |
| **Judging** | Joint judging panel | Joint judging panel |

---

## Format

| Time | Activity |
|---|---|
| 18:00 – 18:15 | Welcome, intro, live data demo |
| 18:15 – 20:15 | Hack time + food |
| 20:15 – 20:45 | Team demos (5 min each) + audience vote |
| 20:45 – 21:00 | Prizes + close |

- Free to attend · Limited seats
- Teams of 1–4 · No pre-built repos · Code on the day

---

## Get Involved

Interested in attending, sponsoring, or mentoring?
Reach out to **afzaalahmad.zeeshan@elastic.co**
