import { Vector3, type PerspectiveCamera } from 'three';

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
  /** Pivot height above the feet (eye level). */
  pivotUp: 1.62,
  /** Extra height of the arm's anchor above the pivot. */
  raise: 0.28,
  /** Shoulder offset to the right (m). */
  shoulder: 0.42,
  /** Arm length at rest and its growth with speed (disabled with reduced motion). */
  arm: 4.2,
  armSpeedGain: 0.06,
  armMaxExtra: 1.2,
  /** Sphere radius of the arm cast and the margin kept from what it hits. */
  probe: 0.22,
  margin: 0.08,
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
const _side = new Vector3();

export class CharacterCamera {
  mode: ViewMode = 'third';
  /** Current arm length (m). */
  arm: number = CHAR_CAMERA.arm;
  /** Current shoulder offset (m), reduced near walls. */
  shoulder: number = CHAR_CAMERA.shoulder;
  /** Camera position and look direction of the last update (local coordinates). */
  readonly position = new Vector3();
  readonly look = new Vector3(0, 0, -1);
  /** Whether the body should be drawn this frame. */
  bodyVisible = true;
  /** Closest the camera came to the analytic terrain while in third person (diagnostics; m). */
  minTerrainClearance = Infinity;
  /** Frames where the arm cast shortened the arm (diagnostics). */
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
      this.aimAt(camera, up);
      return;
    }
    _right.crossVectors(heading, up).normalize();
    // Shoulder: shift the anchor sideways unless a wall is right there.
    let shoulder: number = CHAR_CAMERA.shoulder;
    // Anchor above the head, lowered under a low overhang.
    let raise: number = CHAR_CAMERA.raise;
    if (cast) {
      const hu = cast(_pivot, up, raise + CHAR_CAMERA.probe, CHAR_CAMERA.probe);
      if (hu !== null) raise = Math.max(0, hu - CHAR_CAMERA.probe - CHAR_CAMERA.margin);
    }
    _anchor.copy(_pivot).addScaledVector(up, raise);
    if (cast) {
      _side.copy(_right);
      const hs = cast(_anchor, _side, shoulder + CHAR_CAMERA.probe, CHAR_CAMERA.probe);
      if (hs !== null) shoulder = Math.max(0, hs - CHAR_CAMERA.probe - CHAR_CAMERA.margin);
    }
    this.shoulder = shoulder;
    _anchor.addScaledVector(_right, shoulder);
    // Arm: wanted length (longer when moving fast, unless reduced motion), cast backward.
    const wanted = CHAR_CAMERA.arm + (reducedMotion ? 0 : Math.min(CHAR_CAMERA.armMaxExtra, speed * CHAR_CAMERA.armSpeedGain));
    _dir.copy(_look).negate();
    let allowed = wanted;
    if (cast) {
      const hit = cast(_anchor, _dir, wanted + CHAR_CAMERA.probe, CHAR_CAMERA.probe);
      if (hit !== null) allowed = Math.max(0, hit - CHAR_CAMERA.margin);
    }
    if (allowed < this.arm) {
      // Never through geometry: pull in at once.
      this.arm = allowed;
      if (allowed < wanted - 1e-3) this.pushedFrames++;
    } else if (dt > 0) {
      this.arm += (allowed - this.arm) * (1 - Math.exp(-dt / (CHAR_CAMERA.easeOut / 3)));
      this.arm = Math.min(this.arm, allowed);
    }
    this.position.copy(_anchor).addScaledVector(_dir, this.arm);
    // Analytic terrain clearance (colliders may not be loaded around the camera).
    if (terrain) {
      const deficit = terrain(this.position, up);
      // deficit is relative to 1.6 m clearance; keep at least minGround instead.
      const push = deficit === null ? 0 : deficit - (1.6 - CHAR_CAMERA.minGround);
      if (push > 0) this.position.addScaledVector(up, push);
      const clearance = deficit === null ? 1.6 : 1.6 - deficit + Math.max(0, push);
      this.minTerrainClearance = Math.min(this.minTerrainClearance, clearance);
    }
    this.bodyVisible = this.arm >= CHAR_CAMERA.hideBelow;
    this.aimAt(camera, up);
  }

  /** Orient the camera along the aim direction with radial up. */
  private aimAt(camera: PerspectiveCamera, up: Vector3): void {
    camera.position.copy(this.position);
    camera.up.copy(up);
    camera.lookAt(_target.copy(this.position).add(this.look));
  }
}
