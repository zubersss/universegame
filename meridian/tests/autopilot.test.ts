import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { PLAN_INFLATE, travelRoute } from '../src/debug/autopilot';
import { safetyRadius } from '../src/ship/Cruise';
import { segmentSphereEnter } from '../src/core/mathx';
import { BODIES, BODY_IDS, type BodyId } from '../src/world/bodies';
import { computeSites } from '../src/world/sites';

// N-body readiness of the test autopilot: the travel goal must route between
// every ordered pair of bodies in BODY_IDS (so new bodies need no test changes).

function center(id: BodyId): Vector3 {
  return new Vector3(...BODIES[id].center);
}

/** Where the travel goal plans from: above the departure site, just clear of the inflated envelopes. */
function departure(id: BodyId): Vector3 {
  const n = new Vector3(...computeSites(BODIES[id]).landing.dir);
  return center(id).addScaledVector(n, safetyRadius(BODIES[id]) + PLAN_INFLATE + 2000);
}

describe('autopilot travel routes', () => {
  for (const from of BODY_IDS) {
    for (const to of BODY_IDS) {
      if (from === to) continue;
      it(`${from} → ${to} stays clear of every envelope until the final approach`, () => {
        const route = travelRoute(departure(from), to);
        expect(route.length).toBeGreaterThanOrEqual(2);
        for (const p of route) expect(Number.isFinite(p.x + p.y + p.z)).toBe(true);
        // Every leg but the last stays outside every safety envelope.
        let a = departure(from);
        for (let i = 0; i < route.length - 1; i++) {
          for (const id of BODY_IDS) expect(segmentSphereEnter(a, route[i], center(id), safetyRadius(BODIES[id]))).toBe(-1);
          a = route[i];
        }
        // The last leg is radial onto the destination's landing site and ends inside its envelope.
        const end = route[route.length - 1];
        const S = safetyRadius(BODIES[to]);
        expect(end.distanceTo(center(to))).toBeLessThan(S);
        expect(end.distanceTo(center(to))).toBeGreaterThan(BODIES[to].radius + BODIES[to].atmosphereHeight);
        for (const id of BODY_IDS) if (id !== to) expect(segmentSphereEnter(a, end, center(id), safetyRadius(BODIES[id]))).toBe(-1);
      });
    }
  }
});
