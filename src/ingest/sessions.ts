import { openf1 } from "./client.js";
import { bulkIndex } from "./bulk.js";

interface OpenF1Session {
  session_key: number;
  session_name: string;
  session_type: string;
  date_start: string;
  date_end: string;
  year: number;
  circuit_key: number;
  circuit_short_name: string;
  country_code: string;
  country_name: string;
  location: string;
  meeting_key: number;
}

interface OpenF1Meeting {
  meeting_key: number;
  meeting_name: string;
  meeting_official_name: string;
  location: string;
  country_key: number;
  country_code: string;
  country_name: string;
  circuit_key: number;
  circuit_short_name: string;
  date_start: string;
  year: number;
}

export async function ingestSessions(season: number): Promise<Map<number, { roundNumber: number; eventName: string; sessionName: string }>> {
  const sessionMeta = new Map<number, { roundNumber: number; eventName: string; sessionName: string }>();

  const [sessions, meetings] = await Promise.all([
    openf1<OpenF1Session>("sessions", { year: season }),
    openf1<OpenF1Meeting>("meetings", { year: season }),
  ]);

  // Build meeting_key → round_number + event_name from ordered meeting list
  const meetingMap = new Map<number, { roundNumber: number; eventName: string }>();
  meetings
    .filter(m => m.year === season)
    .sort((a, b) => new Date(a.date_start).getTime() - new Date(b.date_start).getTime())
    .forEach((m, idx) => {
      meetingMap.set(m.meeting_key, { roundNumber: idx + 1, eventName: m.meeting_name });
    });

  const docs = sessions
    .filter(s => s.year === season && s.session_type !== "Practice") // Race + Qualifying only; adjust to include Practice if wanted
    .map(s => {
      const mtg = meetingMap.get(s.meeting_key) ?? { roundNumber: 0, eventName: s.circuit_short_name };
      sessionMeta.set(s.session_key, { roundNumber: mtg.roundNumber, eventName: mtg.eventName, sessionName: s.session_name });
      return {
        season,
        round_number:  mtg.roundNumber,
        session_key:   s.session_key,
        event_name:    mtg.eventName,
        country:       s.country_name,
        location:      s.location,
        circuit_name:  s.circuit_short_name,
        session_name:  s.session_name,
        session_type:  s.session_type,
        session_date:  s.date_start,
      };
    });

  const { ok, err } = await bulkIndex("f1-sessions", docs);
  console.log(`  f1-sessions: ${ok} indexed, ${err} errors`);
  return sessionMeta;
}
