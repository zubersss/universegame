import { describe, expect, it } from 'vitest';
import { Quaternion, Vector3 } from 'three';
import {
  CruiseController, blockedBy, freeDistance, hopDistance, navWaypoint, planPath, routeHop, safetyRadius,
  type CruiseExitReason, type CruiseInput,
} from '../src/ship/Cruise';
import { BODIES, BODY_IDS, SYSTEM_BODY_IDS, SYSTEM_EXTENT, type BodyId } from '../src/world/bodies';
import { bodyGravity } from '../src/world/environment';
import { BODY_HANDOFF, CRUISE, REBASE_DISTANCE, SIM_DT } from '../src/game/config';
import { FloatingOrigin } from '../src/core/origin';
import { quatFromForwardUp } from '../src/core/mathx';
import { cruiseMaxSpeed } from '../src/world/scale';

// Sol travel at the charter H scale, in Node. The game still plays the Quiet
// System (BODY_IDS) until L7b switches it, so these controllers are given the
// Sol ids explicitly.

const SOL = SYSTEM_BODY_IDS.sol;
/** The autopilot's planner inflation (src/debug/autopilot.ts). */
const PLAN_INFLATE = 8000;
/** Handoff activates a body within this many radii (Game.updateHandoff). */
const ACTIVATE_RADII = BODY_HANDOFF.activateRadii + 0.3;
const IDLE: CruiseInput = { pitch: 0, yaw: 0, roll: 0, throttle: 1, brake: false, toggleOff: false };

function center(id: BodyId): Vector3 {
  const c = BODIES[id].center;
  return new Vector3(c[0], c[1], c[2]);
}

function facing(from: Vector3, to: Vector3): Quaternion {
  const f = to.clone().sub(from).normalize();
  const up = Math.abs(f.y) > 0.9 ? new Vector3(1, 0, 0) : new Vector3(0, 1, 0);
  return quatFromForwardUp(f, up);
}

/** Closest distance from `c` to the segment p0->p1. */
function segmentDistance(p0: Vector3, p1: Vector3, c: Vector3): number {
  const d = p1.clone().sub(p0);
  const l2 = d.lengthSq();
  const t = l2 > 0 ? Math.max(0, Math.min(1, c.clone().sub(p0).dot(d) / l2)) : 0;
  return p0.clone().addScaledVector(d, t).distanceTo(c);
}

/** Pursuit gain of the test pilot: full stick beyond about 19° of heading error. */
const STEER_GAIN = 3;

interface Leg {
  /** The route planned at engage (bypass waypoints, then `to`'s center). */
  route: Vector3[];
  start: Vector3;
  /** routeHop at engage: the hop passed to begin(), kept for the whole leg. */
  hop: number;
  exit: CruiseExitReason | null;
  aheadBody: BodyId | null;
  /** Simulated seconds from engaging at rest to the exit. */
  time: number;
  cap: number;
  peak: number;
  stops: number;
  refusedTurns: number;
  exitSpeed: number;
  /** Closest approach to the Sun's center over the whole flight, in Sun radii. */
  sunRadii: number;
  /** Closest approach to any body other than the two ends, in its radii, and which one. */
  otherRadii: number;
  other: BodyId | null;
}

/**
 * Fly one leg as a pilot following the nav marker would: engage cruise at rest
 * just outside `from`'s envelope (on the side facing `to`) with hop = routeHop
 * (the planned route length), then steer every step, at the cruise turn rate,
 * toward planPath()[0] from the current position (the marker: the next bypass
 * waypoint while the direct line is blocked, else `to`) until cruise exits.
 * The whole leg is one cruise: nothing leaves and re-engages at a waypoint.
 */
function flyLeg(from: BodyId, to: BodyId): Leg {
  const dir = center(to).sub(center(from)).normalize();
  const start = center(from).addScaledVector(dir, safetyRadius(BODIES[from]) + 12000);
  const others = SOL.filter((id) => id !== to);
  const route = planPath(start, center(to), PLAN_INFLATE, others);
  const hop = routeHop(start, to, PLAN_INFLATE, SOL);
  const c = new CruiseController(SOL);
  c.begin(start, facing(start, route[0]), new Vector3(), hop);
  const leg: Leg = {
    route, start, hop, exit: null, aheadBody: null, time: 0, cap: c.maxSpeed, peak: 0, stops: 0, refusedTurns: 0, exitSpeed: 0,
    sunRadii: Infinity, otherRadii: Infinity, other: null,
  };
  const steer = (angle: number) => Math.max(-1, Math.min(1, angle * STEER_GAIN));
  const inv = new Quaternion();
  const d = new Vector3();
  const prev = new Vector3();
  while (!leg.exit && leg.time < 300) {
    // The marker's direction in the ship frame (forward -Z): pitch up toward +Y, yaw right toward +X.
    d.copy(planPath(c.pos, center(to), PLAN_INFLATE, others)[0]).sub(c.pos).applyQuaternion(inv.copy(c.quat).invert());
    prev.copy(c.pos);
    leg.exit = c.step(SIM_DT, { ...IDLE, pitch: steer(Math.atan2(d.y, -d.z)), yaw: steer(Math.atan2(d.x, -d.z)) }).exit;
    leg.time += SIM_DT;
    leg.peak = Math.max(leg.peak, c.speed);
    for (const id of SOL) {
      const r = segmentDistance(prev, c.pos, center(id)) / BODIES[id].radius;
      if (id === 'sun') leg.sunRadii = Math.min(leg.sunRadii, r);
      else if (id !== from && id !== to && r < leg.otherRadii) {
        leg.otherRadii = r;
        leg.other = id;
      }
    }
  }
  leg.aheadBody = c.aheadBody;
  leg.stops = c.safetyStops;
  leg.refusedTurns = c.refusedTurns;
  leg.exitSpeed = c.speed;
  return leg;
}

describe('cruise envelope and hop cap', () => {
  it('keeps the Quiet System cruise at 15 km/s and 5 km/s² when no hop is given', () => {
    expect(BODY_IDS).toEqual(SYSTEM_BODY_IDS.quiet);
    expect(cruiseMaxSpeed(0)).toBe(CRUISE.maxSpeed);
    expect(CRUISE.maxSpeed / CRUISE.rampSeconds).toBe(CRUISE.accel);
    const c = new CruiseController();
    expect(c.maxSpeed).toBe(15000);
    expect(c.accel).toBe(5000);
    const p = new Vector3(300000, 400000, 0);
    c.begin(p, facing(p, p.clone().add(new Vector3(1, 0, 0))), new Vector3(CRUISE.maxSpeed, 0, 0));
    expect(c.maxSpeed).toBe(15000);
    expect(c.accel).toBe(5000);
  });

  it('a star keeps a 5R standoff, outside its gravity taper', () => {
    const sun = BODIES.sun;
    expect(sun.kind).toBe('star');
    expect(safetyRadius(sun)).toBe(CRUISE.starStandoffRadii * sun.radius);
    expect(bodyGravity(sun, safetyRadius(sun), 0, 0, new Vector3()).length()).toBe(0);
    // Planets and moons keep surface + atmosphere + margin.
    expect(safetyRadius(BODIES.earth)).toBe(BODIES.earth.radius + BODIES.earth.atmosphereHeight + CRUISE.envelopeMargin);
    // A cruise aimed straight at the Sun stops about 1,000 km from its center.
    const p = center('earth').multiplyScalar(0.8);
    const c = new CruiseController(SOL);
    c.begin(p, facing(p, new Vector3()), new Vector3(), hopDistance(p, 'sun'));
    let exit = null;
    for (let i = 0; i < 60 * 120 && !exit; i++) exit = c.step(SIM_DT, IDLE).exit;
    expect(exit).toBe('approach');
    expect(c.aheadBody).toBe('sun');
    expect(c.safetyStops).toBe(0);
    const d = c.pos.length();
    expect(d).toBeGreaterThan(safetyRadius(sun));
    expect(d).toBeLessThan(safetyRadius(sun) + 6000);
  });

  it('the Earth -> Moon cap is about 21 km/s and the hop takes about 48 s', () => {
    const leg = flyLeg('earth', 'moon');
    // The direct line is clear, so the route hop is the straight-line hop.
    expect(leg.route.length).toBe(1);
    expect(leg.hop).toBeCloseTo(hopDistance(leg.start, 'moon'), 3);
    expect(leg.cap).toBeGreaterThan(20500);
    expect(leg.cap).toBeLessThan(22000);
    expect(leg.peak).toBeCloseTo(leg.cap, 6);
    expect(leg.exit).toBe('approach');
    expect(leg.aheadBody).toBe('moon');
    expect(leg.time).toBeGreaterThan(45);
    expect(leg.time).toBeLessThan(52);
    console.log(`earth->moon: hop ${(leg.hop / 1000).toFixed(0)} km, cap ${(leg.cap / 1000).toFixed(2)} km/s, ${leg.time.toFixed(1)} s`);
  });

  it('retargeting changes the cap without endangering a braking ship', () => {
    // Full speed toward Neptune, then a short hop: the cap falls to 15 km/s within the ramp.
    const p = center('earth').addScaledVector(center('neptune').sub(center('earth')).normalize(), safetyRadius(BODIES.earth) + 12000);
    const a = new CruiseController(SOL);
    a.begin(p, facing(p, center('neptune')), new Vector3(), hopDistance(p, 'neptune'));
    for (let i = 0; i < 60 * 10; i++) a.step(SIM_DT, IDLE);
    expect(a.speed).toBeCloseTo(a.maxSpeed, 6);
    a.retarget(0);
    expect(a.maxSpeed).toBe(CRUISE.maxSpeed);
    let t = 0;
    while (a.speed > CRUISE.maxSpeed && t < 10) {
      a.step(SIM_DT, IDLE);
      t += SIM_DT;
    }
    expect(t).toBeLessThanOrEqual(CRUISE.rampSeconds + SIM_DT);
    expect(a.safetyStops).toBe(0);

    // Braking hard for Jupiter: a retarget must not lower the acceleration it is braking with.
    const q = center('earth').addScaledVector(center('jupiter').sub(center('earth')).normalize(), safetyRadius(BODIES.earth) + 12000);
    const b = new CruiseController(SOL);
    b.begin(q, facing(q, center('jupiter')), new Vector3(), hopDistance(q, 'jupiter'));
    let exit = null;
    let retargeted = false;
    for (let i = 0; i < 60 * 120 && !exit; i++) {
      if (!retargeted && b.limited && b.speed > 50000) {
        const before = b.accel;
        b.retarget(0);
        expect(b.accel).toBe(before);
        retargeted = true;
      }
      exit = b.step(SIM_DT, IDLE).exit;
    }
    expect(retargeted).toBe(true);
    expect(exit).toBe('approach');
    expect(b.aheadBody).toBe('jupiter');
    expect(b.safetyStops).toBe(0);
  });
});

describe('M2 travel legs (First Light)', () => {
  const legs: [BodyId, BodyId][] = [['earth', 'moon'], ['moon', 'mars'], ['earth', 'mars']];
  for (const [from, to] of legs) {
    it(`${from} -> ${to}: one cruise of at most 60 s with no safety stops, Sun at 5R or more, other bodies beyond ${ACTIVATE_RADII}R`, () => {
      const leg = flyLeg(from, to);
      // The planned route is clear of every envelope, not much longer than the
      // direct line, and its length (less the destination envelope) is the hop.
      const pts = [leg.start, ...leg.route];
      let length = 0;
      for (let i = 1; i < pts.length; i++) {
        expect(blockedBy(pts[i - 1], pts[i], PLAN_INFLATE, SOL.filter((id) => id !== to))).toBeNull();
        length += pts[i].distanceTo(pts[i - 1]);
      }
      expect(length).toBeLessThan(1.6 * leg.start.distanceTo(center(to)));
      expect(leg.hop).toBeCloseTo(length - safetyRadius(BODIES[to]), 3);
      expect(leg.cap).toBe(cruiseMaxSpeed(leg.hop));

      // The whole leg, from engaging at rest to the approach exit (LEAD-M2 step 1: at most 60 s simulated).
      expect(leg.exit).toBe('approach');
      expect(leg.aheadBody).toBe(to);
      expect(leg.time).toBeLessThanOrEqual(60);
      expect(leg.stops).toBe(0);
      expect(leg.exitSpeed).toBeLessThanOrEqual(CRUISE.exitSpeed + 1e-6);
      expect(leg.sunRadii).toBeGreaterThanOrEqual(CRUISE.starStandoffRadii);
      expect(leg.otherRadii).toBeGreaterThan(ACTIVATE_RADII);
      console.log(
        `${from}->${to}: ${leg.route.length - 1} bypass waypoint(s), route ${(length / 1000).toFixed(0)} km, cap ${(leg.cap / 1000).toFixed(1)} km/s; ` +
        `leg ${leg.time.toFixed(1)} s, ${leg.refusedTurns} refused turn steps, Sun ≥ ${leg.sunRadii.toFixed(2)}R, nearest other ${leg.other ?? '-'} ${leg.otherRadii.toFixed(2)}R`,
      );
    });
  }

  it('the direct Earth -> Mars line is blocked by the Sun, so the route and its hop go around it', () => {
    const e = center('earth');
    const start = e.clone().addScaledVector(center('mars').sub(e).normalize(), safetyRadius(BODIES.earth) + 12000);
    const others = SOL.filter((id) => id !== 'mars');
    expect(blockedBy(start, center('mars'), PLAN_INFLATE, others)).toBe('sun');
    expect(planPath(start, center('mars'), PLAN_INFLATE, others).length).toBeGreaterThan(1);
    // The bypass hop is longer than the straight-line hop, so the cap rises with it.
    const hop = routeHop(start, 'mars', PLAN_INFLATE, SOL);
    expect(hop).toBeGreaterThan(hopDistance(start, 'mars') + 100000);
    expect(cruiseMaxSpeed(hop)).toBeGreaterThan(cruiseMaxSpeed(hopDistance(start, 'mars')));
    // Inside the destination's envelope the hop is 0 (the 15 km/s floor).
    expect(routeHop(center('mars'), 'mars', PLAN_INFLATE, SOL)).toBe(0);
  });
});

describe('nav marker bypass (navWaypoint)', () => {
  it('Earth -> Mars: the marker reads "bypass Sun", and following it reaches Mars on a path under 1.6x the direct line, clear of the Sun', () => {
    const e = center('earth');
    const mars = center('mars');
    const start = e.clone().addScaledVector(mars.clone().sub(e).normalize(), safetyRadius(BODIES.earth) + 12000);
    const first = navWaypoint(start, 'mars', SOL);
    expect(first.bypass).toBe('sun');
    expect(first.point.distanceTo(mars)).toBeGreaterThan(1000);
    // Walk toward the marker in 5 km steps, reading it again after each, until inside Mars's envelope.
    const sun = center('sun');
    const S = safetyRadius(BODIES.mars);
    const p = start.clone();
    const seen: (BodyId | null)[] = [];
    let length = 0;
    let sunMin = Infinity;
    for (let i = 0; i < 5000 && p.distanceTo(mars) > S; i++) {
      const w = navWaypoint(p, 'mars', SOL);
      if (seen[seen.length - 1] !== w.bypass) seen.push(w.bypass);
      const d = w.point.sub(p);
      const step = Math.min(5000, d.length());
      const q = p.clone().addScaledVector(d.normalize(), step);
      sunMin = Math.min(sunMin, segmentDistance(p, q, sun));
      length += step;
      p.copy(q);
    }
    expect(p.distanceTo(mars)).toBeLessThanOrEqual(S);
    // "bypass Sun" until the line clears, then the marker is Mars itself.
    expect(seen).toEqual(['sun', null]);
    expect(sunMin).toBeGreaterThanOrEqual(safetyRadius(BODIES.sun) + PLAN_INFLATE);
    expect(length + S).toBeLessThan(1.6 * start.distanceTo(mars));
    console.log(`marker walk earth->mars: ${(length / 1000).toFixed(0)} km to the envelope vs ${(start.distanceTo(mars) / 1000).toFixed(0)} km direct, Sun >= ${(sunMin / BODIES.sun.radius).toFixed(2)}R`);
  });

  it('after an approach exit at the Sun, a far-side target reads "bypass Sun" and its marker climbs out clear of the envelope', () => {
    // Cruising straight at Mars from Earth, no steering: the Sun's envelope ends the leg just outside it.
    const e = center('earth');
    const mars = center('mars');
    const sun = center('sun');
    const S = safetyRadius(BODIES.sun);
    const start = e.clone().addScaledVector(mars.clone().sub(e).normalize(), safetyRadius(BODIES.earth) + 12000);
    const c = new CruiseController(SOL);
    c.begin(start, facing(start, mars), new Vector3(), routeHop(start, 'mars', PLAN_INFLATE, SOL));
    let exit: CruiseExitReason | null = null;
    for (let t = 0; !exit && t < 300; t += SIM_DT) exit = c.step(SIM_DT, IDLE).exit;
    expect(exit).toBe('approach');
    expect(c.aheadBody).toBe('sun');
    const gap = c.pos.distanceTo(sun) - S;
    expect(gap).toBeGreaterThan(0);
    expect(gap).toBeLessThan(CRUISE.routeInflate); // inside the inflated band
    // There, and on the Earth side at S + 1.5, 2 and 7 km: the far-side targets
    // are bypassed with a marker whose line stays outside the envelope and that
    // cruise can engage facing; a target the line leaves the Sun toward is not.
    const eside = e.clone().sub(sun).normalize();
    const spots = [c.pos.clone(), ...[1500, 2000, 7000].map((k) => sun.clone().addScaledVector(eside, S + k))];
    for (const p of spots) {
      for (const to of ['mars', 'venus'] as BodyId[]) {
        const w = navWaypoint(p, to, SOL);
        expect(w.bypass).toBe('sun');
        expect(segmentDistance(p, w.point, sun)).toBeGreaterThanOrEqual(S);
        expect(CruiseController.canEngage(p, facing(p, w.point), 0, SOL)).toEqual({ ok: true, reason: null });
      }
    }
    expect(navWaypoint(spots[1], 'earth', SOL)).toEqual({ point: e, bypass: null });
    // Following the marker from the exit point: one cruise to Mars, no safety stop, the Sun at 5R or more.
    const p = c.pos.clone();
    const f = new CruiseController(SOL);
    f.begin(p, facing(p, navWaypoint(p, 'mars', SOL).point), new Vector3(), routeHop(p, 'mars', PLAN_INFLATE, SOL));
    const steer = (angle: number) => Math.max(-1, Math.min(1, angle * STEER_GAIN));
    const inv = new Quaternion();
    const d = new Vector3();
    const prev = new Vector3();
    const seen: (BodyId | null)[] = [];
    let sunMin = Infinity;
    let time = 0;
    let fexit: CruiseExitReason | null = null;
    while (!fexit && time < 300) {
      const w = navWaypoint(f.pos, 'mars', SOL);
      if (seen[seen.length - 1] !== w.bypass) seen.push(w.bypass);
      d.copy(w.point).sub(f.pos).applyQuaternion(inv.copy(f.quat).invert());
      prev.copy(f.pos);
      fexit = f.step(SIM_DT, { ...IDLE, pitch: steer(Math.atan2(d.y, -d.z)), yaw: steer(Math.atan2(d.x, -d.z)) }).exit;
      time += SIM_DT;
      sunMin = Math.min(sunMin, segmentDistance(prev, f.pos, sun));
    }
    expect(fexit).toBe('approach');
    expect(f.aheadBody).toBe('mars');
    expect(f.safetyStops).toBe(0);
    expect(time).toBeLessThanOrEqual(60);
    expect(seen).toEqual(['sun', null]);
    expect(sunMin).toBeGreaterThanOrEqual(CRUISE.starStandoffRadii * BODIES.sun.radius);
  });

  it('a clear line points at the target; a body the ship is inside, or whose envelope the line leaves, and the Quiet System are not bypassed', () => {
    const e = center('earth');
    const moon = center('moon');
    const toMoon = moon.clone().sub(e).normalize();
    const clear = navWaypoint(e.clone().addScaledVector(toMoon, safetyRadius(BODIES.earth) + 12000), 'moon', SOL);
    expect(clear.bypass).toBeNull();
    expect(clear.point.toArray()).toEqual(moon.toArray());
    // Above Earth's far side, outside its inflated envelope, Earth blocks the line: route around it.
    const far = e.clone().addScaledVector(toMoon, -(safetyRadius(BODIES.earth) + 30000));
    expect(navWaypoint(far, 'moon', SOL).bypass).toBe('earth');
    // Parked on the far side (inside Earth's envelope): climbing out clears it, so no bypass.
    const parked = e.clone().addScaledVector(toMoon, -(BODIES.earth.radius + 100));
    expect(navWaypoint(parked, 'moon', SOL).bypass).toBeNull();
    // The Quiet System keeps its direct marker even when a body is in the way.
    const q = SYSTEM_BODY_IDS.quiet;
    const ilex = center('ilex');
    const vesper = center('vesper');
    const behind = ilex.clone().addScaledVector(vesper.clone().sub(ilex).normalize(), -(safetyRadius(BODIES.ilex) + 30000));
    expect(blockedBy(behind, vesper, PLAN_INFLATE, q.filter((id) => id !== 'vesper'))).toBe('ilex');
    const quiet = navWaypoint(behind, 'vesper', q);
    expect(quiet.bypass).toBeNull();
    expect(quiet.point.toArray()).toEqual(vesper.toArray());
  });
});

describe('system edge', () => {
  const out = new Vector3(0, 1, 0);

  it('cruise stops inside SYSTEM_EXTENT without a safety stop', () => {
    const p = out.clone().multiplyScalar(0.9 * SYSTEM_EXTENT);
    const ahead = freeDistance(p, out, SOL);
    expect(ahead.body).toBeNull();
    expect(ahead.distance).toBeCloseTo(0.1 * SYSTEM_EXTENT, 0);
    const c = new CruiseController(SOL);
    c.begin(p, facing(p, p.clone().add(out)), new Vector3(), ahead.distance);
    let exit = null;
    let peak = 0;
    for (let i = 0; i < 60 * 120 && !exit; i++) {
      exit = c.step(SIM_DT, IDLE).exit;
      peak = Math.max(peak, c.speed);
      expect(c.pos.length()).toBeLessThan(SYSTEM_EXTENT);
    }
    expect(exit).toBe('approach');
    expect(c.aheadBody).toBeNull();
    expect(c.safetyStops).toBe(0);
    expect(peak).toBeGreaterThan(300000);
    expect(SYSTEM_EXTENT - c.pos.length()).toBeLessThan(6000);
  });

  it('the exact sweep holds the edge and engaging beyond it is refused', () => {
    const p = out.clone().multiplyScalar(SYSTEM_EXTENT - 200);
    const c = new CruiseController(SOL);
    c.begin(p, facing(p, p.clone().add(out)), new Vector3());
    c.speed = 15000; // inconsistent state on purpose: 200 m from the edge at 15 km/s
    expect(c.step(SIM_DT, IDLE).exit).toBe('safety');
    expect(c.safetyStops).toBe(1);
    expect(c.pos.length()).toBeLessThanOrEqual(SYSTEM_EXTENT);
    expect(c.speed).toBeLessThanOrEqual(CRUISE.exitSpeed);

    const near = out.clone().multiplyScalar(SYSTEM_EXTENT - 3000);
    const r1 = CruiseController.canEngage(near, facing(near, near.clone().add(out)), 300, SOL);
    expect(r1.ok).toBe(false);
    expect(r1.reason).toMatch(/edge of the charted system/);
    expect(CruiseController.canEngage(near, facing(near, new Vector3()), 300, SOL).ok).toBe(true);
    const beyond = out.clone().multiplyScalar(SYSTEM_EXTENT + 10);
    expect(CruiseController.canEngage(beyond, facing(beyond, new Vector3()), 0, SOL).ok).toBe(false);
  });
});

describe('precision at the Sol scale', () => {
  it('floating-origin round trip at 1.5e8 m stays under 1e-6 m', () => {
    const base = new Vector3(1.5e8, -2.1e6, 3.3e7);
    const fo = new FloatingOrigin();
    FloatingOrigin.rounded(base, fo.origin);
    const local = new Vector3();
    const back = new Vector3();
    let seed = 12345;
    const rand = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648) * 2 - 1;
    let roundTrip = 0;
    for (let i = 0; i < 2000; i++) {
      const p = base.clone().add(new Vector3(rand() * 3000.123, rand() * 3000.456, rand() * 3000.789));
      fo.toLocal(p, local);
      if (fo.needsRebase(local)) fo.rebaseAround(local, (d) => local.add(d));
      roundTrip = Math.max(roundTrip, fo.toSystem(local, back).distanceTo(p));
    }
    expect(roundTrip).toBeLessThan(1e-6);

    // A ship moving at 1 km/s for 100 s, rebasing as it goes: the system position
    // tracks the analytic path, and the local frame stays small enough for float32.
    const v = new Vector3(700.25, -300.5, 648.125);
    const fo2 = new FloatingOrigin();
    FloatingOrigin.rounded(base, fo2.origin);
    const pos = fo2.toLocal(base, new Vector3());
    let drift = 0;
    let f32 = 0;
    for (let i = 1; i <= 6000; i++) {
      pos.addScaledVector(v, SIM_DT);
      if (fo2.needsRebase(pos)) fo2.rebaseAround(pos, (d) => pos.add(d));
      expect(pos.length()).toBeLessThan(REBASE_DISTANCE + 50);
      f32 = Math.max(f32, Math.abs(Math.fround(pos.x) - pos.x), Math.abs(Math.fround(pos.y) - pos.y), Math.abs(Math.fround(pos.z) - pos.z));
      drift = Math.max(drift, fo2.toSystem(pos, back).distanceTo(base.clone().addScaledVector(v, i * SIM_DT)));
    }
    expect(fo2.count).toBeGreaterThan(50);
    expect(drift).toBeLessThan(1e-6);
    expect(f32).toBeLessThan(1e-3);
  });

  it('a 90,000 km cruise (Earth -> Neptune) stays within 1 m of the analytic straight line', () => {
    const e = center('earth');
    const dir = center('neptune').sub(e).normalize();
    const start = e.addScaledVector(dir, safetyRadius(BODIES.earth) + 12000);
    const c = new CruiseController(SOL);
    c.begin(start, facing(start, center('neptune')), new Vector3(), hopDistance(start, 'neptune'));
    const fwd = new Vector3(0, 0, -1).applyQuaternion(c.quat);
    let s = 0;
    let worst = 0;
    let exit = null;
    let t = 0;
    while (!exit && t < 120) {
      exit = c.step(SIM_DT, IDLE).exit;
      s += c.speed * SIM_DT;
      t += SIM_DT;
      worst = Math.max(worst, c.pos.distanceTo(start.clone().addScaledVector(fwd, s)));
    }
    expect(exit).toBe('approach');
    expect(c.aheadBody).toBe('neptune');
    expect(c.safetyStops).toBe(0);
    expect(s).toBeGreaterThan(8.9e7);
    expect(t).toBeLessThanOrEqual(60);
    expect(worst).toBeLessThan(1);
    console.log(`earth->neptune: ${(s / 1e6).toFixed(0)},000 km in ${t.toFixed(1)} s at up to ${(c.maxSpeed / 1000).toFixed(0)} km/s, max deviation ${(worst * 1000).toFixed(3)} mm`);
  });
});
