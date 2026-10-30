import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { applyKeepOut, keepOutBodies, keepOutRadius, keepOutWarning, minRadialSpeed } from '../src/game/KeepOut';
import { FLIGHT, KEEP_OUT, SIM_DT } from '../src/game/config';
import { safetyRadius } from '../src/ship/Cruise';
import { BODIES, SOL_M2_BODIES, SYSTEM_BODY_IDS, type BodyId } from '../src/world/bodies';
import { bodyGravity } from '../src/world/environment';

// Keep-out walls (LEAD-M2 step 5), in Node: which bodies get one, where it
// sits, and a piloted ship driven at a wall the way Game drives it (Rapier's
// semi-implicit step under gravity and thrust, then the wall on the velocity).

const SOL = SOL_M2_BODIES;

function center(id: BodyId): Vector3 {
  return new Vector3(...BODIES[id].center);
}

/**
 * Fly at `id` from `startGap` m outside its wall at `speed` m/s inward, with
 * full space thrust inward on top of its gravity, for `seconds`; returns the
 * smallest gap reached and the final state.
 */
function dive(id: BodyId, startGap: number, speed: number, seconds: number, tangential = 0) {
  const def = BODIES[id];
  const c = center(id);
  const n = new Vector3(0.6, -0.48, 0.64).normalize();
  const t = new Vector3().crossVectors(n, new Vector3(0, 0, 1)).normalize();
  const pos = c.clone().addScaledVector(n, keepOutRadius(def) + startGap);
  const vel = n.clone().multiplyScalar(-speed).addScaledVector(t, tangential);
  const g = new Vector3();
  const spin = () => pos.clone().sub(c).cross(vel).length();
  const spin0 = spin();
  let minGap = Infinity;
  let clamped = 0;
  for (let i = 0; i < seconds / SIM_DT; i++) {
    bodyGravity(def, pos.x - c.x, pos.y - c.y, pos.z - c.z, g);
    const thrust = pos.clone().sub(c).normalize().multiplyScalar(-FLIGHT.accelSpace);
    vel.addScaledVector(g, SIM_DT).addScaledVector(thrust, SIM_DT);
    pos.addScaledVector(vel, SIM_DT);
    if (applyKeepOut(pos, vel, SOL).clamped) clamped++;
    minGap = Math.min(minGap, pos.distanceTo(c) - keepOutRadius(def));
  }
  // Gravity, thrust and the wall are all radial, so the angular momentum stays as it was.
  return { minGap, clamped, spinRatio: spin() / spin0 };
}

describe('keep-out walls', () => {
  it('wall every Sol body without a surface in play (Sun, Mercury, Venus, giants), none in the Quiet System', () => {
    expect(keepOutBodies(SOL)).toEqual(['sun', 'mercury', 'venus', 'jupiter', 'saturn', 'uranus', 'neptune']);
    expect(keepOutBodies(SYSTEM_BODY_IDS.quiet)).toEqual([]);
  });

  it('each wall sits above the body\'s relief and atmosphere and inside its cruise envelope', () => {
    for (const id of keepOutBodies(SOL)) {
      const def = BODIES[id];
      const r = keepOutRadius(def);
      expect(r).toBeGreaterThan(def.radius + Math.max(def.atmosphereHeight, def.maxHeight));
      expect(r).toBeLessThan(safetyRadius(def));
    }
  });

  it('allows outward and tangential motion, limits inward speed so the ship stops at the wall, and pushes out inside it', () => {
    expect(minRadialSpeed(0)).toBeCloseTo(0, 9);
    expect(minRadialSpeed(1000)).toBeCloseTo(-Math.sqrt(2 * KEEP_OUT.decel * 1000), 6);
    expect(minRadialSpeed(-10)).toBeGreaterThan(0);
    expect(minRadialSpeed(-1e6)).toBe(KEEP_OUT.maxPush);
    const c = center('jupiter');
    const n = new Vector3(1, 0, 0);
    const pos = c.clone().addScaledVector(n, keepOutRadius(BODIES.jupiter) + 1000);
    const away = new Vector3(300, 40, -20);
    const s = applyKeepOut(pos, away, SOL);
    expect(s.clamped).toBe(false);
    expect(away.toArray()).toEqual([300, 40, -20]);
    expect(s.body).toBe('jupiter');
    const at = new Vector3(-900, 40, -20);
    expect(applyKeepOut(pos, at, SOL).clamped).toBe(true);
    expect(at.x).toBeCloseTo(-Math.sqrt(2 * KEEP_OUT.decel * 1000), 6);
    expect([at.y, at.z]).toEqual([40, -20]);
  });

  for (const id of ['jupiter', 'mercury', 'venus', 'sun'] as BodyId[]) {
    it(`a ship boosting at ${BODIES[id].name} under full thrust stops at its wall and slides along it`, () => {
      const r = dive(id, 8000, FLIGHT.capSpaceBoost, 30, 200);
      // Penetration stays within a few metres (one step of thrust and gravity against the push).
      expect(r.minGap).toBeGreaterThan(-10);
      expect(r.clamped).toBeGreaterThan(0);
      expect(r.spinRatio).toBeCloseTo(1, 9);
    });
  }

  it('a ship found inside a wall is pushed back out', () => {
    const def = BODIES.saturn;
    const c = center('saturn');
    const pos = c.clone().add(new Vector3(0, 0, keepOutRadius(def) - 3000));
    const vel = new Vector3();
    const g = new Vector3();
    for (let i = 0; i < 120 / SIM_DT; i++) {
      bodyGravity(def, pos.x - c.x, pos.y - c.y, pos.z - c.z, g);
      vel.addScaledVector(g, SIM_DT);
      pos.addScaledVector(vel, SIM_DT);
      applyKeepOut(pos, vel, SOL);
    }
    expect(pos.distanceTo(c)).toBeGreaterThan(keepOutRadius(def) - 50);
  });

  it('warns near a wall with an honest reason, and never in the Quiet System', () => {
    const near = (id: BodyId, gap: number) => applyKeepOut(center(id).add(new Vector3(0, keepOutRadius(BODIES[id]) + gap, 0)), new Vector3(), SOL);
    expect(keepOutWarning(near('jupiter', 5000))).toBe('Approach limit · Jupiter: no solid ground; zone access not in this build');
    expect(keepOutWarning(near('mercury', 5000))).toBe('Approach limit · Mercury: no landing site in this build');
    expect(keepOutWarning(near('sun', 5000))).toBe('Approach limit · Sun: keep clear');
    expect(keepOutWarning(near('jupiter', KEEP_OUT.warnBand + 1000))).toBeNull();
    // Earth is surface-ready: no wall, no warning, velocity untouched.
    const down = new Vector3(0, -500, 0);
    const e = applyKeepOut(center('earth').add(new Vector3(0, BODIES.earth.radius + 2000, 0)), down, SOL);
    expect(e).toEqual({ body: null, gap: Infinity, clamped: false });
    expect(down.y).toBe(-500);
    const q = SYSTEM_BODY_IDS.quiet;
    const ilex = applyKeepOut(center('ilex').add(new Vector3(0, BODIES.ilex.radius + 100, 0)), new Vector3(0, -900, 0), q);
    expect(ilex).toEqual({ body: null, gap: Infinity, clamped: false });
  });
});
