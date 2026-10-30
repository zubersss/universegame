import { PerspectiveCamera, Quaternion, Vector3, type Object3D, type Texture } from 'three';
import { RAPIER, GROUPS, type Physics } from '../physics/Physics';
import { WALK } from '../game/config';
import { alignUp } from '../core/mathx';
import { Avatar } from '../avatar/Avatar';
import { CharacterCamera } from './CharacterCamera';
import type { CameraRig } from '../render/CameraRig';
import type { ScriptedPose } from './Transitions';
import type { PowerMotion } from '../avatar/AvatarAnimator';

const HALF = (WALK.height - 2 * WALK.radius) / 2; // capsule cylinder half-height
/** Distance from the capsule center to the bottom of the feet. */
export const FOOT_OFFSET = HALF + WALK.radius;

export interface WalkInput {
  forward: number; // -1..1
  right: number; // -1..1
  sprint: boolean;
  jump: boolean;
  /** Mouse look deltas (radians) this step. */
  yaw: number;
  pitch: number;
}

const _up = new Vector3();
const _right = new Vector3();
const _desired = new Vector3();
const _q = new Quaternion();
const _v = new Vector3();
const _feet = new Vector3();
const _n = new Vector3();
const _rot = { x: 0, y: 0, z: 0, w: 1 };
const _g = new Vector3();
const _m = new Vector3();
/** Cosine of the walking slope limit: ground at least this level is walkable. */
export const WALKABLE_COS = Math.cos((WALK.maxSlopeDeg * Math.PI) / 180);
/** A camera stand-in for lookAt (cameras look down -Z, unlike other objects). */
const _camObj = new PerspectiveCamera();

/**
 * Walker: a kinematic capsule driven by Rapier's character controller. "Up"
 * is radial; the capsule is re-aligned separately each step around its feet
 * (the controller resolves translation only). Optionally carries the visible
 * explorer (attachVisual) and owns the on-foot camera (renderView).
 */
export class Player {
  readonly body: RAPIER.RigidBody;
  readonly collider: RAPIER.Collider;
  readonly cc: RAPIER.KinematicCharacterController;
  /** Capsule center (local coords), current and previous for interpolation. */
  readonly pos = new Vector3();
  readonly prevPos = new Vector3();
  readonly quat = new Quaternion();
  /** Horizontal velocity (tangent plane) and vertical speed along up. */
  readonly vel = new Vector3();
  vVert = 0;
  grounded = false;
  /** Unit heading in the tangent plane (parallel-transported). */
  readonly heading = new Vector3(0, 0, -1);
  /** Camera pitch (rad). */
  pitch = 0;
  readonly up = new Vector3(0, 1, 0);
  /** Current ground snapping distance (the controller starts with WALK.snap). */
  private snapDist: number = WALK.snap;
  /** Seconds airborne (for jump/land sounds). */
  airTime = 0;
  justLanded = false;
  /** The last powered move (moveFree) ran into something steeper than walkable: a wall, not the ground it moves over. */
  hitWall = false;
  stepDistance = 0;
  /** Visible explorer (null until attachVisual; never in headless tests). */
  avatar: Avatar | null = null;
  /** Third/first-person camera. */
  readonly view = new CharacterCamera();
  private readonly balls = new Map<number, RAPIER.Ball>();
  private readonly sweepShape = playerShape();
  private readonly collision = new RAPIER.CharacterCollision();


  constructor(private readonly physics: Physics, center: Vector3, up: Vector3, heading: Vector3) {
    const world = physics.world;
    this.up.copy(up).normalize();
    this.quat.copy(alignUp(new Quaternion(), this.up, _q));
    this.pos.copy(center);
    this.prevPos.copy(center);
    this.body = world.createRigidBody(
      RAPIER.RigidBodyDesc.kinematicPositionBased()
        .setTranslation(center.x, center.y, center.z)
        .setRotation({ x: this.quat.x, y: this.quat.y, z: this.quat.z, w: this.quat.w }),
    );
    this.collider = world.createCollider(
      RAPIER.ColliderDesc.capsule(HALF, WALK.radius).setCollisionGroups(GROUPS.player).setSolverGroups(GROUPS.player).setFriction(0),
      this.body,
    );
    this.cc = world.createCharacterController(WALK.skin);
    this.cc.setMaxSlopeClimbAngle((WALK.maxSlopeDeg * Math.PI) / 180);
    this.cc.setMinSlopeSlideAngle(((WALK.maxSlopeDeg + 5) * Math.PI) / 180);
    this.cc.enableAutostep(WALK.step, 0.2, false);
    this.cc.enableSnapToGround(WALK.snap);
    this.cc.setApplyImpulsesToDynamicBodies(false);
    this.cc.setSlideEnabled(true);
    this.setHeading(heading);
  }

  setHeading(h: Vector3): void {
    this.heading.copy(h).addScaledVector(this.up, -h.dot(this.up));
    if (this.heading.lengthSq() < 1e-8) this.heading.set(1, 0, 0).addScaledVector(this.up, -this.up.x);
    this.heading.normalize();
  }

  /** Feet position (local). */
  feet(out: Vector3): Vector3 {
    return out.copy(this.pos).addScaledVector(this.up, -FOOT_OFFSET);
  }

  /** Interpolated eye position for the camera. */
  eye(alpha: number, out: Vector3): Vector3 {
    out.lerpVectors(this.prevPos, this.pos, alpha);
    return out.addScaledVector(this.up, -FOOT_OFFSET + WALK.eye);
  }

  /**
   * One fixed step. `planetCenter` is the active body center (local);
   * `gravity` the local gravity magnitude.
   */
  /** Radial up from the planet centre; re-align the capsule around its feet (heading transported). */
  private realign(planetCenter: Vector3): void {
    _up.copy(this.pos).sub(planetCenter).normalize();
    if (_up.angleTo(this.up) > 1e-6) {
      const feetOld = _v.copy(this.pos).addScaledVector(this.up, -FOOT_OFFSET);
      this.up.copy(_up);
      alignUp(this.quat, this.up, this.quat);
      this.pos.copy(feetOld).addScaledVector(this.up, FOOT_OFFSET);
      // Parallel-transport the heading into the new tangent plane.
      this.setHeading(this.heading);
    }
  }

  /** Ground snapping distance for the character controller (0 = off). */
  private setSnap(d: number): void {
    if (d === this.snapDist) return;
    if (d > 0) this.cc.enableSnapToGround(d);
    else this.cc.disableSnapToGround();
    this.snapDist = d;
  }

  /** Mouse look: yaw about up, pitch clamped (radians). */
  look(yaw: number, pitch: number): void {
    if (yaw !== 0) {
      _q.setFromAxisAngle(this.up, -yaw);
      this.heading.applyQuaternion(_q);
      this.setHeading(this.heading);
    }
    this.pitch = Math.max(-1.45, Math.min(1.45, this.pitch + pitch));
  }

  /**
   * Powered movement (abilities): move by velocity * dt through the character
   * controller, without gravity (the ability supplies any vertical motion)
   * and, unless `snap` (m) is given, without ground snapping; collisions
   * slide and remove the blocked part of the velocity. Updates vel
   * (horizontal), vVert and grounded like a walking step. Walking re-enables
   * its own snapping on its next step.
   */
  moveFree(dt: number, velocity: Vector3, planetCenter: Vector3, snap = 0, autostep = true): void {
    this.prevPos.copy(this.pos);
    this.realign(planetCenter);
    // Optional ground snapping (running at speed over bumps); off for flight.
    this.setSnap(snap);
    this.cc.setUp({ x: this.up.x, y: this.up.y, z: this.up.z });
    _desired.copy(velocity).multiplyScalar(dt);
    // A flier does not step: pushed against a steep face, autostep would
    // climb it 0.3 m at a time instead of letting it slide along.
    if (!autostep) this.cc.disableAutostep();
    this.cc.computeColliderMovement(this.collider, { x: _desired.x, y: _desired.y, z: _desired.z }, RAPIER.QueryFilterFlags.EXCLUDE_SENSORS, GROUPS.player);
    if (!autostep) this.cc.enableAutostep(WALK.step, 0.2, false);
    const m = this.cc.computedMovement();
    _m.set(m.x, m.y, m.z);
    this.hitWall = false;
    for (let i = 0, n = this.cc.numComputedCollisions(); i < n && !this.hitWall; i++) {
      // normal1: the obstacle's outward normal.
      const c = this.cc.computedCollision(i, this.collision);
      if (c && c.normal1.x * this.up.x + c.normal1.y * this.up.y + c.normal1.z * this.up.z < WALKABLE_COS) this.hitWall = true;
    }
    const wasGrounded = this.grounded;
    this.grounded = this.cc.computedGrounded();
    // The controller snaps only a move that goes down, so a run along the
    // ground would fly off a crest (the top of a descent, the brow of a
    // rise): snapped here instead, onto walkable ground within `snap` below.
    if (snap > 0 && wasGrounded && !this.grounded) this.snapDown(_m, snap);
    this.justLanded = this.grounded && !wasGrounded && this.airTime > 0.25;
    this.airTime = this.grounded ? 0 : this.airTime + dt;
    this.pos.add(_m);
    if (dt > 0) {
      _v.copy(_m).divideScalar(dt);
      this.vVert = _v.dot(this.up);
      this.vel.copy(_v).addScaledVector(this.up, -this.vVert);
    }
    this.body.setNextKinematicTranslation({ x: this.pos.x, y: this.pos.y, z: this.pos.z });
    this.body.setNextKinematicRotation({ x: this.quat.x, y: this.quat.y, z: this.quat.z, w: this.quat.w });
  }

  step(dt: number, input: WalkInput, planetCenter: Vector3, gravity: number): void {
    this.prevPos.copy(this.pos);
    // 1) Radial up and capsule realignment around the feet.
    this.realign(planetCenter);
    // 2) Look.
    this.look(input.yaw, input.pitch);
    // 3) Tangent-plane velocity with acceleration limits.
    _right.crossVectors(this.heading, this.up).normalize();
    const speed = input.sprint ? WALK.sprint : WALK.walk;
    _desired.copy(this.heading).multiplyScalar(input.forward).addScaledVector(_right, input.right);
    if (_desired.lengthSq() > 1) _desired.normalize();
    _desired.multiplyScalar(speed);
    // Keep the existing horizontal velocity in the (possibly rotated) tangent plane.
    this.vel.addScaledVector(this.up, -this.vel.dot(this.up));
    const accel = (this.grounded ? WALK.accel : WALK.airAccel) * dt;
    _v.copy(_desired).sub(this.vel);
    const dl = _v.length();
    if (dl > accel) _v.multiplyScalar(accel / dl);
    this.vel.add(_v);
    // 4) Vertical: jump and local gravity.
    if (this.grounded && input.jump) {
      this.vVert = WALK.jump;
      this.grounded = false;
    } else {
      this.vVert -= gravity * dt;
    }
    if (this.grounded && this.vVert < 0) this.vVert = -0.5;
    // Standing still on walkable ground: hold the position exactly. The
    // controller's skin correction pushes along the slope normal while the
    // downward probe pulls along up, which otherwise ratchets an idle
    // character slowly downhill. Support is re-verified every step.
    if (this.grounded && !input.jump && _desired.lengthSq() < 1e-8 && this.vel.lengthSq() < 1e-4 && this.supported()) {
      this.vel.set(0, 0, 0);
      this.vVert = 0;
      this.justLanded = false;
      this.airTime = 0;
      this.body.setNextKinematicTranslation({ x: this.pos.x, y: this.pos.y, z: this.pos.z });
      this.body.setNextKinematicRotation({ x: this.quat.x, y: this.quat.y, z: this.quat.z, w: this.quat.w });
      return;
    }
    // Snap to ground only when not moving upward.
    this.setSnap(this.vVert <= 0.1 ? WALK.snap : 0);
    // 5) Resolve translation with the character controller.
    this.cc.setUp({ x: this.up.x, y: this.up.y, z: this.up.z });
    _desired.copy(this.vel).addScaledVector(this.up, this.vVert).multiplyScalar(dt);
    this.cc.computeColliderMovement(this.collider, { x: _desired.x, y: _desired.y, z: _desired.z }, RAPIER.QueryFilterFlags.EXCLUDE_SENSORS, GROUPS.player);
    const m = this.cc.computedMovement();
    const wasGrounded = this.grounded;
    this.grounded = this.cc.computedGrounded();
    this.justLanded = this.grounded && !wasGrounded && this.airTime > 0.25;
    this.airTime = this.grounded ? 0 : this.airTime + dt;
    // Blocked motion removes the corresponding velocity (no sticking to walls).
    if (dt > 0) {
      const mv = _v.set(m.x, m.y, m.z);
      const along = mv.dot(this.up) / dt;
      if (this.vVert > 0 && along < this.vVert * 0.5) this.vVert = Math.max(0, along);
      if (this.grounded && this.vVert < 0) this.vVert = 0;
    }
    this.pos.x += m.x;
    this.pos.y += m.y;
    this.pos.z += m.z;
    this.stepDistance += Math.hypot(m.x, m.y, m.z) * (this.grounded ? 1 : 0);
    this.body.setNextKinematicTranslation({ x: this.pos.x, y: this.pos.y, z: this.pos.z });
    this.body.setNextKinematicRotation({ x: this.quat.x, y: this.quat.y, z: this.quat.z, w: this.quat.w });
  }

  /**
   * Walkable ground directly under the capsule within the contact gap a
   * resting capsule has on that slope (skin plus the rounded bottom's rise).
   */
  private supported(): boolean {
    const f = _v.copy(this.pos).addScaledVector(this.up, -FOOT_OFFSET + 0.25);
    const hit = this.physics.castRay(f.x, f.y, f.z, -this.up.x, -this.up.y, -this.up.z, 0.6, GROUPS.queryWalk);
    if (!hit) return false;
    const cosSlope = hit.nx * this.up.x + hit.ny * this.up.y + hit.nz * this.up.z;
    if (cosSlope < Math.cos((WALK.maxSlopeDeg * Math.PI) / 180)) return false;
    const gap = hit.toi - 0.25;
    return gap < WALK.skin + WALK.radius * (1 / cosSlope - 1) + 0.04;
  }

  /** Place the capsule (spawn/recovery); clears motion. */
  /** Re-placements so far (Recover, a reload, a blink): powers and the explorer treat them as placements, not motion. */
  placements = 0;
  /** Called after a floating-origin rebase has shifted the walker (local positions others keep move by `d`). */
  onRebaseHook: ((d: Vector3) => void) | null = null;

  place(center: Vector3, up: Vector3): void {
    this.placements++;
    this.up.copy(up).normalize();
    alignUp(this.quat, this.up, this.quat);
    this.pos.copy(center);
    this.prevPos.copy(center);
    this.vel.set(0, 0, 0);
    this.vVert = 0;
    // Placed, not dropped: no landing thump on the next step.
    this.airTime = 0;
    this.justLanded = false;
    this.body.setTranslation({ x: center.x, y: center.y, z: center.z }, true);
    this.body.setRotation({ x: this.quat.x, y: this.quat.y, z: this.quat.z, w: this.quat.w }, true);
    this.setHeading(this.heading);
  }

  onRebase(d: Vector3): void {
    this.pos.add(d);
    this.prevPos.add(d);
    this.view.onRebase(d);
    this.avatar?.onRebase(d);
    this.onRebaseHook?.(d);
  }

  /** Add the visible explorer to the scene (once). */
  attachVisual(parent: Object3D, envSource: (() => Texture | null) | null = null): void {
    if (this.avatar) return;
    this.avatar = new Avatar(parent, (o, d, max) => this.groundRay(o, d, max), this.heading, envSource);
  }

  /**
   * Per rendered frame: place the camera (third person by default) and pose
   * the explorer. dt = 0 freezes the animation (pause, loading).
   */
  renderView(dt: number, alpha: number, rig: CameraRig, reducedMotion: boolean, scripted: ScriptedPose | null = null, power: PowerMotion | null = null): void {
    // A scripted transition (ladder) moves only the visible body; the camera
    // follows it from behind its direction of travel (clear of the hull),
    // swinging there at a limited rate and back to the aim afterwards.
    const feet = scripted ? _feet.copy(scripted.feet) : _feet.lerpVectors(this.prevPos, this.pos, alpha).addScaledVector(this.up, -FOOT_OFFSET);
    this.view.update(dt, rig.camera, feet, this.up, this.heading, this.pitch, scripted ? 0 : this.speed, (f, d, m, r) => this.armCast(f, d, m, r), rig.terrainClearance, reducedMotion, power);
    if (scripted && scripted.cameraWeight > 0) {
      // Blend toward the transition's cinematic camera (the climber's head may be inside the hull).
      const cam = rig.camera;
      _camObj.position.copy(scripted.cameraEye);
      _camObj.up.copy(this.up);
      _camObj.lookAt(scripted.cameraTarget);
      cam.position.lerp(scripted.cameraEye, scripted.cameraWeight);
      cam.quaternion.slerp(_camObj.quaternion, scripted.cameraWeight);
      cam.updateMatrixWorld();
    }
    const showBody = this.view.bodyVisible || (!!scripted && scripted.cameraWeight > 0.5);
    const a = this.avatar;
    if (!a) return;
    a.setVisible(showBody);
    a.update({
      dt,
      feet,
      up: this.up,
      grounded: scripted ? true : this.grounded,
      vVert: scripted ? 0 : this.vVert,
      moveVel: scripted ? scripted.moveVel : this.vel,
      lookHeading: this.heading,
      lookPitch: this.pitch,
      faceDir: scripted ? scripted.faceDir : null,
      climb: scripted ? scripted.climb : null,
      power,
      placements: this.placements,
    });
  }

  /**
   * Aim ray matching the screen centre: the camera's view direction, starting
   * where that ray passes the eye (so ranges are measured from the body).
   */
  aim(origin: Vector3, dir: Vector3): void {
    const eye = this.eye(1, _v);
    if (this.view.mode === 'first' || this.view.position.lengthSq() === 0) {
      origin.copy(eye);
      dir.copy(this.heading).multiplyScalar(Math.cos(this.pitch)).addScaledVector(this.up, Math.sin(this.pitch)).normalize();
      return;
    }
    dir.copy(this.view.view);
    const along = Math.max(0, _n.copy(eye).sub(this.view.position).dot(dir));
    origin.copy(this.view.position).addScaledVector(dir, along);
  }

  /**
   * Free distance for the walker's capsule moved along a unit direction,
   * starting `lift` metres above its position (clears small steps the
   * controller climbs anyway); Infinity when clear for `dist`.
   */
  sweepCapsule(dir: Vector3, dist: number, lift: number, normal?: Vector3): number {
    _n.copy(this.pos).addScaledVector(this.up, lift);
    const hit = this.physics.world.castShape(
      { x: _n.x, y: _n.y, z: _n.z }, { x: this.quat.x, y: this.quat.y, z: this.quat.z, w: this.quat.w },
      { x: dir.x, y: dir.y, z: dir.z }, this.sweepShape, 0, dist, true, undefined, GROUPS.queryWalk,
    );
    // normal1: the hit surface's outward normal, facing the capsule.
    if (hit && normal) normal.set(hit.normal1.x, hit.normal1.y, hit.normal1.z);
    return hit ? hit.time_of_impact : Infinity;
  }

  /** Extend a computed move `m` down onto walkable ground within `dist` below its end (the capsule swept straight down); grounds the walker when it does. */
  private snapDown(m: Vector3, dist: number): void {
    _n.copy(this.pos).add(m);
    const hit = this.physics.world.castShape(
      { x: _n.x, y: _n.y, z: _n.z }, { x: this.quat.x, y: this.quat.y, z: this.quat.z, w: this.quat.w },
      { x: -this.up.x, y: -this.up.y, z: -this.up.z }, this.sweepShape, WALK.skin, dist, true, undefined, GROUPS.queryWalk,
    );
    if (!hit || hit.normal1.x * this.up.x + hit.normal1.y * this.up.y + hit.normal1.z * this.up.z < WALKABLE_COS) return;
    m.addScaledVector(this.up, -hit.time_of_impact);
    this.grounded = true;
  }

  /**
   * Ground under a point (searched from `rise` metres above it down to
   * `depth` below): its height above the walker's feet along up, and its
   * normal; null when there is none in that span. By default anything the
   * walker stands on counts; `terrainOnly` reads the shape of the land alone.
   */
  groundAt(point: Vector3, rise: number, depth: number, terrainOnly = false): { h: number; normal: Vector3 } | null {
    _n.copy(point).addScaledVector(this.up, rise);
    const hit = this.physics.castRay(_n.x, _n.y, _n.z, -this.up.x, -this.up.y, -this.up.z, rise + depth, terrainOnly ? GROUPS.queryTerrain : GROUPS.queryWalk);
    if (!hit) return null;
    const feet = this.feet(_v);
    _n.addScaledVector(this.up, -hit.toi).sub(feet);
    return { h: _n.dot(this.up), normal: _g.set(hit.nx, hit.ny, hit.nz) };
  }

  /** The walker's capsule fits with its feet at this point (nothing it collides with intersects it). */
  fitsAt(feet: Vector3): boolean {
    _n.copy(feet).addScaledVector(this.up, FOOT_OFFSET + WALK.skin);
    const blocked = this.physics.world.intersectionWithShape(
      { x: _n.x, y: _n.y, z: _n.z }, { x: this.quat.x, y: this.quat.y, z: this.quat.z, w: this.quat.w }, this.sweepShape, undefined, GROUPS.queryWalk,
    );
    return !blocked;
  }

  /** First hit along a ray against what the walker collides with (terrain, props, ship; never itself). */
  rayHit(o: Vector3, d: Vector3, max: number): { dist: number; normal: Vector3 } | null {
    const hit = this.physics.castRay(o.x, o.y, o.z, d.x, d.y, d.z, max, GROUPS.queryWalk);
    return hit ? { dist: hit.toi, normal: _n.set(hit.nx, hit.ny, hit.nz) } : null;
  }

  /** Walkable ground below a point (the avatar's foot placement). */
  private groundRay(o: Vector3, d: Vector3, max: number): { dist: number; normal: Vector3 } | null {
    return this.rayHit(o, d, max);
  }

  /** Sphere cast for the camera arm against terrain, props and the ship. */
  private armCast(from: Vector3, dir: Vector3, max: number, radius: number): number | null {
    let ball = this.balls.get(radius);
    if (!ball) {
      ball = new RAPIER.Ball(radius);
      this.balls.set(radius, ball);
    }
    const hit = this.physics.world.castShape(
      { x: from.x, y: from.y, z: from.z }, _rot, { x: dir.x, y: dir.y, z: dir.z }, ball, 0, max, true, undefined, GROUPS.queryWalk,
    );
    return hit ? hit.time_of_impact : null;
  }

  /** Re-read the capsule position after an external shift (physics.shiftAll moved the body). */
  get speed(): number {
    return this.vel.length();
  }

  dispose(): void {
    this.avatar?.dispose();
    this.avatar = null;
    this.physics.world.removeCharacterController(this.cc);
    this.physics.world.removeRigidBody(this.body);
  }
}

/** Capsule shape matching the player (for clearance checks). */
export function playerShape(): RAPIER.Capsule {
  return new RAPIER.Capsule(HALF, WALK.radius);
}
