import { describe, expect, it } from 'vitest';
import { Group, Vector3 } from 'three';
import { newScriptedPose, ShipTransition, TRANSITION, type TransitionWorld } from '../src/player/Transitions';
import { BOARDING_POINT, GEAR_PAD_BOTTOM_Y } from '../src/ship/ShipModel';
import { Avatar } from '../src/avatar/Avatar';

// Parked ship at the origin with identity rotation, flat ground at the pads.
const UP = new Vector3(0, 1, 0);
function world(groundY: number | null = GEAR_PAD_BOTTOM_Y): TransitionWorld {
  return {
    shipToLocal: (v, out) => out.copy(v),
    upAt: (_p, out) => out.copy(UP),
    groundBelow: (p, up, out) => (groundY === null || p.y < groundY ? null : out.copy(p).setY(groundY)),
  };
}
const exitSpot = new Vector3(-4.1, GEAR_PAD_BOTTOM_Y + 0.02, -1.2);
const heading = new Vector3(0, 0, -1);

function samples(tr: ShipTransition, dt = 1 / 60) {
  const out = [];
  for (let t = 0; t <= tr.duration + 1e-9; t += dt) {
    const p = tr.sample(t, newScriptedPose());
    out.push({ t, feet: p.feet.clone(), face: p.faceDir.clone(), climb: p.climb ? { ...p.climb } : null, vel: p.moveVel.clone() });
  }
  return out;
}

describe('ladder transitions', () => {
  it('exit: out of the hatch, down the ladder, over to the capsule, facing the heading', () => {
    const tr = ShipTransition.exit(world(), exitSpot, heading)!;
    expect(tr).not.toBeNull();
    const s = samples(tr);
    const first = s[0];
    const last = s[s.length - 1];
    // Starts on the ladder (third rung), climbing, facing +X (toward the hull).
    expect(first.feet.x).toBeCloseTo(BOARDING_POINT.x - TRANSITION.standoff, 6);
    expect(first.feet.y).toBeGreaterThan(GEAR_PAD_BOTTOM_Y + 1.2);
    expect(first.climb?.blend).toBe(1);
    expect(first.face.x).toBeCloseTo(1, 6);
    // Ends exactly at the capsule's feet, facing the walker's heading, not climbing.
    expect(last.feet.distanceTo(exitSpot)).toBeLessThan(1e-6);
    expect(last.face.distanceTo(heading)).toBeLessThan(1e-6);
    expect(last.climb).toBeNull();
    // Continuous: never faster than the climb or walk speeds (with easing headroom).
    for (let i = 1; i < s.length; i++) expect(s[i].feet.distanceTo(s[i - 1].feet)).toBeLessThan((TRANSITION.walkSpeed * 1.6) / 60);
    expect(tr.duration).toBeGreaterThan(1.2);
    expect(tr.duration).toBeLessThan(3);
  });

  it('board: over to the ladder, turn to it, climb into the hatch', () => {
    const tr = ShipTransition.board(world(), exitSpot)!;
    const s = samples(tr);
    expect(s[0].feet.distanceTo(exitSpot)).toBeLessThan(1e-6);
    expect(s[0].climb).toBeNull();
    const last = s[s.length - 1];
    expect(last.feet.y).toBeGreaterThan(GEAR_PAD_BOTTOM_Y + 1.2);
    expect(last.climb?.blend).toBe(1);
    expect(last.face.x).toBeCloseTo(1, 6);
    for (let i = 1; i < s.length; i++) expect(s[i].feet.distanceTo(s[i - 1].feet)).toBeLessThan((TRANSITION.walkSpeed * 1.6) / 60);
  });

  it('is skipped when the ladder ground is missing or the exit spot is far from the ladder', () => {
    expect(ShipTransition.exit(world(null), exitSpot, heading)).toBeNull();
    expect(ShipTransition.board(world(null), exitSpot)).toBeNull();
    expect(ShipTransition.exit(world(), new Vector3(7, GEAR_PAD_BOTTOM_Y, 6.5), heading)).toBeNull();
  });

  it('drives the explorer: climb pose on the ladder, gait on the ground, feet re-planted after', () => {
    const tr = ShipTransition.exit(world(), exitSpot, heading)!;
    const av = new Avatar(new Group(), null, heading);
    const pose = newScriptedPose();
    const dt = 1 / 60;
    let climbed = false;
    for (let t = 0; t <= tr.duration + 0.5; t += dt) {
      tr.sample(t, pose);
      av.update({ dt, feet: pose.feet, up: UP, grounded: true, vVert: 0, moveVel: pose.moveVel, lookHeading: heading, lookPitch: 0, faceDir: pose.faceDir, climb: pose.climb });
      if (av.anim.state === 'climb') climbed = true;
    }
    expect(climbed).toBe(true);
    expect(av.anim.entries.climb).toBe(1);
    expect(av.anim.state).toBe('idle');
    expect(av.facing.distanceTo(heading)).toBeLessThan(0.01);
    expect(av.maxSlip).toBeLessThan(0.002);
    av.dispose();
  });
});
