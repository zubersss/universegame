import { Color, MeshStandardMaterial, type Texture } from 'three';
import { patchAerial } from '../render/Atmosphere';
import type { BodyDef } from '../world/bodies';

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
  u.uSpecialRough.value = def.id === 'cairn' ? 0.22 : def.id === 'vesper' ? 0.35 : 0.95;
  u.uSpecialSheen.value = def.id === 'cairn' ? 1 : def.id === 'vesper' ? 0.6 : 0;
  u.uBump.value = def.id === 'vesper' ? 0.7 : 1;
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
  vec3 rockC = mix(uA2, uB2, tBiome) * (0.78 + 0.32 * crack);
  rockMask = smoothstep(0.4, 0.62, tRock + (dM.r - 0.5) * 0.3 + (dF.g - 0.5) * 0.12);
  // The large scale contributes only its smooth noise (r): its pebble and crack channels
  // would tile into a dotted lattice at range.
  vec3 albedo = ground * (0.8 + 0.4 * dM.r) * (0.84 + 0.32 * dF.r) * (0.9 + 0.2 * dF.b);
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
            vec3 tw = pow(abs(tN), vec3(4.0));
            tw /= (tw.x + tw.y + tw.z);
            float viewDist = length(vViewPosition);
            // Each detail scale fades out before its tiles shrink to a few pixels, where the
            // repetition would read as a lattice (vertex attributes carry the far variation).
            float fineW = 1.0 - smoothstep(35.0, 140.0, viewDist);
            float medW = 1.0 - smoothstep(250.0, 900.0, viewDist);
            vec4 dF = mix(vec4(0.5), triSample(vTile * 0.25, tw), fineW); // 4 m tiles, near only
            vec4 dM = mix(vec4(0.5), triSample(vTile * 0.0625, tw), medW); // 16 m tiles
            #ifdef TERRAIN_LOW
              vec4 dL = vec4(0.5);
            #else
              float largeW = 1.0 - smoothstep(700.0, 2000.0, viewDist);
              vec4 dL = mix(vec4(0.5), triSample(vTile * 0.0078125, tw), largeW); // 128 m tiles
            #endif
            float rockMask, specMask;
            vec3 albedo = terrainAlbedo(vSurf, dF, dM, dL, rockMask, specMask);
            diffuseColor.rgb = albedo;`,
          )
          .replace(
            '#include <roughnessmap_fragment>',
            `float roughnessFactor = mix(mix(0.92, 0.78, rockMask), uSpecialRough, specMask);`,
          )
          .replace(
            '#include <normal_fragment_maps>',
            `#include <normal_fragment_maps>
            {
              float bh = (dF.a - 0.5) * 0.05 * uBump * (1.0 - specMask * uSpecialSheen * 0.8) + (dM.a - 0.5) * 0.16 * uBump;
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
