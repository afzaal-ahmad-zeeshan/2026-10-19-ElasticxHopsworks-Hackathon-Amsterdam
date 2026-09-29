import "dotenv/config";
import { es } from "./client.js";
import { createIndices } from "./mappings.js";
import { ingestSessions } from "./sessions.js";
import { ingestResults } from "./results.js";
import { ingestLaps } from "./laps.js";
import { ingestStints } from "./stints.js";
import { ingestWeather } from "./weather.js";
import { ingestTelemetry } from "./telemetry.js";

const SEASON = 2024;
const only = process.argv.find((_, i, a) => a[i - 1] === "--only");

async function main() {
  const info = await es.info();
  console.log(`Connected to Elasticsearch ${info.version.number}`);

  console.log("\nCreating indices...");
  await createIndices(/* drop= */ true);

  console.log("\nIngesting sessions...");
  const sessionMeta = await ingestSessions(SEASON);

  if (!only || only === "sessions") {
    console.log("\nIngesting results (via Jolpica/Ergast)...");
    await ingestResults(SEASON);
  }

  if (!only || only === "laps") {
    console.log("\nIngesting laps...");
    await ingestLaps(SEASON, sessionMeta);
  }

  if (!only || only === "laps") {
    console.log("\nIngesting stints (tyre data)...");
    await ingestStints(SEASON, sessionMeta);
  }

  if (!only || only === "weather") {
    console.log("\nIngesting weather...");
    await ingestWeather(SEASON, sessionMeta);
  }

  if (!only || only === "telemetry") {
    console.log("\nIngesting telemetry (this is the big one — may take 30-60 min)...");
    await ingestTelemetry(SEASON, sessionMeta);
  }

  console.log("\n=== Final counts ===");
  for (const idx of ["f1-sessions", "f1-results", "f1-laps", "f1-stints", "f1-weather", "f1-telemetry"]) {
    const { count } = await es.count({ index: idx });
    console.log(`  ${idx}: ${count.toLocaleString()} docs`);
  }
}

main().catch(err => { console.error(err); process.exit(1); });
