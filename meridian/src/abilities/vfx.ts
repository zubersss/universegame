import {
  AdditiveBlending,
  Color,
  CylinderGeometry,
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
// target marker (green-ish when the step is allowed, red when refused), a
// short flash where a blink leaves and arrives, and faint speed streaks
// around the body at superspeed. Additive, unlit, no depth writes; nothing
// moves with reduced motion except the marker.

export interface VfxFrame {
  up: Vector3;
  camera: Vector3;
  /** Blink aim marker: feet point, allowed or refused (null hides it). */
  aim: { feet: Vector3; ok: boolean } | null;
  /** Superspeed: body centre, direction and speed (null hides the streaks). */
  dash: { center: Vector3; dir: Vector3; speed: number } | null;
}

const STREAKS = 10;
const FLASH_TIME = 0.35;
const REFUSED = new Color(0xff4a4a);

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

export class PowerVfx {
  readonly root = new Group();
  private readonly marker = new Group();
  private readonly ringMat: MeshBasicMaterial;
  private readonly beamMat: MeshBasicMaterial;
  private readonly flashMat: MeshBasicMaterial[] = [];
  private readonly flashes: { mesh: Mesh; t: number }[] = [];
  private readonly streakMat: MeshBasicMaterial;
  private readonly streaks: { mesh: Mesh; offset: Vector3; phase: number }[] = [];
  private readonly color: Color;
  private time = 0;

  constructor(parent: Object3D, color: string) {
    this.color = new Color(color);
    this.root.name = 'power-vfx';
    // Marker: a ring on the ground and a short beam.
    this.ringMat = additive(this.color.clone(), 0.85);
    this.beamMat = additive(this.color.clone(), 0.35);
    const ring = new Mesh(new RingGeometry(0.42, 0.56, 40).rotateX(-Math.PI / 2), this.ringMat);
    const inner = new Mesh(new RingGeometry(0.0, 0.18, 24).rotateX(-Math.PI / 2), this.ringMat);
    const beam = new Mesh(new CylinderGeometry(0.025, 0.025, 1.8, 8).translate(0, 0.9, 0), this.beamMat);
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
    this.root.add(this.marker);
    parent.add(this.root);
  }

  /** A short flash (blink departure or arrival) at a point. */
  flash(at: Vector3): void {
    const f = this.flashes[0].t >= this.flashes[1].t ? this.flashes[0] : this.flashes[1];
    f.t = 0;
    f.mesh.position.copy(at);
    f.mesh.visible = true;
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
      const pulse = reducedMotion ? 1 : 1 + 0.08 * Math.sin(this.time * 6);
      this.marker.scale.set(pulse, 1, pulse);
    } else this.marker.visible = false;
    // Flashes.
    for (let i = 0; i < this.flashes.length; i++) {
      const fl = this.flashes[i];
      if (!fl.mesh.visible) continue;
      fl.t += dt;
      const u = Math.min(1, fl.t / FLASH_TIME);
      fl.mesh.scale.setScalar(reducedMotion ? 0.9 : 0.25 + 1.4 * u);
      this.flashMat[i].opacity = 0.7 * (1 - u) * (1 - u);
      if (u >= 1) fl.mesh.visible = false;
    }
    // Streaks (none with reduced motion).
    const d = f.dash;
    const strength = d && !reducedMotion ? Math.min(1, Math.max(0, (d.speed - 20) / 80)) : 0;
    this.streakMat.opacity = 0.32 * strength;
    for (const s of this.streaks) {
      s.mesh.visible = strength > 0.01;
      if (!s.mesh.visible || !d) continue;
      // Frame: z along the travel direction, y up.
      _z.copy(d.dir).normalize();
      _y.copy(up).addScaledVector(_z, -up.dot(_z)).normalize();
      _x.crossVectors(_y, _z).normalize();
      s.phase = (s.phase + dt * (0.8 + d.speed / 60)) % 1;
      _p.copy(d.center).addScaledVector(_x, s.offset.x).addScaledVector(_y, s.offset.y - 0.9).addScaledVector(_z, s.offset.z - 6 * s.phase);
      s.mesh.position.copy(_p);
      // The quad lies along the travel direction, facing the camera.
      _toCam.copy(_p).sub(f.camera);
      _side.crossVectors(_z, _toCam).normalize();
      _normal.crossVectors(_side, _z).normalize();
      _m.makeBasis(_side, _z, _normal);
      s.mesh.quaternion.setFromRotationMatrix(_m);
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
    for (const m of this.flashMat) m.dispose();
  }
}
