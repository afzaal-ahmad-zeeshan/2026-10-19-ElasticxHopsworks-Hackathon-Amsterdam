# Hack Night: Elastic × Hopsworks — Amsterdam
### Alternative Dataset Option: Schiphol Airport Flight Data
### 19 October 2026 · Amsterdam

---

## The Pitch

Amsterdam Schiphol is one of Europe's five busiest airports — 500+ flights per day, 350+ destinations, and a hub for KLM connecting every continent. Every flight generates a stream of structured, time-stamped events: scheduled departure, gate assignment, boarding, pushback, takeoff, landing, baggage status.

On October 19 we hand that operational data to developers in Amsterdam and ask: **what can you predict, detect, or optimize in two hours?**

---

## The Data

**Source:** [Schiphol Public Flights API](https://developer.schiphol.nl)  
**Access:** Free registration at developer.schiphol.nl — app_id + app_key, passed as request headers  
**Format:** JSON, REST  
**Coverage:** Real-time + rolling history (departures and arrivals)

### Key Endpoints

| Endpoint | What It Returns |
|---|---|
| `GET /flights` | All flights — filterable by direction, airline, schedule date, flight number |
| `GET /flights/{id}` | Single flight detail |
| `GET /destinations` | All served destinations with city, country, IATA code |
| `GET /airlines` | Airline codes and names |
| `GET /aircraft-types` | Aircraft type catalogue (IATA/ICAO, manufacturer, subtype) |
| `GET /gates` | Gate and pier identifiers |

### Key Fields per Flight

| Field | Description |
|---|---|
| `flightName` | Flight number (e.g. KL0805) |
| `flightDirection` | D = Departure, A = Arrival |
| `scheduleDateTime` | Scheduled time (ISO 8601) |
| `actualOffBlockTime` | Actual pushback time |
| `estimatedLandingTime` | ETA for arrivals |
| `publicFlightState` | Status code: SCH · DEP · ARR · LND · DIV · CNX |
| `route.destinations` | Array of IATA destination codes |
| `aircraftType.iataMain` | Aircraft type (e.g. 73H, 789, 32A) |
| `airline.icao` | Airline identifier |
| `gate`, `pier`, `terminal` | Physical location at Schiphol |
| `transfersCount` | Number of transfer passengers |
| `passengersExpected` | Expected pax count |
| `codeshares` | Codeshare partner flights |

### Data Scale

| Metric | Volume |
|---|---|
| Daily flights (both directions) | ~1,000 movements |
| Served destinations | 350+ worldwide |
| Airlines | 100+ |
| Annual passengers | 70M+ |
| Delay fields | Actual vs scheduled across 4 milestones |

---

## The Elastic Story

Ingest the Schiphol API into Elasticsearch and make every flight queryable in seconds:

```esql
FROM flights
| WHERE airline_icao == "KLM" AND direction == "D"
| STATS avg_delay_min = AVG(delay_minutes), flights = COUNT(*) BY destination
| WHERE avg_delay_min > 15
| SORT avg_delay_min DESC
| LIMIT 10
```

**Dashboard ideas:**
- Live departure board with delay status colour-coding
- Delay heatmap by hour-of-day × day-of-week
- Route map: most disrupted origin–destination pairs
- Airline on-time performance ranking
- Aircraft type utilisation by terminal

---

## The Hopsworks Story

Raw flight events → Feature Store → ML predictions → back to Kibana

```
Schiphol API (real-time + historical)
        │
        ▼
Ingest Pipeline (Python)
        │
        ├── delay_risk_features
        │     airline · aircraft_type · route_load · hour_of_day
        │     weather_condition · connecting_flight_count
        │
        └── disruption_cascade_features
              upstream_delay · aircraft_rotation_gap
              gate_occupancy · slot_pressure
        │
        ▼
Feature View → Train model → Hopsworks Model Registry
        │
        ▼
Serve predictions → Kibana alert: "Flight KL805 — 78% delay risk"
```

**Feature group ideas:**
- `airline_performance` — rolling on-time rate per airline, per route
- `slot_pressure` — number of flights departing within ±30 min window
- `aircraft_rotation` — time since last landing for same tail number
- `route_demand` — seasonal load factor by destination

---

## Why This Works for Amsterdam

Schiphol is 20 minutes from the city centre. Every person in the room has passed through it. The airport is literally visible on a clear day from parts of Amsterdam. This is not abstract enterprise data — it is the infrastructure they live next to.

KLM is headquartered here. Schiphol is headquartered here. The audience has domain intuition that makes the data immediately legible and the challenge immediately real.

---

## F1 vs Schiphol — Comparison

| | F1 Telemetry | Schiphol Flights |
|---|---|---|
| **Data familiarity** | Fan-accessible, global | Local, everyone has a story |
| **Data volume** | 57M rows pre-loaded | ~1,000 events/day live |
| **Real-time angle** | Historical only | Live API available |
| **ML target** | Lap time, tyre strategy | Delay prediction, disruption cascade |
| **Hopsworks fit** | Tyre degradation features | Airline/route performance features |
| **Setup friction** | Zero (pre-ingested) | API key registration required |
| **Complexity** | High (telemetry interpretation) | Low–medium (flights are intuitive) |
| **Wow factor** | 57M rows, 10Hz sensors | Real-time live data during the hack |

**Recommendation:** Schiphol works best if you want **live data during the event** — participants see their models update as flights actually depart. F1 works best if you want **zero setup friction** with a larger pre-loaded dataset.

---

## Hybrid Option

Pre-load 30 days of historical Schiphol data before the event, then keep the live API streaming during the hack. Participants start with a trained baseline and can watch their model's predictions against real departures in Kibana as the evening progresses.

---

## Get Involved

Interested in attending, sponsoring, or mentoring?  
Reach out to **afzaalahmad.zeeshan@elastic.co**

---

*Data via [Schiphol Developer Portal](https://developer.schiphol.nl) — free registration, REST API, JSON.*
