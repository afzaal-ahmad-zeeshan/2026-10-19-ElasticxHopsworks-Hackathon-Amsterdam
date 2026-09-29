import "dotenv/config";
import { es } from "./client.js";

const INDICES = ["f1-sessions", "f1-results", "f1-laps", "f1-stints", "f1-weather", "f1-telemetry"];

async function main() {
  const info = await es.info();
  console.log(`Connected to ES ${info.version.number}\n`);

  console.log("=== Document counts ===");
  for (const idx of INDICES) {
    try {
      const { count } = await es.count({ index: idx });
      console.log(`  ${idx.padEnd(18)}: ${count.toLocaleString().padStart(12)} docs`);
    } catch {
      console.log(`  ${idx.padEnd(18)}: (not found)`);
    }
  }

  console.log("\n=== Top 5 drivers by fastest lap (Dutch GP Race) ===");
  try {
    const resp = await es.esql.query({
      query: `
        FROM f1-laps
        | WHERE event_name == "Dutch Grand Prix" AND session_name == "Race"
        | WHERE lap_duration_ms IS NOT NULL AND is_pit_out_lap == false
        | STATS fastest_lap_ms = MIN(lap_duration_ms) BY driver_code
        | SORT fastest_lap_ms ASC
        | LIMIT 5
      `,
    });
    const cols = resp.columns.map((c: { name: string }) => c.name);
    for (const row of resp.values as (string | number)[][]) {
      const ms = row[cols.indexOf("fastest_lap_ms")] as number;
      const s = (ms / 1000).toFixed(3);
      console.log(`  ${row[cols.indexOf("driver_code")]}: ${s}s`);
    }
  } catch (e) {
    console.log("  (data not yet ingested)");
  }
}

main().catch(err => { console.error(err); process.exit(1); });
