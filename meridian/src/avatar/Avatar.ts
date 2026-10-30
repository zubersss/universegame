import { Matrix4, Quaternion, Vector3, type MeshStandardMaterial, type Object3D, type Texture } from 'three';
import { buildAvatar, B, DIM, restPosition, type AvatarRig } from './AvatarModel';
import { AvatarAnimator, BALL_F, type FootGround, type GroundFn, type PowerMotion } from './AvatarAnimator';

/** Downward ray against walkable geometry: distance to the hit and its normal, or null. */
export type GroundRay = (origin: Vector3, dir: Vector3, maxDist: number) => { dist: number; normal: Vector3 } | null;

export interface AvatarFrame {
  /** Render frame time (s); 0 freezes the animation (pause, loading). */
  dt: number;
  /** Interpolated feet point (bottom of the capsule axis, local coordinates). */
  feet: Vector3;
  /** Radial up at the feet. */
  up: Vector3;
  grounded: boolean;
  /** Vertical speed along up (m/s). */
  vVert: number;
  /** Intended horizontal velocity (tangent plane): the body turns toward it. */
  moveVel: Vector3;
  /** Camera heading (tangent plane) and pitch: the head looks there. */
  lookHeading: Vector3;
  lookPitch: number;
  /** Scripted facing (ladder, end of a transition): the body turns toward it instead of toward moveVel. */
  faceDir?: Vector3 | null;
  /** Ladder climbing pose (blend 0..1, phase in climb cycles). */
  climb?: { blend: number; phase: number } | null;
  /** A power moving the body (flight leans the whole body into the direction of travel). */
  power?: PowerMotion | null;
}

/** Body pitch in flight at cruise speed and above (rad, forward). */
const FLIGHT_LEAN = 1.2;
/** The body pitches about its middle, this far above the feet (m). */
const PITCH_PIVOT = 0.95;

const TURN_RATE = 10; // rad/s the body turns toward the movement direction
const TELEPORT = 3; // m in one frame: treated as a placement, not motion
const SKIN = 0.02; // the character controller keeps the capsule this far above the ground

const _q = new Quaternion();
const _m = new Matrix4();
const _x = new Vector3();
const _z = new Vector3();
const _o = new Vector3();
const _t = new Vector3();
const _a = new Vector3();
const _down = new Vector3();
const _xAxis = new Vector3(1, 0, 0);

/**
 * The explorer in the world: the rig placed at the walking capsule's feet,
 * turned toward the direction of travel, animated by AvatarAnimator with a
 * per-foot ground query, plus a planted-foot slip measurement for tests.
 * Purely visual: it never moves the capsule.
 */
export class Avatar {
  readonly rig: AvatarRig;
  readonly anim = new AvatarAnimator();
  /** Body facing (unit, tangent plane). */
  readonly facing = new Vector3(0, 0, -1);
  /** Largest tangent-plane drift of a planted foot so far (m). */
  maxSlip = 0;
  /** Planted-foot samples measured (for tests: proves the metric ran). */
  slipSamples = 0;
  /** Of those, samples taken while the body was moving (> 0.5 m/s). */
  slipSamplesMoving = 0;
  private readonly root = new Vector3();
  private readonly prevRoot = new Vector3();
  private hasPrev = false;
  private readonly up = new Vector3(0, 1, 0);
  private readonly right = new Vector3(1, 0, 0);
  private readonly anchors = [new Vector3(), new Vector3()];
  private readonly anchored = [false, false];
  private readonly hipsRestY: number;
  /** This frame's target root and the previous frame's (sub-step interpolation). */
  private readonly target = new Vector3();
  private readonly from = new Vector3();
  private readonly motion = new Vector3();
  private wasClimbing = false;
  /** Current whole-body pitch (rad, forward > 0). */
  bodyPitch = 0;
  private readonly groundFn: GroundFn;

  constructor(parent: Object3D, private readonly ray: GroundRay | null, heading: Vector3, private readonly envSource: (() => Texture | null) | null = null) {
    this.rig = buildAvatar();
    this.hipsRestY = restPosition('hips').y;
    this.facing.copy(heading).normalize();
    parent.add(this.rig.root);
    // The scene's reflection map can be rebuilt (and the old one disposed)
    // after this frame's update: pick it up at draw time, per material.
    if (envSource) {
      for (const m of this.rig.meshes) m.onBeforeRender = () => this.syncEnv(m.material as MeshStandardMaterial);
    }
    this.groundFn = (_side, forward, lateral, yaw) => this.footGround(forward, lateral, yaw);
  }

  get state(): string {
    return this.anim.state;
  }

  setVisible(v: boolean): void {
    this.rig.root.visible = v;
  }

  get visible(): boolean {
    return this.rig.root.visible;
  }

  /** Share the scene's reflection map so the visor and plates read like the ship. */
  private syncEnv(m: MeshStandardMaterial): void {
    const t = this.envSource ? this.envSource() : null;
    if (m.envMap === t) return;
    // Only adding or removing the map changes the shader.
    if (!m.envMap !== !t) m.needsUpdate = true;
    m.envMap = t;
  }

  /**
   * Place, orient and animate for one rendered frame. A long frame (slow
   * device, dropped steps) is animated in sub-steps of at most 1/60 s with
   * the body's motion and turn spread evenly, so the gait never skips a
   * stance.
   */
  update(f: AvatarFrame): void {
    this.up.copy(f.up).normalize();
    const up = this.up;
    // Root: capsule feet, lowered by the controller's skin so the soles touch.
    const target = this.target.copy(f.feet).addScaledVector(up, -SKIN);
    if (!this.hasPrev) this.prevRoot.copy(target);
    const dTan = this.motion.copy(target).sub(this.prevRoot);
    if (dTan.length() > TELEPORT) {
      // A placement (recovery, restore), not motion: no landing, feet under the body.
      this.prevRoot.copy(target);
      dTan.set(0, 0, 0);
      this.anchored[0] = this.anchored[1] = false;
      this.anim.resetAir();
      this.anim.resetFeet();
    }
    const start = this.from.copy(this.prevRoot);
    // Tangent-plane motion this frame.
    dTan.addScaledVector(up, -dTan.dot(up));

    this.facing.addScaledVector(up, -this.facing.dot(up));
    if (this.facing.lengthSq() < 1e-8) this.facing.copy(f.lookHeading).addScaledVector(up, -f.lookHeading.dot(up));
    this.facing.normalize();
    // Turn toward the scripted facing, else the intended movement direction (tangent plane).
    const toward = f.faceDir ?? f.moveVel;
    _t.copy(toward).addScaledVector(up, -toward.dot(up));
    let turn = 0;
    if (f.dt > 0 && _t.lengthSq() > (f.faceDir ? 1e-6 : 0.16)) {
      _t.normalize();
      const ang = Math.atan2(_a.crossVectors(this.facing, _t).dot(up), this.facing.dot(_t));
      turn = Math.max(-TURN_RATE * f.dt, Math.min(TURN_RATE * f.dt, ang));
    }

    // Off the ladder again: re-plant the feet under the body.
    const climbing = !!f.climb && f.climb.blend > 0;
    if (this.wasClimbing && !climbing) this.anim.resetFeet();
    this.wasClimbing = climbing;
    const n = f.dt > 0 ? Math.min(8, Math.max(1, Math.ceil(f.dt * 60 - 1e-6))) : 1;
    const sub = f.dt / n;
    const lookPitch = f.lookPitch * 0.6;
    for (let k = 1; k <= n; k++) {
      // Motion in the body's frame before this sub-step's turn.
      this.right.crossVectors(this.facing, up).normalize();
      const moved = dTan.dot(this.facing) / n;
      const side = dTan.dot(this.right) / n;
      if (turn !== 0) {
        _q.setFromAxisAngle(up, turn / n);
        this.facing.applyQuaternion(_q).normalize();
        this.right.crossVectors(this.facing, up).normalize();
      }
      this.root.lerpVectors(start, target, k / n);
      // Head follows the camera: yaw of the look heading relative to the body, and pitch.
      const lookYaw = Math.atan2(_a.crossVectors(this.facing, f.lookHeading).dot(up), this.facing.dot(f.lookHeading));
      this.anim.update({
        dt: sub,
        forwardDist: moved,
        lateralDist: side,
        turn: turn / n,
        grounded: f.grounded,
        vVert: f.vVert,
        ground: f.grounded && this.ray && !climbing ? this.groundFn : null,
        climb: f.climb ?? null,
        lookYaw: Math.abs(lookYaw) < 1.9 ? lookYaw : 0,
        lookPitch,
        power: f.power ?? null,
      });
    }
    this.root.copy(target);
    // Flight: the whole body leans forward with speed (smoothed).
    const pw = f.power;
    const lean = pw && pw.mode === 'flight' ? FLIGHT_LEAN * Math.min(1, pw.speed / 60) : 0;
    if (f.dt > 0) this.bodyPitch += (lean - this.bodyPitch) * (1 - Math.exp(-f.dt / 0.3));

    // Basis: forward = -Z, up = +Y, right = +X.
    _z.copy(this.facing).negate();
    _x.copy(this.right);
    _m.makeBasis(_x, up, _z);
    const root = this.rig.root;
    root.position.copy(this.root);
    root.quaternion.setFromRotationMatrix(_m);
    if (Math.abs(this.bodyPitch) > 1e-4) {
      // Pitch about the body's middle (rotation about its right axis, forward = -Z).
      _q.setFromAxisAngle(_xAxis, -this.bodyPitch);
      root.quaternion.multiply(_q);
      _t.set(0, PITCH_PIVOT, 0).applyQuaternion(root.quaternion);
      root.position.addScaledVector(up, PITCH_PIVOT).sub(_t);
    }
    this.anim.applyTo(this.rig.bones, this.hipsRestY);
    root.updateMatrixWorld(true);
    if (f.dt > 0) this.measureSlip();
    this.prevRoot.copy(this.root);
    this.hasPrev = true;
  }

  /** Ground under a foot, from a short ray along -up starting above the foot. */
  private footGround(forward: number, lateral: number, yaw: number): FootGround | null {
    if (!this.ray) return null;
    const up = this.up;
    _o.copy(this.root).addScaledVector(this.facing, forward).addScaledVector(this.right, lateral).addScaledVector(up, 0.6);
    _down.copy(up).negate();
    const hit = this.ray(_o, _down, 1.3);
    if (!hit) return null;
    const n = hit.normal;
    const nu = n.dot(up);
    if (nu < 0.5) return null; // wall or steep face: keep the flat target
    // The sole matches the ground by rolling across the foot, then pitching
    // along it: n = (cos p sin r, cos p cos r, sin p) in the foot's (right,
    // up, back) frame, so r = atan2(n.right, n.up) and p = asin(n.back).
    _t.copy(this.facing).multiplyScalar(Math.cos(yaw)).addScaledVector(this.right, -Math.sin(yaw));
    const pitch = Math.asin(Math.max(-1, Math.min(1, -n.dot(_t) / n.length())));
    _t.copy(this.right).multiplyScalar(Math.cos(yaw)).addScaledVector(this.facing, Math.sin(yaw));
    return { h: 0.6 - hit.dist, pitch, roll: Math.atan2(n.dot(_t), nu) };
  }

  /** Track how far the ball of a planted foot drifts in the tangent plane. */
  private measureSlip(): void {
    for (let i = 0; i < 2; i++) {
      const planted = this.anim.planted[i];
      if (!planted) {
        this.anchored[i] = false;
        continue;
      }
      const bone = this.rig.bones[i === 0 ? B.footL : B.footR];
      _t.set(0, -DIM.ankleY, -BALL_F).applyMatrix4(bone.matrixWorld);
      if (!this.anchored[i]) {
        this.anchors[i].copy(_t);
        this.anchored[i] = true;
        continue;
      }
      _a.copy(_t).sub(this.anchors[i]);
      _a.addScaledVector(this.up, -_a.dot(this.up));
      this.maxSlip = Math.max(this.maxSlip, _a.length());
      this.slipSamples++;
      if (this.anim.speed > 0.5) this.slipSamplesMoving++;
    }
  }

  onRebase(d: Vector3): void {
    this.prevRoot.add(d);
    this.root.add(d);
    this.anchors[0].add(d);
    this.anchors[1].add(d);
    this.rig.root.position.add(d);
  }

  dispose(): void {
    this.rig.dispose();
  }
}
