import {
  AddEquation,
  BufferAttribute,
  BufferGeometry,
  Color,
  CustomBlending,
  FrontSide,
  Group,
  Mesh,
  OneFactor,
  ShaderMaterial,
  SphereGeometry,
  SrcAlphaFactor,
  Vector3,
  type Scene,
} from 'three';
import { BODIES, BODY_IDS, type BodyDef, type BodyId } from '../world/bodies';
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
    uSunDir: atmoUniforms.uSunDir,
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

export class BodyProxy {
  readonly group = new Group();
  readonly atmo: AtmoSet;
  surface: Mesh | null = null;
  water: Mesh | null = null;
  shell: Mesh | null = null;
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

  /** Place the proxy for a camera at system position `camSys` (double precision). */
  update(camSys: Vector3, cloudTime: number, cloudAmbient: Color): void {
    const c = this.def.center;
    this.group.position.set((c[0] - camSys.x) * BG_SCALE, (c[1] - camSys.y) * BG_SCALE, (c[2] - camSys.z) * BG_SCALE);
    this.group.scale.setScalar(BG_SCALE);
    this.group.visible = this.ready && !this.suppressed;
    this.atmo.uPlanetCenter.value.copy(this.group.position);
    // Clouds manage their own group transform inside the proxy group (identity here).
    this.clouds.update(cloudTime, _zero, cloudAmbient, 1);
  }

  dispose(): void {
    for (const m of [this.surface, this.water, this.shell]) {
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
    for (const id of ids) {
      const p = new BodyProxy(BODIES[id], cloudQuality);
      this.proxies.set(id, p);
      this.group.add(p.group);
    }
    if (backend) {
      const reqs: { id: BodyId; face: number }[] = [];
      for (const id of ids) for (let f = 0; f < 6; f++) reqs.push({ id, face: f });
      backend.onResult = (jobId, data, err) => {
        this.pending--;
        if (!data) {
          console.error('Proxy root generation failed', err);
        } else {
          this.addRoot(data);
        }
        if (this.pending === 0) backend.dispose();
      };
      reqs.forEach((r, i) => {
        this.pending++;
        backend.post(i + 1, { key: chunkKey(r.face, 0, 0, 0), bodyId: r.id, face: r.face, level: 0, x: 0, y: 0, priority: 0 }, 0);
      });
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
    for (const p of this.proxies.values()) p.dispose();
    this.backend?.dispose();
  }
}
