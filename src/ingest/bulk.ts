import { es } from "./client.js";

export async function bulkIndex(index: string, docs: object[]): Promise<{ ok: number; err: number }> {
  if (docs.length === 0) return { ok: 0, err: 0 };

  const BATCH = 1000;
  let ok = 0, err = 0;

  for (let i = 0; i < docs.length; i += BATCH) {
    const batch = docs.slice(i, i + BATCH);
    const operations = batch.flatMap(doc => [{ index: { _index: index } }, doc]);
    const result = await es.bulk({ operations, refresh: false });
    for (const item of result.items) {
      if (item.index?.error) err++;
      else ok++;
    }
  }

  return { ok, err };
}
