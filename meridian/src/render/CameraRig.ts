import { PerspectiveCamera, Quaternion, Vector3 } from 'three';
import { CAMERA } from '../game/config';
import { tangentFrame } from '../core/mathx';

const _desired = new Vector3();
const _target = new Vector3();
const _fwd = new Vector3();
const _up = new Vector3();
const _right = new Vector3();
const _tf = new Vector3();

export type CameraMode = 'chase' | 'orbit' | 'firstPerson';

/**
 * Ship chase camera (exponential smoothing, look-ahead, terrain avoidance),
 * a landed/title orbit camera, and the first-person camera.
 */
export class CameraRig {
  mode: CameraMode = 'orbit';
  readonly offset = new Vector3(0, CAMERA.chaseUp, CAMERA.chaseBack);
  readonly smoothUp = new Vector3(0, 1, 0);
  private initialized = false;
  fov: number = CAMERA.fov;
  // Orbit parameters.
  orbitYaw = 2.35;
  orbitPitch = 0.16;
  orbitDist = 24;
  /** Optional terrain clearance probe: returns height of the terrain surface above which the camera must stay (m along up), or null. */
  terrainClearance: ((p: Vector3, up: Vector3) => number | null) | null = null;

  constructor(readonly camera: PerspectiveCamera) {}

  reset(): void {
    this.initialized = false;
  }

  onRebase(d: Vector3): void {
    this.camera.position.add(d);
  }

  /** Smoothly approach the FOV target (disabled with reduced motion). */
  updateFov(dt: number, boost: boolean, reducedMotion: boolean): void {
    const target = reducedMotion ? CAMERA.fov : boost ? CAMERA.boostFov : CAMERA.fov;
    this.fov += (target - this.fov) * (1 - Math.exp(-dt * 3));
    if (Math.abs(this.camera.fov - this.fov) > 0.01) {
      this.camera.fov = this.fov;
      this.camera.updateProjectionMatrix();
    }
  }

  chase(dt: number, shipPos: Vector3, shipQuat: Quaternion, speed: number, radialUp: Vector3, cruise: boolean): void {
    const back = CAMERA.chaseBack * (cruise ? 1.6 : 1 + Math.min(speed / 1500, 0.5));
    const upOff = CAMERA.chaseUp * (cruise ? 1.3 : 1);
    _desired.set(0, upOff, back).applyQuaternion(shipQuat);
    _up.set(0, 1, 0).applyQuaternion(shipQuat);
    if (!this.initialized || this.mode !== 'chase') {
      this.offset.copy(_desired);
      this.smoothUp.copy(_up);
      this.initialized = true;
      this.mode = 'chase';
    }
    const kp = 1 - Math.exp(-CAMERA.posK * dt);
    const kr = 1 - Math.exp(-CAMERA.rotK * dt);
    this.offset.lerp(_desired, kp);
    this.offset.setLength(_desired.length());
    // Blend the camera up between ship up and radial up for a calmer horizon.
    _tf.copy(_up).lerp(radialUp, 0.35).normalize();
    this.smoothUp.lerp(_tf, kr).normalize();
    const cam = this.camera;
    cam.position.copy(shipPos).add(this.offset);
    this.avoidTerrain(cam.position, radialUp);
    _fwd.set(0, 0, -1).applyQuaternion(shipQuat);
    _target.copy(shipPos).addScaledVector(_fwd, CAMERA.lookAhead).addScaledVector(_up, 1.5);
    cam.up.copy(this.smoothUp);
    cam.lookAt(_target);
  }

  /** Orbit around a point using the local radial up (landed showcase / title). */
  orbit(dt: number, center: Vector3, radialUp: Vector3, headingHint: Vector3, mouseDX: number, mouseDY: number, auto: boolean): void {
    this.mode = 'orbit';
    this.initialized = false;
    this.orbitYaw -= mouseDX * 0.004;
    this.orbitPitch = Math.min(1.2, Math.max(-0.05, this.orbitPitch + mouseDY * 0.003));
    if (auto) this.orbitYaw += dt * 0.035;
    tangentFrame(radialUp, headingHint, _fwd, _right);
    const cy = Math.cos(this.orbitYaw);
    const sy = Math.sin(this.orbitYaw);
    const cp = Math.cos(this.orbitPitch);
    const sp = Math.sin(this.orbitPitch);
    _desired
      .copy(_fwd)
      .multiplyScalar(cy * cp)
      .addScaledVector(_right, sy * cp)
      .addScaledVector(radialUp, sp)
      .multiplyScalar(this.orbitDist);
    const cam = this.camera;
    cam.position.copy(center).add(_desired);
    this.avoidTerrain(cam.position, radialUp);
    _target.copy(center).addScaledVector(radialUp, 1.0);
    cam.up.copy(radialUp);
    cam.lookAt(_target);
  }

  /** First-person: eye position plus heading/pitch in the local tangent frame. */
  firstPerson(eye: Vector3, up: Vector3, heading: Vector3, pitch: number): void {
    this.mode = 'firstPerson';
    this.initialized = false;
    const cam = this.camera;
    cam.position.copy(eye);
    _right.crossVectors(heading, up).normalize();
    _fwd.copy(heading).multiplyScalar(Math.cos(pitch)).addScaledVector(up, Math.sin(pitch));
    _target.copy(eye).add(_fwd);
    cam.up.copy(up);
    cam.lookAt(_target);
  }

  private avoidTerrain(p: Vector3, up: Vector3): void {
    if (!this.terrainClearance) return;
    const deficit = this.terrainClearance(p, up);
    if (deficit !== null && deficit > 0) p.addScaledVector(up, deficit);
  }
}
