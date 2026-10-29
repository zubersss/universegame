import {
  AdditiveBlending,
  BufferAttribute,
  BufferGeometry,
  DynamicDrawUsage,
  Points,
  ShaderMaterial,
  Vector3,
  type Quaternion,
} from 'three';
import { NOZZLES } from './ShipModel';

const MAX = 240;
const _n = new Vector3();
const _back = new Vector3();

/** Small pooled exhaust effect driven by the ship's actual forward thrust. */
export class Exhaust {
  readonly points: Points;
  private readonly pos = new Float32Array(MAX * 3);
  private readonly life = new Float32Array(MAX * 2); // x = age/lifetime (0..1), y = size scale
  private readonly vel = new Float32Array(MAX * 3);
  private readonly age = new Float32Array(MAX);
  private readonly lifetime = new Float32Array(MAX);
  private alive = 0;
  private spawnAcc = 0;
  private seed = 12345;
  private readonly geo: BufferGeometry;

  constructor() {
    this.geo = new BufferGeometry();
    const pa = new BufferAttribute(this.pos, 3);
    pa.setUsage(DynamicDrawUsage);
    const la = new BufferAttribute(this.life, 2);
    la.setUsage(DynamicDrawUsage);
    this.geo.setAttribute('position', pa);
    this.geo.setAttribute('life', la);
    this.geo.setDrawRange(0, 0);
    const mat = new ShaderMaterial({
      uniforms: { uScale: { value: 400 } },
      vertexShader: /* glsl */ `
        attribute vec2 life;
        uniform float uScale;
        varying float vT;
        #include <common>
        #include <logdepthbuf_pars_vertex>
        void main() {
          vT = life.x;
          vec4 mv = modelViewMatrix * vec4(position, 1.0);
          gl_Position = projectionMatrix * mv;
          float s = mix(0.25, 0.9, life.x) * life.y;
          gl_PointSize = clamp(s * uScale / max(-mv.z, 0.5), 1.0, 28.0);
          #include <logdepthbuf_vertex>
        }`,
      fragmentShader: /* glsl */ `
        varying float vT;
        #include <common>
        #include <logdepthbuf_pars_fragment>
        void main() {
          #include <logdepthbuf_fragment>
          vec2 d = gl_PointCoord - 0.5;
          float a = smoothstep(0.5, 0.0, length(d));
          vec3 hot = vec3(1.0, 0.62, 0.32) * 1.6;
          vec3 cool = vec3(0.5, 0.36, 0.3) * 0.2;
          vec3 c = mix(hot, cool, smoothstep(0.0, 0.6, vT));
          float fade = (1.0 - vT) * (1.0 - vT);
          gl_FragColor = vec4(c * a * fade, 1.0);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,
      transparent: true,
      depthWrite: false,
      blending: AdditiveBlending,
    });
    this.points = new Points(this.geo, mat);
    this.points.frustumCulled = false;
    this.points.renderOrder = 5;
  }

  private rnd(): number {
    this.seed = (this.seed * 1664525 + 1013904223) >>> 0;
    return this.seed / 4294967296;
  }

  setPixelScale(viewportHeight: number, fovDeg: number): void {
    (this.points.material as ShaderMaterial).uniforms.uScale.value = viewportHeight / (2 * Math.tan((fovDeg * Math.PI) / 360));
  }

  /** Advance particles; emit from the nozzles at a rate set by thrust (0..1). */
  update(dt: number, shipPos: Vector3, shipQuat: Quaternion, shipVel: Vector3, thrust: number, boost: boolean): void {
    // Age and integrate existing particles; compact dead ones.
    let w = 0;
    for (let i = 0; i < this.alive; i++) {
      const a = this.age[i] + dt;
      if (a >= this.lifetime[i]) continue;
      this.age[w] = a;
      this.lifetime[w] = this.lifetime[i];
      for (let k = 0; k < 3; k++) {
        this.vel[w * 3 + k] = this.vel[i * 3 + k] * (1 - 2.2 * dt);
        this.pos[w * 3 + k] = this.pos[i * 3 + k] + this.vel[i * 3 + k] * dt;
      }
      this.life[w * 2] = a / this.lifetime[w];
      this.life[w * 2 + 1] = this.life[i * 2 + 1];
      w++;
    }
    this.alive = w;
    // Emit.
    const rate = thrust > 0.05 ? 30 + thrust * 120 + (boost ? 80 : 0) : 0;
    this.spawnAcc += rate * dt;
    _back.set(0, 0, 1).applyQuaternion(shipQuat);
    while (this.spawnAcc >= 1 && this.alive < MAX) {
      this.spawnAcc -= 1;
      const nz = NOZZLES[this.alive & 1];
      _n.copy(nz).applyQuaternion(shipQuat).add(shipPos);
      const i = this.alive++;
      const ej = 18 + thrust * 30 + (boost ? 20 : 0);
      const jx = (this.rnd() - 0.5) * 3;
      const jy = (this.rnd() - 0.5) * 3;
      const jz = (this.rnd() - 0.5) * 3;
      const t0 = this.rnd() * dt;
      this.vel[i * 3] = shipVel.x + _back.x * ej + jx;
      this.vel[i * 3 + 1] = shipVel.y + _back.y * ej + jy;
      this.vel[i * 3 + 2] = shipVel.z + _back.z * ej + jz;
      this.pos[i * 3] = _n.x + this.vel[i * 3] * t0;
      this.pos[i * 3 + 1] = _n.y + this.vel[i * 3 + 1] * t0;
      this.pos[i * 3 + 2] = _n.z + this.vel[i * 3 + 2] * t0;
      this.age[i] = 0;
      this.lifetime[i] = 0.08 + this.rnd() * 0.14 + thrust * 0.08;
      this.life[i * 2] = 0;
      this.life[i * 2 + 1] = 0.6 + thrust * 0.6 + (boost ? 0.3 : 0);
    }
    if (this.spawnAcc > 1) this.spawnAcc = 0;
    this.geo.setDrawRange(0, this.alive);
    (this.geo.attributes.position as BufferAttribute).needsUpdate = true;
    (this.geo.attributes.life as BufferAttribute).needsUpdate = true;
  }

  onRebase(d: Vector3): void {
    for (let i = 0; i < this.alive; i++) {
      this.pos[i * 3] += d.x;
      this.pos[i * 3 + 1] += d.y;
      this.pos[i * 3 + 2] += d.z;
    }
  }

  clear(): void {
    this.alive = 0;
    this.geo.setDrawRange(0, 0);
  }
}
