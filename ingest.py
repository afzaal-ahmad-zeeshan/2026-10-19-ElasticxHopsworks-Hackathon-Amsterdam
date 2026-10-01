"""
F1 data ingest for Elastic x Hopsworks Hackathon Amsterdam 2026.
Sources data via FastF1 (covers 2018–present, no API key required).

Usage:
    pip install -r requirements.txt
    python ingest.py

Set ELASTICSEARCH_URL and ELASTICSEARCH_API_KEY in .env (or export them).
Configure SEASONS and SESSION_TYPES below to control what gets loaded.
"""

import os, warnings, json
warnings.filterwarnings("ignore")
from dotenv import load_dotenv
load_dotenv()

import fastf1
import pandas as pd
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
from tqdm import tqdm

ES_URL     = os.environ["ELASTICSEARCH_URL"]
ES_API_KEY = os.environ.get("ELASTICSEARCH_API_KEY")
ES_USER    = os.environ.get("ELASTICSEARCH_USERNAME")
ES_PASS    = os.environ.get("ELASTICSEARCH_PASSWORD")
# F1_SEASONS=2023,2024 overrides; add 2018–2022 for deeper history
SEASONS        = [int(s) for s in os.environ.get("F1_SEASONS", "2023,2024").split(",") if s.strip()]
SESSION_TYPES  = ["Race", "Qualifying"]
CACHE_DIR      = "./fastf1_cache"

os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

es = (Elasticsearch(ES_URL, api_key=ES_API_KEY) if ES_API_KEY
      else Elasticsearch(ES_URL, basic_auth=(ES_USER, ES_PASS)))
print(f"Connected to ES {es.info()['version']['number']}")

MAPPINGS = {
    "f1-sessions": {"mappings": {"properties": {
        "season":       {"type": "integer"},
        "round_number": {"type": "integer"},
        "session_key":  {"type": "integer"},
        "event_name":   {"type": "keyword"},
        "country":      {"type": "keyword"},
        "location":     {"type": "keyword"},
        "circuit_name": {"type": "keyword"},
        "session_name": {"type": "keyword"},
        "session_type": {"type": "keyword"},
        "session_date": {"type": "date", "format": "strict_date_optional_time"},
    }}},
    "f1-results": {"mappings": {"properties": {
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
        "fastest_lap_ms": {"type": "integer"},
    }}},
    "f1-laps": {"mappings": {"properties": {
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
        "position":          {"type": "integer"},
    }}},
    "f1-weather": {"mappings": {"properties": {
        "season":             {"type": "integer"},
        "round_number":       {"type": "integer"},
        "session_key":        {"type": "integer"},
        "event_name":         {"type": "keyword"},
        "session_name":       {"type": "keyword"},
        "session_time_s":     {"type": "float"},
        "air_temperature":    {"type": "float"},
        "track_temperature":  {"type": "float"},
        "humidity":           {"type": "float"},
        "pressure":           {"type": "float"},
        "wind_speed":         {"type": "float"},
        "wind_direction":     {"type": "integer"},
        "rainfall":           {"type": "boolean"},
    }}},
    "f1-telemetry": {"mappings": {"properties": {
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
        "z":              {"type": "float"},
    }}},
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def td_ms(td):
    if pd.isnull(td):
        return None
    try:
        return int(td.total_seconds() * 1000)
    except Exception:
        return None

def td_s(td):
    if pd.isnull(td):
        return None
    try:
        return round(td.total_seconds(), 3)
    except Exception:
        return None

def safe(val):
    if hasattr(val, "item"):
        return val.item()
    try:
        if pd.isnull(val):
            return None
    except Exception:
        pass
    return val

def bulk_index(actions_gen):
    ok = err = 0
    for success, info in streaming_bulk(es, actions_gen, chunk_size=1000, raise_on_error=False):
        if success:
            ok += 1
        else:
            err += 1
    return ok, err

# ── Setup ─────────────────────────────────────────────────────────────────────

def setup_indices():
    for name, body in MAPPINGS.items():
        if es.indices.exists(index=name):
            es.indices.delete(index=name)
        es.indices.create(index=name, body=body)
    print(f"  Created {len(MAPPINGS)} indices")

# ── Session loader ────────────────────────────────────────────────────────────

def process_session(season, round_num, event_name, country, location, stype):
    try:
        session = fastf1.get_session(season, round_num, stype)
        session.load(telemetry=True, weather=True, laps=True, messages=False)
    except Exception as e:
        print(f"    Skip {event_name} {stype}: {e}")
        return

    meta = dict(
        season=season, round_number=round_num,
        event_name=event_name, session_name=stype,
        session_key=getattr(session, "session_key", None),
    )

    # Session doc
    es.index(index="f1-sessions", document={
        **meta,
        "country":      country,
        "location":     location,
        "circuit_name": str(session.event.get("OfficialEventName", location)),
        "session_type": stype,
        "session_date": str(session.date.date()) if session.date else None,
    })

    # Results
    try:
        res = session.results
        if res is not None and len(res):
            ok, _ = bulk_index(
                {"_index": "f1-results", "_source": {
                    **meta,
                    "driver_number":  safe(r.get("DriverNumber")),
                    "driver_code":    safe(r.get("Abbreviation")),
                    "full_name":      safe(r.get("FullName")),
                    "team_name":      safe(r.get("TeamName")),
                    "position":       safe(r.get("Position")),
                    "points":         safe(r.get("Points")),
                    "grid_position":  safe(r.get("GridPosition")),
                    "status":         safe(r.get("Status")),
                    "fastest_lap_ms": td_ms(r.get("FastestLapTime")),
                }}
                for _, r in res.iterrows()
            )
    except Exception:
        pass

    # Laps
    laps_ok = 0
    try:
        laps = session.laps
        if laps is not None and len(laps):
            laps_ok, _ = bulk_index(
                {"_index": "f1-laps", "_source": {
                    **meta,
                    "driver_number":     safe(r.get("DriverNumber")),
                    "driver_code":       safe(r.get("Driver")),
                    "team_name":         safe(r.get("Team")),
                    "lap_number":        safe(r.get("LapNumber")),
                    "lap_duration_ms":   td_ms(r.get("LapTime")),
                    "duration_sector_1": td_ms(r.get("Sector1Time")),
                    "duration_sector_2": td_ms(r.get("Sector2Time")),
                    "duration_sector_3": td_ms(r.get("Sector3Time")),
                    "compound":          safe(r.get("Compound")),
                    "tyre_life":         safe(r.get("TyreLife")),
                    "is_pit_out_lap":    bool(r.get("IsPitOutLap", False)),
                    "is_pit_in_lap":     bool(r.get("IsPitInLap", False)),
                    "track_status":      safe(r.get("TrackStatus")),
                    "position":          safe(r.get("Position")),
                }}
                for _, r in laps.iterrows()
            )
    except Exception:
        pass

    # Weather
    try:
        wx = session.weather_data
        if wx is not None and len(wx):
            bulk_index(
                {"_index": "f1-weather", "_source": {
                    **meta,
                    "session_time_s":    td_s(r.get("Time")),
                    "air_temperature":   safe(r.get("AirTemp")),
                    "track_temperature": safe(r.get("TrackTemp")),
                    "humidity":          safe(r.get("Humidity")),
                    "pressure":          safe(r.get("Pressure")),
                    "wind_speed":        safe(r.get("WindSpeed")),
                    "wind_direction":    safe(r.get("WindDirection")),
                    "rainfall":          bool(r.get("Rainfall", False)),
                }}
                for _, r in wx.iterrows()
            )
    except Exception:
        pass

    # Telemetry — FastF1 advantage: lap-linked, includes X/Y/Z track coordinates
    tel_ok = 0
    try:
        for drv in session.drivers:
            try:
                drv_info = session.get_driver(drv)
                drv_code = drv_info.get("Abbreviation", drv) if drv_info is not None else drv
                drv_num  = int(drv_info.get("DriverNumber", 0)) if drv_info is not None else 0
                team     = drv_info.get("TeamName", "") if drv_info is not None else ""
                drv_laps = session.laps.pick_drivers(drv)
                for _, lap in drv_laps.iterrows():
                    lap_num = safe(lap.get("LapNumber"))
                    try:
                        tel = lap.get_telemetry()
                        if tel is None or len(tel) == 0:
                            continue
                        ok, _ = bulk_index(
                            {"_index": "f1-telemetry", "_source": {
                                **meta,
                                "driver_number":  drv_num,
                                "driver_code":    drv_code,
                                "team_name":      team,
                                "lap_number":     lap_num,
                                "session_time_s": td_s(t.get("SessionTime")),
                                "speed":          safe(t.get("Speed")),
                                "rpm":            safe(t.get("RPM")),
                                "throttle":       safe(t.get("Throttle")),
                                "brake":          bool(t.get("Brake", False)),
                                "drs":            safe(t.get("DRS")),
                                "n_gear":         safe(t.get("nGear")),
                                "x":              safe(t.get("X")),
                                "y":              safe(t.get("Y")),
                                "z":              safe(t.get("Z")),
                            }}
                            for _, t in tel.iterrows()
                        )
                        tel_ok += ok
                    except Exception:
                        pass
            except Exception:
                pass
    except Exception:
        pass

    print(f"    {event_name} {stype}: laps={laps_ok} telemetry={tel_ok}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Setting up indices...")
    setup_indices()

    for season in SEASONS:
        schedule = fastf1.get_event_schedule(season, include_testing=False)
        print(f"\n=== Season {season} ({len(schedule)} rounds) ===")
        for _, event in tqdm(schedule.iterrows(), total=len(schedule), desc=f"{season}"):
            round_num  = int(event["RoundNumber"])
            country    = str(event["Country"])
            location   = str(event["Location"])
            event_name = str(event["EventName"])
            for stype in SESSION_TYPES:
                process_session(season, round_num, event_name, country, location, stype)

    print("\n=== Final document counts ===")
    for idx in MAPPINGS:
        count = es.count(index=idx)["count"]
        print(f"  {idx}: {count:,}")

if __name__ == "__main__":
    main()
