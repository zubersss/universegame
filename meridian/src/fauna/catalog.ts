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
const MINERALS = new Set(['ilex-chalk', 'vesper-glass', 'vesper-pillar', 'cairn-rime', 'cairn-boulder', 'cairn-pebbles']);

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
