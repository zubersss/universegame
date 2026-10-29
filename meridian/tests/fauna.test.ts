import { describe, expect, it } from 'vitest';
import { InstancedMesh, Matrix4, Vector3 } from 'three';
import { BODIES, GENERATOR_VERSION, SAVE_SCHEMA_VERSION, WORLD_SEED } from '../src/world/bodies';
import { computeSites, tangentBasis } from '../src/world/sites';
import { getSurface, SurfaceGenerator } from '../src/world/surface';
import { chunkAt, dirToFace } from '../src/world/cube';
import { FAUNA, faunaFor, type FaunaSpecies } from '../src/fauna/faunaSpecies';
import { spawnCell, spawnLevel, type Spawn } from '../src/fauna/spawn';
import { newCreatureState, stepBehaviour, type BehaviourParams, type Threats } from '../src/fauna/behaviour';
import { Creature, FaunaSystem, type FaunaContext } from '../src/fauna/FaunaSystem';
import { Expedition } from '../src/game/Expedition';
import { DEFAULT_SETTINGS } from '../src/game/settings';
import { exportJson, importJson, type SaveData } from '../src/save/SaveSystem';
import { CATALOG, catalogById } from '../src/fauna/catalog';
import { mulberry32 } from '../src/core/rng';

const ilex = BODIES.ilex;
const sites = computeSites(ilex);
const fresh = () => getSurface(ilex, sites.clearings);

/** Spawn cells in a square around the Ilex landing site. */
function cellsAround(n: number): [number, number, number][] {
  const L = spawnLevel(ilex);
  const f = dirToFace(...sites.landing.dir);
  const c = chunkAt(f.face, f.u, f.v, L);
  const out: [number, number, number][] = [];
  for (let j = -n; j <= n; j++) for (let i = -n; i <= n; i++) {
    const x = c.x + i, y = c.y + j;
    if (x >= 0 && y >= 0 && x < 2 ** L && y < 2 ** L) out.push([f.face, x, y]);
  }
  return out;
}

const fingerprint = (s: Spawn[]) => s.map((c) => `${c.id}|${c.home.map((v) => v.toFixed(12)).join(',')}|${c.x.toFixed(6)},${c.z.toFixed(6)}|${c.h.toFixed(6)}|${c.seed}`);

describe('fauna spawning', () => {
  it('is deterministic per seed, independent of generator instance and cell order', () => {
    const cells = cellsAround(3);
    const a = cells.flatMap(([f, x, y]) => fingerprint(spawnCell(ilex, fresh(), sites, faunaFor('ilex'), f, x, y)));
    const g = fresh();
    const b = [...cells].reverse().flatMap(([f, x, y]) => fingerprint(spawnCell(ilex, g, sites, faunaFor('ilex'), f, x, y)));
    expect(a.length).toBeGreaterThan(0);
    expect([...b].sort()).toEqual([...a].sort());
    expect(new Set(a.map((s) => s.split('|')[0])).size).toBe(a.length); // unique IDs
  });

  it('places herds near the Ilex landing site, outside the clearing and relay pad', () => {
    const g = fresh();
    const all = cellsAround(2).flatMap(([f, x, y]) => spawnCell(ilex, g, sites, faunaFor('ilex'), f, x, y));
    const R = ilex.radius;
    const dist = (d: readonly number[], e: readonly number[]) => Math.hypot(d[0] - e[0], d[1] - e[1], d[2] - e[2]) * R;
    const near = all.filter((s) => dist(s.home, sites.landing.dir) < 1500);
    expect(near.length).toBeGreaterThan(0);
    for (const s of all) {
      expect(dist(s.home, sites.landing.dir)).toBeGreaterThan(55);
      expect(Math.hypot(s.x, s.z)).toBeLessThanOrEqual(s.species.behaviour.homeRadius);
      expect(s.h).toBeGreaterThanOrEqual(s.species.hMin);
      expect(s.h).toBeLessThanOrEqual(s.species.hMax);
      // Scan records must pass save validation (ATLAS owns the schema).
      expect(s.id).toMatch(/^(ilex|vesper|cairn):[a-z0-9:/_-]+$/);
    }
  });

  it('appending a species never moves existing herds', () => {
    const extra: FaunaSpecies = { ...FAUNA[0], id: 'ilex-zzz', habitat: () => 1 };
    const g = fresh();
    for (const [f, x, y] of cellsAround(2)) {
      const before = fingerprint(spawnCell(ilex, g, sites, [FAUNA[0]], f, x, y));
      const after = fingerprint(spawnCell(ilex, g, sites, [extra, FAUNA[0]], f, x, y).filter((s) => s.species.id === FAUNA[0].id));
      expect(after).toEqual(before);
    }
  });
});

const P: BehaviourParams = {
  walkSpeed: 1, fleeSpeed: 3, turnRate: 1.5, homeRadius: 20, alertRadius: 25, fleeRadius: 9, shipFleeRadius: 120,
  idleMin: 2, idleMax: 4, callRate: 0,
};
const none = (): Threats => ({ player: false, px: 0, pz: 0, ship: false, sx: 0, sz: 0 });

describe('fauna behaviour', () => {
  it('idles, then wanders to a target inside the home radius and idles again', () => {
    const s = newCreatureState(0, 0, 0, 1);
    const rnd = mulberry32(7);
    stepBehaviour(s, P, none(), 0.5, rnd);
    expect(s.mode).toBe('idle');
    stepBehaviour(s, P, none(), 0.6, rnd);
    expect(s.mode).toBe('wander');
    expect(Math.hypot(s.tx, s.tz)).toBeLessThanOrEqual(P.homeRadius);
    let t = 0;
    while (s.mode === 'wander' && t < 120) {
      stepBehaviour(s, P, none(), 0.05, rnd);
      t += 0.05;
    }
    expect(s.mode).toBe('idle');
    expect(Math.hypot(s.x - s.tx, s.z - s.tz)).toBeLessThan(0.7);
  });

  it('stays near home over a long undisturbed soak', () => {
    const s = newCreatureState(3, -2, 1, 0);
    const rnd = mulberry32(11);
    let maxR = 0;
    for (let i = 0; i < 20 * 60 * 10; i++) {
      stepBehaviour(s, P, none(), 0.05, rnd);
      maxR = Math.max(maxR, Math.hypot(s.x, s.z));
      expect(Number.isFinite(s.x + s.z + s.yaw + s.speed)).toBe(true);
    }
    expect(maxR).toBeLessThan(P.homeRadius + 3);
  });

  it('stops to watch an approaching player, flees when close (one alarm), and returns home when calm', () => {
    const s = newCreatureState(0, 0, 0, 5);
    const rnd = mulberry32(3);
    const th = none();
    th.player = true;
    th.px = 20;
    th.pz = 0;
    expect(stepBehaviour(s, P, th, 0.1, rnd)).toBeNull();
    expect(s.mode).toBe('alert');
    for (let i = 0; i < 30; i++) stepBehaviour(s, P, th, 0.1, rnd);
    expect(s.mode).toBe('alert');
    expect(Math.abs(s.yaw - Math.PI / 2)).toBeLessThan(0.1); // faces the observer (+x)
    th.px = 6;
    const events: (string | null)[] = [];
    for (let i = 0; i < 40; i++) events.push(stepBehaviour(s, P, th, 0.1, rnd));
    expect(s.mode).toBe('flee');
    expect(events.filter((e) => e === 'alarm')).toHaveLength(1);
    expect(s.x).toBeLessThan(-3); // moved away from +x
    // Observer leaves: after the calm period it wanders back toward home.
    th.player = false;
    let t = 0;
    while (s.mode === 'flee' && t < 10) {
      stepBehaviour(s, P, th, 0.1, rnd);
      t += 0.1;
    }
    expect(s.mode).toBe('wander');
    expect(t).toBeLessThanOrEqual(2.5 + 1e-9); // calm period (it may already have outrun the threat radius)
    expect(Math.hypot(s.tx, s.tz)).toBeLessThanOrEqual(P.homeRadius);
  });

  it('flees from a loud ship but not from a quiet one at the same distance', () => {
    const rnd = mulberry32(5);
    const quiet = newCreatureState(0, 0, 0, 5);
    stepBehaviour(quiet, P, { ...none(), ship: false, sx: 50, sz: 0 }, 0.1, rnd);
    expect(quiet.mode).toBe('idle');
    const loud = newCreatureState(0, 0, 0, 5);
    expect(stepBehaviour(loud, P, { ...none(), ship: true, sx: 50, sz: 0 }, 0.1, rnd)).toBe('alarm');
    expect(loud.mode).toBe('flee');
  });
});

describe('fauna system', () => {
  const gen = fresh();
  const landing = new Vector3(...sites.landing.dir).multiplyScalar(ilex.radius + sites.landing.height);

  function system(): FaunaSystem {
    return new FaunaSystem(ilex, gen, sites, 3);
  }

  it('loads herds around the camera, snaps them to the ground and culls beyond range', () => {
    const f = system();
    const ctx: FaunaContext = { view: landing.clone(), planetLocal: new Vector3(), player: null, ship: landing.clone(), shipLoud: false };
    for (let i = 0; i < 60; i++) f.update(1 / 60, ctx);
    expect(f.stats.pending).toBe(0);
    expect(f.stats.creatures).toBeGreaterThan(0);
    const all = f.nearby(landing, 5000);
    for (const c of all) {
      const ground = ilex.radius + gen.height(c.up.x, c.up.y, c.up.z);
      expect(Math.abs(c.p.length() - ground)).toBeLessThan(0.2);
    }
    expect(f.stats.drawn).toBe(all.filter((c) => c.dist <= c.species.range).length);
    f.dispose();
  });

  it('a creature flees from the player walking up to it, and is reported by nearby()', () => {
    const f = system();
    const ctx: FaunaContext = { view: landing.clone(), planetLocal: new Vector3(), player: null, ship: landing.clone(), shipLoud: false };
    for (let i = 0; i < 30; i++) f.update(1 / 60, ctx);
    const target = f.nearby(landing, 3000).sort((a, b) => a.dist - b.dist)[0];
    expect(target).toBeDefined();
    // Camera and player 5 m from the creature.
    const up = target.up.clone();
    const side = new Vector3(1, 0, 0).cross(up).normalize();
    const player = target.p.clone().addScaledVector(side, 5).addScaledVector(up, 1.6);
    ctx.view.copy(player);
    ctx.player = player;
    const events: string[] = [];
    f.onEvent = (ev, c) => {
      if (c === target) events.push(ev);
    };
    const start = target.p.clone();
    for (let i = 0; i < 120; i++) f.update(1 / 60, ctx);
    expect(target.state.mode).toBe('flee');
    expect(events).toContain('alarm');
    expect(target.p.distanceTo(player)).toBeGreaterThan(start.distanceTo(player));
    expect(f.nearby(player, 40)).toContain(target);
    f.dispose();
  });
});

describe('journal catalog', () => {
  it('has unique IDs and includes every fauna species with field notes', () => {
    expect(new Set(CATALOG.map((e) => e.id)).size).toBe(CATALOG.length);
    for (const sp of FAUNA) {
      const e = catalogById(sp.id);
      expect(e?.kind).toBe('fauna');
      expect(sp.description.length).toBeGreaterThan(80);
      expect(sp.id).toMatch(/^(ilex|vesper|cairn)-[a-z]+$/);
    }
    expect(catalogById('cairn-pebbles')).toBeUndefined(); // not scannable
  });
});

describe('fauna placement and floating origin', () => {
  const gen = fresh();

  it('stands on the flattened clearing surface, not the raw terrain, inside a landing clearing', () => {
    const f = new FaunaSystem(ilex, gen, sites, 3);
    const dir = sites.landing.dir;
    const home = [...dir] as [number, number, number];
    const [a1, a2] = tangentBasis(home);
    // 40 m from the centre: inside the flat part (r0 = 55 m) where raw terrain differs.
    let checked = 0;
    for (const [x, z] of [[40, 0], [0, 40], [-40, 0], [0, -40], [28, 28]]) {
      const c = new Creature({ id: 'ilex:fauna:test:0', species: FAUNA[0], home, t1: a1, t2: a2, x, z, yaw: 0, h: 2, seed: 1 });
      f.place(c);
      expect(Math.abs(c.p.length() - (ilex.radius + sites.landing.height - 0.03 * 2))).toBeLessThan(0.02);
      const raw = new SurfaceGenerator(ilex).height(c.up.x, c.up.y, c.up.z);
      if (Math.abs(raw - sites.landing.height) > 0.05) checked++;
    }
    expect(checked).toBeGreaterThan(0); // the clearing really changes the height there
    f.dispose();
  });

  it('keeps planet-relative positions when the floating origin moves (rebase)', () => {
    const f = new FaunaSystem(ilex, gen, sites, 3);
    const landing = new Vector3(...sites.landing.dir).multiplyScalar(ilex.radius + sites.landing.height);
    const planetLocal = new Vector3(-landing.x + 300, -landing.y, -landing.z + 120);
    const ctx: FaunaContext = { view: landing.clone(), planetLocal, player: null, ship: landing.clone(), shipLoud: false };
    for (let i = 0; i < 40; i++) f.update(1 / 60, ctx);
    const local = () => {
      const out: Record<string, number[]> = {};
      const m = new Matrix4();
      const v = new Vector3();
      for (const mesh of f.group.children as InstancedMesh[]) {
        for (let i = 0; i < mesh.count; i++) {
          mesh.getMatrixAt(i, m);
          v.setFromMatrixPosition(m).add(f.group.position);
          out[`${mesh.id}:${i}`] = v.toArray();
        }
      }
      return out;
    };
    const planetRel = () => f.nearby(landing, 5000).map((c) => c.p.toArray());
    const before = local();
    const relBefore = planetRel();
    expect(Object.keys(before).length).toBeGreaterThan(0);
    // Rebase by d: local coordinates (and the body center) shift by d; nothing else changes.
    const d = new Vector3(-2048, 1024, 3072);
    planetLocal.add(d);
    f.update(0, ctx);
    const after = local();
    for (const k of Object.keys(before)) {
      for (let j = 0; j < 3; j++) expect(after[k][j] - before[k][j]).toBeCloseTo(d.getComponent(j), 3);
    }
    expect(planetRel()).toEqual(relBefore);
    f.dispose();
  });

  it('a journal with a creature entry survives a save export/import round trip', () => {
    const e = new Expedition();
    e.scan('ilex:fauna:ilex-trine:3/45/67:0:2', 'ilex-trine');
    const data = {
      schema: SAVE_SCHEMA_VERSION, generator: GENERATOR_VERSION, seed: WORLD_SEED, savedAt: '2026-10-29T12:00:00.000Z', playTime: 1, mode: 'LANDED', body: 'ilex',
      ship: { sys: [1, 2, 60000], quat: [0, 0, 0, 1], vel: [0, 0, 0], gear: 1, throttle: 0 },
      player: null, cruise: null, lastSafeLanding: null, navTarget: null, settings: { ...DEFAULT_SETTINGS }, expedition: e.state,
    } as unknown as SaveData;
    const r = importJson(exportJson(data));
    expect(r.ok ? null : r.error).toBeNull();
    if (r.ok) {
      expect(r.data.expedition.species).toEqual(['ilex-trine']);
      expect(r.data.expedition.scanned).toEqual(['ilex:fauna:ilex-trine:3/45/67:0:2']);
    }
  });
});

describe('journal progress and species order', () => {
  it('counts per world and kind, ignoring unknown and other-world IDs', async () => {
    const { worldProgress, progressLine } = await import('../src/fauna/catalog');
    const p = worldProgress('ilex', ['ilex-trine', 'ilex-fan', 'vesper-glass', 'ilex-nothing', 'ilex-fan']);
    expect(p.byKind.fauna.found).toBe(1);
    expect(p.byKind.flora.found).toBe(1);
    expect(p.found).toBe(2);
    expect(p.total).toBe(CATALOG.filter((e) => e.body === 'ilex').length);
    expect(progressLine(p)).toMatch(/^Flora 1 of \d+ · Minerals 0 of \d+ · Fauna 1 of \d+$/);
    expect(worldProgress('cairn', []).byKind.fauna.total).toBe(0);
    expect(progressLine(worldProgress('cairn', []))).not.toMatch(/Fauna/);
  });

  it('every existing body has at least four flora/mineral species, and the original species keep their per-body order', async () => {
    const { speciesFor } = await import('../src/props/species');
    // Per-body index is part of the prop placement hash: these prefixes must never change.
    const original: Record<string, string[]> = {
      ilex: ['ilex-lantern', 'ilex-chalk', 'ilex-fan'],
      vesper: ['vesper-glass', 'vesper-pillar', 'vesper-bristle'],
      cairn: ['cairn-rime', 'cairn-boulder', 'cairn-pebbles'],
    };
    for (const [b, ids] of Object.entries(original)) {
      expect(speciesFor(b as 'ilex').slice(0, ids.length).map((s) => s.id)).toEqual(ids);
    }
    for (const b of ['ilex', 'vesper'] as const) expect(CATALOG.filter((e) => e.body === b && e.kind !== 'fauna').length).toBeGreaterThanOrEqual(4);
  });
});

describe('curious species and Vesper herds', () => {
  it('a curious creature closes in to its distance, stops, and never strays past its leash', () => {
    const p: BehaviourParams = { ...P, curiousDistance: 15, alertRadius: 32, fleeRadius: 6 };
    const s = newCreatureState(0, 0, 0, 5);
    const rnd = mulberry32(9);
    const th = none();
    th.player = true;
    th.px = 28;
    th.pz = 0;
    for (let i = 0; i < 600; i++) stepBehaviour(s, p, th, 0.05, rnd);
    expect(s.mode).toBe('alert');
    const d = Math.hypot(s.x - th.px, s.z - th.pz);
    expect(d).toBeGreaterThan(14);
    expect(d).toBeLessThan(16.5);
    expect(s.speed).toBeLessThan(0.05);
    // Observer far from home: it follows only to 2.5× the home radius.
    th.px = 200;
    const t = newCreatureState(0, 0, 0, 5);
    t.mode = 'alert';
    t.timer = 1e9;
    for (let i = 0; i < 4000; i++) {
      t.mode = 'alert'; // keep it watching (the observer is beyond the alert radius here)
      stepBehaviour(t, p, th, 0.05, rnd);
    }
    expect(Math.hypot(t.x, t.z)).toBeLessThan(P.homeRadius * 2.5 + 1);
  });

  it('spawns dune sledge herds near the Vesper landing site', () => {
    const vesper = BODIES.vesper;
    const vs = computeSites(vesper);
    const g = getSurface(vesper, vs.clearings);
    const L = spawnLevel(vesper);
    const f = dirToFace(...vs.landing.dir);
    const c = chunkAt(f.face, f.u, f.v, L);
    const all: Spawn[] = [];
    for (let j = -3; j <= 3; j++) for (let i = -3; i <= 3; i++) all.push(...spawnCell(vesper, g, vs, faunaFor('vesper'), f.face, c.x + i, c.y + j));
    expect(all.length).toBeGreaterThan(0);
    expect(all.every((s) => s.species.id === 'vesper-sledge')).toBe(true);
    const near = Math.min(...all.map((s) => Math.hypot(s.home[0] - vs.landing.dir[0], s.home[1] - vs.landing.dir[1], s.home[2] - vs.landing.dir[2]) * vesper.radius));
    expect(near).toBeLessThan(1500);
  });

  it('emits footfalls per the species gait (3 beats for the trine) with beat indices', () => {
    const f = new FaunaSystem(ilex, getSurface(ilex, sites.clearings), sites, 3);
    const landing = new Vector3(...sites.landing.dir).multiplyScalar(ilex.radius + sites.landing.height);
    const ctx: FaunaContext = { view: landing.clone(), planetLocal: new Vector3(), player: null, ship: landing.clone(), shipLoud: false };
    f.update(1 / 60, ctx);
    for (let i = 0; i < 30; i++) f.update(1 / 60, ctx);
    const c = f.nearby(landing, 3000).sort((a, b) => a.dist - b.dist)[0];
    ctx.view.copy(c.p); // camera on it: full-rate updates, footfalls in range
    c.state.mode = 'wander';
    c.state.tx = 1e4;
    c.state.tz = 0;
    const beats: number[] = [];
    f.onEvent = (ev, cr) => {
      if (ev === 'step' && cr === c) beats.push(cr.beat);
    };
    for (let i = 0; i < 600; i++) f.update(1 / 60, ctx);
    expect(beats.length).toBeGreaterThan(3);
    expect(new Set(beats)).toEqual(new Set([0, 1, 2]));
    f.dispose();
  });
});

describe('fauna sound intensity', () => {
  it('accents the first footfall, scales with pace, and keeps alarms loudest', async () => {
    const { faunaSoundIntensity } = await import('../src/fauna/FaunaSystem');
    const spawn = { id: 'ilex:fauna:t:0', species: FAUNA[0], home: [0, 1, 0] as [number, number, number], t1: [1, 0, 0] as [number, number, number], t2: [0, 0, 1] as [number, number, number], x: 0, z: 0, yaw: 0, h: 2, seed: 1 };
    const c = new Creature(spawn);
    c.state.speed = FAUNA[0].behaviour.walkSpeed;
    c.beat = 0;
    const accent = faunaSoundIntensity('step', c);
    c.beat = 1;
    const plain = faunaSoundIntensity('step', c);
    expect(accent).toBeGreaterThan(plain);
    c.state.speed = FAUNA[0].behaviour.fleeSpeed;
    expect(faunaSoundIntensity('step', c)).toBeGreaterThan(plain);
    expect(faunaSoundIntensity('alarm', c)).toBe(1);
    expect(faunaSoundIntensity('call', c)).toBeLessThan(1);
    for (const ev of ['step', 'call', 'alarm'] as const) expect(faunaSoundIntensity(ev, c)).toBeLessThanOrEqual(1);
  });
});
