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
      inventory: { ilex: 1, vesper: 0, cairn: 0, orrin: 0, saro: 0 },
      collected: ['ilex:sample:0', 'ilex:sample:2', 'vesper:sample:1'],
      relays: ['ilex', 'vesper'],
      species: ['ilex-lantern', 'vesper-glass'],
      scanned: ['ilex:ilex-lantern:5/10/2/3:4', 'vesper:relay'],
      transmitted: false,
      extendedTransmitted: false,
    },
    ...overrides,
  };
}

/** A schema-1 record exactly as the three-body release wrote it. */
function v1(overrides: Record<string, unknown> = {}, expedition: Record<string, unknown> = {}): Record<string, unknown> {
  const d = sample();
  const { extendedTransmitted: _x, ...exp } = d.expedition;
  return {
    ...d,
    schema: 1,
    expedition: { ...exp, inventory: { ilex: 1, vesper: 0, cairn: 0 }, ...expedition },
    ...overrides,
  };
}

/** Every relay active and both surveys transmitted (schema 2 only). */
function complete(): SaveData {
  const bodies = ['ilex', 'vesper', 'cairn', 'orrin', 'saro'] as const;
  return sample({
    body: 'saro',
    lastSafeLanding: { body: 'saro', posPlanet: [1000, 37000, 5000], quat: [0, 0, 0, 1] },
    navTarget: null,
    expedition: {
      inventory: { ilex: 0, vesper: 0, cairn: 0, orrin: 1, saro: 0 },
      collected: [...bodies.map((b) => `${b}:sample:0`), 'orrin:sample:2'],
      relays: [...bodies],
      species: ['ilex-lantern', 'orrin-moss'],
      scanned: ['orrin:relay', 'saro:saro-salt:7/1/2/3:4'],
      transmitted: true,
      extendedTransmitted: true,
    },
  });
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
    ['inventory not backed by collection', sample({ expedition: { ...sample().expedition, inventory: { ilex: 3, vesper: 0, cairn: 0, orrin: 0, saro: 0 } } })],
    ['schema-2 inventory missing a body', { ...sample(), expedition: { ...sample().expedition, inventory: { ilex: 1, vesper: 0, cairn: 0 } } }],
    ['unknown inventory body', { ...sample(), expedition: { ...sample().expedition, inventory: { ...sample().expedition.inventory, pluto: 0 } } }],
    ['schema-2 extended flag missing', (() => { const d = sample(); const { extendedTransmitted: _x, ...e } = d.expedition; return { ...d, expedition: e }; })()],
    ['extended flag not boolean', { ...sample(), expedition: { ...sample().expedition, extendedTransmitted: 1 } }],
    ['extended survey before the core survey', { ...complete(), expedition: { ...complete().expedition, transmitted: false } }],
    ['extended survey without its relays', { ...complete(), expedition: { ...complete().expedition, relays: ['ilex', 'vesper', 'cairn', 'orrin'] } }],
    ['future schema', { ...sample(), schema: 3 }],
    ['schema 1 naming a new body', v1({ body: 'orrin' })],
    ['schema 1 with a new body in its inventory', v1({}, { inventory: { ilex: 1, vesper: 0, cairn: 0, orrin: 0 } })],
    ['schema 1 with a new body relay', v1({}, { relays: ['ilex', 'saro'] })],
    ['schema 1 with a new body sample', v1({}, { collected: ['ilex:sample:0', 'saro:sample:0'] })],
    ['schema 1 navigating to a new body', v1({ navTarget: 'saro' })],
    ['corrupt schema 1 record', { schema: 1, garbage: true }],
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

  it('accepts schema 2 progress on every world, including the Extended Survey', () => {
    const d = complete();
    const r = validateSave(d);
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.data).toEqual(d);
  });

  it('migrates schema 1 to schema 2 keeping all progress', () => {
    const r = validateSave(v1());
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.data).toEqual(sample());
    expect(r.data.schema).toBe(2);
    expect(r.data.expedition.inventory).toEqual({ ilex: 1, vesper: 0, cairn: 0, orrin: 0, saro: 0 });
    expect(r.data.expedition.extendedTransmitted).toBe(false);
    // A finished schema-1 expedition stays finished; the Extended Survey is still open.
    const done = v1({ navTarget: null }, {
      inventory: { ilex: 0, vesper: 0, cairn: 1 },
      collected: ['ilex:sample:0', 'vesper:sample:1', 'cairn:sample:2', 'cairn:sample:0'],
      relays: ['ilex', 'vesper', 'cairn'],
      transmitted: true,
    });
    const r2 = validateSave(done);
    expect(r2.ok).toBe(true);
    if (r2.ok) {
      expect(r2.data.expedition.transmitted).toBe(true);
      expect(r2.data.expedition.extendedTransmitted).toBe(false);
      expect(r2.data.expedition.relays).toEqual(['ilex', 'vesper', 'cairn']);
      expect(r2.data.expedition.inventory.cairn).toBe(1);
    }
  });

  it('exports and imports across schemas', () => {
    // A schema-1 backup file imports (migrated); re-exporting writes schema 2 that imports identically.
    const a = importJson(JSON.stringify(v1(), null, 1));
    expect(a.ok).toBe(true);
    if (!a.ok) return;
    const text = exportJson(a.data);
    expect(JSON.parse(text).schema).toBe(2);
    const b = importJson(text);
    expect(b.ok).toBe(true);
    if (b.ok) expect(b.data).toEqual(a.data);
    const c = importJson(exportJson(complete()));
    expect(c.ok).toBe(true);
    if (c.ok) expect(c.data).toEqual(complete());
  });

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

  it('loads schema-1 records from storage migrated and rotates them into the backup on the next write', async () => {
    const kv = new FakeKv();
    kv.data.set(SAVE_KEY, v1());
    kv.data.set(PREV_KEY, v1({ playTime: 100 }));
    const store = new SaveStore(kv as unknown as KvStore);
    await store.read();
    expect(store.latest.data).toEqual(sample());
    expect(store.previous.data?.playTime).toBe(100);
    expect(store.previous.data?.schema).toBe(2);
    expect(await store.write(complete())).toBe(true);
    // The old (valid, schema-1) latest record is kept as the previous-good backup.
    expect((kv.data.get(PREV_KEY) as { schema: number }).schema).toBe(1);
    const again = new SaveStore(kv as unknown as KvStore);
    await again.read();
    expect(again.latest.data).toEqual(complete());
    expect(again.previous.data).toEqual(sample());
  });

  it('quarantines a corrupt latest record next to a valid schema-1 backup', async () => {
    const kv = new FakeKv();
    kv.data.set(SAVE_KEY, v1({ schema: 1, expedition: 'broken' }));
    kv.data.set(PREV_KEY, v1());
    const store = new SaveStore(kv as unknown as KvStore);
    await store.read();
    expect(store.latest.present).toBe(true);
    expect(store.latest.data).toBeNull();
    expect(store.latest.error).toMatch(/progress/);
    expect(store.previous.data).toEqual(sample());
    expect(await store.write(sample())).toBe(true);
    expect((kv.data.get(CORRUPT_KEY) as { expedition: unknown }).expedition).toBe('broken');
    // The corrupt record never becomes the backup.
    expect((kv.data.get(PREV_KEY) as { schema: number }).schema).toBe(1);
  });

  it('works without storage: writes report failure, nothing throws', async () => {
    const st = new SaveStore(null);
    await st.read();
    expect(st.available).toBe(false);
    expect(await st.write(sample())).toBe(false);
    expect(st.failure).toMatch(/unavailable/);
  });
});
