import {
  AdditiveBlending,
  BufferGeometry,
  Color,
  Float32BufferAttribute,
  Points,
  ShaderMaterial,
  Vector3,
} from 'three';
import { mulberry32 } from '../core/rng';

const BOX = 48;

/**
 * Small drifting motes (pollen/dust) that wrap around the camera. Wrapping is
 * done against the camera's *system* position modulo the box, so origin
 * rebases never make the field jump.
 */
export class Motes {
  readonly points: Points;
  private readonly mat: ShaderMaterial;
  private time = 0;

  constructor(count = 420) {
    const rnd = mulberry32(77);
    const pos: number[] = [];
    const seed: number[] = [];
    for (let i = 0; i < count; i++) {
      pos.push(rnd() * BOX, rnd() * BOX, rnd() * BOX);
      seed.push(rnd());
    }
    const g = new BufferGeometry();
    g.setAttribute('position', new Float32BufferAttribute(pos, 3));
    g.setAttribute('seed', new Float32BufferAttribute(seed, 1));
    this.mat = new ShaderMaterial({
      uniforms: {
        uCamLocal: { value: new Vector3() },
        uCamMod: { value: new Vector3() },
        uTime: { value: 0 },
        uWind: { value: new Vector3(0.6, 0.05, 0.3) },
        uColor: { value: new Color(1, 1, 1) },
        uIntensity: { value: 0 },
        uScale: { value: 400 },
      },
      vertexShader: /* glsl */ `
        attribute float seed;
        uniform vec3 uCamLocal, uCamMod, uWind;
        uniform float uTime, uScale;
        varying float vFade;
        varying float vSeed;
        #include <common>
        #include <logdepthbuf_pars_vertex>
        void main() {
          vec3 drift = uWind * uTime + vec3(sin(uTime * 0.6 + seed * 31.0), sin(uTime * 0.45 + seed * 17.0) * 0.6, cos(uTime * 0.5 + seed * 23.0)) * 0.8;
          vec3 rel = mod(position + drift - uCamMod, ${BOX.toFixed(1)}) - ${(BOX / 2).toFixed(1)};
          vec3 wp = uCamLocal + rel;
          vec4 mv = viewMatrix * vec4(wp, 1.0);
          gl_Position = projectionMatrix * mv;
          float d = length(rel);
          vFade = (1.0 - smoothstep(${(BOX * 0.3).toFixed(1)}, ${(BOX * 0.5).toFixed(1)}, d)) * smoothstep(0.5, 2.5, d);
          vSeed = seed;
          gl_PointSize = clamp((0.035 + seed * 0.04) * uScale / max(-mv.z, 0.1), 1.0, 6.0);
          #include <logdepthbuf_vertex>
        }`,
      fragmentShader: /* glsl */ `
        varying float vFade;
        varying float vSeed;
        uniform vec3 uColor;
        uniform float uIntensity, uTime;
        #include <common>
        #include <logdepthbuf_pars_fragment>
        void main() {
          #include <logdepthbuf_fragment>
          float r = length(gl_PointCoord - 0.5);
          float a = smoothstep(0.5, 0.0, r) * vFade * uIntensity * (0.6 + 0.4 * sin(uTime * 2.0 + vSeed * 40.0));
          gl_FragColor = vec4(uColor * a, 1.0);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,
      transparent: true,
      depthWrite: false,
      blending: AdditiveBlending,
    });
    this.points = new Points(g, this.mat);
    this.points.frustumCulled = false;
    this.points.renderOrder = 7;
  }

  /**
   * @param camLocal camera position (local); @param camSystem camera position (system, double)
   * @param intensity 0 disables (airless bodies, high altitude)
   */
  update(dt: number, camLocal: Vector3, camSystem: Vector3, color: Color, intensity: number, viewportH: number, fovDeg: number): void {
    this.time += dt;
    const u = this.mat.uniforms;
    u.uTime.value = this.time;
    u.uCamLocal.value.copy(camLocal);
    const m = (x: number) => ((x % BOX) + BOX) % BOX;
    u.uCamMod.value.set(m(camSystem.x), m(camSystem.y), m(camSystem.z));
    (u.uColor.value as Color).copy(color);
    u.uIntensity.value = intensity;
    u.uScale.value = viewportH / (2 * Math.tan((fovDeg * Math.PI) / 360));
    this.points.visible = intensity > 0.01;
  }
}
