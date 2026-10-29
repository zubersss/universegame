import { describe, expect, it } from 'vitest';
import {
  CORRUPT_KEY, PREV_KEY, SAVE_KEY, SaveStore, exportJson, importJson, validateSave, type SaveData,
} from '../src/save/SaveSystem';
import type { KvStore } from '../src/save/db';
import { GENERATOR_VERSION, SAVE_SCHEMA_VERSION, WORLD_SEED } from '../src/world/bodies';
import { DEFAULT_SETTINGS } from '../src/game/settings';

function sample(overrides: Partial<SaveData> = {}): SaveData {
  return {
    schema: SAVE_SCHEMA_VERSION,
    generator: GENERATOR_VERSION,
    seed: WORLD_SEED,
    savedAt: '2026-10-29T12:00:00.000Z',
    playTime: 321.5,
    mode: 'LANDED',
    body: 'vesper',
    ship: { sys: [790000.5, -41000.25, -598000.125], quat: [0, 0, 0, 1], vel: [0, 0, 0], gear: 1, throttle: 0 },
    player: null,
    cruise: null,
    lastSafeLanding: { body: 'vesper', posPlanet: [-17000, -41000, 4500], quat: [0, 0.7071067811865476, 0, 0.7071067811865476] },
    navTarget: 'cairn',
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
    expect(validateSave(sample({ mode: 'ON_FOOT', player: { sys: [790010, -41000, -598000], heading: [1, 0, 0], pitch: 0.2 } })).ok).toBe(true);
    expect(validateSave(sample({ mode: 'CRUISING', body: null, cruise: { speed: 12000, throttle: 1 } })).ok).toBe(true);
  });

  const bad: [string, unknown][] = [
    ['not an object', 'hello'],
    ['wrong schema', { ...sample(), schema: 99 }],
    ['other generator', { ...sample(), generator: GENERATOR_VERSION + 1 }],
    ['other seed', { ...sample(), seed: 12345 }],
    ['NaN coordinate', sample({ ship: { ...sample().ship, sys: [NaN, 0, 0] } })],
    ['infinite velocity', sample({ ship: { ...sample().ship, vel: [Infinity, 0, 0] } })],
    ['coordinate out of bounds', sample({ ship: { ...sample().ship, sys: [9e9, 0, 0] } })],
    ['non-unit quaternion', sample({ ship: { ...sample().ship, quat: [0, 0, 0, 0.5] } })],
    ['unknown body', { ...sample(), body: 'pluto' }],
    ['surface mode without body', sample({ body: null })],
    ['on foot without player', sample({ mode: 'ON_FOOT' })],
    ['player while landed', sample({ player: { sys: [0, 0, 0], heading: [1, 0, 0], pitch: 0 } })],
    ['cruise state while landed', sample({ cruise: { speed: 100, throttle: 1 } })],
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

  it('rejects malformed files', () => {
    expect(importJson('{not json').ok).toBe(false);
    expect(importJson('x'.repeat(2_000_001)).ok).toBe(false);
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
    kv.data.set(SAVE_KEY, { schema: 1, garbage: true });
    kv.data.set(PREV_KEY, good);
    const st = new SaveStore(kv as unknown as KvStore);
    await st.read();
    expect(st.latest.present).toBe(true);
    expect(st.latest.data).toBeNull();
    expect(st.latest.error).toBeTruthy();
    expect(st.previous.data?.playTime).toBe(7);
    // Player picks the previous save and plays on: the next write preserves the corrupt original.
    expect(await st.write(sample({ playTime: 8 }))).toBe(true);
    expect(kv.data.get(CORRUPT_KEY)).toEqual({ schema: 1, garbage: true });
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

  it('works without storage: writes report failure, nothing throws', async () => {
    const st = new SaveStore(null);
    await st.read();
    expect(st.available).toBe(false);
    expect(await st.write(sample())).toBe(false);
    expect(st.failure).toMatch(/unavailable/);
  });
});
