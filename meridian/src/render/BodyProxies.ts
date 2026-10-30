import {
  AddEquation,
  BufferAttribute,
  BufferGeometry,
  Color,
  CustomBlending,
  DoubleSide,
  FrontSide,
  Group,
  Mesh,
  NormalBlending,
  OneFactor,
  Quaternion,
  RingGeometry,
  ShaderMaterial,
  SphereGeometry,
  SrcAlphaFactor,
  Vector3,
  type Scene,
} from 'three';
import { BODIES, BODY_IDS, sunDirFor, type BodyDef, type BodyId } from '../world/bodies';
import { ATMO_GLSL, atmoUniforms, transmittanceLUT } from './Atmosphere';
import { Clouds } from './Clouds';
import { TERRAIN_ALBEDO_GLSL } from '../terrain/terrainMaterial';
import { GRID_INDEX_COUNT, GRID_VERTS, makeChunkIndex, type ChunkData } from '../terrain/chunkGen';
import type { ChunkBackend } from '../terrain/ChunkStore';
import { chunkKey } from '../world/cube';
import { SEA_WATER } from '../terrain/waterMaterial';

/** Scene units per meter in the scaled background scene. */
export const BG_SCALE = 1e-4;

/** Lighting values shared with the local scene so a proxy and the local terrain shade alike. */
export interface ProxyLighting {
  sunColor: Color; // color x intensity
  hemiSky: Color; // color x intensity
  hemiGround: Color;
  hemiUp: Vector3;
  cloudAmbient: Color;
}

type AtmoSet = typeof atmoUniforms & { uUnit: { value: number } };

function makeAtmo(def: BodyDef): AtmoSet {
  const u: AtmoSet = {
    uPlanetCenter: { value: new Vector3() },
    uPlanetRadius: { value: def.radius },
    uAtmoRadius: { value: def.radius + Math.max(def.atmosphereHeight, 1) },
    uBetaR: { value: new Vector3() },
    uBetaM: { value: new Vector3() },
    uHR: { value: 1 },
    uHM: { value: 1 },
    uMieG: { value: 0.7 },
    // Each body is lit from its own direction to its star (the local scene's uSunDir belongs to Lighting).
    uSunDir: { value: new Vector3(...sunDirFor(def)) },
    uSunIntensity: { value: 0 },
    uTransLUT: { value: transmittanceLUT(def) },
    uAtmoOn: { value: def.atmosphere ? 1 : 0 },
    uAirglow: { value: new Vector3() },
    uAerialScale: atmoUniforms.uAerialScale,
    uUnit: { value: 1 / BG_SCALE },
  };
  const a = def.atmosphere;
  if (a) {
    u.uBetaR.value.set(...a.rayleigh);
    u.uBetaM.value.set(...a.mie);
    u.uHR.value = a.rayleighH;
    u.uHM.value = a.mieH;
    u.uMieG.value = a.mieG;
    u.uSunIntensity.value = a.sunIntensity;
    u.uAirglow.value.set(...a.airglow);
  }
  return u;
}

const lin = (hex: number) => new Color(hex).convertSRGBToLinear();

/**
 * Proxy surface: the body's level-0 terrain mesh (the same chunks the local
 * terrain starts from) with the shared terrain albedo, the local scene's
 * sun/hemisphere lighting, and the same aerial perspective integral.
 */
function surfaceMaterial(def: BodyDef, atmo: AtmoSet, aerialSteps: number, light: ProxyLighting): ShaderMaterial {
  const p = def.palette;
  return new ShaderMaterial({
    uniforms: {
      ...atmo,
      uA1: { value: lin(p.a1) },
      uA2: { value: lin(p.a2) },
      uA3: { value: lin(p.a3) },
      uB1: { value: lin(p.b1) },
      uB2: { value: lin(p.b2) },
      uB3: { value: lin(p.b3) },
      uSpecial: { value: lin(p.special) },
      uSunCol: { value: light.sunColor },
      uHemiSky: { value: light.hemiSky },
      uHemiGround: { value: light.hemiGround },
      uHemiUp: { value: light.hemiUp },
    },
    vertexShader: /* glsl */ `
      attribute vec4 surf;
      varying vec3 vN;
      varying vec4 vSurf;
      varying vec3 vWorld;
      #include <common>
      #include <logdepthbuf_pars_vertex>
      void main() {
        vN = normalize(mat3(modelMatrix) * normal);
        vSurf = surf;
        vec4 w = modelMatrix * vec4(position, 1.0);
        vWorld = w.xyz;
        gl_Position = projectionMatrix * viewMatrix * w;
        #include <logdepthbuf_vertex>
      }`,
    fragmentShader: /* glsl */ `
      varying vec3 vN;
      varying vec4 vSurf;
      varying vec3 vWorld;
      uniform vec3 uSunCol, uHemiSky, uHemiGround, uHemiUp;
      uniform float uUnit;
      ${ATMO_GLSL}
      ${TERRAIN_ALBEDO_GLSL}
      #include <common>
      #include <logdepthbuf_pars_fragment>
      void main() {
        #include <logdepthbuf_fragment>
        float rockMask, specMask;
        vec3 albedo = terrainAlbedo(vSurf, vec4(0.5), vec4(0.5), vec4(0.5), rockMask, specMask);
        vec3 N = normalize(vN);
        vec3 irr = uSunCol * max(dot(N, uSunDir), 0.0) + mix(uHemiGround, uHemiSky, dot(N, uHemiUp) * 0.5 + 0.5);
        vec3 col = albedo * RECIPROCAL_PI * irr;
        gl_FragColor = vec4(col, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
        // Aerial perspective after tone mapping, exactly where the local terrain
        // applies it (patchAerial replaces the fog chunk), so the 3R swap matches.
        if (uAtmoOn > 0.5) {
          vec3 ro = (cameraPosition - uPlanetCenter) * uUnit;
          vec3 d = (vWorld - cameraPosition) * uUnit;
          float dist = length(d);
          vec3 T;
          vec3 S = atmoScatter(ro, d / dist, dist * uAerialScale, ${aerialSteps}, T);
          gl_FragColor.rgb = gl_FragColor.rgb * T + S;
        }
      }`,
  });
}

/** Proxy liquid surface: depth-tinted, sun glint, same lighting and aerial perspective as the proxy surface. */
function proxyWaterMaterial(atmo: AtmoSet, aerialSteps: number, light: ProxyLighting): ShaderMaterial {
  return new ShaderMaterial({
    uniforms: {
      ...atmo,
      uShallow: { value: lin(SEA_WATER.shallow) },
      uDeep: { value: lin(SEA_WATER.deep) },
      uDepthScale: { value: SEA_WATER.depthScale },
      uSunCol: { value: light.sunColor },
      uHemiSky: { value: light.hemiSky },
      uHemiGround: { value: light.hemiGround },
      uHemiUp: { value: light.hemiUp },
    },
    vertexShader: /* glsl */ `
      attribute float depth;
      varying vec3 vN;
      varying vec3 vWorld;
      varying float vDepth;
      #include <common>
      #include <logdepthbuf_pars_vertex>
      void main() {
        vN = normalize(mat3(modelMatrix) * normal);
        vDepth = depth;
        vec4 w = modelMatrix * vec4(position, 1.0);
        vWorld = w.xyz;
        gl_Position = projectionMatrix * viewMatrix * w;
        #include <logdepthbuf_vertex>
      }`,
    fragmentShader: /* glsl */ `
      varying vec3 vN;
      varying vec3 vWorld;
      varying float vDepth;
      uniform vec3 uSunCol, uHemiSky, uHemiGround, uHemiUp, uShallow, uDeep;
      uniform float uUnit, uDepthScale;
      ${ATMO_GLSL}
      #include <common>
      #include <logdepthbuf_pars_fragment>
      void main() {
        #include <logdepthbuf_fragment>
        vec3 N = normalize(vN);
        vec3 V = normalize(cameraPosition - vWorld);
        vec3 albedo = mix(uShallow, uDeep, 1.0 - exp(-max(vDepth, 0.0) / uDepthScale));
        float nl = max(dot(N, uSunDir), 0.0);
        vec3 irr = uSunCol * nl + mix(uHemiGround, uHemiSky, dot(N, uHemiUp) * 0.5 + 0.5);
        vec3 H = normalize(V + uSunDir);
        float spec = pow(max(dot(N, H), 0.0), 180.0) * 2.5 * nl;
        float fres = 0.02 + 0.98 * pow(1.0 - max(dot(N, V), 0.0), 5.0);
        vec3 col = albedo * RECIPROCAL_PI * irr + uSunCol * spec * 0.08 + uHemiSky * fres * 0.25;
        gl_FragColor = vec4(col, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
        if (uAtmoOn > 0.5) {
          vec3 ro = (cameraPosition - uPlanetCenter) * uUnit;
          vec3 d = (vWorld - cameraPosition) * uUnit;
          float dist = length(d);
          vec3 T;
          vec3 S = atmoScatter(ro, d / dist, dist * uAerialScale, ${aerialSteps}, T);
          gl_FragColor.rgb = gl_FragColor.rgb * T + S;
        }
      }`,
  });
}

/** Limb shell: the atmosphere seen beside the planet disk (same integral as the sky pass). */
function shellMaterial(atmo: AtmoSet, skySteps: number): ShaderMaterial {
  return new ShaderMaterial({
    uniforms: { ...atmo },
    vertexShader: /* glsl */ `
      varying vec3 vWorld;
      #include <common>
      #include <logdepthbuf_pars_vertex>
      void main() {
        vec4 w = modelMatrix * vec4(position, 1.0);
        vWorld = w.xyz;
        gl_Position = projectionMatrix * viewMatrix * w;
        #include <logdepthbuf_vertex>
      }`,
    fragmentShader: /* glsl */ `
      varying vec3 vWorld;
      uniform float uUnit;
      ${ATMO_GLSL}
      #include <common>
      #include <logdepthbuf_pars_fragment>
      void main() {
        #include <logdepthbuf_fragment>
        vec3 ro = (cameraPosition - uPlanetCenter) * uUnit;
        vec3 rd = normalize(vWorld - cameraPosition);
        // Rays that reach the surface are shaded by the surface material.
        if (atmoRaySphere(ro, rd, uPlanetRadius * 0.9995).x > 0.0) discard;
        vec3 T;
        vec3 S = atmoScatter(ro, rd, 1e9, ${skySteps}, T);
        gl_FragColor = vec4(S, dot(T, vec3(0.3333)));
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
    side: FrontSide,
    depthWrite: false,
    transparent: true,
    blending: CustomBlending,
    blendEquation: AddEquation,
    blendSrc: OneFactor,
    blendDst: SrcAlphaFactor,
    blendSrcAlpha: OneFactor,
    blendDstAlpha: SrcAlphaFactor,
  });
}

/**
 * Saturn's main rings in planet radii (equatorial radius 60,268 km): D
 * 66,900-74,510 km, C 74,658-92,000, B 92,000-117,580, Cassini Division
 * 117,580-122,170, A 122,170-136,775 with the Encke gap at 133,589 (325 km
 * wide), F at 140,180. Reference values entered without a fetched source
 * (estimated); the optical depths are a visual approximation.
 */
const RING_GLSL = /* glsl */ `
  float ringBand(float r, float a, float b) {
    return smoothstep(a - 0.002, a + 0.002, r) * (1.0 - smoothstep(b - 0.002, b + 0.002, r));
  }
  // Normal optical depth at r planet radii (0 outside the rings); fw is the
  // radial footprint of a pixel, so ringlets finer than a pixel average out.
  float ringTau(float r, float fw) {
    float t = 0.03 * ringBand(r, 1.110, 1.236)
      + 0.12 * ringBand(r, 1.239, 1.527)
      + 1.7 * ringBand(r, 1.527, 1.951)
      + 0.09 * ringBand(r, 1.951, 2.027)
      + 0.55 * ringBand(r, 2.027, 2.269) * (1.0 - ringBand(r, 2.2139, 2.2193))
      + 0.35 * ringBand(r, 2.3245, 2.3275);
    float w = sin(r * 517.0) * sin(r * 211.0 + 1.3) * clamp(1.0 - fw * 517.0 / 3.0, 0.0, 1.0);
    return t * (0.8 + 0.2 * w);
  }
`;
const RINGS: Record<string, { inner: number; outer: number }> = { saturn: { inner: 1.1, outer: 2.34 } };

/** Ring layer in the body's equatorial plane, lit by the Sun and shadowed by the planet. */
function ringMaterial(def: BodyDef, atmo: AtmoSet, light: ProxyLighting): ShaderMaterial {
  return new ShaderMaterial({
    uniforms: {
      uSunDir: atmo.uSunDir,
      uNorth: { value: new Vector3(...def.frame.north) },
      uR: { value: def.radius },
      uSunCol: { value: light.sunColor },
    },
    vertexShader: /* glsl */ `
      varying vec3 vLocal;
      varying vec3 vWorld;
      #include <common>
      #include <logdepthbuf_pars_vertex>
      void main() {
        vLocal = position;
        vec4 w = modelMatrix * vec4(position, 1.0);
        vWorld = w.xyz;
        gl_Position = projectionMatrix * viewMatrix * w;
        #include <logdepthbuf_vertex>
      }`,
    fragmentShader: /* glsl */ `
      varying vec3 vLocal;
      varying vec3 vWorld;
      uniform vec3 uSunDir, uNorth, uSunCol;
      uniform float uR;
      ${RING_GLSL}
      #include <common>
      #include <logdepthbuf_pars_fragment>
      void main() {
        #include <logdepthbuf_fragment>
        float r = length(vLocal) / uR;
        float tau = ringTau(r, fwidth(r));
        vec3 V = normalize(cameraPosition - vWorld);
        float muV = abs(dot(V, uNorth));
        float muS = dot(uSunDir, uNorth);
        // Slant opacity through the particle layer.
        float alpha = 1.0 - exp(-tau / max(muV, 0.02));
        if (alpha < 0.002) discard;
        // Lit face: Lommel-Seeliger reflection of a particle layer (dim when the Sun grazes the
        // plane, as near the 2025 equinox) plus planetshine; the far face glows where it is thin.
        bool sameSide = muS * dot(V, uNorth) > 0.0;
        float ls = abs(muS) / (abs(muS) + muV + 1e-4);
        float lit = sameSide ? 0.2 + 1.6 * ls : 0.05 + 0.3 * exp(-tau);
        // The planet's shadow across the rings.
        vec3 P = vLocal / uR;
        float along = dot(P, uSunDir);
        float off = length(P - along * uSunDir);
        lit *= along > 0.0 ? 1.0 : smoothstep(0.985, 1.015, off);
        vec3 col = mix(vec3(0.42, 0.38, 0.33), vec3(0.86, 0.79, 0.66), smoothstep(1.45, 1.6, r));
        col = mix(col, vec3(0.74, 0.69, 0.6), smoothstep(2.0, 2.05, r));
        gl_FragColor = vec4(col * uSunCol * lit * RECIPROCAL_PI, alpha);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
    transparent: true,
    depthWrite: false,
    side: DoubleSide,
    blending: NormalBlending,
  });
}

/** Banded cloud-deck look of a giant planet (procedural, labelled fictional detail). */
interface GiantLook {
  bands: number;
  contrast: number;
  turbulence: number;
  /** Storm spot: latitude (deg), longitude (deg), half-size (deg lon, deg lat), strength 0..1. */
  spot: [number, number, number, number, number];
}

const GIANT_LOOKS: Record<string, GiantLook> = {
  jupiter: { bands: 14, contrast: 0.9, turbulence: 0.55, spot: [-22, 0, 9, 4.5, 1] },
  saturn: { bands: 18, contrast: 0.45, turbulence: 0.25, spot: [0, 0, 1, 1, 0] },
  uranus: { bands: 8, contrast: 0.12, turbulence: 0.1, spot: [0, 0, 1, 1, 0] },
  neptune: { bands: 10, contrast: 0.35, turbulence: 0.3, spot: [-20, 40, 7, 3.5, 0.8] },
};

/**
 * Smooth giant globe: latitude bands in the body frame with seeded-looking
 * turbulence, an optional storm spot, the proxy lighting and post-tone-mapping
 * aerial perspective (same order as the local terrain).
 */
function giantMaterial(def: BodyDef, atmo: AtmoSet, aerialSteps: number, light: ProxyLighting): ShaderMaterial {
  const p = def.palette;
  const look = GIANT_LOOKS[def.id] ?? { bands: 12, contrast: 0.5, turbulence: 0.3, spot: [0, 0, 1, 1, 0] };
  const f = def.frame;
  return new ShaderMaterial({
    uniforms: {
      ...atmo,
      uA1: { value: lin(p.a1) },
      uA2: { value: lin(p.a2) },
      uA3: { value: lin(p.a3) },
      uB1: { value: lin(p.b1) },
      uB2: { value: lin(p.b2) },
      uSpot: { value: lin(p.special) },
      uNorth: { value: new Vector3(...f.north) },
      uMeridian: { value: new Vector3(...f.meridian) },
      uEast: { value: new Vector3(...f.east) },
      uLook: { value: new Vector3(look.bands, look.contrast, look.turbulence) },
      uSpotDef: { value: [...look.spot] },
      uRinged: { value: RINGS[def.id] ? 1 : 0 },
      uSunCol: { value: light.sunColor },
      uHemiSky: { value: light.hemiSky },
      uHemiGround: { value: light.hemiGround },
      uHemiUp: { value: light.hemiUp },
    },
    vertexShader: /* glsl */ `
      varying vec3 vN;
      varying vec3 vDir;
      varying vec3 vWorld;
      #include <common>
      #include <logdepthbuf_pars_vertex>
      void main() {
        vDir = normalize(position);
        vN = normalize(mat3(modelMatrix) * normal);
        vec4 w = modelMatrix * vec4(position, 1.0);
        vWorld = w.xyz;
        gl_Position = projectionMatrix * viewMatrix * w;
        #include <logdepthbuf_vertex>
      }`,
    fragmentShader: /* glsl */ `
      varying vec3 vN;
      varying vec3 vDir;
      varying vec3 vWorld;
      uniform vec3 uA1, uA2, uA3, uB1, uB2, uSpot, uNorth, uMeridian, uEast, uLook;
      uniform float uSpotDef[5];
      uniform vec3 uSunCol, uHemiSky, uHemiGround, uHemiUp;
      uniform float uUnit;
      uniform float uRinged;
      ${ATMO_GLSL}
      ${RING_GLSL}
      #include <common>
      #include <logdepthbuf_pars_fragment>
      float gh(vec3 p) { p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
      float gnoise(vec3 x) {
        vec3 i = floor(x); vec3 f = fract(x); f = f * f * (3.0 - 2.0 * f);
        return mix(mix(mix(gh(i), gh(i + vec3(1,0,0)), f.x), mix(gh(i + vec3(0,1,0)), gh(i + vec3(1,1,0)), f.x), f.y),
                   mix(mix(gh(i + vec3(0,0,1)), gh(i + vec3(1,0,1)), f.x), mix(gh(i + vec3(0,1,1)), gh(i + vec3(1,1,1)), f.x), f.y), f.z);
      }
      void main() {
        #include <logdepthbuf_fragment>
        vec3 d = normalize(vDir);
        float y = clamp(dot(d, uNorth), -1.0, 1.0);
        float lat = asin(y);
        float lon = atan(dot(d, uEast), dot(d, uMeridian));
        // Turbulence stretched along the bands (zonal jets).
        vec3 q = vec3(cos(lat) * cos(lon), cos(lat) * sin(lon), y * 6.0) * 3.0;
        float turb = gnoise(q) * 0.6 + gnoise(q * 2.7) * 0.3 + gnoise(q * 7.3) * 0.1;
        float t = lat * uLook.x / 3.14159 + (turb - 0.5) * uLook.z;
        float band = sin(t * 3.14159 * 2.0) + 0.45 * sin(t * 3.14159 * 4.6 + 1.7);
        vec3 zone = mix(uA1, uA3, smoothstep(0.2, 0.9, turb));
        vec3 belt = mix(uA2, uB2, smoothstep(0.3, 0.8, turb));
        vec3 albedo = mix(zone, belt, smoothstep(-0.4, 0.4, band) * uLook.y);
        albedo = mix(albedo, uB1, (1.0 - uLook.y) * 0.5);
        // Storm spot (Great Red Spot / Great Dark Spot style).
        float sLat = radians(uSpotDef[0]);
        float dLon = atan(sin(lon - radians(uSpotDef[1])), cos(lon - radians(uSpotDef[1])));
        vec2 e = vec2(dLon * cos(lat) / radians(uSpotDef[2]), (lat - sLat) / radians(uSpotDef[3]));
        float spot = smoothstep(1.0, 0.55, length(e)) * uSpotDef[4];
        albedo = mix(albedo, uSpot, spot);
        vec3 N = normalize(vN);
        // Shadow of the rings: where the path to the Sun crosses the ring plane.
        float ringSun = 1.0;
        float sn = dot(uSunDir, uNorth);
        if (uRinged > 0.5 && abs(sn) > 1e-3) {
          float t = -dot(d, uNorth) / sn;
          if (t > 0.0) ringSun = exp(-ringTau(length(d + t * uSunDir), 0.01) / abs(sn));
        }
        vec3 irr = uSunCol * max(dot(N, uSunDir), 0.0) * ringSun + mix(uHemiGround, uHemiSky, dot(N, uHemiUp) * 0.5 + 0.5);
        gl_FragColor = vec4(albedo * RECIPROCAL_PI * irr, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
        if (uAtmoOn > 0.5) {
          vec3 ro = (cameraPosition - uPlanetCenter) * uUnit;
          vec3 dv = (vWorld - cameraPosition) * uUnit;
          float dist = length(dv);
          vec3 T;
          vec3 S = atmoScatter(ro, dv / dist, dist * uAerialScale, ${aerialSteps}, T);
          gl_FragColor.rgb = gl_FragColor.rgb * T + S;
        }
      }`,
  });
}

/** Proxies never shrink below this angular radius (radians; about 1.5 px at 1080p and 60 deg), so far bodies stay findable. */
const MIN_ANGULAR_RADIUS = 0.0015;

export class BodyProxy {
  readonly group = new Group();
  readonly atmo: AtmoSet;
  surface: Mesh | null = null;
  water: Mesh | null = null;
  shell: Mesh | null = null;
  rings: Mesh | null = null;
  readonly clouds: Clouds;
  readonly roots = new Map<string, ChunkData>();
  /** Hidden while this body is the active (locally rendered) body. */
  suppressed = false;

  constructor(readonly def: BodyDef, cloudQuality: number) {
    this.atmo = makeAtmo(def);
    this.clouds = new Clouds(this.atmo, 1 / BG_SCALE, [64, 32]);
    this.clouds.setBody(def, cloudQuality);
    this.group.add(this.clouds.group);
    this.group.visible = false;
  }

  get ready(): boolean {
    return this.surface !== null;
  }

  /** Build the surface from the six level-0 roots. */
  build(aerialSteps: number, skySteps: number, light: ProxyLighting): void {
    const roots: ChunkData[] = [];
    for (let f = 0; f < 6; f++) {
      const d = this.roots.get(chunkKey(f, 0, 0, 0));
      if (!d) return;
      roots.push(d);
    }
    const pos = new Float32Array(6 * GRID_VERTS * 3);
    const nrm = new Float32Array(6 * GRID_VERTS * 3);
    const surf = new Uint8Array(6 * GRID_VERTS * 4);
    const gridIndex = makeChunkIndex().subarray(0, GRID_INDEX_COUNT);
    const index = new Uint16Array(6 * GRID_INDEX_COUNT);
    roots.forEach((d, f) => {
      const [cx, cy, cz] = d.center;
      for (let i = 0; i < GRID_VERTS; i++) {
        const o = (f * GRID_VERTS + i) * 3;
        pos[o] = d.positions[i * 3] + cx;
        pos[o + 1] = d.positions[i * 3 + 1] + cy;
        pos[o + 2] = d.positions[i * 3 + 2] + cz;
        nrm[o] = d.normals[i * 3];
        nrm[o + 1] = d.normals[i * 3 + 1];
        nrm[o + 2] = d.normals[i * 3 + 2];
      }
      surf.set(d.attrs.subarray(0, GRID_VERTS * 4), f * GRID_VERTS * 4);
      for (let k = 0; k < GRID_INDEX_COUNT; k++) index[f * GRID_INDEX_COUNT + k] = gridIndex[k] + f * GRID_VERTS;
    });
    const g = new BufferGeometry();
    g.setAttribute('position', new BufferAttribute(pos, 3));
    g.setAttribute('normal', new BufferAttribute(nrm, 3));
    g.setAttribute('surf', new BufferAttribute(surf, 4, true));
    g.setIndex(new BufferAttribute(index, 1));
    g.computeBoundingSphere();
    this.surface = new Mesh(g, surfaceMaterial(this.def, this.atmo, aerialSteps, light));
    this.group.add(this.surface);
    this.buildWater(roots, aerialSteps, light);
    if (this.def.atmosphere) {
      const sg = new SphereGeometry(this.def.radius + this.def.atmosphereHeight, 96, 48);
      this.shell = new Mesh(sg, shellMaterial(this.atmo, skySteps));
      this.shell.renderOrder = 1;
      this.group.add(this.shell);
    }
  }

  /** Liquid surface over the roots' wet areas (the same sheets the local terrain's level 0 draws). */
  private buildWater(roots: ChunkData[], aerialSteps: number, light: ProxyLighting): void {
    const wet = roots.filter((d) => d.water && d.water.index.length > 0);
    if (wet.length === 0) return;
    const pos = new Float32Array(wet.length * GRID_VERTS * 3);
    const nrm = new Float32Array(wet.length * GRID_VERTS * 3);
    const depth = new Float32Array(wet.length * GRID_VERTS);
    const count = wet.reduce((n, d) => n + d.water!.index.length, 0);
    const index = new Uint32Array(count);
    let k = 0;
    wet.forEach((d, f) => {
      const w = d.water!;
      const [cx, cy, cz] = d.center;
      for (let i = 0; i < GRID_VERTS; i++) {
        const o = (f * GRID_VERTS + i) * 3;
        pos[o] = w.positions[i * 3] + cx;
        pos[o + 1] = w.positions[i * 3 + 1] + cy;
        pos[o + 2] = w.positions[i * 3 + 2] + cz;
        nrm[o] = w.normals[i * 3];
        nrm[o + 1] = w.normals[i * 3 + 1];
        nrm[o + 2] = w.normals[i * 3 + 2];
      }
      depth.set(w.depth, f * GRID_VERTS);
      for (let i = 0; i < w.index.length; i++) index[k++] = w.index[i] + f * GRID_VERTS;
    });
    const g = new BufferGeometry();
    g.setAttribute('position', new BufferAttribute(pos, 3));
    g.setAttribute('normal', new BufferAttribute(nrm, 3));
    g.setAttribute('depth', new BufferAttribute(depth, 1));
    g.setIndex(new BufferAttribute(index, 1));
    g.computeBoundingSphere();
    this.water = new Mesh(g, proxyWaterMaterial(this.atmo, aerialSteps, light));
    this.group.add(this.water);
  }

  /** Giants (explore 'zone'): a smooth banded globe, viewable up close, with no terrain roots. */
  buildGiant(aerialSteps: number, skySteps: number, light: ProxyLighting): void {
    if (this.surface) return;
    const g = new SphereGeometry(this.def.radius, 256, 128);
    this.surface = new Mesh(g, giantMaterial(this.def, this.atmo, aerialSteps, light));
    this.group.add(this.surface);
    if (this.def.atmosphere) {
      const sg = new SphereGeometry(this.def.radius + this.def.atmosphereHeight, 128, 64);
      this.shell = new Mesh(sg, shellMaterial(this.atmo, skySteps));
      this.shell.renderOrder = 1;
      this.group.add(this.shell);
    }
    const ring = RINGS[this.def.id];
    if (ring) {
      const R = this.def.radius;
      const rg = new RingGeometry(ring.inner * R, ring.outer * R, 512, 1);
      // RingGeometry lies in the XY plane: turn its normal (+Z) onto the body's north pole.
      rg.applyQuaternion(new Quaternion().setFromUnitVectors(new Vector3(0, 0, 1), new Vector3(...this.def.frame.north)));
      this.rings = new Mesh(rg, ringMaterial(this.def, this.atmo, light));
      this.rings.renderOrder = 2;
      this.group.add(this.rings);
    }
  }

  /** Place the proxy for a camera at system position `camSys` (double precision). */
  update(camSys: Vector3, cloudTime: number, cloudAmbient: Color): void {
    const c = this.def.center;
    const dx = c[0] - camSys.x;
    const dy = c[1] - camSys.y;
    const dz = c[2] - camSys.z;
    // Minimum on-screen size: a far body is drawn larger (geometry and atmosphere units together).
    const grow = Math.max(1, (MIN_ANGULAR_RADIUS * Math.sqrt(dx * dx + dy * dy + dz * dz)) / this.def.radius);
    this.group.position.set(dx * BG_SCALE, dy * BG_SCALE, dz * BG_SCALE);
    this.group.scale.setScalar(BG_SCALE * grow);
    this.atmo.uUnit.value = 1 / (BG_SCALE * grow);
    this.group.visible = this.ready && !this.suppressed;
    this.atmo.uPlanetCenter.value.copy(this.group.position);
    // Clouds manage their own group transform inside the proxy group (identity here); hidden on enlarged far bodies.
    this.clouds.group.visible = grow === 1;
    this.clouds.update(cloudTime, _zero, cloudAmbient, 1);
  }

  dispose(): void {
    for (const m of [this.surface, this.water, this.shell, this.rings]) {
      if (!m) continue;
      m.geometry.dispose();
      (m.material as ShaderMaterial).dispose();
    }
    this.clouds.setBody(null, 0);
  }
}

const _zero = new Vector3();

/**
 * Low-detail globes for every body in the scaled background scene. Their
 * level-0 root chunks are generated once by a dedicated worker and also
 * handed to the local terrain cache (`onRoot`), so activating a body starts
 * from exactly the mesh its proxy showed.
 */
export class BodyProxies {
  readonly group = new Group();
  readonly proxies = new Map<BodyId, BodyProxy>();
  readonly light: ProxyLighting = {
    sunColor: new Color(5, 5, 5),
    hemiSky: new Color(0.1, 0.1, 0.1),
    hemiGround: new Color(0.1, 0.1, 0.1),
    hemiUp: new Vector3(0, 1, 0),
    cloudAmbient: new Color(0.02, 0.022, 0.03),
  };
  onRoot: ((d: ChunkData) => void) | null = null;
  private pending = 0;
  private disposed = false;

  /** Release the root worker once no job is outstanding (all roots built, or retries exhausted). */
  private finishRoots(): void {
    if (this.pending === 0 && this.backend) this.backend.dispose();
  }

  constructor(
    scene: Scene,
    private readonly backend: ChunkBackend | null,
    private readonly aerialSteps: number,
    private readonly skySteps: number,
    cloudQuality: number,
    /** Bodies to show (default: the bodies the game plays). */
    ids: readonly BodyId[] = BODY_IDS,
  ) {
    scene.add(this.group);
    // Stars are drawn by Space; giants are smooth globes built here; the rest come from terrain roots.
    const shown = ids.filter((id) => BODIES[id].kind !== 'star');
    for (const id of shown) {
      const p = new BodyProxy(BODIES[id], cloudQuality);
      this.proxies.set(id, p);
      this.group.add(p.group);
      if (BODIES[id].explore === 'zone') p.buildGiant(aerialSteps, skySteps, this.light);
    }
    const terrainIds = shown.filter((id) => BODIES[id].explore !== 'zone');
    if (backend) {
      const reqs: { id: BodyId; face: number }[] = [];
      for (const id of terrainIds) for (let f = 0; f < 6; f++) reqs.push({ id, face: f });
      const attempts = new Map<number, number>();
      const post = (i: number) => {
        const r = reqs[i - 1];
        backend.post(i, { key: chunkKey(r.face, 0, 0, 0), bodyId: r.id, face: r.face, level: 0, x: 0, y: 0, priority: 0 }, 0);
      };
      backend.onResult = (jobId, data, err) => {
        this.pending--;
        if (!data) {
          // Retry with back-off (e.g. a dataset that failed to download): a body
          // must not lose its proxy for the session over one transient failure.
          const n = (attempts.get(jobId) ?? 0) + 1;
          attempts.set(jobId, n);
          if (n === 1 || n === 6) console.error('Proxy root generation failed', err);
          if (n < 6 && !this.disposed) {
            this.pending++;
            setTimeout(() => (this.disposed ? (this.pending--, this.finishRoots()) : post(jobId)), 2000 * 2 ** (n - 1));
          }
        } else {
          this.addRoot(data);
        }
        this.finishRoots();
      };
      reqs.forEach((_, i) => {
        this.pending++;
        post(i + 1);
      });
      this.finishRoots(); // nothing to generate (e.g. only giants): release the worker now
    }
  }

  /** Accept a level-0 root (from the proxy worker or the local terrain). */
  addRoot(d: ChunkData): void {
    if (d.level !== 0) return;
    const p = this.proxies.get(d.bodyId);
    if (!p || p.ready || p.roots.has(d.key)) return;
    p.roots.set(d.key, d);
    this.onRoot?.(d);
    if (p.roots.size === 6) p.build(this.aerialSteps, this.skySteps, this.light);
  }

  setCloudQuality(q: number): void {
    for (const p of this.proxies.values()) p.clouds.setBody(p.def, q);
  }

  get readyCount(): number {
    let n = 0;
    for (const p of this.proxies.values()) if (p.ready) n++;
    return n;
  }

  update(camSys: Vector3, suppressed: BodyId | null, cloudTime: number): void {
    for (const [id, p] of this.proxies) {
      p.suppressed = id === suppressed;
      p.update(camSys, cloudTime, this.light.cloudAmbient);
    }
  }

  dispose(): void {
    this.disposed = true;
    for (const p of this.proxies.values()) p.dispose();
    this.backend?.dispose();
  }
}
