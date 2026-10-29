import {
  BufferGeometry,
  Color,
  CustomBlending,
  DataTexture,
  Float32BufferAttribute,
  LinearFilter,
  Material,
  Matrix4,
  Mesh,
  OneFactor,
  RGBAFormat,
  ShaderMaterial,
  SrcAlphaFactor,
  UnsignedByteType,
  Vector3,
  ClampToEdgeWrapping,
  AddEquation,
  type WebGLProgramParametersWithUniforms,
} from 'three';
import type { BodyDef } from '../world/bodies';
import { SUN_DIR } from '../world/bodies';

// Height-aware Rayleigh/Mie-inspired single-scattering approximation. The same
// parameters and GLSL drive the sky pass and the aerial perspective applied in
// surface materials, so sky and ground haze agree. This is an approximation
// with a fudge term for multiple scattering, not physically exact scattering.

const LUT_W = 256;
const LUT_H = 64;
const MS_FACTOR = 0.07;

/** Shared uniform objects (same instances referenced by every patched material). */
export const atmoUniforms = {
  uPlanetCenter: { value: new Vector3() },
  uPlanetRadius: { value: 60000 },
  uAtmoRadius: { value: 68000 },
  uBetaR: { value: new Vector3() },
  uBetaM: { value: new Vector3() },
  uHR: { value: 1500 },
  uHM: { value: 600 },
  uMieG: { value: 0.76 },
  uSunDir: { value: new Vector3(SUN_DIR[0], SUN_DIR[1], SUN_DIR[2]) },
  uSunIntensity: { value: 20 },
  uTransLUT: { value: null as DataTexture | null },
  uAtmoOn: { value: 0 },
  uAirglow: { value: new Vector3() },
  uAerialScale: { value: 1 },
};

export const ATMO_GLSL = /* glsl */ `
uniform vec3 uPlanetCenter;
uniform float uPlanetRadius;
uniform float uAtmoRadius;
uniform vec3 uBetaR;
uniform vec3 uBetaM;
uniform float uHR;
uniform float uHM;
uniform float uMieG;
uniform vec3 uSunDir;
uniform float uSunIntensity;
uniform sampler2D uTransLUT;
uniform float uAtmoOn;
uniform vec3 uAirglow;
uniform float uAerialScale;

vec2 atmoRaySphere(vec3 ro, vec3 rd, float r) {
  float b = dot(ro, rd);
  float c = dot(ro, ro) - r * r;
  float d = b * b - c;
  if (d < 0.0) return vec2(1e20, -1e20);
  d = sqrt(d);
  return vec2(-b - d, -b + d);
}
vec2 atmoDensity(float h) {
  float x = h / (uAtmoRadius - uPlanetRadius);
  float f = 1.0 - smoothstep(0.82, 1.0, x);
  h = max(h, 0.0);
  return vec2(exp(-h / uHR), exp(-h / uHM)) * f;
}
vec3 atmoSunTrans(float h, float mu) {
  float hn = clamp(h / (uAtmoRadius - uPlanetRadius), 0.0, 1.0);
  return texture2D(uTransLUT, vec2(clamp(mu * 0.5 + 0.5, 0.0, 1.0), hn)).rgb;
}
// Single scattering along ro + rd * t for t in [0, tMax]; ro is planet-relative.
vec3 atmoScatter(vec3 ro, vec3 rd, float tMax, const int steps, out vec3 trans) {
  trans = vec3(1.0);
  vec2 ta = atmoRaySphere(ro, rd, uAtmoRadius);
  float t0 = max(ta.x, 0.0);
  float t1 = min(ta.y, tMax);
  vec2 tp = atmoRaySphere(ro, rd, uPlanetRadius * 0.9995);
  if (tp.x > 0.0) t1 = min(t1, tp.x);
  if (t1 <= t0) return vec3(0.0);
  float ds = (t1 - t0) / float(steps);
  vec2 od = vec2(0.0);
  vec3 sumR = vec3(0.0);
  vec3 sumM = vec3(0.0);
  vec3 sumMS = vec3(0.0);
  float glow = 0.0;
  for (int i = 0; i < steps; i++) {
    vec3 p = ro + rd * (t0 + (float(i) + 0.5) * ds);
    float r = length(p);
    float h = r - uPlanetRadius;
    vec2 d = atmoDensity(h) * ds;
    od += d * 0.5;
    vec3 tv = exp(-(uBetaR * od.x + uBetaM * 1.1 * od.y));
    od += d * 0.5;
    float mu = dot(p / r, uSunDir);
    vec3 ts = atmoSunTrans(h, mu);
    sumR += d.x * tv * ts;
    sumM += d.y * tv * ts;
    sumMS += (d.x * uBetaR + d.y * uBetaM) * tv * smoothstep(-0.3, 0.35, mu);
    glow += d.x;
  }
  trans = exp(-(uBetaR * od.x + uBetaM * 1.1 * od.y));
  float c = dot(rd, uSunDir);
  float pR = 0.0596831 * (1.0 + c * c);
  float g = uMieG;
  float g2 = g * g;
  float pM = 0.0795775 * (1.0 - g2) / pow(max(1.0 + g2 - 2.0 * g * c, 1e-4), 1.5);
  return uSunIntensity * (uBetaR * sumR * pR + uBetaM * sumM * pM + sumMS * ${MS_FACTOR.toFixed(3)} * 0.0795775)
    + uAirglow * glow * 0.00012;
}
`;

function densityFade(h: number, hatm: number): number {
  const x = Math.min(Math.max(h / hatm, 0), 1);
  const t = Math.min(Math.max((x - 0.82) / 0.18, 0), 1);
  return 1 - t * t * (3 - 2 * t);
}

/** CPU transmittance LUT T(h, mu) to the atmosphere top (0 if the planet blocks). */
export function buildTransmittanceLUT(def: BodyDef): DataTexture {
  const a = def.atmosphere!;
  const R = def.radius;
  const Ha = def.atmosphereHeight;
  const Ra = R + Ha;
  const data = new Uint8Array(LUT_W * LUT_H * 4);
  const steps = 48;
  for (let j = 0; j < LUT_H; j++) {
    const h = (j / (LUT_H - 1)) * Ha;
    const r0 = R + h;
    const muH = -Math.sqrt(Math.max(0, 1 - (R / r0) * (R / r0)));
    for (let i = 0; i < LUT_W; i++) {
      const mu = (i / (LUT_W - 1)) * 2 - 1;
      // ray from (0, r0) in direction (sqrt(1-mu^2), mu)
      const dx = Math.sqrt(Math.max(0, 1 - mu * mu));
      const dy = mu;
      const b = r0 * dy;
      const c = r0 * r0 - Ra * Ra;
      const tExit = -b + Math.sqrt(Math.max(0, b * b - c));
      let odR = 0;
      let odM = 0;
      const ds = tExit / steps;
      for (let k = 0; k < steps; k++) {
        const t = (k + 0.5) * ds;
        const px = dx * t;
        const py = r0 + dy * t;
        const hh = Math.hypot(px, py) - R;
        const f = densityFade(hh, Ha);
        const hc = Math.max(hh, 0);
        odR += Math.exp(-hc / a.rayleighH) * f * ds;
        odM += Math.exp(-hc / a.mieH) * f * ds;
      }
      // Soft planet occlusion across roughly the sun's angular size.
      const vis = smooth01((mu - muH + 0.012) / 0.024);
      const o = (j * LUT_W + i) * 4;
      for (let ch = 0; ch < 3; ch++) {
        const T = Math.exp(-(a.rayleigh[ch] * odR + a.mie[ch] * 1.1 * odM)) * vis;
        data[o + ch] = Math.round(Math.min(1, Math.max(0, T)) * 255);
      }
      data[o + 3] = 255;
    }
  }
  const tex = new DataTexture(data, LUT_W, LUT_H, RGBAFormat, UnsignedByteType);
  tex.magFilter = LinearFilter;
  tex.minFilter = LinearFilter;
  tex.wrapS = ClampToEdgeWrapping;
  tex.wrapT = ClampToEdgeWrapping;
  tex.needsUpdate = true;
  return tex;
}

function smooth01(x: number): number {
  const t = Math.min(Math.max(x, 0), 1);
  return t * t * (3 - 2 * t);
}

const lutCache = new Map<string, DataTexture>();
let emptyLut: DataTexture | null = null;

function getEmptyLut(): DataTexture {
  if (!emptyLut) {
    emptyLut = new DataTexture(new Uint8Array([255, 255, 255, 255]), 1, 1, RGBAFormat, UnsignedByteType);
    emptyLut.needsUpdate = true;
  }
  return emptyLut;
}

/** The cached transmittance LUT for a body (a 1x1 white texture for airless bodies). */
export function transmittanceLUT(def: BodyDef): DataTexture {
  if (!def.atmosphere) return getEmptyLut();
  let lut = lutCache.get(def.id);
  if (!lut) {
    lut = buildTransmittanceLUT(def);
    lutCache.set(def.id, lut);
  }
  return lut;
}

/** Point the shared atmosphere uniforms at a body (or disable for airless bodies). */
export function setAtmosphereBody(def: BodyDef | null): void {
  const u = atmoUniforms;
  if (!def || !def.atmosphere) {
    u.uAtmoOn.value = 0;
    u.uTransLUT.value = getEmptyLut();
    if (def) {
      u.uPlanetRadius.value = def.radius;
      u.uAtmoRadius.value = def.radius + 1;
    }
    return;
  }
  const a = def.atmosphere;
  let lut = lutCache.get(def.id);
  if (!lut) {
    lut = buildTransmittanceLUT(def);
    lutCache.set(def.id, lut);
  }
  u.uAtmoOn.value = 1;
  u.uTransLUT.value = lut;
  u.uPlanetRadius.value = def.radius;
  u.uAtmoRadius.value = def.radius + def.atmosphereHeight;
  u.uBetaR.value.set(a.rayleigh[0], a.rayleigh[1], a.rayleigh[2]);
  u.uBetaM.value.set(a.mie[0], a.mie[1], a.mie[2]);
  u.uHR.value = a.rayleighH;
  u.uHM.value = a.mieH;
  u.uMieG.value = a.mieG;
  u.uSunIntensity.value = a.sunIntensity;
  u.uAirglow.value.set(a.airglow[0], a.airglow[1], a.airglow[2]);
}

// ---------------------------------------------------------------- sky pass

export function createSkyMesh(steps: number): Mesh {
  const g = new BufferGeometry();
  // One oversized triangle covering clip space.
  g.setAttribute('position', new Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3));
  const mat = new ShaderMaterial({
    uniforms: {
      ...atmoUniforms,
      uInvProj: { value: new Matrix4() },
      uCamRot: { value: new Matrix4() },
      // The sky is drawn with its own camera, so the eye position is passed explicitly.
      uEye: { value: new Vector3() },
    },
    defines: { SKY_STEPS: steps },
    vertexShader: /* glsl */ `
      uniform mat4 uInvProj;
      uniform mat4 uCamRot;
      varying vec3 vDir;
      void main() {
        vec4 v = uInvProj * vec4(position.xy, 1.0, 1.0);
        vDir = (uCamRot * vec4(v.xyz / v.w, 0.0)).xyz;
        gl_Position = vec4(position.xy, 1.0, 1.0);
      }`,
    fragmentShader: /* glsl */ `
      varying vec3 vDir;
      uniform vec3 uEye;
      ${ATMO_GLSL}
      void main() {
        if (uAtmoOn < 0.5) { gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0); return; }
        vec3 rd = normalize(vDir);
        vec3 ro = uEye - uPlanetCenter;
        vec3 T;
        vec3 S = atmoScatter(ro, rd, 1e9, SKY_STEPS, T);
        float tAvg = dot(T, vec3(0.3333));
        gl_FragColor = vec4(S, tAvg);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
    depthTest: false,
    depthWrite: false,
    blending: CustomBlending,
    blendEquation: AddEquation,
    blendSrc: OneFactor,
    blendDst: SrcAlphaFactor,
    blendSrcAlpha: OneFactor,
    blendDstAlpha: SrcAlphaFactor,
    transparent: true,
  });
  const m = new Mesh(g, mat);
  m.frustumCulled = false;
  return m;
}

/** Update the sky pass camera uniforms (call each frame before rendering). */
export function updateSkyMesh(sky: Mesh, camera: { projectionMatrixInverse: Matrix4; matrixWorld: Matrix4; position: Vector3 }): void {
  const m = sky.material as ShaderMaterial;
  m.uniforms.uInvProj.value.copy(camera.projectionMatrixInverse);
  m.uniforms.uCamRot.value.extractRotation(camera.matrixWorld);
  m.uniforms.uEye.value.copy(camera.position);
}

// ------------------------------------------------------ material aerial patch

/**
 * Add aerial perspective (atmosphere haze matching the sky) to a built-in
 * material by replacing its fog chunk. Optionally chains another onBeforeCompile.
 */
export function patchAerial(
  material: Material,
  steps: number,
  extra?: (shader: WebGLProgramParametersWithUniforms) => void,
  cacheKey = '',
): void {
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, atmoUniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vAtmoWorld;')
      .replace(
        '#include <project_vertex>',
        `#include <project_vertex>
        {
          vec4 aw = vec4(transformed, 1.0);
          #ifdef USE_INSTANCING
            aw = instanceMatrix * aw;
          #endif
          vAtmoWorld = (modelMatrix * aw).xyz;
        }`,
      );
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>\nvarying vec3 vAtmoWorld;\n${ATMO_GLSL}`)
      .replace(
        '#include <fog_fragment>',
        `if (uAtmoOn > 0.5) {
          vec3 aRo = cameraPosition - uPlanetCenter;
          vec3 aD = vAtmoWorld - cameraPosition;
          float aDist = length(aD);
          vec3 aT;
          vec3 aS = atmoScatter(aRo, aD / max(aDist, 1e-3), aDist * uAerialScale, ${steps}, aT);
          gl_FragColor.rgb = gl_FragColor.rgb * aT + aS;
        }`,
      );
    extra?.(shader);
  };
  material.customProgramCacheKey = () => `aerial${steps}:${cacheKey}`;
}

// ------------------------------------------------------------ CPU estimates

const _p = new Vector3();

/**
 * CPU mirror of the shader integral for a single direction, used to derive
 * light colors (sun transmittance, sky ambient). Returns inscattered radiance.
 */
export function cpuScatter(def: BodyDef, roPlanet: Vector3, rd: Vector3, steps: number, out: Color): Color {
  out.setRGB(0, 0, 0);
  const a = def.atmosphere;
  if (!a) return out;
  const R = def.radius;
  const Ra = R + def.atmosphereHeight;
  const b = roPlanet.dot(rd);
  const c = roPlanet.lengthSq() - Ra * Ra;
  const disc = b * b - c;
  if (disc < 0) return out;
  const sq = Math.sqrt(disc);
  const t0 = Math.max(-b - sq, 0);
  let t1 = -b + sq;
  const cp = roPlanet.lengthSq() - R * R;
  const discP = b * b - cp;
  if (discP > 0) {
    const tp = -b - Math.sqrt(discP);
    if (tp > 0) t1 = Math.min(t1, tp);
  }
  if (t1 <= t0) return out;
  const sun = atmoUniforms.uSunDir.value;
  const ds = (t1 - t0) / steps;
  let odR = 0;
  let odM = 0;
  const sR = [0, 0, 0];
  const sM = [0, 0, 0];
  for (let i = 0; i < steps; i++) {
    _p.copy(roPlanet).addScaledVector(rd, t0 + (i + 0.5) * ds);
    const r = _p.length();
    const h = r - R;
    const f = densityFade(h, def.atmosphereHeight);
    const hc = Math.max(h, 0);
    const dR = Math.exp(-hc / a.rayleighH) * f * ds;
    const dM = Math.exp(-hc / a.mieH) * f * ds;
    odR += dR * 0.5;
    odM += dM * 0.5;
    const mu = _p.dot(sun) / r;
    for (let ch = 0; ch < 3; ch++) {
      const tv = Math.exp(-(a.rayleigh[ch] * odR + a.mie[ch] * 1.1 * odM));
      const ts = sunTransCPU(def, h, mu, ch);
      sR[ch] += dR * tv * ts;
      sM[ch] += dM * tv * ts;
    }
    odR += dR * 0.5;
    odM += dM * 0.5;
  }
  const cth = rd.dot(sun);
  const pR = 0.0596831 * (1 + cth * cth);
  const g = a.mieG;
  const pM = (0.0795775 * (1 - g * g)) / Math.pow(Math.max(1 + g * g - 2 * g * cth, 1e-4), 1.5);
  out.setRGB(
    a.sunIntensity * (a.rayleigh[0] * sR[0] * pR + a.mie[0] * sM[0] * pM),
    a.sunIntensity * (a.rayleigh[1] * sR[1] * pR + a.mie[1] * sM[1] * pM),
    a.sunIntensity * (a.rayleigh[2] * sR[2] * pR + a.mie[2] * sM[2] * pM),
  );
  return out;
}

/** Transmittance from a point at height h toward the sun (CPU, sampled from the cached LUT data). */
export function sunTransCPU(def: BodyDef, h: number, mu: number, ch: number): number {
  if (!def.atmosphere) return 1;
  let lut = lutCache.get(def.id);
  if (!lut) {
    lut = buildTransmittanceLUT(def);
    lutCache.set(def.id, lut);
  }
  const data = lut.image.data as Uint8Array;
  const u = Math.min(Math.max(mu * 0.5 + 0.5, 0), 1) * (LUT_W - 1);
  const v = Math.min(Math.max(h / def.atmosphereHeight, 0), 1) * (LUT_H - 1);
  const i0 = Math.floor(u);
  const j0 = Math.floor(v);
  const i1 = Math.min(i0 + 1, LUT_W - 1);
  const j1 = Math.min(j0 + 1, LUT_H - 1);
  const fu = u - i0;
  const fv = v - j0;
  const at = (i: number, j: number) => data[(j * LUT_W + i) * 4 + ch] / 255;
  return (at(i0, j0) * (1 - fu) + at(i1, j0) * fu) * (1 - fv) + (at(i0, j1) * (1 - fu) + at(i1, j1) * fu) * fv;
}
