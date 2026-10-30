import { Vector3 } from 'three';
import { BOARDING_POINT, GEAR_PAD_BOTTOM_Y } from '../ship/ShipModel';

// Scripted ship <-> foot transitions (charter K: board and exit animations).
// The walking capsule never moves during them (the ability hooks hold it);
// only the explorer's visible body follows a path: out of the hatch, down
// the ladder and over to where the capsule stands, or the reverse. Paths are
// built once in the floating-origin frame from the parked ship's transform.

/** What a transition needs from the world. */
export interface TransitionWorld {
  /** Ship-local point to local (floating-origin) coordinates. */
  shipToLocal(v: Vector3, out: Vector3): Vector3;
  /** Radial up at a local point. */
  upAt(p: Vector3, out: Vector3): Vector3;
  /** Ground point below a local point (null when nothing is there). */
  groundBelow(p: Vector3, up: Vector3, out: Vector3): Vector3 | null;
}

/** The scripted body pose at one moment. */
export interface ScriptedPose {
  /** Feet point (as the capsule's feet would be: ground + controller skin). */
  feet: Vector3;
  /** Facing target (tangent plane). */
  faceDir: Vector3;
  /** Path velocity (drives the gait while walking). */
  moveVel: Vector3;
  /** Ladder pose (null when walking). */
  climb: { blend: number; phase: number } | null;
  /** Cinematic camera: eye and look-at point, and how much it replaces the character camera (0..1). */
  cameraEye: Vector3;
  cameraTarget: Vector3;
  cameraWeight: number;
}

export const TRANSITION = {
  /** Feet stand this far out from the ladder's plane while climbing (m). */
  standoff: 0.36,
  /** Highest climbed rung: feet on the third rung, head inside the hatch. */
  topRung: 2,
  climbSpeed: 1.6,
  walkSpeed: 2.4,
  /** Seconds to turn toward the ladder or the final heading. */
  turn: 0.3,
  /** Exit spots farther than this from the ladder skip the walk (s/he steps straight out instead). */
  maxWalk: 4.5,
  /** Rung spacing (m): one climb cycle is two rungs. */
  rung: 0.42,
  /** Seconds the cinematic camera takes to blend in (boarding) or out (exit). */
  cameraBlend: 0.6,
  /** Cinematic camera: out from the ladder, toward the nose, above the ground (m). */
  cameraOut: 4.6,
  cameraSide: 1.6,
  cameraUp: 1.7,
} as const;

const SKIN = 0.02;

interface Segment {
  kind: 'climb' | 'walk' | 'turn';
  from: Vector3;
  to: Vector3;
  face: Vector3;
  duration: number;
}

const _a = new Vector3();
const _b = new Vector3();

export class ShipTransition {
  readonly duration: number;
  private readonly segments: Segment[] = [];
  /** Where the cinematic camera stands (outside the hull, facing the ladder) and its up. */
  private readonly eye: Vector3;
  private readonly up: Vector3;

  private constructor(readonly kind: 'exit' | 'board', segments: Segment[], eye: Vector3, up: Vector3) {
    this.segments = segments;
    this.duration = segments.reduce((s, g) => s + g.duration, 0);
    this.eye = eye;
    this.up = up;
  }

  /**
   * Out of the hatch and down the ladder, then over to the capsule's feet and
   * turn to the walker's heading. Null when the ladder ground cannot be found.
   */
  static exit(w: TransitionWorld, capsuleFeet: Vector3, heading: Vector3): ShipTransition | null {
    const ladder = ladderPoints(w);
    if (!ladder) return null;
    const segs: Segment[] = [];
    segs.push(climbSeg(ladder.top, ladder.base, ladder.face));
    const d = _a.copy(capsuleFeet).sub(ladder.base);
    const up = w.upAt(ladder.base, _b);
    d.addScaledVector(up, -d.dot(up));
    if (d.length() > TRANSITION.maxWalk) return null;
    if (d.length() > 0.05) segs.push(walkSeg(ladder.base, capsuleFeet));
    segs.push({ kind: 'turn', from: capsuleFeet.clone(), to: capsuleFeet.clone(), face: heading.clone(), duration: TRANSITION.turn });
    return new ShipTransition('exit', segs, ladder.eye, ladder.up);
  }

  /** From the capsule's feet over to the ladder, turn to it and climb into the hatch. */
  static board(w: TransitionWorld, capsuleFeet: Vector3): ShipTransition | null {
    const ladder = ladderPoints(w);
    if (!ladder) return null;
    const segs: Segment[] = [];
    if (_a.copy(ladder.base).sub(capsuleFeet).length() > 0.05) segs.push(walkSeg(capsuleFeet, ladder.base));
    segs.push({ kind: 'turn', from: ladder.base.clone(), to: ladder.base.clone(), face: ladder.face.clone(), duration: TRANSITION.turn });
    segs.push(climbSeg(ladder.base, ladder.top, ladder.face));
    return new ShipTransition('board', segs, ladder.eye, ladder.up);
  }

  /** The body pose t seconds into the transition (clamped to its ends). */
  sample(t: number, out: ScriptedPose): ScriptedPose {
    let rem = Math.max(0, t);
    let seg = this.segments[this.segments.length - 1];
    let u = 1;
    for (const s of this.segments) {
      if (rem <= s.duration) {
        seg = s;
        u = s.duration > 0 ? rem / s.duration : 1;
        break;
      }
      rem -= s.duration;
    }
    out.feet.lerpVectors(seg.from, seg.to, seg.kind === 'walk' ? easeInOut(u) : u);
    out.moveVel.set(0, 0, 0);
    out.climb = null;
    if (seg.kind === 'walk') {
      _a.copy(seg.to).sub(seg.from);
      const len = _a.length();
      out.faceDir.copy(_a).normalize();
      // Speed along the path (derivative of the eased position).
      out.moveVel.copy(out.faceDir).multiplyScalar((len / seg.duration) * easeInOutRate(u));
    } else {
      out.faceDir.copy(seg.face);
    }
    if (seg.kind === 'climb') {
      const climbed = seg.from.distanceTo(out.feet);
      // Blend in over the first and out over the last 0.15 s on the ground end.
      const edge = Math.min(1, (this.kind === 'exit' ? seg.duration - rem : rem) / 0.15);
      out.climb = { blend: Math.max(0, Math.min(1, edge)), phase: climbed / (2 * TRANSITION.rung) };
    }
    // Cinematic camera: outside the hull, watching the climber's chest. It
    // takes over at the start of boarding and hands back at the end of an exit.
    out.cameraEye.copy(this.eye);
    out.cameraTarget.copy(out.feet).addScaledVector(this.up, 1.2);
    const tt = Math.max(0, Math.min(this.duration, t));
    out.cameraWeight = this.kind === 'board' ? easeInOut(Math.min(1, tt / TRANSITION.cameraBlend)) : 1 - easeInOut(Math.max(0, Math.min(1, (tt - (this.duration - TRANSITION.cameraBlend)) / TRANSITION.cameraBlend)));
    return out;
  }
}

export function newScriptedPose(): ScriptedPose {
  return { feet: new Vector3(), faceDir: new Vector3(0, 0, -1), moveVel: new Vector3(), climb: null, cameraEye: new Vector3(), cameraTarget: new Vector3(), cameraWeight: 0 };
}

function easeInOut(u: number): number {
  return u * u * (3 - 2 * u);
}
function easeInOutRate(u: number): number {
  return 6 * u * (1 - u);
}

function climbSeg(from: Vector3, to: Vector3, face: Vector3): Segment {
  return { kind: 'climb', from: from.clone(), to: to.clone(), face: face.clone(), duration: from.distanceTo(to) / TRANSITION.climbSpeed };
}

function walkSeg(from: Vector3, to: Vector3): Segment {
  const dir = to.clone().sub(from);
  return { kind: 'walk', from: from.clone(), to: to.clone(), face: dir.normalize(), duration: Math.max(0.35, from.distanceTo(to) / TRANSITION.walkSpeed) };
}

/** Ladder base (feet on the ground), top (feet on the highest rung), the climber's facing, up and the cinematic eye. */
function ladderPoints(w: TransitionWorld): { base: Vector3; top: Vector3; face: Vector3; up: Vector3; eye: Vector3 } | null {
  const bp = BOARDING_POINT;
  // The ladder stands in the ship's YZ plane at the boarding point; the climber is on its -X side, facing +X.
  const baseShip = new Vector3(bp.x - TRANSITION.standoff, GEAR_PAD_BOTTOM_Y, bp.z);
  const topShip = new Vector3(bp.x - TRANSITION.standoff, bp.y + 0.35 + TRANSITION.topRung * TRANSITION.rung, bp.z);
  const top = w.shipToLocal(topShip, new Vector3());
  const above = w.shipToLocal(baseShip.clone().setY(bp.y + 1), new Vector3());
  const up = w.upAt(above, new Vector3());
  const ground = w.groundBelow(above, up, new Vector3());
  if (!ground) return null;
  const base = ground.addScaledVector(up, SKIN);
  const face = w.shipToLocal(new Vector3(bp.x + 1, bp.y, bp.z), new Vector3()).sub(w.shipToLocal(new Vector3(bp.x, bp.y, bp.z), new Vector3()));
  face.addScaledVector(up, -face.dot(up)).normalize();
  // Top: on the ladder above the base (the ladder is vertical in the ship frame; keep it above the base).
  const lift = top.clone().sub(base).dot(up);
  // Cinematic eye: out from the ladder (away from the hull) and toward the nose (ship -Z).
  const nose = w.shipToLocal(new Vector3(bp.x, bp.y, bp.z - 1), new Vector3()).sub(w.shipToLocal(new Vector3(bp.x, bp.y, bp.z), new Vector3()));
  nose.addScaledVector(up, -nose.dot(up)).normalize();
  const eye = base.clone().addScaledVector(face, -TRANSITION.cameraOut).addScaledVector(nose, TRANSITION.cameraSide).addScaledVector(up, TRANSITION.cameraUp);
  return { base, top: base.clone().addScaledVector(up, Math.max(0.5, lift)), face, up: up.clone(), eye };
}
