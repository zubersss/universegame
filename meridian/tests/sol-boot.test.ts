// L7b/L6b: Sol behind ?system=sol. The system switch made at boot, the start
// pose (and the photo camera's site frame), the handoff (activation) policy,
// the cruise hop (and a restored cruise's cap), saves on landable bodies and
// across systems, the navigation panel's digit keys and the background far
// plane, in Node; boot's order and Game's use of the policy and the hop are
// checked in their source. The browser journey is e2e/journey/travel.spec.ts ("Sol: Earth -> Moon hop").
import { readdirSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { afterEach, beforeAll, describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import {
  BODIES, BODY_IDS, GENERATOR_VERSION, PLAY_SYSTEM, SOL_M2_BODIES, SOL_TRAVEL_ORDER, SYSTEM_BODY_IDS, SYSTEM_EXTENT, WORLD_SEED,
  setPlaySystem, sunDirFor, type BodyId,
} from '../src/world/bodies';
import { BELTS } from '../src/world/catalog';
import { EARTH_META, installEarthData, loadEarthData, type LayerName } from '../src/world/earthData';
import { bodyDataReady, getSurface } from '../src/world/surface';
import { computeSites, tangentBasis } from '../src/world/sites';
import { generateChunk } from '../src/terrain/chunkGen';
import { canActivate, playBodies, proxyBodies, siteFrame, startBodyOf, startSite, surfaceReady, systemFromQuery } from '../src/game/playSystem';
import { CRUISE, SIM_DT, SURFACE_READY } from '../src/game/config';
import { CruiseController, blockedBy, cruiseHop, hopDistance, planPath, resumeCap, routeHop, safetyRadius } from '../src/ship/Cruise';
import { cruiseMaxSpeed } from '../src/world/scale';
import { quatFromForwardUp } from '../src/core/mathx';
import { CORRUPT_KEY, PREV_KEY, SAVE_KEY, SAVE_SCHEMA, SaveStore, unloadableNote, validateSave, type SaveData } from '../src/save/SaveSystem';
import type { KvStore } from '../src/save/db';
import { newExpedition, powerFor } from '../src/game/Expedition';
import { DEFAULT_SETTINGS } from '../src/game/settings';
import { kindLabel, navKeyIndex, navKeyLabel } from '../src/ui/Panel';
import { BG_FAR } from '../src/render/RenderSystem';
import { BG_SCALE } from '../src/render/BodyProxies';

const center = (id: BodyId) => new Vector3(...BODIES[id].center);

beforeAll(async () => {
  // Earth is a data body: its sites need the rasters in this thread (boot awaits ensureBodyData).
  const dir = fileURLToPath(new URL('../src/data/earth/', import.meta.url));
  const layers = EARTH_META.layers as Record<LayerName, { file: string }>;
  installEarthData(await loadEarthData(async (name) => readFileSync(dir + layers[name].file)));
});

// Every test starts and ends in the default Quiet System.
afterEach(() => setPlaySystem(playBodies('quiet')));

/** A landed Sol save at Earth (schema 2), valid while Sol is in play. */
function solSave(overrides: Partial<SaveData> = {}): SaveData {
  const R = BODIES.earth.radius;
  const c = BODIES.earth.center;
  return {
    schema: SAVE_SCHEMA,
    generator: GENERATOR_VERSION,
    seed: WORLD_SEED,
    savedAt: '2026-10-30T12:00:00.000Z',
    playTime: 42,
    system: 'sol',
    mode: 'LANDED',
    bodyId: 'earth',
    ship: { sys: [c[0] + R + 100, c[1], c[2]], quat: [0, 0, 0, 1], vel: [0, 0, 0], gear: 1, throttle: 0 },
    player: null,
    cruise: null,
    lastSafeLanding: { bodyId: 'earth', posPlanet: [R + 100, 0, 0], quat: [0, 0, 0, 1] },
    navTarget: 'moon',
    discoveries: ['earth'],
    unlocked: [powerFor('earth')!],
    settings: { ...DEFAULT_SETTINGS },
    expedition: newExpedition(),
    ...overrides,
  };
}

/** A landed Quiet save at Ilex (schema 2), valid while the Quiet System is in play. */
function quietSave(): SaveData {
  const R = BODIES.ilex.radius;
  return solSave({
    system: 'quiet',
    bodyId: 'ilex',
    ship: { sys: [R + 100, 0, 0], quat: [0, 0, 0, 1], vel: [0, 0, 0], gear: 1, throttle: 0 },
    lastSafeLanding: { bodyId: 'ilex', posPlanet: [R + 100, 0, 0], quat: [0, 0, 0, 1] },
    navTarget: 'vesper',
    discoveries: ['ilex'],
    unlocked: [],
  });
}

describe('play system switch (?system=)', () => {
  it('reads quiet or sol from the query; anything else is the Quiet System', () => {
    expect(systemFromQuery(null)).toBe('quiet');
    expect(systemFromQuery('quiet')).toBe('quiet');
    expect(systemFromQuery('sol')).toBe('sol');
    for (const v of ['', 'SOL', 'Sol', 'sol ', 'proxima', 'earth']) expect(systemFromQuery(v)).toBe('quiet');
    expect(systemFromQuery(new URLSearchParams('?preset=low&system=sol').get('system'))).toBe('sol');
    expect(systemFromQuery(new URLSearchParams('?preset=low').get('system'))).toBe('quiet');
  });

  it("plays the whole Quiet System, or Sol's ten M2 bodies in travel order (belts are not bodies)", () => {
    expect(playBodies('quiet')).toEqual(SYSTEM_BODY_IDS.quiet);
    const sol = playBodies('sol');
    expect(sol).toEqual(SOL_M2_BODIES);
    expect(sol).toHaveLength(10);
    const order = SOL_TRAVEL_ORDER.flatMap((e) => ('body' in e ? [e.body] : []));
    expect(order.filter((id) => sol.includes(id))).toEqual([...sol]);
    expect(sol.some((id) => BELTS.some((b) => b.id === id))).toBe(false);
  });

  it('boot sets the system once, before it reads saves, loads surface data or builds the game', () => {
    // Save validation reads BODY_IDS at call time and the Game constructor builds
    // the proxies, the start pose and the cruise from it, so the order is the contract.
    const src = readFileSync(new URL('../src/game/boot.ts', import.meta.url), 'utf8');
    const set = src.indexOf("setPlaySystem(playBodies(systemFromQuery(params.get('system'))));");
    expect(set).toBeGreaterThan(src.indexOf('export async function boot('));
    expect(src.match(/setPlaySystem\(/g)).toHaveLength(1);
    for (const later of ['new SaveStore(kv)', 'await saves.read()', 'ensureBodyData(d)', 'game = new Game(']) {
      expect(src.indexOf(later)).toBeGreaterThan(set);
    }
    expect(src.indexOf('ensureBodyData(d)')).toBeLessThan(src.indexOf('game = new Game('));
    // Nothing else in the game switches the system (bodies.ts defines it).
    const root = fileURLToPath(new URL('../src/', import.meta.url));
    const callers = readdirSync(root, { recursive: true, encoding: 'utf8' })
      .filter((f) => f.endsWith('.ts') && readFileSync(root + f, 'utf8').includes('setPlaySystem('))
      .map((f) => f.replaceAll('\\', '/'));
    expect(callers.sort()).toEqual(['game/boot.ts', 'world/bodies.ts']);
  });

  it('save validation follows the system in play (BODY_IDS is read at call time)', () => {
    expect(PLAY_SYSTEM).toBe('quiet');
    expect(validateSave(quietSave()).ok).toBe(true);
    expect(validateSave(solSave()).ok).toBe(false);
    setPlaySystem(playBodies('sol'));
    expect(PLAY_SYSTEM).toBe('sol');
    expect(BODY_IDS).toEqual(SOL_M2_BODIES);
    const r = validateSave(quietSave());
    expect(r.ok).toBe(false);
    expect(r.ok ? '' : r.error).toMatch(/another star system/);
    expect(validateSave(solSave()).ok).toBe(true);
  });
});

describe('saves across systems (one save slot until step 10)', () => {
  /** In-memory stand-in for the IndexedDB store (as in save.test). */
  class MemKv {
    data = new Map<string, unknown>();
    async get(key: string) {
      return this.data.get(key);
    }
    async put(key: string, value: unknown) {
      this.data.set(key, structuredClone(value));
    }
    async rotateAndPut(key: string, backupKey: string, value: unknown, keep: (old: unknown) => boolean) {
      const old = this.data.get(key);
      if (old !== undefined && keep(old)) this.data.set(backupKey, old);
      this.data.set(key, structuredClone(value));
    }
  }
  const store = async (records: Record<string, unknown>) => {
    const kv = new MemKv();
    for (const [k, v] of Object.entries(records)) kv.data.set(k, v);
    const st = new SaveStore(kv as unknown as KvStore);
    await st.read();
    return { kv, st };
  };

  it('in Sol a Quiet System save says saving here replaces it; the first save sets it aside in the free key', async () => {
    setPlaySystem(playBodies('sol'));
    const { kv, st } = await store({ [SAVE_KEY]: quietSave() });
    expect(st.latest).toMatchObject({ data: null, present: true });
    expect([st.otherSystem, st.asideFree]).toEqual([{ latest: 'quiet', previous: null }, true]);
    expect(unloadableNote(st)).toBe(
      'The latest save is from the Quiet System and cannot be continued in Sol. Saving in this system replaces it: ' +
        'the first save sets it aside in browser storage, where no menu can load it. Start a new expedition.',
    );
    expect(await st.write(solSave())).toBe(true);
    expect(kv.data.get(CORRUPT_KEY)).toEqual(quietSave());
    expect(kv.data.get(SAVE_KEY)).toEqual(solSave());
    expect(kv.data.has(PREV_KEY)).toBe(false);
    expect(st.asideFree).toBe(false);
  });

  it('with the corrupt key taken the note says neither save is kept; saving never overwrites that key', async () => {
    setPlaySystem(playBodies('sol'));
    const earlier = { schema: SAVE_SCHEMA, garbage: true };
    const quietPrev = { ...quietSave(), playTime: 7 };
    const { kv, st } = await store({ [SAVE_KEY]: quietSave(), [PREV_KEY]: quietPrev, [CORRUPT_KEY]: earlier });
    expect([st.otherSystem, st.asideFree, st.previous.data]).toEqual([{ latest: 'quiet', previous: 'quiet' }, false, null]);
    expect(unloadableNote(st)).toBe(
      'The latest save is from the Quiet System and cannot be continued in Sol. Saving in this system replaces both saves from ' +
        'the Quiet System, and neither is kept. Start a new expedition.',
    );
    // The first save drops the latest (never rotated into the backup), the second rotates over the previous: as the note said.
    expect(await st.write(solSave())).toBe(true);
    expect([kv.data.get(CORRUPT_KEY), kv.data.get(PREV_KEY)]).toEqual([earlier, quietPrev]);
    expect(await st.write(solSave({ playTime: 43 }))).toBe(true);
    expect([kv.data.get(CORRUPT_KEY), kv.data.get(PREV_KEY), (kv.data.get(SAVE_KEY) as SaveData).playTime]).toEqual([earlier, solSave(), 43]);
    // With the key free the latest is set aside and only the previous goes.
    const free = await store({ [SAVE_KEY]: quietSave(), [PREV_KEY]: quietPrev });
    expect(unloadableNote(free.st)).toMatch(/replaces both saves from the Quiet System: the first save sets the latest aside in browser storage/);
  });

  it('in the Quiet System a Sol save reads the same way; any other unloadable save keeps the M1 note', async () => {
    const sol = await store({ [SAVE_KEY]: solSave() });
    expect(sol.st.otherSystem.latest).toBe('sol');
    expect(unloadableNote(sol.st)).toMatch(/^The latest save is from Sol and cannot be continued in the Quiet System\. Saving in this system replaces it: /);
    const bad = await store({ [SAVE_KEY]: { schema: SAVE_SCHEMA, system: 'sol', garbage: true }, [PREV_KEY]: quietSave() });
    expect(bad.st.otherSystem.latest).toBe('sol');
    // A current-schema record from this system that fails validation is not another system's save.
    const broken = await store({ [SAVE_KEY]: { ...quietSave(), mode: 'FLYING' }, [PREV_KEY]: quietSave() });
    expect(broken.st.otherSystem).toEqual({ latest: null, previous: null });
    expect(unloadableNote(broken.st)).toBe('The latest save could not be loaded (Bad mode.). It is kept aside unchanged. Load the previous save or start a new expedition.');
    // The title shows this note for every present but unloadable latest save.
    const src = readFileSync(new URL('../src/game/boot.ts', import.meta.url), 'utf8');
    expect(src).toMatch(/\} else if \(l\.present\) \{\s*\/\/[^\n]*\n\s*menus\.setContinueAvailable\(false, unloadableNote\(saves\), true\);/);
  });

  it('M1 gap, pinned: with the corrupt key taken an unloadable save from this system is dropped although the note says kept aside', async () => {
    const earlier = { schema: SAVE_SCHEMA, ship: 'garbage-1' };
    const { kv, st } = await store({ [SAVE_KEY]: { schema: SAVE_SCHEMA, ship: 'garbage-2' }, [PREV_KEY]: quietSave(), [CORRUPT_KEY]: earlier });
    expect([st.otherSystem, st.asideFree]).toEqual([{ latest: null, previous: null }, false]);
    // The M1 note, unchanged so the Quiet title stays as it was; a later step makes it true or rewords it.
    expect(unloadableNote(st)).toMatch(/\. It is kept aside unchanged\. Load the previous save or start a new expedition\.$/);
    expect(await st.write({ ...quietSave(), playTime: 43 })).toBe(true);
    expect([kv.data.get(CORRUPT_KEY), kv.data.get(PREV_KEY), (kv.data.get(SAVE_KEY) as SaveData).playTime]).toEqual([earlier, quietSave(), 43]);
  });
});

describe('start pose', () => {
  it('a new expedition starts on Ilex in the Quiet System and on Earth in Sol', () => {
    expect(startBodyOf('quiet').id).toBe('ilex');
    expect(startBodyOf('sol').id).toBe('earth');
    expect(() => startBodyOf('proxima')).toThrow(/No start body/);
    for (const s of ['quiet', 'sol'] as const) expect(surfaceReady(startBodyOf(s))).toBe(true);
  });

  it('keeps the Quiet System opening exactly: the Ilex clearing, facing the relay', () => {
    const sites = computeSites(BODIES.ilex);
    const s = startSite(BODIES.ilex);
    // Game.startPose before L7b, verbatim.
    const n = new Vector3(...sites.landing.dir);
    const relay = new Vector3(...sites.relay.dir);
    const fwd = relay.sub(n.clone().multiplyScalar(relay.dot(n))).normalize();
    expect(s.dir.toArray()).toEqual(n.toArray());
    expect(s.forward.toArray()).toEqual(fwd.toArray());
    expect(s.height).toBe(sites.landing.height);
  });

  it("starts Sol at Earth's First Light landing site: daylit dry land, facing the first route waypoint", () => {
    const earth = BODIES.earth;
    expect(earth.surface).toBe('data');
    expect(bodyDataReady(earth)).toBe(true);
    const sites = computeSites(earth);
    const s = startSite(earth);
    expect(s.dir.toArray()).toEqual([...sites.landing.dir]);
    expect(s.height).toBe(sites.landing.height);
    expect(s.height).toBeGreaterThan(earth.seaLevel!);
    // In daylight at EPOCH (the light is sunDirFor(earth) on the active body).
    expect(s.dir.dot(new Vector3(...sunDirFor(earth)))).toBeGreaterThan(0.25);
    // A unit tangent pointing at the route start, so the opening view looks along the route.
    expect(s.forward.length()).toBeCloseTo(1, 12);
    expect(Math.abs(s.forward.dot(s.dir))).toBeLessThan(1e-9);
    const w = new Vector3(...sites.route[0].dir);
    expect(w.sub(s.dir.clone().multiplyScalar(w.dot(s.dir))).normalize().dot(s.forward)).toBeCloseTo(1, 9);
    // The pose quaternion is well formed (Game.startPose builds it the same way).
    const q = quatFromForwardUp(s.forward, s.dir);
    expect(Math.hypot(q.x, q.y, q.z, q.w)).toBeCloseTo(1, 9);
    expect(new Vector3(0, 1, 0).applyQuaternion(q).dot(s.dir)).toBeCloseTo(1, 9);
  });

  it('without a route or relay the forward falls back to a surface tangent', () => {
    // Mercury has no First Light route, and outside the Quiet survey the relay sits on the landing site.
    const def = BODIES.mercury;
    const sites = computeSites(def);
    expect(sites.route).toEqual([]);
    expect(sites.relay.dir).toEqual(sites.landing.dir);
    const s = startSite(def);
    expect(s.forward.length()).toBeCloseTo(1, 12);
    expect(Math.abs(s.forward.dot(s.dir))).toBeLessThan(1e-9);
  });

  it('the photo test camera frames Earth, the Moon and Mars (the relay sits on the site) and Ilex as before', () => {
    for (const id of ['earth', 'moon', 'mars'] as const) {
      const def = BODIES[id];
      const sites = computeSites(def);
      expect(sites.relay.dir).toEqual(sites.landing.dir); // a frame built from the relay collapses here
      const { up, forward, right } = siteFrame(def, sites);
      for (const v of [up, forward, right]) {
        expect(v.toArray().every(Number.isFinite)).toBe(true);
        expect(v.length()).toBeCloseTo(1, 9);
      }
      for (const [a, b] of [[up, forward], [up, right], [forward, right]]) expect(Math.abs(a.dot(b))).toBeLessThan(1e-9);
      expect(up.toArray()).toEqual([...sites.landing.dir]);
      expect(forward.toArray()).toEqual(startSite(def).forward.toArray());
    }
    // The Quiet System keeps the frame applyPhotoCamera built from the relay before, verbatim.
    const sites = computeSites(BODIES.ilex);
    const n = new Vector3(...sites.landing.dir);
    const relay = new Vector3(...sites.relay.dir);
    const fz = relay.sub(n.clone().multiplyScalar(relay.dot(n))).normalize();
    const f = siteFrame(BODIES.ilex, sites);
    expect([f.up, f.forward, f.right].map((v) => v.toArray())).toEqual([n, fz, new Vector3().crossVectors(fz, n).normalize()].map((v) => v.toArray()));
    // applyPhotoCamera reads this frame from the active body's sites.
    const src = readFileSync(new URL('../src/game/Game.ts', import.meta.url), 'utf8');
    const photo = src.slice(src.indexOf('private applyPhotoCamera('), src.indexOf('private navMarker('));
    expect(photo).toMatch(/const \{ up: n, forward: fz, right: fx \} = siteFrame\(b\.def, b\.sites\);/);
    expect(photo).not.toMatch(/sites\.relay/);
  });

  it('the start pose is a valid last safe landing (newExpedition records it)', () => {
    setPlaySystem(playBodies('sol'));
    const earth = BODIES.earth;
    const s = startSite(earth);
    const p = s.dir.clone().multiplyScalar(earth.radius + s.height);
    const q = quatFromForwardUp(s.forward, s.dir);
    const sys = p.clone().add(center('earth'));
    const save = solSave({
      ship: { ...solSave().ship, sys: [sys.x, sys.y, sys.z], quat: [q.x, q.y, q.z, q.w] },
      lastSafeLanding: { bodyId: 'earth', posPlanet: [p.x, p.y, p.z], quat: [q.x, q.y, q.z, q.w] },
    });
    expect(validateSave(save).ok).toBe(true);
  });
});

describe('activation policy', () => {
  it('in Sol only Earth, the Moon and Mars take the surface handoff; the Sun never does', () => {
    expect(SURFACE_READY).toEqual(['earth', 'moon', 'mars']);
    expect(SOL_M2_BODIES.filter((id) => surfaceReady(BODIES[id]))).toEqual(['earth', 'moon', 'mars']);
    expect(SOL_M2_BODIES.filter((id) => canActivate(BODIES[id], false, null))).toEqual(['earth', 'moon', 'mars']);
    for (const cruising of [false, true]) {
      for (const target of [null, ...SOL_M2_BODIES]) {
        expect(canActivate(BODIES.sun, cruising, target)).toBe(false);
        for (const giant of ['jupiter', 'saturn', 'uranus', 'neptune']) expect(canActivate(BODIES[giant], cruising, target)).toBe(false);
      }
    }
    // Mercury and Venus have catalog surfaces but are approach-only in this build.
    for (const id of ['mercury', 'venus']) {
      expect(BODIES[id].explore).toBe('surface');
      expect(canActivate(BODIES[id], false, id)).toBe(false);
    }
  });

  it('while cruising only the nav target activates', () => {
    for (const id of SURFACE_READY) {
      expect(canActivate(BODIES[id], true, null)).toBe(false);
      for (const target of SOL_M2_BODIES) expect(canActivate(BODIES[id], true, target)).toBe(id === target);
    }
  });

  it('the Quiet System keeps its handoff: every body, in every mode', () => {
    for (const id of SYSTEM_BODY_IDS.quiet) {
      expect(surfaceReady(BODIES[id])).toBe(true);
      for (const cruising of [false, true]) {
        for (const target of [null, ...SYSTEM_BODY_IDS.quiet]) expect(canActivate(BODIES[id], cruising, target)).toBe(true);
      }
    }
  });

  it('the game applies the policy in its handoff and on restore', () => {
    const src = readFileSync(new URL('../src/game/Game.ts', import.meta.url), 'utf8');
    const method = (start: string, next: string) => src.slice(src.indexOf(start), src.indexOf(next, src.indexOf(start)));
    // The handoff's activation scan skips what canActivate refuses (mode and nav
    // target read live) and a data body whose surface data is not loaded.
    const handoff = method('private updateHandoff(', 'private setRef(');
    expect(handoff).toMatch(
      /const cruising = this\.mode === 'CRUISING';\s*for \(const id of BODY_IDS\) \{\s*const def = BODIES\[id\];\s*if \(!canActivate\(def, cruising, this\.navTarget\) \|\| !bodyDataReady\(def\)\) continue;\s*if \(distTo\(sys, def\.center\) < \(BODY_HANDOFF\.activateRadii \+ 0\.3\) \* def\.radius\) \{\s*this\.activateBody\(def\);/,
    );
    expect(handoff.match(/this\.activateBody\(/g)).toHaveLength(1);
    // Restore activates the saved body only if it is surface-ready, else scans with
    // canActivate for the saved mode and nav target; it activates nothing else.
    const restore = method('  restore(data: SaveData): void {', 'private placeRestoredPlayer(');
    expect(restore).toMatch(/let bodyId = data\.bodyId && surfaceReady\(BODIES\[data\.bodyId\]\) \? data\.bodyId : null;/);
    expect(restore).toMatch(/for \(const id of BODY_IDS\) \{\s*const def = BODIES\[id\];\s*if \(!canActivate\(def, data\.mode === 'CRUISING', data\.navTarget\)\) continue;/);
    expect(restore.match(/this\.activateBody\(/g)).toEqual(['this.activateBody(']);
    expect(restore).toMatch(/if \(bodyId && !this\.body\) this\.activateBody\(BODIES\[bodyId\]\);/);
    // The only other activations park the ship on a landing: the start body (the
    // constructor and New Expedition) or Recover's last safe landing (which saves
    // and landings keep surface-ready).
    expect(src.match(/this\.activateBody\(/g)).toHaveLength(4);
    expect(src).toMatch(/const def = this\.startBody;\s*this\.activateBody\(def\);/);
    expect(src.match(/this\.placeShipLanded\([^)]*\)/g)).toEqual([
      'this.placeShipLanded(pose.bodyId, pose.posPlanet, pose.quat)',
      'this.placeShipLanded(this.startBody.id, start.posPlanet, start.quat)',
    ]);
  });

  it('every activatable Sol body has its First Light sites and no Quiet survey objects', () => {
    for (const id of SURFACE_READY) {
      const s = computeSites(BODIES[id]);
      expect(Math.hypot(...s.landing.dir)).toBeCloseTo(1, 12);
      expect(s.samples).toEqual([]);
      expect(s.route).toHaveLength(3);
      expect(s.scans).toHaveLength(3);
    }
  });

  it('a save names a surface mode only on a surface-ready body', () => {
    setPlaySystem(playBodies('sol'));
    expect(validateSave(solSave()).ok).toBe(true);
    for (const id of ['mercury', 'venus', 'jupiter', 'sun']) {
      const d = BODIES[id];
      const at: [number, number, number] = [d.center[0] + d.radius + 100, d.center[1], d.center[2]];
      const landed = validateSave(solSave({ bodyId: id, ship: { ...solSave().ship, sys: at } }));
      expect(landed.ok).toBe(false);
      const last = validateSave(solSave({ lastSafeLanding: { bodyId: id, posPlanet: [d.radius + 100, 0, 0], quat: [0, 0, 0, 1] } }));
      expect(last.ok).toBe(false);
    }
    // Flight near a body that never activates is still a valid save (no body named).
    const j = BODIES.jupiter;
    const near: [number, number, number] = [j.center[0] + safetyRadius(j) + 5000, j.center[1], j.center[2]];
    expect(validateSave(solSave({ mode: 'PILOTING', bodyId: null, ship: { ...solSave().ship, sys: near, gear: 0 } })).ok).toBe(true);
  });
});

describe('cruise hop', () => {
  const facing = (from: Vector3, to: Vector3) => quatFromForwardUp(to.clone().sub(from).normalize(), new Vector3(0, 1, 0));
  const FULL = { pitch: 0, yaw: 0, roll: 0, throttle: 1, brake: false, toggleOff: false };

  it('the Quiet System keeps its fixed 15 km/s cruise, as does a cruise without a target', () => {
    const p = new Vector3(300000, 400000, 0);
    for (const t of [null, 'ilex', 'vesper', 'cairn']) expect(cruiseHop(p, t)).toBe(0);
    const c = new CruiseController();
    c.begin(p, facing(p, center('vesper')), new Vector3(), cruiseHop(p, 'vesper'));
    expect(c.maxSpeed).toBe(15000);
    expect(c.accel).toBe(5000);
    c.retarget(cruiseHop(p, 'cairn'));
    expect(c.maxSpeed).toBe(15000);
    expect(c.accel).toBe(5000);
  });

  it("in Sol the cap follows the route to the nav target: the shortest Earth -> Moon hop (from Earth's Moon-facing side) is about 21 km/s", () => {
    setPlaySystem(playBodies('sol'));
    // The plan's 21 km/s figure: the direct line is clear only from this side of Earth.
    const start = center('earth').addScaledVector(center('moon').sub(center('earth')).normalize(), safetyRadius(BODIES.earth) + 12000);
    expect(blockedBy(start, center('moon'), CRUISE.routeInflate, SOL_M2_BODIES.filter((id) => id !== 'moon'))).toBeNull();
    const hop = cruiseHop(start, 'moon');
    expect(hop).toBe(routeHop(start, 'moon', CRUISE.routeInflate));
    expect(hop).toBeCloseTo(hopDistance(start, 'moon'), 6);
    expect(cruiseMaxSpeed(hop)).toBeGreaterThan(20500);
    expect(cruiseMaxSpeed(hop)).toBeLessThan(22000);
    expect(cruiseHop(start, null)).toBe(0);

    // One leg at the cap: the peak never passes it, and a retarget re-caps the cruise.
    const c = new CruiseController();
    c.begin(start, facing(start, center('moon')), new Vector3(), hop);
    const cap = c.maxSpeed;
    let exit = null;
    for (let i = 0; i < 60 * 70 && !exit; i++) exit = c.step(SIM_DT, FULL).exit;
    expect(exit).toBe('approach');
    expect(c.aheadBody).toBe('moon');
    expect(c.safetyStops).toBe(0);
    expect(c.legStats()).toEqual({ hop, cap, entry: 0, peak: c.peak });
    expect(c.peak).toBeLessThanOrEqual(cap);
    expect(c.peak).toBeCloseTo(cap, 6);
    c.begin(c.pos, c.quat, new Vector3(), cruiseHop(c.pos, 'neptune'));
    expect(c.peak).toBe(0);
    expect(c.maxSpeed).toBeGreaterThan(cap);
    c.retarget(cruiseHop(c.pos, null));
    expect(c.maxSpeed).toBe(CRUISE.maxSpeed);
  });

  it("from the opening pose, on Earth's far side, the route to the Moon bypasses Earth: about 30.9 km/s", () => {
    setPlaySystem(playBodies('sol'));
    const earth = BODIES.earth;
    const moon = BODIES.moon;
    const site = startSite(earth);
    const toMoon = center('moon').sub(center('earth')).normalize();
    // About 152° from the Moon (if Earth's First Light site moves, this case and
    // the e2e journey's first-leg band move with it).
    expect(site.dir.dot(toMoon)).toBeLessThan(-0.85);
    // Where cruise first engages: above the start site, as clear of Earth's
    // envelope as the autopilot climbs (the route inflation plus 2 km).
    const engage = center('earth').addScaledVector(site.dir, safetyRadius(earth) + CRUISE.routeInflate + 2000);
    const others = SOL_M2_BODIES.filter((id) => id !== 'moon');
    expect(blockedBy(engage, center('moon'), CRUISE.routeInflate, others)).toBe('earth');
    // The hop is the length of the planned bypass, not the straight line.
    const path = planPath(engage, center('moon'), CRUISE.routeInflate, others);
    expect(path.length).toBeGreaterThan(1);
    let length = 0;
    for (let i = 0; i < path.length; i++) length += (i ? path[i - 1] : engage).distanceTo(path[i]);
    const hop = cruiseHop(engage, 'moon');
    expect(hop).toBeCloseTo(length - safetyRadius(moon), 3);
    expect(hop).toBeGreaterThan(hopDistance(engage, 'moon') + 50000);
    expect(cruiseMaxSpeed(hop)).toBeGreaterThan(30500);
    expect(cruiseMaxSpeed(hop)).toBeLessThan(31300);
    // Wherever the climb ends (within 15° of the site, 10-60 km outside the
    // envelope) the first leg's cap stays in the band the e2e journey asserts.
    const t = new Vector3(...tangentBasis(site.dir.toArray())[0]);
    const b = site.dir.clone().cross(t);
    for (const tilt of [0, 5, 10, 15]) {
      for (let k = 0; k < 12; k++) {
        const a = (k / 12) * 2 * Math.PI;
        const r = (tilt * Math.PI) / 180;
        const dir = site.dir.clone().multiplyScalar(Math.cos(r)).addScaledVector(t, Math.sin(r) * Math.cos(a)).addScaledVector(b, Math.sin(r) * Math.sin(a));
        for (const out of [10000, 35000, 60000]) {
          const cap = cruiseMaxSpeed(cruiseHop(center('earth').addScaledVector(dir, safetyRadius(earth) + out), 'moon'));
          expect(cap).toBeGreaterThan(29000);
          expect(cap).toBeLessThan(33500);
        }
      }
    }

    // Fly the travel autopilot's route (planPath to a gate above the Moon's
    // landing site, then a radial leg into its envelope), re-engaging at each
    // waypoint as the autopilot does: every leg is capped by its own hop, ends
    // within 60 s and needs no safety stop; the last ends at the Moon.
    const n = new Vector3(...computeSites(moon).landing.dir);
    const gate = center('moon').addScaledVector(n, safetyRadius(moon) + 60000);
    const route = [...planPath(engage, gate, CRUISE.routeInflate), center('moon').addScaledVector(n, safetyRadius(moon) - 5000)];
    expect(route.length).toBeGreaterThanOrEqual(3);
    const pos = engage.clone();
    const legs: { exit: string | null; time: number; hop: number; cap: number; peak: number }[] = [];
    for (const [i, wp] of route.entries()) {
      const c = new CruiseController();
      const hopHere = cruiseHop(pos, 'moon');
      c.begin(pos, facing(pos, wp), wp.clone().sub(pos).setLength(CRUISE.exitSpeed), hopHere);
      let exit = null;
      let time = 0;
      while (!exit && time < 120) {
        // The autopilot leaves cruise near an intermediate waypoint (its 'leaving' rule).
        const v = c.speed;
        const leave = i < route.length - 1 && c.pos.distanceTo(wp) < (v * v) / (2 * CRUISE.accel) + v * 0.5 + 4000;
        exit = c.step(SIM_DT, { ...FULL, toggleOff: leave }).exit;
        time += SIM_DT;
      }
      const s = c.legStats();
      expect(s.hop).toBe(hopHere);
      expect(s.cap).toBe(cruiseMaxSpeed(hopHere));
      expect(s.entry).toBeCloseTo(CRUISE.exitSpeed, 6);
      expect(s.peak).toBeLessThanOrEqual(s.cap);
      expect(c.safetyStops).toBe(0);
      legs.push({ exit, time, ...s });
      pos.copy(c.pos);
    }
    expect(legs[0].cap).toBe(cruiseMaxSpeed(hop));
    expect(legs.map((l) => l.exit)).toEqual([...route.slice(1).map(() => 'toggle'), 'approach']);
    for (const l of legs) expect(l.time).toBeLessThanOrEqual(60);
    expect(hopDistance(pos, 'moon')).toBeLessThan(10000);
  });

  it("a retarget mid-leg never hides the leg's faster part: the log keeps its longest hop and cap", () => {
    setPlaySystem(playBodies('sol'));
    const start = center('earth').addScaledVector(center('neptune').sub(center('earth')).normalize(), safetyRadius(BODIES.earth) + 12000);
    const c = new CruiseController();
    const far = cruiseHop(start, 'neptune');
    c.begin(start, facing(start, center('neptune')), new Vector3(), far);
    for (let i = 0; i < 60 * 10; i++) c.step(SIM_DT, FULL);
    const farCap = cruiseMaxSpeed(far);
    expect(c.peak).toBeCloseTo(farCap, 6);
    // Tab + another digit while cruising: a nearer destination lowers the live cap below the speed reached.
    const near = cruiseHop(c.pos, 'mars');
    c.retarget(near);
    expect(c.hop).toBe(near);
    expect(c.maxSpeed).toBe(cruiseMaxSpeed(near));
    expect(c.maxSpeed).toBeLessThan(c.peak);
    expect(c.legStats()).toEqual({ hop: far, cap: farCap, entry: 0, peak: c.peak });
    // The ship sheds the excess; the leg's peak stays within the leg's cap.
    for (let i = 0; i < 60 * 5; i++) c.step(SIM_DT, FULL);
    expect(c.speed).toBeLessThanOrEqual(c.maxSpeed);
    expect(c.legStats().peak).toBeLessThanOrEqual(c.legStats().cap);
    expect(c.safetyStops).toBe(0);

    // A retarget to a farther body raises the leg's cap with it.
    const m = new CruiseController();
    const moonHop = cruiseHop(start, 'moon');
    m.begin(start, facing(start, center('neptune')), new Vector3(), moonHop);
    expect(m.legStats().cap).toBe(cruiseMaxSpeed(moonHop));
    m.retarget(far);
    expect(m.legStats()).toMatchObject({ hop: far, cap: farCap });
    for (let i = 0; i < 60 * 5; i++) m.step(SIM_DT, FULL);
    expect(m.peak).toBeGreaterThan(cruiseMaxSpeed(moonHop));
    expect(m.peak).toBeLessThanOrEqual(m.legStats().cap);
    // Nor does a later lower retarget lower the leg's record.
    m.retarget(moonHop);
    expect(m.legStats().cap).toBe(farCap);
  });

  it("a cruise restored from a save keeps its leg's cap: the saved speed ÷ throttle floors it", () => {
    setPlaySystem(playBodies('sol'));
    // A leg from Earth toward Neptune, saved after 20 s at a steady throttle: the route left is shorter, so its own cap is lower.
    const start = center('earth').addScaledVector(center('neptune').sub(center('earth')).normalize(), safetyRadius(BODIES.earth) + 12000);
    const far = cruiseHop(start, 'neptune');
    const fly = (c: CruiseController, throttle: number, seconds: number) => {
      for (let i = 0; i < 60 * seconds; i++) c.step(SIM_DT, { ...FULL, throttle });
    };
    const legAt = (throttle: number) => {
      const leg = new CruiseController();
      leg.begin(start, facing(start, center('neptune')), new Vector3(), far);
      fly(leg, throttle, 20);
      return leg;
    };
    // Restored as Game.restore does: begin at the saved speed and hop left, the cap floored by resumeCap.
    const restore = (leg: CruiseController, minCap: number) => {
      const r = new CruiseController();
      r.begin(leg.pos, leg.quat, leg.velocity(new Vector3()), cruiseHop(leg.pos, 'neptune'), minCap);
      r.speed = leg.speed;
      return r;
    };
    for (const throttle of [1, 0.5]) {
      const leg = legAt(throttle);
      const saved = leg.speed;
      expect(saved).toBe(throttle * cruiseMaxSpeed(far));
      const left = cruiseHop(leg.pos, 'neptune');
      expect(cruiseMaxSpeed(left)).toBeLessThan(0.8 * cruiseMaxSpeed(far));
      const r = restore(leg, resumeCap('neptune', saved, throttle));
      expect([r.hop, r.maxSpeed]).toEqual([left, cruiseMaxSpeed(far)]);
      expect(r.accel).toBeCloseTo(leg.accel, 6);
      // It flies on as the uninterrupted leg does, never past its cap.
      const old = restore(leg, saved);
      fly(old, throttle, 10);
      for (let i = 0; i < 60 * 10; i++) {
        leg.step(SIM_DT, { ...FULL, throttle });
        r.step(SIM_DT, { ...FULL, throttle });
      }
      expect(r.speed).toBe(saved);
      expect(r.pos.distanceTo(leg.pos)).toBeLessThan(1);
      expect(r.legStats()).toMatchObject({ hop: left, cap: cruiseMaxSpeed(far) });
      expect(r.legStats().peak).toBeLessThanOrEqual(r.legStats().cap);
      expect(r.safetyStops).toBe(0);
      // A floor of the saved speed alone (the first fix) holds it only at full throttle; below, it slows to throttle x the route left's cap.
      expect(old.speed).toBe(throttle === 1 ? saved : throttle * cruiseMaxSpeed(left));
    }
    // Without a floor it slowed to the remaining route's cap within the 3 s ramp (the trip took about 45 s again).
    const bare = restore(legAt(1), 0);
    fly(bare, 1, 4);
    expect(bare.speed).toBe(bare.maxSpeed);
    expect(bare.maxSpeed).toBeLessThan(0.8 * cruiseMaxSpeed(far));

    // Within the ramp after a throttle change the speed has not settled: saved 1 s after
    // lowering the throttle to 0.5, the floor is above the leg's cap, so the restored
    // cruise holds the saved speed while the uninterrupted leg slows on to 0.5 x its cap.
    const falling = legAt(1);
    fly(falling, 0.5, 1);
    const mid = falling.speed;
    expect(mid).toBeGreaterThan(0.5 * cruiseMaxSpeed(far));
    const rf = restore(falling, resumeCap('neptune', mid, 0.5));
    expect(rf.maxSpeed).toBe(Math.min(mid / 0.5, cruiseMaxSpeed(2 * SYSTEM_EXTENT)));
    expect(rf.maxSpeed).toBeGreaterThan(cruiseMaxSpeed(far));
    fly(falling, 0.5, 5);
    fly(rf, 0.5, 5);
    expect([falling.speed, rf.speed]).toEqual([0.5 * cruiseMaxSpeed(far), mid]);

    // The floor is bounded by the hop rule: in Sol never above the longest hop's cap (the save bound) ...
    expect(resumeCap('neptune', 1e9, 1)).toBe(cruiseMaxSpeed(2 * SYSTEM_EXTENT));
    expect(resumeCap('neptune', 1e6, 0.01)).toBe(cruiseMaxSpeed(2 * SYSTEM_EXTENT));
    // ... at zero throttle it is the saved speed ...
    expect(resumeCap('neptune', 1e6, 0)).toBe(1e6);
    // ... and the fixed 15 km/s without a target or in the Quiet System, whose restored cruise is unchanged.
    expect(resumeCap(null, 1e6, 0.5)).toBe(CRUISE.maxSpeed);
    setPlaySystem(playBodies('quiet'));
    const p = new Vector3(300000, 400000, 0);
    for (const v of [0, 9000, 15000, 18000]) {
      for (const t of [0, 0.3, 1]) {
        const q = new CruiseController();
        q.begin(p, facing(p, center('vesper')), new Vector3(), cruiseHop(p, 'vesper'), resumeCap('vesper', v, t));
        expect([q.maxSpeed, q.accel]).toEqual([CRUISE.maxSpeed, CRUISE.accel]);
      }
    }
  });

  it("the game caps every engage, restore and retarget by the nav target's hop and logs each leg from the controller", () => {
    const src = readFileSync(new URL('../src/game/Game.ts', import.meta.url), 'utf8');
    expect(src.match(/this\.cruise\.begin\([^;]*;/g)).toEqual([
      'this.cruise.begin(_v4, ship.currQuat, ship.vel, cruiseHop(_v4, this.navTarget));',
      'this.cruise.begin(sys, quat, fwd.clone().multiplyScalar(data.cruise.speed), cruiseHop(sys, data.navTarget), resumeCap(data.navTarget, data.cruise.speed, data.cruise.throttle));',
    ]);
    expect(src).toMatch(/pushBounded\(this\.cruiseLog, \{ start: this\.cruiseStart, end: this\.simTime, target: this\.navTarget, \.\.\.this\.cruise\.legStats\(\), exit: reason \}\);/);
    expect(src.match(/pushBounded\(this\.cruiseLog,/g)).toHaveLength(1);
    // Mid-cruise retargets go through the controller (the log keeps the leg's longest hop).
    expect(src).toMatch(/if \(this\.mode === 'CRUISING'\) this\.cruise\.retarget\(cruiseHop\(this\.cruise\.pos, id\)\);/);
  });
});

describe('navigation panel keys', () => {
  it('Digit1-Digit9 pick rows 1-9 and Digit0 row 10; nothing else picks a row', () => {
    for (let d = 1; d <= 9; d++) expect(navKeyIndex(`Digit${d}`)).toBe(d - 1);
    expect(navKeyIndex('Digit0')).toBe(9);
    for (const code of ['Numpad1', 'KeyA', 'Tab', 'Digit', 'Digit10', 'digit1', '1']) expect(navKeyIndex(code)).toBeNull();
    for (let i = 0; i < 10; i++) expect(navKeyIndex(`Digit${navKeyLabel(i)}`)).toBe(i);
    expect(navKeyLabel(10)).toBeNull();
    expect(navKeyLabel(-1)).toBeNull();
  });

  it('in Sol every row has a key: 5 is the Moon and 0 is Neptune; the Quiet System keeps 1-3', () => {
    setPlaySystem(playBodies('sol'));
    const rows = [...BODY_IDS];
    expect(rows.every((_, i) => navKeyLabel(i) !== null)).toBe(true);
    expect(rows[navKeyIndex('Digit5')!]).toBe('moon');
    expect(rows[navKeyIndex('Digit1')!]).toBe('sun');
    expect(rows[navKeyIndex('Digit0')!]).toBe('neptune');
    setPlaySystem(playBodies('quiet'));
    expect(BODY_IDS.map((_, i) => navKeyLabel(i))).toEqual(['1', '2', '3']);
    expect(BODY_IDS[navKeyIndex('Digit2')!]).toBe('vesper');
  });

  it('labels each row Star, Planet or Moon', () => {
    expect(kindLabel(BODIES.sun)).toBe('Star');
    for (const id of ['mercury', 'earth', 'jupiter', 'neptune', 'ilex', 'vesper']) expect(kindLabel(BODIES[id])).toBe('Planet');
    for (const id of ['moon', 'cairn']) expect(kindLabel(BODIES[id])).toBe('Moon');
  });
});

describe('distant bodies', () => {
  it('every body in play but the Sun gets a terrain globe, and its roots generate as the proxy worker does', () => {
    expect(proxyBodies()).toEqual(SYSTEM_BODY_IDS.quiet);
    setPlaySystem(playBodies('sol'));
    const ids = proxyBodies();
    expect(ids).toEqual(SOL_M2_BODIES.filter((id) => id !== 'sun'));
    // The Sun has no terrain: the worker's sites lookup would fail for every root.
    expect(() => computeSites(BODIES.sun)).toThrow(/no surface/);
    for (const id of ids) {
      const def = BODIES[id];
      const gen = getSurface(def, computeSites(def).clearings);
      for (let face = 0; face < 6; face++) expect(generateChunk(def, gen, face, 0, 0, 0, 1).bodyId).toBe(id);
    }
  });
});

describe('background camera', () => {
  it('its far plane spans the charted system, so no proxy in play is clipped', () => {
    expect(BG_FAR).toBeGreaterThanOrEqual(33000);
    let widest = 0;
    for (const a of SOL_M2_BODIES) {
      for (const b of SOL_M2_BODIES) widest = Math.max(widest, center(a).distanceTo(center(b)) + BODIES[b].radius);
    }
    expect(widest * BG_SCALE).toBeLessThan(BG_FAR);
    // A ship at Earth sees Neptune about 9,000 units away (beyond the old 4,000).
    expect(center('earth').distanceTo(center('neptune')) * BG_SCALE).toBeGreaterThan(4000);
  });
});
