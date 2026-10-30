import { Vector3, type PerspectiveCamera } from 'three';
import { WALK } from '../game/config';

// Third-person camera for the explorer: a spring arm behind and slightly
// right of the head, looking exactly along the aim direction (heading and
// pitch), so the crosshair is the aim ray. The arm is shortened instantly
// by a sphere cast against the world (terrain, props, ship) and eases back
// out when clear; an analytic terrain clearance covers places whose
// colliders are not loaded. C toggles first person.

export type ViewMode = 'third' | 'first';

/** Sphere cast from `from` along unit `dir`: distance to the first hit, or null. */
export type ArmCast = (from: Vector3, dir: Vector3, maxDist: number, radius: number) => number | null;

/**
 * Terrain deficit at a point: how far (m along up) it must rise to be 1.6 m
 * above the analytic terrain surface, or null when it already is (CameraRig's
 * terrainClearance contract).
 */
export type TerrainDeficit = (p: Vector3, up: Vector3) => number | null;

export const CHAR_CAMERA = {
  /** Pivot height above the feet: the walker's eye level. */
  pivotUp: WALK.eye,
  /** Extra height of the arm's anchor above the pivot. */
  raise: 0.28,
  /** Shoulder offset to the right (m). */
  shoulder: 0.42,
  /** Arm length at rest and its growth with speed (disabled with reduced motion). */
  arm: 4.2,
  armSpeedGain: 0.06,
  armMaxExtra: 1.2,
  /**
   * Sphere radius of the casts and the margin kept from what they hit: 0.2 m
   * in all covers the near plane's corners (~0.16 m at 70 deg on 16:9) while
   * still fitting the gap between the helmet and a low ceiling.
   */
  probe: 0.12,
  margin: 0.08,
  /** The camera's centre ray crosses the eye's aim ray this far ahead (m): small parallax over the scan range. */
  converge: 25,
  /** Seconds to ease back out after being pushed in. */
  easeOut: 0.3,
  /** Minimum camera height above the analytic terrain (m). */
  minGround: 0.45,
  /** Below this arm length the body would fill the view: hide it. */
  hideBelow: 0.75,
} as const;

const _look = new Vector3();
const _right = new Vector3();
const _pivot = new Vector3();
const _anchor = new Vector3();
const _dir = new Vector3();
const _target = new Vector3();

export class CharacterCamera {
  mode: ViewMode = 'third';
  /** Current arm length (m). */
  arm: number = CHAR_CAMERA.arm;
  /** Current shoulder offset (m), reduced near walls. */
  shoulder: number = CHAR_CAMERA.shoulder;
  /** Current anchor height above the eye (m), reduced under overhangs. */
  raise: number = CHAR_CAMERA.raise;
  /** Camera position and look direction of the last update (local coordinates). */
  readonly position = new Vector3();
  /** The aim direction (heading and pitch) of the last update. */
  readonly look = new Vector3(0, 0, -1);
  /** The camera's actual view direction of the last update (crosshair ray). */
  readonly view = new Vector3(0, 0, -1);
  /** Whether the body should be drawn this frame. */
  bodyVisible = true;
  /** Closest the camera came to the analytic terrain while in third person (diagnostics; m). */
  minTerrainClearance = Infinity;
  /** Frames where geometry pulled the arm in (diagnostics). */
  pushedFrames = 0;

  toggle(): void {
    this.mode = this.mode === 'third' ? 'first' : 'third';
    this.arm = 0.5;
  }

  onRebase(d: Vector3): void {
    this.position.add(d);
  }

  /**
   * Place the camera for one rendered frame. `feet` is the interpolated feet
   * point, `heading`/`pitch` the aim, `speed` the ground speed (pull-back).
   */
  update(
    dt: number,
    camera: PerspectiveCamera,
    feet: Vector3,
    up: Vector3,
    heading: Vector3,
    pitch: number,
    speed: number,
    cast: ArmCast | null,
    terrain: TerrainDeficit | null,
    reducedMotion: boolean,
  ): void {
    _look.copy(heading).multiplyScalar(Math.cos(pitch)).addScaledVector(up, Math.sin(pitch)).normalize();
    this.look.copy(_look);
    _pivot.copy(feet).addScaledVector(up, CHAR_CAMERA.pivotUp);
    if (this.mode === 'first') {
      this.position.copy(_pivot);
      this.bodyVisible = false;
      this.aimAt(camera, up, _target.copy(_pivot).add(_look));
      return;
    }
    _right.crossVectors(heading, up).normalize();
    const margin = CHAR_CAMERA.margin;
    const ease = dt > 0 ? 1 - Math.exp(-dt / (CHAR_CAMERA.easeOut / 3)) : 0;
    // Free length along a direction: a sphere cast's hit is how far its centre
    // travels before touching, so keep `margin` short of it (Infinity = clear).
    const free = (from: Vector3, dir: Vector3, range: number) => {
      if (!cast) return Infinity;
      const h = cast(from, dir, range + margin, CHAR_CAMERA.probe);
      return h === null ? Infinity : Math.max(0, h - margin);
    };
    // Geometry pulls an offset in at once; otherwise it eases toward its rest
    // length (both ways), never past what is free. Continuous at the cast range.
    const follow = (cur: number, rest: number, room: number) => {
      if (room < cur) return room;
      const target = Math.min(rest, room);
      return Math.min(room, cur + (target - cur) * ease);
    };
    // Anchor above the head (lowered under an overhang), then shifted to the shoulder.
    this.raise = follow(this.raise, CHAR_CAMERA.raise, free(_pivot, up, CHAR_CAMERA.raise));
    _anchor.copy(_pivot).addScaledVector(up, this.raise);
    this.shoulder = follow(this.shoulder, CHAR_CAMERA.shoulder, free(_anchor, _right, CHAR_CAMERA.shoulder));
    _anchor.addScaledVector(_right, this.shoulder);
    // Arm: rest length (longer when moving fast, unless reduced motion), cast backward.
    const wanted = CHAR_CAMERA.arm + (reducedMotion ? 0 : Math.min(CHAR_CAMERA.armMaxExtra, speed * CHAR_CAMERA.armSpeedGain));
    _dir.copy(_look).negate();
    const room = free(_anchor, _dir, wanted);
    if (room < this.arm) this.pushedFrames++;
    this.arm = follow(this.arm, wanted, room);
    this.position.copy(_anchor).addScaledVector(_dir, this.arm);
    // Analytic terrain clearance (colliders may not be loaded around the camera).
    if (terrain) {
      const deficit = terrain(this.position, up);
      // deficit is relative to 1.6 m clearance; keep at least minGround instead.
      const push = deficit === null ? 0 : deficit - (1.6 - CHAR_CAMERA.minGround);
      if (push > 0) this.position.addScaledVector(up, push);
      // Measured where the camera ends up (capped at 1.6 m by the contract).
      const after = terrain(this.position, up);
      this.minTerrainClearance = Math.min(this.minTerrainClearance, after === null ? 1.6 : 1.6 - after);
    }
    this.bodyVisible = this.arm >= CHAR_CAMERA.hideBelow;
    // Look at the point the eye aims at, `converge` metres out.
    this.aimAt(camera, up, _target.copy(_pivot).addScaledVector(_look, CHAR_CAMERA.converge));
  }

  /** Place and orient the camera (radial up) toward a target point. */
  private aimAt(camera: PerspectiveCamera, up: Vector3, target: Vector3): void {
    camera.position.copy(this.position);
    camera.up.copy(up);
    camera.lookAt(target);
    this.view.copy(target).sub(this.position).normalize();
  }
}
