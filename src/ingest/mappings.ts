import { es } from "./client.js";

export const INDICES = [
  "f1-sessions",
  "f1-results",
  "f1-laps",
  "f1-stints",
  "f1-weather",
  "f1-telemetry",
] as const;

export type IndexName = (typeof INDICES)[number];

const MAPPINGS: Record<IndexName, object> = {
  "f1-sessions": {
    mappings: { properties: {
      season:       { type: "integer" },
      round_number: { type: "integer" },
      session_key:  { type: "integer" },
      country:      { type: "keyword" },
      location:     { type: "keyword" },
      circuit_name: { type: "keyword" },
      session_name: { type: "keyword" },
      session_type: { type: "keyword" },
      session_date: { type: "date", format: "strict_date_optional_time" },
    }},
  },
  "f1-results": {
    mappings: { properties: {
      season:         { type: "integer" },
      round_number:   { type: "integer" },
      event_name:     { type: "keyword" },
      session_name:   { type: "keyword" },
      driver_number:  { type: "integer" },
      driver_code:    { type: "keyword" },
      full_name:      { type: "keyword" },
      team_name:      { type: "keyword" },
      position:       { type: "integer" },
      points:         { type: "float" },
      grid_position:  { type: "integer" },
      status:         { type: "keyword" },
      fastest_lap_ms: { type: "integer" },
    }},
  },
  "f1-laps": {
    mappings: { properties: {
      season:         { type: "integer" },
      round_number:   { type: "integer" },
      session_key:    { type: "integer" },
      event_name:     { type: "keyword" },
      session_name:   { type: "keyword" },
      driver_number:  { type: "integer" },
      driver_code:    { type: "keyword" },
      team_name:      { type: "keyword" },
      lap_number:     { type: "integer" },
      lap_duration_ms:   { type: "integer" },
      duration_sector_1: { type: "integer" },
      duration_sector_2: { type: "integer" },
      duration_sector_3: { type: "integer" },
      is_pit_out_lap: { type: "boolean" },
      date_start:     { type: "date", format: "strict_date_optional_time" },
    }},
  },
  "f1-stints": {
    mappings: { properties: {
      season:          { type: "integer" },
      round_number:    { type: "integer" },
      session_key:     { type: "integer" },
      event_name:      { type: "keyword" },
      session_name:    { type: "keyword" },
      driver_number:   { type: "integer" },
      driver_code:     { type: "keyword" },
      team_name:       { type: "keyword" },
      stint_number:    { type: "integer" },
      lap_start:       { type: "integer" },
      lap_end:         { type: "integer" },
      compound:        { type: "keyword" },
      tyre_age_at_start: { type: "integer" },
    }},
  },
  "f1-weather": {
    mappings: { properties: {
      season:          { type: "integer" },
      round_number:    { type: "integer" },
      session_key:     { type: "integer" },
      event_name:      { type: "keyword" },
      session_name:    { type: "keyword" },
      date:            { type: "date", format: "strict_date_optional_time" },
      air_temperature: { type: "float" },
      track_temperature: { type: "float" },
      humidity:        { type: "float" },
      pressure:        { type: "float" },
      wind_speed:      { type: "float" },
      wind_direction:  { type: "integer" },
      rainfall:        { type: "boolean" },
    }},
  },
  "f1-telemetry": {
    mappings: { properties: {
      season:         { type: "integer" },
      round_number:   { type: "integer" },
      session_key:    { type: "integer" },
      event_name:     { type: "keyword" },
      session_name:   { type: "keyword" },
      driver_number:  { type: "integer" },
      driver_code:    { type: "keyword" },
      team_name:      { type: "keyword" },
      date:           { type: "date", format: "strict_date_optional_time" },
      speed:          { type: "integer" },
      rpm:            { type: "integer" },
      throttle:       { type: "integer" },
      brake:          { type: "boolean" },
      drs:            { type: "integer" },
      n_gear:         { type: "integer" },
    }},
  },
};

export async function createIndices(drop = false) {
  for (const name of INDICES) {
    if (drop && await es.indices.exists({ index: name })) {
      await es.indices.delete({ index: name });
    }
    if (!await es.indices.exists({ index: name })) {
      await es.indices.create({ index: name, ...MAPPINGS[name] });
      console.log(`  Created ${name}`);
    } else {
      console.log(`  Exists  ${name}`);
    }
  }
}
