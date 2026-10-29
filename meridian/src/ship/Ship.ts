import { Quaternion, Vector3, type Group } from 'three';
import { RAPIER, GROUPS, type Physics } from '../physics/Physics';
import { FLIGHT } from '../game/config';
import { buildShipModel, GEAR_FEET, GEAR_PAD_RADIUS, hullColliderPoints, setGearDeploy, setPlumes, type ShipVisual } from './ShipModel';
import { FlightModel } from './FlightModel';


/** Ship simulation: one dynamic Rapier body with the assisted flight model (no rendering). */
export class ShipSim {
  readonly body: RAPIER.RigidBody;
  readonly hull: RAPIER.Collider;
  readonly feet: RAPIER.Collider[] = [];
  readonly flight = new FlightModel();
  // Interpolation state (local coordinates).
  readonly prevPos = new Vector3();
  readonly currPos = new Vector3();
  readonly prevQuat = new Quaternion();
  readonly currQuat = new Quaternion();
  readonly vel = new Vector3();
  readonly angvel = new Vector3();
  /** Gear deploy fraction (visual), 0..1. */
  gear = 1;
  gearTarget = 1;
  private feetEnabled = true;

  constructor(protected readonly physics: Physics, pos: Vector3, quat: Quaternion) {
    const world = physics.world;
    const desc = RAPIER.RigidBodyDesc.dynamic()
      .setTranslation(pos.x, pos.y, pos.z)
      .setRotation({ x: quat.x, y: quat.y, z: quat.z, w: quat.w })
      .setCcdEnabled(true)
      .setCanSleep(false)
      .setLinearDamping(0)
      .setAngularDamping(0);
    this.body = world.createRigidBody(desc);
    const hullDesc = RAPIER.ColliderDesc.convexHull(hullColliderPoints());
    if (!hullDesc) throw new Error('Ship hull collider construction failed');
    hullDesc
      .setMass(FLIGHT.mass)
      .setFriction(0.6)
      .setRestitution(0.04)
      .setCollisionGroups(GROUPS.ship)
      .setSolverGroups(GROUPS.ship);
    this.hull = world.createCollider(hullDesc, this.body);
    for (const f of GEAR_FEET) {
      const d = RAPIER.ColliderDesc.ball(GEAR_PAD_RADIUS)
        .setTranslation(f.x, f.y + GEAR_PAD_RADIUS, f.z)
        .setDensity(0)
        .setFriction(1.2)
        .setRestitution(0)
        .setCollisionGroups(GROUPS.ship)
        .setSolverGroups(GROUPS.ship);
      this.feet.push(world.createCollider(d, this.body));
    }
    this.syncFromBody(true);
  }

  /** Read the body state into the current interpolation buffer (prev is set by beginStep). */
  syncFromBody(resetPrev = false): void {
    const t = this.body.translation();
    const r = this.body.rotation();
    const lv = this.body.linvel();
    const av = this.body.angvel();
    this.currPos.set(t.x, t.y, t.z);
    this.currQuat.set(r.x, r.y, r.z, r.w).normalize();
    this.vel.set(lv.x, lv.y, lv.z);
    this.angvel.set(av.x, av.y, av.z);
    if (resetPrev) {
      this.prevPos.copy(this.currPos);
      this.prevQuat.copy(this.currQuat);
    }
  }

  /** Save the current state as previous before a simulation step. */
  beginStep(): void {
    this.prevPos.copy(this.currPos);
    this.prevQuat.copy(this.currQuat);
  }

  /** Apply the controller outputs for this step (forces are replaced, not accumulated). */
  applyControl(force: Vector3, angvel: Vector3): void {
    this.body.resetForces(true);
    this.body.resetTorques(true);
    this.body.addForce({ x: force.x, y: force.y, z: force.z }, true);
    this.body.setAngvel({ x: angvel.x, y: angvel.y, z: angvel.z }, true);
  }

  /** Teleport-free pose set (used for spawn/restore only). */
  setPose(pos: Vector3, quat: Quaternion, vel?: Vector3): void {
    this.body.setTranslation({ x: pos.x, y: pos.y, z: pos.z }, true);
    this.body.setRotation({ x: quat.x, y: quat.y, z: quat.z, w: quat.w }, true);
    this.body.setLinvel(vel ? { x: vel.x, y: vel.y, z: vel.z } : { x: 0, y: 0, z: 0 }, true);
    this.body.setAngvel({ x: 0, y: 0, z: 0 }, true);
    this.syncFromBody(true);
  }

  onRebase(d: Vector3): void {
    this.prevPos.add(d);
    this.currPos.add(d);
  }

  /** Enable/disable gear-foot colliders to match the visible gear. */
  updateGearColliders(): void {
    const want = this.gear > 0.9;
    if (want !== this.feetEnabled) {
      for (const f of this.feet) f.setEnabled(want);
      this.feetEnabled = want;
    }
  }

  /** World-space (local coords) position of a ship-local point using the current physics pose. */
  localToWorld(p: Vector3, out: Vector3): Vector3 {
    return out.copy(p).applyQuaternion(this.currQuat).add(this.currPos);
  }

  get speed(): number {
    return this.vel.length();
  }

  forward(out: Vector3): Vector3 {
    return out.set(0, 0, -1).applyQuaternion(this.currQuat);
  }

  up(out: Vector3): Vector3 {
    return out.set(0, 1, 0).applyQuaternion(this.currQuat);
  }

  dispose(): void {
    this.physics.world.removeRigidBody(this.body);
  }
}

/** The player's ship: simulation plus its visual model. */
export class Ship extends ShipSim {
  readonly visual: ShipVisual;
  /** Engine glow smoothing. */
  private glow = 0;

  constructor(physics: Physics, pos: Vector3, quat: Quaternion) {
    super(physics, pos, quat);
    this.visual = buildShipModel();
  }

  get root(): Group {
    return this.visual.root;
  }

  /** Visual update: interpolated transform, gear animation, engine glow. */
  updateVisual(alpha: number, dt: number, landed: boolean): void {
    const root = this.visual.root;
    root.position.lerpVectors(this.prevPos, this.currPos, alpha);
    root.quaternion.slerpQuaternions(this.prevQuat, this.currQuat, alpha);
    // Gear animation (about 1.4 s full travel).
    const step = dt / 1.4;
    if (this.gear < this.gearTarget) this.gear = Math.min(this.gearTarget, this.gear + step);
    else if (this.gear > this.gearTarget) this.gear = Math.max(this.gearTarget, this.gear - step);
    setGearDeploy(this.visual.gearLegs, this.gear);
    this.visual.ladder.visible = landed;
    // Engine glow and plumes follow the actual forward thrust.
    const thrust = landed ? 0 : Math.min(1, this.flight.forwardThrust / 35);
    const boost = !landed && this.flight.boostActive;
    const target = landed ? 0.04 : 0.35 + thrust * 3.2 + (boost ? 1.6 : 0);
    this.glow += (target - this.glow) * (1 - Math.exp(-dt / 0.15));
    this.visual.engineMaterial.emissiveIntensity = this.glow;
    setPlumes(this.visual, thrust, boost, dt);
  }
}
