import { describe, expect, it } from 'vitest';
import {
  CORRUPT_KEY, LEGACY_KEY, PREV_KEY, SAVE_KEY, SAVE_SCHEMA, SaveStore, exportJson, importJson, legacySummary, validateSave, type SaveData, type V3,
} from '../src/save/SaveSystem';
import type { KvStore } from '../src/save/db';
import { BODIES, GENERATOR_VERSION, SYSTEM_EXTENT, WORLD_SEED } from '../src/world/bodies';
import { DEFAULT_SETTINGS } from '../src/game/settings';
// A schema-1 record exactly as the published MERIDIAN build wrote it. Frozen:
// never edit it (it stands for real players' saves; e2e/journey/saves.spec.ts uses it too).
import SCHEMA1 from './fixtures/save-schema1.json';

const schema1 = (): Record<string, unknown> => structuredClone(SCHEMA1);

function sample(overrides: Partial<SaveData> = {}): SaveData {
  return {
    schema: SAVE_SCHEMA,
    generator: GENERATOR_VERSION,
    seed: WORLD_SEED,
    savedAt: '2026-10-29T12:00:00.000Z',
    playTime: 321.5,
    system: 'quiet',
    mode: 'LANDED',
    bodyId: 'vesper',
    ship: { sys: [790000.5, -41000.25, -598000.125], quat: [0, 0, 0, 1], vel: [0, 0, 0], gear: 1, throttle: 0 },
    player: null,
    cruise: null,
    lastSafeLanding: { bodyId: 'vesper', posPlanet: [-17000, -41000, 4500], quat: [0, 0.7071067811865476, 0, 0.7071067811865476] },
    navTarget: 'cairn',
    discoveries: ['ilex', 'vesper'],
    unlocked: [],
    settings: { ...DEFAULT_SETTINGS },
    expedition: {
      inventory: { ilex: 1, vesper: 0, cairn: 0 },
      collected: ['ilex:sample:0', 'ilex:sample:2', 'vesper:sample:1'],
      relays: ['ilex', 'vesper'],
      species: ['ilex-lantern', 'vesper-glass'],
      scanned: ['ilex:ilex-lantern:5/10/2/3:4', 'vesper:relay'],
      transmitted: false,
    },
    ...overrides,
  };
}

/** On foot on a body, the ship and the player `shipR` and `playerR` radii from its center (along +x). */
function onFootAt(id: string, shipR: number, playerR: number): SaveData {
  const d = BODIES[id];
  const at = (k: number): V3 => [d.center[0] + k * d.radius, d.center[1], d.center[2]];
  return sample({ mode: 'ON_FOOT', bodyId: id, ship: { ...sample().ship, sys: at(shipR) }, player: { sys: at(playerR), heading: [0, 0, 1], pitch: 0, abilityState: null } });
}

/** Cruising in open space at `sys`, flying −z at `speed`. */
function cruising(sys: V3, speed: number): SaveData {
  return sample({ mode: 'CRUISING', bodyId: null, ship: { ...sample().ship, sys, vel: [0, 0, -speed], gear: 0, throttle: 1 }, cruise: { speed, throttle: 1 } });
}

function omit(o: object, key: string): Record<string, unknown> {
  const r: Record<string, unknown> = { ...o };
  delete r[key];
  return r;
}

/** In-memory stand-in for the IndexedDB store with optional failure injection. */
class FakeKv {
  data = new Map<string, unknown>();
  failWrites: Error | null = null;
  async get(key: string) {
    return this.data.get(key);
  }
  async put(key: string, value: unknown) {
    if (this.failWrites) throw this.failWrites;
    this.data.set(key, structuredClone(value));
  }
  async rotateAndPut(key: string, backupKey: string, value: unknown, keep: (old: unknown) => boolean) {
    if (this.failWrites) throw this.failWrites;
    const old = this.data.get(key);
    if (old !== undefined && keep(old)) this.data.set(backupKey, old);
    this.data.set(key, structuredClone(value));
  }
}

describe('save validation', () => {
  it('accepts a coherent snapshot and survives a JSON round trip', () => {
    const d = sample();
    const r = importJson(exportJson(d));
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.data).toEqual(d);
  });

  it('accepts on-foot and cruising snapshots with their extra state', () => {
    expect(validateSave(sample({ mode: 'ON_FOOT', player: { sys: [790010, -41000, -598000], heading: [1, 0, 0], pitch: 0.2, abilityState: null } })).ok).toBe(true);
    expect(validateSave(sample({ mode: 'CRUISING', bodyId: null, cruise: { speed: 12000, throttle: 1 } })).ok).toBe(true);
  });

  it('accepts Sol-scale cruise state: Neptune distance at 2e6 m/s, out to the system extent', () => {
    const neptune = Math.hypot(...BODIES.neptune.center);
    expect(neptune).toBeGreaterThan(5e7); // ten times the schema-1 bound
    expect(validateSave(cruising([0, 0, -neptune], 2e6)).ok).toBe(true);
    expect(validateSave(cruising([0.7 * SYSTEM_EXTENT, 0, -0.7 * SYSTEM_EXTENT], 2e6)).ok).toBe(true);
  });

  it('accepts a landing pose and an on-foot player up to 4 R from the body center', () => {
    const R = BODIES.vesper.radius;
    expect(validateSave(sample({ lastSafeLanding: { ...sample().lastSafeLanding!, posPlanet: [0, 3.9 * R, 0] } })).ok).toBe(true);
    expect(validateSave(onFootAt('cairn', 3.9, 3.95)).ok).toBe(true);
  });

  it('accepts arrivals as discoveries and catalog powers as unlocks', () => {
    const d = sample({ discoveries: ['ilex', 'vesper', 'cairn'], unlocked: ['skyborne-flight', 'lunar-step', 'redline'] });
    const r = validateSave(d);
    expect(r.ok).toBe(true);
    if (r.ok) expect([r.data.discoveries, r.data.unlocked]).toEqual([d.discoveries, d.unlocked]);
  });

  const ON_FOOT = onFootAt('cairn', 1, 1.01);
  const bad: [string, unknown][] = [
    ['not an object', 'hello'],
    ['wrong schema', { ...sample(), schema: 99 }],
    ['other generator', { ...sample(), generator: GENERATOR_VERSION + 1 }],
    ['other seed', { ...sample(), seed: 12345 }],
    ['missing system', omit(sample(), 'system')],
    ['unknown system', { ...sample(), system: 'andromeda' }],
    ['a system not in play', { ...sample(), system: 'proxima' }],
    ['Sol with Quiet System bodies', { ...sample(), system: 'sol' }],
    ['NaN coordinate', sample({ ship: { ...sample().ship, sys: [NaN, 0, 0] } })],
    ['infinite velocity', sample({ ship: { ...sample().ship, vel: [Infinity, 0, 0] } })],
    ['coordinate out of bounds', sample({ ship: { ...sample().ship, sys: [9e9, 0, 0] } })],
    ['cruising beyond the system extent', cruising([0, 0, -1.01 * SYSTEM_EXTENT], 2e6)],
    ['cruising beyond the system extent diagonally', cruising([0.8 * SYSTEM_EXTENT, 0, -0.8 * SYSTEM_EXTENT], 2e6)],
    ['piloting at 1e5 m/s', sample({ mode: 'PILOTING', ship: { ...sample().ship, vel: [1e5, 0, 0] } })],
    ['landed at the body core', sample({ ship: { ...sample().ship, sys: [...BODIES.vesper.center] as V3 } })],
    ['last landing near the body core', sample({ lastSafeLanding: { ...sample().lastSafeLanding!, posPlanet: [0, 0, 0] } })],
    ['piloting above 20 km/s across axes', sample({ mode: 'PILOTING', ship: { ...sample().ship, vel: [15000, 15000, 0] } })],
    ['cruise above the longest hop cap', cruising([0, 0, -1e8], 1e7)],
    ['non-unit quaternion', sample({ ship: { ...sample().ship, quat: [0, 0, 0, 0.5] } })],
    ['unknown body', { ...sample(), bodyId: 'pluto' }],
    ['catalog body not in play', { ...sample(), bodyId: 'earth' }],
    ['the Sun as a body', { ...sample(), bodyId: 'sun' }],
    ['the schema-1 body field', omit({ ...sample(), body: 'vesper' }, 'bodyId')],
    ['landed 10 R from its body', sample({ ship: { ...sample().ship, sys: [BODIES.vesper.center[0] + 10 * BODIES.vesper.radius, 0, BODIES.vesper.center[2]] } })],
    ['on foot beyond 4 R', onFootAt('cairn', 3.9, 4.05)],
    ['relays on bodies not in play', sample({ expedition: { ...sample().expedition, relays: ['earth', 'mars', 'moon'], transmitted: true } })],
    ['last landing on a body not in play', sample({ lastSafeLanding: { ...sample().lastSafeLanding!, bodyId: 'sun' } })],
    ['last landing pose beyond 4 R', sample({ lastSafeLanding: { ...sample().lastSafeLanding!, posPlanet: [0, 4.1 * BODIES.vesper.radius, 0] } })],
    ['navigation to a body not in play', { ...sample(), navTarget: 'neptune' }],
    ['surface mode without body', sample({ bodyId: null })],
    ['on foot without player', sample({ mode: 'ON_FOOT' })],
    ['player while landed', sample({ player: { sys: [0, 0, 0], heading: [1, 0, 0], pitch: 0, abilityState: null } })],
    ['an ability state before PLAYER defines one', { ...ON_FOOT, player: { ...ON_FOOT.player!, abilityState: 'flight' } }],
    ['on foot without the ability state field', { ...ON_FOOT, player: omit(ON_FOOT.player!, 'abilityState') }],
    ['cruise state while landed', sample({ cruise: { speed: 100, throttle: 1 } })],
    ['missing discoveries', omit(sample(), 'discoveries')],
    ['unknown discovery', sample({ discoveries: ['pluto'] })],
    ['discovery of a body not in the catalog', sample({ discoveries: ['ilex', 'pluto'] })],
    ['duplicate discovery', sample({ discoveries: ['ilex', 'ilex'] })],
    ['missing unlocked list', omit(sample(), 'unlocked')],
    ['unknown power', sample({ unlocked: ['teleport'] })],
    ['walk as an unlock', sample({ unlocked: ['walk'] })],
    ['duplicate power', sample({ unlocked: ['redline', 'redline'] })],
    ['inventory not backed by collection', sample({ expedition: { ...sample().expedition, inventory: { ilex: 3, vesper: 0, cairn: 0 } } })],
    ['duplicate collected ID', sample({ expedition: { ...sample().expedition, collected: ['ilex:sample:0', 'ilex:sample:0'] } })],
    ['unknown sample ID', sample({ expedition: { ...sample().expedition, collected: ['ilex:sample:7'] } })],
    ['transmitted early', sample({ expedition: { ...sample().expedition, transmitted: true } })],
    ['bad throttle', sample({ ship: { ...sample().ship, throttle: 2 } })],
  ];
  for (const [name, value] of bad) {
    it(`rejects: ${name}`, () => {
      const r = validateSave(value);
      expect(r.ok).toBe(false);
    });
  }

  it('refuses the schema-1 record for play as earlier-version history', () => {
    const r = validateSave(schema1());
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/earlier version/);
  });

  it('rejects malformed files', () => {
    expect(importJson('{not json').ok).toBe(false);
    expect(importJson('x'.repeat(2_000_001)).ok).toBe(false);
  });
});

describe('schema-2 acceptance', () => {
  it('accepts ordinary flight near a body and catalog discoveries', () => {
    expect(validateSave(sample({ mode: 'PILOTING', ship: { ...sample().ship, vel: [180, -12, 40], gear: 0, throttle: 0.6 } })).ok).toBe(true);
    expect(validateSave(sample({ discoveries: ['ilex', 'earth', 'moon'] })).ok).toBe(true);
    expect(validateSave(sample({ discoveries: ['ilex', 'pluto'] })).ok).toBe(false);
  });
});

describe('save store', () => {
  it('keeps the previous good record in the same write', async () => {
    const kv = new FakeKv();
    const st = new SaveStore(kv as unknown as KvStore);
    await st.read();
    expect(await st.write(sample({ playTime: 1 }))).toBe(true);
    expect(await st.write(sample({ playTime: 2 }))).toBe(true);
    expect((kv.data.get(SAVE_KEY) as SaveData).playTime).toBe(2);
    expect((kv.data.get(PREV_KEY) as SaveData).playTime).toBe(1);
  });

  it('never overwrites a corrupt latest record silently or rotates it into the backup', async () => {
    const kv = new FakeKv();
    const good = sample({ playTime: 7 });
    kv.data.set(SAVE_KEY, { schema: SAVE_SCHEMA, garbage: true });
    kv.data.set(PREV_KEY, good);
    const st = new SaveStore(kv as unknown as KvStore);
    await st.read();
    expect(st.latest.present).toBe(true);
    expect(st.latest.data).toBeNull();
    expect(st.latest.error).toBeTruthy();
    expect(st.previous.data?.playTime).toBe(7);
    // Player picks the previous save and plays on: the next write preserves the corrupt original.
    expect(await st.write(sample({ playTime: 8 }))).toBe(true);
    expect(kv.data.get(CORRUPT_KEY)).toEqual({ schema: SAVE_SCHEMA, garbage: true });
    expect((kv.data.get(PREV_KEY) as SaveData).playTime).toBe(7);
    expect((kv.data.get(SAVE_KEY) as SaveData).playTime).toBe(8);
  });

  it('reports failed writes honestly and keeps the last good record', async () => {
    const kv = new FakeKv();
    const st = new SaveStore(kv as unknown as KvStore);
    await st.write(sample({ playTime: 1 }));
    const quota = new Error('quota');
    quota.name = 'QuotaExceededError';
    kv.failWrites = quota;
    expect(await st.write(sample({ playTime: 2 }))).toBe(false);
    expect(st.failure).toMatch(/full/);
    expect((kv.data.get(SAVE_KEY) as SaveData).playTime).toBe(1);
    expect(st.latest.data?.playTime).toBe(1);
  });

  it('keeps the frozen schema-1 record read-only under save-legacy and starts fresh', async () => {
    const kv = new FakeKv();
    kv.data.set(SAVE_KEY, schema1());
    const st = new SaveStore(kv as unknown as KvStore);
    await st.read();
    expect(st.latest).toEqual({ data: null, error: null, present: false });
    expect(st.legacy).toEqual({ schema: 1, savedAt: '2026-10-29T12:00:00.000Z', playTime: 4321.5, body: 'vesper', relays: 2, transmitted: false });
    expect(kv.data.get(LEGACY_KEY)).toEqual(SCHEMA1);
    // Saving the new game neither treats the old record as corrupt nor rotates it into the backup.
    expect(await st.write(sample({ playTime: 1 }))).toBe(true);
    expect(kv.data.has(CORRUPT_KEY)).toBe(false);
    expect(kv.data.has(PREV_KEY)).toBe(false);
    expect(kv.data.get(LEGACY_KEY)).toEqual(SCHEMA1);
    const again = new SaveStore(kv as unknown as KvStore);
    await again.read();
    expect(again.latest.data?.playTime).toBe(1);
    expect(again.legacy?.playTime).toBe(4321.5);
  });

  it('offers neither of a published build\'s two schema-1 records for play', async () => {
    const kv = new FakeKv();
    kv.data.set(SAVE_KEY, schema1());
    kv.data.set(PREV_KEY, { ...schema1(), playTime: 4000 });
    const st = new SaveStore(kv as unknown as KvStore);
    await st.read();
    expect(st.latest.present).toBe(false);
    expect(st.previous).toEqual({ data: null, error: null, present: false });
    expect(st.legacy?.playTime).toBe(4321.5); // the latest record is the history
  });

  it('classifies only older-schema records as legacy', () => {
    expect(legacySummary(sample())).toBeNull();
    expect(legacySummary({ ...sample(), schema: SAVE_SCHEMA + 1 })).toBeNull();
    expect(legacySummary('garbage')).toBeNull();
    expect(legacySummary({ schema: 0.5 })).toBeNull();
    // A damaged current-schema record is corrupt, not history; a damaged schema-1 record is history.
    expect(legacySummary({ schema: SAVE_SCHEMA, garbage: true })).toBeNull();
    expect(legacySummary({ schema: 1, garbage: true }))
      .toEqual({ schema: 1, savedAt: null, playTime: null, body: null, relays: null, transmitted: null });
    expect(legacySummary({ schema: SAVE_SCHEMA - 1, savedAt: 7, playTime: -1, body: null, expedition: { relays: 'x', transmitted: 1 } }))
      .toEqual({ schema: SAVE_SCHEMA - 1, savedAt: null, playTime: null, body: null, relays: null, transmitted: null });
    // An old backup file is still refused for play, with a reason.
    const r = importJson(JSON.stringify(SCHEMA1));
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/earlier version/);
  });

  it('works without storage: writes report failure, nothing throws', async () => {
    const st = new SaveStore(null);
    await st.read();
    expect(st.available).toBe(false);
    expect(await st.write(sample())).toBe(false);
    expect(st.failure).toMatch(/unavailable/);
  });
});
