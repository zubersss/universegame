import {
  AdditiveBlending,
  BufferGeometry,
  Color,
  CylinderGeometry,
  DoubleSide,
  Float32BufferAttribute,
  Group,
  Matrix4,
  Mesh,
  MeshBasicMaterial,
  PlaneGeometry,
  RingGeometry,
  SphereGeometry,
  Vector3,
  type Object3D,
} from 'three';

// Restrained power feedback (charter K/L: visual feedback with a readable
// camera; spectacle never obscures aiming, terrain or landings): the blink
// target marker (the power colour when the step is allowed, red when
// refused; readable at any range), a short flash where a blink leaves and
// arrives, faint speed lines around the body at superspeed and in fast
// flight, and two thin trails from the boots at flight boost. Neither of
// the last two comes near the camera. Unlit, no depth writes, additive
// except the marker; with reduced motion the speed lines are off and the
// flashes do not grow (the marker and the trails do not move with the scene).

export interface VfxFrame {
  up: Vector3;
  camera: Vector3;
  /** Blink aim marker: feet point, allowed or refused (null hides it). */
  aim: { feet: Vector3; ok: boolean } | null;
  /** Speed lines: body centre, direction of travel, speed and strength 0..1 (null hides them). */
  rush: { center: Vector3; dir: Vector3; speed: number; strength: number } | null;
  /** Flight trails: the boot tips, direction of travel and strength 0..1 (null hides them). */
  trails: { from: readonly [Vector3, Vector3]; dir: Vector3; strength: number } | null;
}

const STREAKS = 10;
const FLASH_TIME = 0.35;
/** Largest flash radius (m), and how far the camera must be beyond it to show the flash: never drawn around the eye (first person). */
const FLASH_MAX = 1.65;
const FLASH_CLEAR = 0.3;
const REFUSED = new Color(0xff4a4a);
/** Beyond this distance from the camera (m) the blink marker widens to keep its apparent size. */
const MARKER_FULL = 15;
/** Longest flight trail (m). */
const TRAIL_MAX = 14;
/** No trail comes closer to the camera than this (m): seen from the chase camera they stay short. */
const TRAIL_CLEAR = 4;
/** Speed lines thin out between these distances of their centre from the camera (m). */
const STREAK_NEAR = 3;
const STREAK_FULL = 6;

const clamp01 = (x: number) => Math.min(1, Math.max(0, x));

/** Speed-line strength: superspeed from 20 m/s (full at 100), flight from 60 m/s (faint at the 90 m/s cruise, full at 200 with boost). */
export function rushStrength(mode: 'flight' | 'dash', speed: number): number {
  return mode === 'dash' ? clamp01((speed - 20) / 80) : clamp01((speed - 60) / 140);
}

/** Flight trail strength: only above cruise (boost), full at 200 m/s. */
export function trailStrength(speed: number): number {
  return clamp01((speed - 100) / 100);
}

/** A tapered quad from y = 0 (head, bright) to y = -1 (tail, dark: additive, so it fades out). */
function trailGeometry(head: number, tail: number): BufferGeometry {
  const g = new BufferGeometry();
  g.setAttribute('position', new Float32BufferAttribute([-head / 2, 0, 0, head / 2, 0, 0, -tail / 2, -1, 0, tail / 2, -1, 0], 3));
  g.setAttribute('color', new Float32BufferAttribute([1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0], 3));
  g.setIndex([0, 2, 1, 1, 2, 3]);
  return g;
}

const _m = new Matrix4();
const _side = new Vector3();
const _normal = new Vector3();
const _toCam = new Vector3();
const _x = new Vector3();
const _y = new Vector3();
const _z = new Vector3();
const _p = new Vector3();
const Y = new Vector3(0, 1, 0);

function additive(color: Color, opacity: number): MeshBasicMaterial {
  return new MeshBasicMaterial({ color, transparent: true, opacity, blending: AdditiveBlending, depthWrite: false, toneMapped: false });
}

/**
 * Turn a quad at `at` so its y axis lies along `axis` and its front face
 * (+z, the side materials draw) turns toward the camera; false when seen
 * exactly end-on (nothing to draw).
 */
function faceCamera(mesh: Mesh, at: Vector3, axis: Vector3, camera: Vector3): boolean {
  _toCam.copy(camera).sub(at);
  _side.crossVectors(axis, _toCam);
  if (_side.lengthSq() < 1e-10) return false;
  _side.normalize();
  _normal.crossVectors(_side, axis).normalize();
  _m.makeBasis(_side, axis, _normal);
  mesh.quaternion.setFromRotationMatrix(_m);
  return true;
}

export class PowerVfx {
  readonly root = new Group();
  private readonly marker = new Group();
  private readonly ringMat: MeshBasicMaterial;
  private readonly beamMat: MeshBasicMaterial;
  private readonly flashMat: MeshBasicMaterial[] = [];
  private readonly flashes: { mesh: Mesh; t: number }[] = [];
  private readonly streakMat: MeshBasicMaterial;
  private readonly streaks: { mesh: Mesh; offset: Vector3; phase: number }[] = [];
  private readonly trailMat: MeshBasicMaterial;
  private readonly trails: Mesh[] = [];
  private readonly color: Color;
  private time = 0;

  constructor(parent: Object3D, color: string) {
    this.color = new Color(color);
    this.root.name = 'power-vfx';
    // Marker: a ring on the ground and a short beam.
    // Normal blending, not additive, so the refused red reads as red on bright
    // ground; the ring draws over terrain bumps so the target point always
    // shows, and from both sides (a target above the camera is seen from below).
    this.ringMat = new MeshBasicMaterial({ color: this.color.clone(), side: DoubleSide, transparent: true, opacity: 0.85, depthWrite: false, depthTest: false, toneMapped: false });
    this.beamMat = new MeshBasicMaterial({ color: this.color.clone(), transparent: true, opacity: 0.45, depthWrite: false, toneMapped: false });
    const ring = new Mesh(new RingGeometry(0.42, 0.56, 40).rotateX(-Math.PI / 2), this.ringMat);
    const inner = new Mesh(new RingGeometry(0.0, 0.18, 24).rotateX(-Math.PI / 2), this.ringMat);
    const beam = new Mesh(new CylinderGeometry(0.025, 0.025, 1.8, 8).translate(0, 0.9, 0), this.beamMat);
    ring.renderOrder = inner.renderOrder = 10;
    ring.position.y = inner.position.y = 0.03;
    this.marker.add(ring, inner, beam);
    this.marker.visible = false;
    // Flashes: two reusable spheres (departure and arrival).
    for (let i = 0; i < 2; i++) {
      const mat = additive(this.color.clone(), 0);
      const mesh = new Mesh(new SphereGeometry(1, 16, 10), mat);
      mesh.visible = false;
      this.flashMat.push(mat);
      this.flashes.push({ mesh, t: FLASH_TIME });
      this.root.add(mesh);
    }
    // Streaks: thin quads along the direction of travel.
    this.streakMat = additive(new Color(0xffd2b0), 0);
    const geo = new PlaneGeometry(0.035, 3.2);
    for (let i = 0; i < STREAKS; i++) {
      const a = (i / STREAKS) * Math.PI * 2 + 0.37 * i;
      const r = 0.9 + ((i * 0.618) % 1) * 1.4;
      const mesh = new Mesh(geo, this.streakMat);
      mesh.visible = false;
      this.streaks.push({ mesh, offset: new Vector3(Math.cos(a) * r, 0.4 + ((i * 0.382) % 1) * 1.4, Math.sin(a) * r), phase: (i * 0.29) % 1 });
      this.root.add(mesh);
    }
    // Trails: a pale vapour line behind each boot.
    this.trailMat = new MeshBasicMaterial({ color: new Color(0xdde8ff), vertexColors: true, transparent: true, opacity: 0, blending: AdditiveBlending, depthWrite: false, toneMapped: false });
    const trailGeo = trailGeometry(0.045, 0.03);
    for (let i = 0; i < 2; i++) {
      const mesh = new Mesh(trailGeo, this.trailMat);
      mesh.visible = false;
      this.trails.push(mesh);
      this.root.add(mesh);
    }
    this.root.add(this.marker);
    parent.add(this.root);
  }

  /** A floating-origin rebase moved everything by `d`: the flashes and marker placed earlier move too. */
  shift(d: Vector3): void {
    for (const f of this.flashes) f.mesh.position.add(d);
    this.marker.position.add(d);
  }

  /** A short flash (blink departure or arrival) at a point; drawn from the next update. */
  flash(at: Vector3): void {
    const f = this.flashes[0].t >= this.flashes[1].t ? this.flashes[0] : this.flashes[1];
    f.t = 0;
    f.mesh.position.copy(at);
  }

  update(dt: number, f: VfxFrame, reducedMotion: boolean): void {
    this.time += dt;
    const up = f.up;
    // Marker.
    if (f.aim) {
      this.marker.visible = true;
      this.marker.position.copy(f.aim.feet);
      this.marker.quaternion.setFromUnitVectors(Y, up);
      const c = f.aim.ok ? this.color : REFUSED;
      this.ringMat.color.copy(c);
      this.beamMat.color.copy(c);
      // Wider with distance so it keeps a readable size out to the range; its
      // height stays the explorer's 1.8 m as a size cue.
      const wide = Math.max(1, f.aim.feet.distanceTo(f.camera) / MARKER_FULL);
      const pulse = reducedMotion ? 1 : 1 + 0.08 * Math.sin(this.time * 6);
      this.marker.scale.set(pulse * wide, 1, pulse * wide);
    } else this.marker.visible = false;
    // Flashes, except where the camera is in or near one (in first person the
    // arrival flash would grow around the eye and fill the view).
    for (let i = 0; i < this.flashes.length; i++) {
      const fl = this.flashes[i];
      fl.mesh.visible = false;
      if (fl.t >= FLASH_TIME) continue;
      fl.t += dt;
      const u = Math.min(1, fl.t / FLASH_TIME);
      fl.mesh.scale.setScalar(reducedMotion ? 0.9 : 0.25 + (FLASH_MAX - 0.25) * u);
      this.flashMat[i].opacity = 0.7 * (1 - u) * (1 - u);
      fl.mesh.visible = u < 1 && fl.mesh.position.distanceTo(f.camera) > FLASH_MAX + FLASH_CLEAR;
    }
    // Speed lines (none with reduced motion).
    const d = f.rush;
    const strength = d && !reducedMotion ? clamp01(d.strength) : 0;
    this.streakMat.opacity = 0.32 * strength;
    for (const s of this.streaks) {
      s.mesh.visible = false;
      if (strength <= 0.01 || !d) continue;
      // Frame: z along the travel direction, y up (any perpendicular when travelling straight up or down).
      _z.copy(d.dir).normalize();
      _y.copy(up).addScaledVector(_z, -up.dot(_z));
      if (_y.lengthSq() < 1e-6) _y.set(Math.abs(_z.x) < 0.9 ? 1 : 0, Math.abs(_z.x) < 0.9 ? 0 : 1, 0).addScaledVector(_z, -(Math.abs(_z.x) < 0.9 ? _z.x : _z.y));
      _y.normalize();
      _x.crossVectors(_y, _z).normalize();
      s.phase = (s.phase + dt * (0.8 + d.speed / 60)) % 1;
      _p.copy(d.center).addScaledVector(_x, s.offset.x).addScaledVector(_y, s.offset.y - 0.9).addScaledVector(_z, s.offset.z - 6 * s.phase);
      s.mesh.position.copy(_p);
      // Thinner, then gone, close to the camera (never a smear across the view).
      const fade = clamp01((_p.distanceTo(f.camera) - STREAK_NEAR) / (STREAK_FULL - STREAK_NEAR));
      s.mesh.scale.set(fade, 1, 1);
      s.mesh.visible = fade > 0.05 && faceCamera(s.mesh, _p, _z, f.camera);
    }
    // Trails: from each boot back along the travel direction, cut where they would come near the camera.
    const tr = f.trails;
    const ts = tr ? clamp01(tr.strength) : 0;
    this.trailMat.opacity = 0.24 * ts;
    for (let i = 0; i < this.trails.length; i++) {
      const m = this.trails[i];
      m.visible = false;
      if (ts <= 0.01 || !tr) continue;
      _z.copy(tr.dir).normalize();
      const from = tr.from[i];
      let len = TRAIL_MAX * (0.4 + 0.6 * ts);
      // The trail runs toward the camera when the boots are ahead of it: it
      // passes `perp` from it at `ahead` metres back; stop TRAIL_CLEAR short.
      _p.copy(from).sub(f.camera);
      const ahead = _p.dot(_z);
      const perp2 = _p.lengthSq() - ahead * ahead;
      if (ahead > 0 && perp2 < TRAIL_CLEAR * TRAIL_CLEAR) len = Math.min(len, ahead - Math.sqrt(TRAIL_CLEAR * TRAIL_CLEAR - perp2));
      if (!(len > 0.5)) continue;
      m.position.copy(from);
      m.scale.set(1, len, 1);
      m.visible = faceCamera(m, from, _z, f.camera);
    }
  }

  dispose(): void {
    this.root.removeFromParent();
    this.root.traverse((o) => {
      const m = o as Mesh;
      if (m.isMesh) m.geometry.dispose();
    });
    this.ringMat.dispose();
    this.beamMat.dispose();
    this.streakMat.dispose();
    this.trailMat.dispose();
    for (const m of this.flashMat) m.dispose();
  }
}
