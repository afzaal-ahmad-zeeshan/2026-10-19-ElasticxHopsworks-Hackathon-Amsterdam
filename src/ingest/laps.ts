import { openf1 } from "./client.js";
import { bulkIndex } from "./bulk.js";

interface OpenF1Lap {
  session_key: number;
  driver_number: number;
  lap_number: number;
  lap_duration: number | null;
  duration_sector_1: number | null;
  duration_sector_2: number | null;
  duration_sector_3: number | null;
  is_pit_out_lap: boolean;
  date_start: string;
  // OpenF1 doesn't carry driver_code here — joined via driverMap
}

interface OpenF1Driver {
  session_key: number;
  driver_number: number;
  name_acronym: string;
  full_name: string;
  team_name: string;
}

type SessionMeta = { roundNumber: number; eventName: string; sessionName: string };

export async function ingestLaps(
  season: number,
  sessionMeta: Map<number, SessionMeta>
) {
  let totalOk = 0, totalErr = 0;

  for (const [sessionKey, meta] of sessionMeta) {
    const [laps, drivers] = await Promise.all([
      openf1<OpenF1Lap>("laps", { session_key: sessionKey }),
      openf1<OpenF1Driver>("drivers", { session_key: sessionKey }),
    ]);

    const driverMap = new Map(drivers.map(d => [d.driver_number, { code: d.name_acronym, team: d.team_name }]));

    const docs = laps.map(l => {
      const drv = driverMap.get(l.driver_number);
      return {
        season,
        round_number:      meta.roundNumber,
        session_key:       sessionKey,
        event_name:        meta.eventName,
        session_name:      meta.sessionName,
        driver_number:     l.driver_number,
        driver_code:       drv?.code ?? null,
        team_name:         drv?.team ?? null,
        lap_number:        l.lap_number,
        lap_duration_ms:   l.lap_duration != null ? Math.round(l.lap_duration * 1000) : null,
        duration_sector_1: l.duration_sector_1 != null ? Math.round(l.duration_sector_1 * 1000) : null,
        duration_sector_2: l.duration_sector_2 != null ? Math.round(l.duration_sector_2 * 1000) : null,
        duration_sector_3: l.duration_sector_3 != null ? Math.round(l.duration_sector_3 * 1000) : null,
        is_pit_out_lap:    l.is_pit_out_lap,
        date_start:        l.date_start,
      };
    });

    const { ok, err } = await bulkIndex("f1-laps", docs);
    totalOk += ok; totalErr += err;
  }

  console.log(`  f1-laps: ${totalOk} indexed, ${totalErr} errors`);
}
