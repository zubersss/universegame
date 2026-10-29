import { Color, MeshStandardMaterial, Vector4, type Texture } from 'three';
import { patchAerial } from '../render/Atmosphere';
import type { BodyDef, BodyId } from '../world/bodies';

/** Number of quantized morph variants (materials share one program). */
export const MORPH_LEVELS = 8;

export interface TerrainUniforms {
  uA1: { value: Color };
  uA2: { value: Color };
  uA3: { value: Color };
  uB1: { value: Color };
  uB2: { value: Color };
  uB3: { value: Color };
  uSpecial: { value: Color };
  uSpecialRough: { value: number };
  uSpecialSheen: { value: number };
  uDetail: { value: Texture | null };
  uBump: { value: number };
  uSediment: { value: Color };
  /** x = strata amount, y = strata spacing (m), z = macro variation, w = sediment amount. */
  uLook: { value: Vector4 };
  /** x = rock on peaks, y = max terrain height (m), z/w = slope rock start/end (1 - cos). */
  uLook2: { value: Vector4 };
}

/**
 * Per-body surface look (data, not code paths): how rock, strata, sediment
 * and km-scale colour variation are blended. New bodies get identity by
 * filling these in; anything left out falls back to DEFAULT_LOOK.
 */
export interface TerrainLook {
  /** Roughness of the special material (ice, glass, loam). */
  specialRough: number;
  /** 0..1: how much smoother (less bumpy) the special material is. */
  specialSheen: number;
  /** Detail bump strength multiplier. */
  bump: number;
  /** 0..1 horizontal banding on exposed rock (height-mapped, so cliffs never stretch). */
  strata: number;
  /** Strata band spacing in meters. */
  strataSpacing: number;
  /** 0..1 strength of km-scale colour variation that breaks tiling. */
  macro: number;
  /** Colour of fine sediment collecting in low, flat ground (sRGB hex). */
  sediment: number;
  /** 0..1 how much sediment covers basin floors. */
  sedimentAmount: number;
  /** 0..1 extra bare rock exposed on the highest ground. */
  peakRock: number;
  /** Slope (1 - cos of the incline) where rock starts and fully takes over. */
  rockSlope: [number, number];
}

export const DEFAULT_LOOK: TerrainLook = {
  specialRough: 0.8, specialSheen: 0, bump: 1, strata: 0.3, strataSpacing: 9, macro: 0.5,
  sediment: 0x8a7a60, sedimentAmount: 0.35, peakRock: 0.25, rockSlope: [0.16, 0.34],
};

/**
 * Looks for the current bodies until `BodyDef` carries its own (requested
 * from ATLAS). Keyed data, merged over DEFAULT_LOOK.
 */
const BODY_LOOKS: Partial<Record<BodyId, Partial<TerrainLook>>> = {
  // Chalk ridges: fine pale bedding, ochre silt in the hollows.
  ilex: { specialRough: 0.95, specialSheen: 0, bump: 1, strata: 0.45, strataSpacing: 6, macro: 0.55, sediment: 0x9c8a5c, sedimentAmount: 0.35, peakRock: 0.3 },
  // Rust mesas: strong terrace banding, pale dust settling in the lows.
  vesper: { specialRough: 0.35, specialSheen: 0.6, bump: 0.7, strata: 0.75, strataSpacing: 14, macro: 0.6, sediment: 0xc9ae88, sedimentAmount: 0.45, peakRock: 0.2 },
  // Airless regolith: faint layering, darker fines in crater floors.
  cairn: { specialRough: 0.22, specialSheen: 1, bump: 1, strata: 0.2, strataSpacing: 11, macro: 0.45, sediment: 0x6c7076, sedimentAmount: 0.4, peakRock: 0.35 },
};

export function terrainLook(def: BodyDef): TerrainLook {
  const own = (def as BodyDef & { look?: Partial<TerrainLook> }).look;
  return { ...DEFAULT_LOOK, ...BODY_LOOKS[def.id], ...own };
}

export function makeTerrainUniforms(detail: Texture): TerrainUniforms {
  return {
    uA1: { value: new Color() },
    uA2: { value: new Color() },
    uA3: { value: new Color() },
    uB1: { value: new Color() },
    uB2: { value: new Color() },
    uB3: { value: new Color() },
    uSpecial: { value: new Color() },
    uSpecialRough: { value: 0.8 },
    uSpecialSheen: { value: 0 },
    uDetail: { value: detail },
    uBump: { value: 1 },
    uSediment: { value: new Color() },
    uLook: { value: new Vector4(0, 10, 0, 0) },
    uLook2: { value: new Vector4(0, 1000, 0.16, 0.34) },
  };
}

/** Point the shared terrain uniforms at a body's palette (linear colors). */
export function setTerrainPalette(u: TerrainUniforms, def: BodyDef): void {
  const p = def.palette;
  u.uA1.value.setHex(p.a1).convertSRGBToLinear();
  u.uA2.value.setHex(p.a2).convertSRGBToLinear();
  u.uA3.value.setHex(p.a3).convertSRGBToLinear();
  u.uB1.value.setHex(p.b1).convertSRGBToLinear();
  u.uB2.value.setHex(p.b2).convertSRGBToLinear();
  u.uB3.value.setHex(p.b3).convertSRGBToLinear();
  u.uSpecial.value.setHex(p.special).convertSRGBToLinear();
  const look = terrainLook(def);
  u.uSpecialRough.value = look.specialRough;
  u.uSpecialSheen.value = look.specialSheen;
  u.uBump.value = look.bump;
  u.uSediment.value.setHex(look.sediment).convertSRGBToLinear();
  u.uLook.value.set(look.strata, Math.max(1, look.strataSpacing), look.macro, look.sedimentAmount);
  u.uLook2.value.set(look.peakRock, Math.max(1, def.maxHeight), look.rockSlope[0], look.rockSlope[1]);
}

const VERT_PARS = /* glsl */ `
attribute vec3 morphDelta;
attribute vec4 morphNormal;
attribute vec3 tileCoord;
attribute vec4 surf;
uniform float uMorph;
varying vec3 vTile;
varying vec4 vSurf;
varying vec3 vTerrainN;
`;

/**
 * Terrain albedo from the per-vertex surface attributes (biome, rockiness,
 * variation, special) and three detail samples. Shared by the terrain
 * material and the distant body proxies (which pass vec4(0.5), the detail
 * textures' mean) so both representations agree in color.
 */
export const TERRAIN_ALBEDO_GLSL = /* glsl */ `
uniform vec3 uA1, uA2, uA3, uB1, uB2, uB3, uSpecial;
vec3 terrainAlbedo(vec4 surf, vec4 dF, vec4 dM, vec4 dL, out float rockMask, out float specMask) {
  float tBiome = surf.x;
  float tRock = surf.y;
  float tVar = surf.z;
  float tSpec = surf.w;
  float macro = dL.r * 0.5 + tVar * 0.5;
  vec3 groundA = mix(uA1, uA3, smoothstep(0.3, 0.8, macro));
  vec3 groundB = mix(uB1, uB1 * 0.82, smoothstep(0.35, 0.8, macro));
  vec3 ground = mix(groundA, groundB, tBiome);
  float crack = mix(0.5, dM.g, 0.8) * 0.6 + dF.g * 0.4;
  vec3 rockC = mix(uA2, uB2, tBiome) * (0.78 + 0.32 * crack) * (0.92 + 0.16 * dL.g);
  rockMask = smoothstep(0.4, 0.62, tRock + (dM.r - 0.5) * 0.3 + (dF.g - 0.5) * 0.12);
  vec3 albedo = ground * (0.8 + 0.4 * dM.r) * (0.84 + 0.32 * dF.r) * (0.9 + 0.2 * dF.b) * (0.9 + 0.2 * dL.b);
  albedo = mix(albedo, rockC, rockMask);
  specMask = smoothstep(0.22, 0.6, tSpec + (dM.r - 0.5) * 0.35) * (1.0 - rockMask * 0.7);
  vec3 specC = uSpecial * (0.85 + 0.3 * dM.r);
  albedo = mix(albedo, specC, specMask);
  albedo *= mix((0.74 + 0.52 * tVar) * (0.86 + 0.28 * dL.r), 1.0, specMask * 0.6);
  return albedo;
}
`;

const FRAG_PARS = /* glsl */ `
${TERRAIN_ALBEDO_GLSL}
uniform float uSpecialRough, uSpecialSheen, uBump;
uniform vec3 uSediment;
uniform vec4 uLook, uLook2;
uniform sampler2D uDetail;
varying vec3 vTile;
varying vec4 vSurf;
varying vec3 vTerrainN;

vec4 triSample(vec3 p, vec3 w) {
  #ifdef TERRAIN_LOW
    // Biplanar-lite: dominant projection only.
    if (w.x > w.y && w.x > w.z) return texture2D(uDetail, p.yz);
    if (w.y > w.z) return texture2D(uDetail, p.zx);
    return texture2D(uDetail, p.xy);
  #else
    return texture2D(uDetail, p.yz) * w.x + texture2D(uDetail, p.zx) * w.y + texture2D(uDetail, p.xy) * w.z;
  #endif
}

// Km-scale variation in planet coordinates (not the 1,024 m tile frame), at two
// incommensurate scales so no repeat is visible from any height. Low: one scale.
float terrainMacro(vec3 pRel, vec3 w) {
  float m = triSample(pRel * (1.0 / 2300.0), w).r;
  #ifndef TERRAIN_LOW
    m = m * 0.55 + triSample(pRel.zxy * (1.0 / 8900.0) + 0.37, w).b * 0.45;
  #endif
  return m;
}

vec3 terrainPerturb(vec3 surf_pos, vec3 surf_norm, vec2 dHdxy, float faceDirection) {
  vec3 vSigmaX = normalize(dFdx(surf_pos.xyz));
  vec3 vSigmaY = normalize(dFdy(surf_pos.xyz));
  vec3 vN = surf_norm;
  vec3 R1 = cross(vSigmaY, vN);
  vec3 R2 = cross(vN, vSigmaX);
  float fDet = dot(vSigmaX, R1) * faceDirection;
  vec3 vGrad = sign(fDet) * (dHdxy.x * R1 + dHdxy.y * R2);
  return normalize(abs(fDet) * surf_norm - vGrad);
}
`;

/**
 * Create the terrain material variants. variants[k] renders with morph = k / MORPH_LEVELS.
 * All variants share one shader program (same cache key and code).
 */
export function createTerrainMaterials(u: TerrainUniforms, aerialSteps: number, low: boolean): MeshStandardMaterial[] {
  const mats: MeshStandardMaterial[] = [];
  for (let k = 0; k <= MORPH_LEVELS; k++) {
    const m = new MeshStandardMaterial({ color: 0xffffff, roughness: 0.9, metalness: 0 });
    const morph = { value: k / MORPH_LEVELS };
    if (low) m.defines = { TERRAIN_LOW: '' };
    patchAerial(
      m,
      aerialSteps,
      (shader) => {
        Object.assign(shader.uniforms, u, { uMorph: morph });
        shader.vertexShader = shader.vertexShader
          .replace('#include <common>', `#include <common>\n${VERT_PARS}`)
          .replace(
            '#include <beginnormal_vertex>',
            `vec3 objectNormal = normalize(mix(normal, morphNormal.xyz, uMorph));
            #ifdef USE_TANGENT
              vec3 objectTangent = vec3( tangent.xyz );
            #endif`,
          )
          .replace(
            '#include <begin_vertex>',
            `vec3 transformed = position + morphDelta * uMorph;
            vTile = tileCoord + morphDelta * uMorph;
            vSurf = surf;
            vTerrainN = objectNormal;`,
          );
        shader.fragmentShader = shader.fragmentShader
          .replace('#include <common>', `#include <common>\n${FRAG_PARS}`)
          .replace(
            '#include <map_fragment>',
            `#include <map_fragment>
            vec3 tN = normalize(vTerrainN);
            vec3 tw = pow(abs(tN), vec3(6.0));
            tw /= (tw.x + tw.y + tw.z);
            float viewDist = length(vViewPosition);
            float fineW = 1.0 - smoothstep(35.0, 140.0, viewDist);
            vec4 dF = mix(vec4(0.5), triSample(vTile * 0.25, tw), fineW); // 4 m tiles, near only
            #ifdef TERRAIN_LOW
              vec4 dM = triSample(vTile * 0.0625, tw);                    // 16 m tiles
              vec4 dL = vec4(0.5);
            #else
              vec4 dM = triSample(vTile * 0.0625, tw);                    // 16 m tiles
              vec4 dL = triSample(vTile * 0.0078125, tw);                 // 128 m tiles
            #endif
            // Planet frame: local up, slope and height for material zones.
            vec3 pRel = vAtmoWorld - uPlanetCenter;
            float pR = length(pRel);
            vec3 pUp = pRel / pR;
            float hN = clamp((pR - uPlanetRadius) / uLook2.y, 0.0, 1.0);
            float slope = 1.0 - dot(tN, pUp);
            vec3 uw = pow(abs(pUp), vec3(8.0));
            uw /= (uw.x + uw.y + uw.z);
            // Macro variation fades out where the distant proxies (no macro) take over.
            float macro = (terrainMacro(pRel, uw) - 0.5) * uLook.z * (1.0 - smoothstep(25000.0, 90000.0, viewDist));
            vec4 tS = vSurf;
            tS.z = clamp(tS.z + macro * 0.9, 0.0, 1.0);
            float slopeRock = smoothstep(uLook2.z, uLook2.w, slope + (dM.r - 0.5) * 0.08);
            float peak = smoothstep(0.55, 0.95, hN + (dL.r - 0.5) * 0.25) * uLook2.x;
            tS.y = max(tS.y, max(slopeRock, peak));
            float rockMask, specMask;
            vec3 albedo = terrainAlbedo(tS, dF, dM, dL, rockMask, specMask);
            // Strata in height space: horizontal bands on every cliff, antialiased away.
            float sPh = (pR - uPlanetRadius) / uLook.y + (dM.g - 0.5) * 0.6 + macro * 3.0;
            float sAA = 1.0 - smoothstep(0.25, 0.7, fwidth(sPh));
            float band = sin(sPh * 6.2831853) * 0.65 + sin(sPh * 15.71 + 1.3) * 0.35;
            float strata = band * uLook.x * rockMask * sAA;
            albedo *= 1.0 + 0.22 * strata;
            // Sediment collects on low, flat ground (and fills the flattest hollows).
            float flat = 1.0 - smoothstep(0.015, 0.09, slope);
            float low = 1.0 - smoothstep(0.08, 0.45, hN + (dL.g - 0.5) * 0.2 + macro * 0.3);
            float sed = clamp(flat * low * uLook.w * (0.75 + 0.5 * dM.b), 0.0, 1.0) * (1.0 - rockMask) * (1.0 - specMask);
            albedo = mix(albedo, uSediment * (0.86 + 0.28 * dF.r) * (0.9 + 0.2 * dL.r), sed);
            // Broad tonal drift on everything (sun-bleached vs. shadowed ground at km scale).
            albedo *= 1.0 + macro * 0.35;
            diffuseColor.rgb = albedo;`,
          )
          .replace(
            '#include <roughnessmap_fragment>',
            `float roughnessFactor = mix(mix(mix(0.92, 0.78, rockMask), 0.97, sed), uSpecialRough, specMask);`,
          )
          .replace(
            '#include <normal_fragment_maps>',
            `#include <normal_fragment_maps>
            {
              // Detail normals: fine bump near only, medium bump fades with distance;
              // rock is rougher, sediment smoother, strata step the cliff faces.
              float midW = 1.0 - smoothstep(300.0, 1500.0, viewDist);
              float relief = uBump * (1.0 + 0.6 * rockMask) * (1.0 - 0.6 * sed);
              float bh = (dF.a - 0.5) * 0.05 * relief * (1.0 - specMask * uSpecialSheen * 0.8) + (dM.a - 0.5) * 0.16 * relief * midW + strata * 0.05;
              vec2 dH = vec2(dFdx(bh), dFdy(bh));
              normal = terrainPerturb(-vViewPosition, normal, dH, faceDirection);
            }`,
          );
      },
      `terrain${low ? 'L' : ''}`,
    );
    mats.push(m);
  }
  return mats;
}
