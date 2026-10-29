import type { BodyId } from '../world/bodies';
import { SPECIES } from '../props/species';
import { FAUNA } from './faunaSpecies';

// One journal namespace for everything that can be discovered: scannable
// flora/minerals (props) and fauna. Journal and expedition rules use this.

export type LifeKind = 'flora' | 'mineral' | 'fauna';

export interface CatalogEntry {
  id: string;
  body: BodyId;
  name: string;
  description: string;
  kind: LifeKind;
}

/** Prop species that are minerals rather than plants. */
const MINERALS = new Set(['ilex-chalk', 'vesper-glass', 'vesper-pillar', 'cairn-rime', 'cairn-boulder', 'cairn-pebbles', 'vesper-fulgurite', 'cairn-bloom']);

export const CATALOG: CatalogEntry[] = [
  ...SPECIES.filter((s) => s.scannable).map((s) => ({
    id: s.id, body: s.body, name: s.name, description: s.description, kind: (MINERALS.has(s.id) ? 'mineral' : 'flora') as LifeKind,
  })),
  ...FAUNA.map((s) => ({ id: s.id, body: s.body, name: s.name, description: s.description, kind: 'fauna' as LifeKind })),
];

export function catalogFor(body: BodyId): CatalogEntry[] {
  return CATALOG.filter((e) => e.body === body);
}

export function catalogById(id: string): CatalogEntry | undefined {
  return CATALOG.find((e) => e.id === id);
}

export interface WorldProgress {
  found: number;
  total: number;
  byKind: Record<LifeKind, { found: number; total: number }>;
}

/** Journal completion for one body from the logged species IDs (unknown IDs ignored). */
export function worldProgress(body: BodyId, logged: readonly string[]): WorldProgress {
  const byKind: WorldProgress['byKind'] = { flora: { found: 0, total: 0 }, mineral: { found: 0, total: 0 }, fauna: { found: 0, total: 0 } };
  let found = 0;
  let total = 0;
  for (const e of CATALOG) {
    if (e.body !== body) continue;
    const k = byKind[e.kind];
    k.total++;
    total++;
    if (logged.includes(e.id)) {
      k.found++;
      found++;
    }
  }
  return { found, total, byKind };
}

/** "Flora 1 of 3 · Minerals 0 of 1 · Fauna 0 of 1" (kinds without species omitted). */
export function progressLine(p: WorldProgress): string {
  const parts: string[] = [];
  const names: [LifeKind, string][] = [['flora', 'Flora'], ['mineral', 'Minerals'], ['fauna', 'Fauna']];
  for (const [k, n] of names) if (p.byKind[k].total > 0) parts.push(`${n} ${p.byKind[k].found} of ${p.byKind[k].total}`);
  return parts.join(' · ');
}
