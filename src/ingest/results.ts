import { jolpica } from "./client.js";
import { bulkIndex } from "./bulk.js";

interface JolpicaResultRow {
  position: string;
  positionText: string;
  points: string;
  grid: string;
  status: string;
  Driver: { driverId: string; code: string; givenName: string; familyName: string };
  Constructor: { name: string };
  FastestLap?: { Time?: { millis?: string } };
}

interface JolpicaRaceResult {
  round: string;
  raceName: string;
  Results: JolpicaResultRow[];
  QualifyingResults?: JolpicaResultRow[];
}

export async function ingestResults(season: number) {
  const data = await jolpica<{ RaceTable: { Races: JolpicaRaceResult[] } }>(`/${season}/results`);
  const docs = data.RaceTable.Races.flatMap(race =>
    race.Results.map(r => ({
      season,
      round_number:   parseInt(race.round),
      event_name:     race.raceName,
      session_name:   "Race",
      driver_code:    r.Driver.code,
      full_name:      `${r.Driver.givenName} ${r.Driver.familyName}`,
      team_name:      r.Constructor.name,
      position:       parseInt(r.position) || null,
      points:         parseFloat(r.points),
      grid_position:  parseInt(r.grid) || null,
      status:         r.status,
      fastest_lap_ms: r.FastestLap?.Time?.millis ? parseInt(r.FastestLap.Time.millis) : null,
    }))
  );

  const { ok, err } = await bulkIndex("f1-results", docs);
  console.log(`  f1-results: ${ok} indexed, ${err} errors`);
}
