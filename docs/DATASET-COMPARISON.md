# Dataset Comparison — F1 Telemetry vs Schiphol Flights
### Elastic × Hopsworks Hack Night · Amsterdam · 19 October 2026

| | **F1 Telemetry (FastF1)** | **Schiphol Flights API** |
|---|---|---|
| **What we ingest** | 2024 season — speed, throttle, brake, gear, X/Y coords at ~10Hz per driver; lap times, tyre compounds, pit stops, weather, race results | Historical flight movements — scheduled vs actual times, gate, aircraft type, airline, destination, pax count, flight status |
| **Coverage** | 2024 full season, 24 race weekends, 20 drivers | Historical data pre-ingested before the event (depth TBD — API has no documented cutoff) |
| **Data volume** | ~28M rows | ~30K rows per month — smaller but highly structured and time-rich |
| **Story** | Every throttle input from every driver across a full championship season — build race strategy tools, driver models, tyre degradation curves | KLM and 100+ airlines into 350+ destinations — build delay predictors, disruption models, route performance tools |
| **ML targets for Hopsworks** | Tyre degradation, driver fingerprinting, lap delta prediction, pit stop optimisation | Delay risk scoring, disruption cascade (rotation gap → downstream delay), airline on-time performance, slot pressure |
| **Hopsworks feature groups** | `tyre_degradation`, `driver_consistency`, `sector_times`, `pit_strategy` | `airline_performance`, `aircraft_rotation`, `slot_pressure`, `route_demand` |
| **Attendee access** | Read-only API key — query pre-loaded Elasticsearch cluster from minute one | Read-only API key — same pre-loaded cluster model; attendees can also register their own free Schiphol developer account at developer.schiphol.nl and build live apps on top |
| **Setup friction** | Zero | Zero — plus optional personal Schiphol API key for those who want to extend beyond the pre-loaded data |
| **Wow factor** | Scale — 28M rows, 10Hz sensors, real race data including Zandvoort | Familiar — Schiphol is 20 min away, KLM is a neighbour, every attendee has a delay story |

## What attendees must bring

- Laptop with Python 3.9+ and a code editor
- Hopsworks account (free tier — signup link sent before the event)
- Everything else is provided: Elasticsearch cluster, read-only API key, starter notebooks, Kibana dashboards

## What we expect on the night

1. Pull starter code from the event repo
2. Explore the data in Kibana Discover / Lens
3. Define a feature group in Hopsworks and run a feature pipeline
4. Train a model using the Hopsworks feature view
5. Push predictions back to Elasticsearch and build a Kibana dashboard
6. 5-minute demo — what did you predict, does it hold up?

> Schiphol also has a public developer portal (developer.schiphol.nl) — attendees who want to go beyond the pre-loaded dataset can register their own free API key and build apps that hit the live API directly.

---

*F1 data via [FastF1](https://github.com/theOehrly/Fast-F1) · Schiphol data via [Schiphol Developer Portal](https://developer.schiphol.nl)*
