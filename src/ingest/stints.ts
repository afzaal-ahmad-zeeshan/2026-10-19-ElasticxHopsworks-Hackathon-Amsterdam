import { openf1 } from "./client.js";
import { bulkIndex } from "./bulk.js";

interface OpenF1Stint {
  session_key: number;
  driver_number: number;
  stint_number: number;
  lap_start: number;
  lap_end: number;
  compound: string;
  tyre_age_at_start: number;
}

interface OpenF1Driver {
  session_key: number;
  driver_number: number;
  name_acronym: string;
  team_name: string;
}

type SessionMeta = { roundNumber: number; eventName: string; sessionName: string };

export async function ingestStints(
  season: number,
  sessionMeta: Map<number, SessionMeta>
) {
  let totalOk = 0, totalErr = 0;

  for (const [sessionKey, meta] of sessionMeta) {
    const [stints, drivers] = await Promise.all([
      openf1<OpenF1Stint>("stints", { session_key: sessionKey }),
      openf1<OpenF1Driver>("drivers", { session_key: sessionKey }),
    ]);

    const driverMap = new Map(drivers.map(d => [d.driver_number, { code: d.name_acronym, team: d.team_name }]));

    const docs = stints.map(s => {
      const drv = driverMap.get(s.driver_number);
      return {
        season,
        round_number:       meta.roundNumber,
        session_key:        sessionKey,
        event_name:         meta.eventName,
        session_name:       meta.sessionName,
        driver_number:      s.driver_number,
        driver_code:        drv?.code ?? null,
        team_name:          drv?.team ?? null,
        stint_number:       s.stint_number,
        lap_start:          s.lap_start,
        lap_end:            s.lap_end,
        compound:           s.compound,
        tyre_age_at_start:  s.tyre_age_at_start,
      };
    });

    const { ok, err } = await bulkIndex("f1-stints", docs);
    totalOk += ok; totalErr += err;
  }

  console.log(`  f1-stints: ${totalOk} indexed, ${totalErr} errors`);
}
