// L7b/L6b: Sol behind ?system=sol. The system switch made at boot, the start
// pose, the handoff (activation) policy, the cruise hop, saves on landable
// bodies, the navigation panel's digit keys and the background far plane, in
// Node. The browser journey is e2e/journey/travel.spec.ts ("Sol: Earth -> Moon hop").
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { afterEach, beforeAll, describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import {
  BODIES, BODY_IDS, GENERATOR_VERSION, PLAY_SYSTEM, SOL_M2_BODIES, SOL_TRAVEL_ORDER, SYSTEM_BODY_IDS, WORLD_SEED,
  setPlaySystem, sunDirFor, type BodyId,
} from '../src/world/bodies';
import { BELTS } from '../src/world/catalog';
import { EARTH_META, installEarthData, loadEarthData, type LayerName } from '../src/world/earthData';
import { bodyDataReady, getSurface } from '../src/world/surface';
import { computeSites } from '../src/world/sites';
import { generateChunk } from '../src/terrain/chunkGen';
import { canActivate, playBodies, proxyBodies, startBodyOf, startSite, surfaceReady, systemFromQuery } from '../src/game/playSystem';
import { CRUISE, SIM_DT, SURFACE_READY } from '../src/game/config';
import { CruiseController, cruiseHop, routeHop, safetyRadius } from '../src/ship/Cruise';
import { cruiseMaxSpeed } from '../src/world/scale';
import { quatFromForwardUp } from '../src/core/mathx';
import { SAVE_SCHEMA, validateSave, type SaveData } from '../src/save/SaveSystem';
import { newExpedition } from '../src/game/Expedition';
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
    unlocked: [BODIES.earth.power!],
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

  it('boot switches before saves are read: validation follows the system in play', () => {
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

  it('in Sol the cap follows the route to the nav target: Earth -> Moon at about 21 km/s', () => {
    setPlaySystem(playBodies('sol'));
    const start = center('earth').addScaledVector(center('moon').sub(center('earth')).normalize(), safetyRadius(BODIES.earth) + 12000);
    const hop = cruiseHop(start, 'moon');
    expect(hop).toBe(routeHop(start, 'moon', CRUISE.routeInflate));
    expect(cruiseMaxSpeed(hop)).toBeGreaterThan(20500);
    expect(cruiseMaxSpeed(hop)).toBeLessThan(22000);
    expect(cruiseHop(start, null)).toBe(0);

    // One leg at the cap: the peak never passes it, and a retarget re-caps the cruise.
    const c = new CruiseController();
    c.begin(start, facing(start, center('moon')), new Vector3(), hop);
    const cap = c.maxSpeed;
    let exit = null;
    for (let i = 0; i < 60 * 70 && !exit; i++) exit = c.step(SIM_DT, { pitch: 0, yaw: 0, roll: 0, throttle: 1, brake: false, toggleOff: false }).exit;
    expect(exit).toBe('approach');
    expect(c.aheadBody).toBe('moon');
    expect(c.safetyStops).toBe(0);
    expect(c.peak).toBeLessThanOrEqual(cap);
    expect(c.peak).toBeCloseTo(cap, 6);
    c.begin(c.pos, c.quat, new Vector3(), cruiseHop(c.pos, 'neptune'));
    expect(c.peak).toBe(0);
    expect(c.maxSpeed).toBeGreaterThan(cap);
    c.retarget(cruiseHop(c.pos, null));
    expect(c.maxSpeed).toBe(CRUISE.maxSpeed);
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
