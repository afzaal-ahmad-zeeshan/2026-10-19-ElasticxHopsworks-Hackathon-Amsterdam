import { openf1 } from "./client.js";
import { bulkIndex } from "./bulk.js";

interface OpenF1Weather {
  session_key: number;
  date: string;
  air_temperature: number;
  track_temperature: number;
  humidity: number;
  pressure: number;
  wind_speed: number;
  wind_direction: number;
  rainfall: boolean;
}

type SessionMeta = { roundNumber: number; eventName: string; sessionName: string };

export async function ingestWeather(
  season: number,
  sessionMeta: Map<number, SessionMeta>
) {
  let totalOk = 0, totalErr = 0;

  for (const [sessionKey, meta] of sessionMeta) {
    const rows = await openf1<OpenF1Weather>("weather", { session_key: sessionKey });

    const docs = rows.map(w => ({
      season,
      round_number:      meta.roundNumber,
      session_key:       sessionKey,
      event_name:        meta.eventName,
      session_name:      meta.sessionName,
      date:              w.date,
      air_temperature:   w.air_temperature,
      track_temperature: w.track_temperature,
      humidity:          w.humidity,
      pressure:          w.pressure,
      wind_speed:        w.wind_speed,
      wind_direction:    w.wind_direction,
      rainfall:          w.rainfall,
    }));

    const { ok, err } = await bulkIndex("f1-weather", docs);
    totalOk += ok; totalErr += err;
  }

  console.log(`  f1-weather: ${totalOk} indexed, ${totalErr} errors`);
}
