import { openf1 } from "./client.js";
import { bulkIndex } from "./bulk.js";

interface OpenF1CarData {
  session_key: number;
  driver_number: number;
  date: string;
  speed: number;
  rpm: number;
  throttle: number;
  brake: number; // 0 or 1
  drs: number;
  n_gear: number;
}

interface OpenF1Driver {
  session_key: number;
  driver_number: number;
  name_acronym: string;
  team_name: string;
}

type SessionMeta = { roundNumber: number; eventName: string; sessionName: string };

export async function ingestTelemetry(
  season: number,
  sessionMeta: Map<number, SessionMeta>
) {
  let totalOk = 0, totalErr = 0;

  for (const [sessionKey, meta] of sessionMeta) {
    console.log(`    telemetry: ${meta.eventName} ${meta.sessionName} (session ${sessionKey})...`);

    const drivers = await openf1<OpenF1Driver>("drivers", { session_key: sessionKey });
    const driverMap = new Map(drivers.map(d => [d.driver_number, { code: d.name_acronym, team: d.team_name }]));

    // Fetch per driver to avoid hitting API size limits
    for (const [driverNum, drv] of driverMap) {
      try {
        const rows = await openf1<OpenF1CarData>("car_data", {
          session_key:   sessionKey,
          driver_number: driverNum,
        });

        const docs = rows.map(r => ({
          season,
          round_number:  meta.roundNumber,
          session_key:   sessionKey,
          event_name:    meta.eventName,
          session_name:  meta.sessionName,
          driver_number: r.driver_number,
          driver_code:   drv.code,
          team_name:     drv.team,
          date:          r.date,
          speed:         r.speed,
          rpm:           r.rpm,
          throttle:      r.throttle,
          brake:         r.brake === 1,
          drs:           r.drs,
          n_gear:        r.n_gear,
        }));

        const { ok, err } = await bulkIndex("f1-telemetry", docs);
        totalOk += ok; totalErr += err;
      } catch {
        // skip driver if API fails
      }
    }
  }

  console.log(`  f1-telemetry: ${totalOk} indexed, ${totalErr} errors`);
}
