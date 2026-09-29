import { Client } from "@elastic/elasticsearch";
import "dotenv/config";

export const es = new Client({
  node: process.env.ELASTICSEARCH_URL!,
  auth: { apiKey: process.env.ELASTICSEARCH_API_KEY! },
});

const OPENF1_BASE = "https://api.openf1.org/v1";

export async function openf1<T>(
  endpoint: string,
  params: Record<string, string | number>
): Promise<T[]> {
  const url = new URL(`${OPENF1_BASE}/${endpoint}`);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`OpenF1 ${endpoint} → ${res.status}`);
  return res.json() as Promise<T[]>;
}

// Jolpica (Ergast replacement) for results and standings
const JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1";

export async function jolpica<T>(path: string): Promise<T> {
  const res = await fetch(`${JOLPICA_BASE}${path}.json?limit=1000`);
  if (!res.ok) throw new Error(`Jolpica ${path} → ${res.status}`);
  const json = await res.json() as { MRData: T };
  return json.MRData;
}
