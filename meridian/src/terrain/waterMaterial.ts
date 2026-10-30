import { Color, MeshStandardMaterial } from 'three';
import { patchAerial } from '../render/Atmosphere';

/** Shared uniforms of the liquid-surface material (one set per body). */
export interface WaterUniforms {
  uWaterTime: { value: number };
  uShallow: { value: Color };
  uDeep: { value: Color };
  /** Depth (m) over which the colour goes from shallow to deep. */
  uDepthScale: { value: number };
}

export interface LiquidLook {
  shallow: number; // sRGB hex
  deep: number;
  depthScale: number;
  roughness: number;
}

export const SEA_WATER: LiquidLook = { shallow: 0x2a8a8f, deep: 0x07223d, depthScale: 9, roughness: 0.14 };

/**
 * Liquid surface: a near-specular sheet coloured by depth (shallow shelves
 * read turquoise, open water deep blue), small analytic waves in planet
 * coordinates, a Fresnel reflection of the sky from the same scattering
 * integral as the sky pass, and the shared aerial perspective. Opaque: the
 * shoreline is the depth-tested intersection with the terrain.
 */
export function createWaterMaterial(look: LiquidLook, aerialSteps: number, low: boolean): { material: MeshStandardMaterial; uniforms: WaterUniforms } {
  const uniforms: WaterUniforms = {
    uWaterTime: { value: 0 },
    uShallow: { value: new Color(look.shallow).convertSRGBToLinear() },
    uDeep: { value: new Color(look.deep).convertSRGBToLinear() },
    uDepthScale: { value: look.depthScale },
  };
  const m = new MeshStandardMaterial({ color: 0xffffff, roughness: look.roughness, metalness: 0 });
  if (low) m.defines = { WATER_LOW: '' };
  patchAerial(
    m,
    aerialSteps,
    (shader) => {
      Object.assign(shader.uniforms, uniforms);
      shader.vertexShader = shader.vertexShader
        .replace(
          '#include <common>',
          `#include <common>
          attribute float depth;
          attribute vec3 tileCoord;
          varying float vDepth;
          varying vec3 vWaterTile;
          varying vec3 vWaterUp;`,
        )
        .replace(
          '#include <begin_vertex>',
          `#include <begin_vertex>
          vDepth = depth;
          vWaterTile = tileCoord;
          vWaterUp = normalize(normal);`,
        );
      shader.fragmentShader = shader.fragmentShader
        .replace(
          '#include <common>',
          `#include <common>
          uniform float uWaterTime, uDepthScale;
          uniform vec3 uShallow, uDeep;
          varying float vDepth;
          varying vec3 vWaterTile;
          varying vec3 vWaterUp;
          // Gradient of a few travelling waves in planet metres (world space).
          vec3 waveGrad(vec3 p, float t) {
            vec3 g = vec3(0.0);
            g += vec3(0.8, 0.1, 0.6) * cos(dot(p, vec3(0.8, 0.1, 0.6)) * 0.21 + t * 1.3) * 0.21 * 0.12;
            g += vec3(-0.3, 0.7, 0.65) * cos(dot(p, vec3(-0.3, 0.7, 0.65)) * 0.37 + t * 1.7) * 0.37 * 0.07;
            g += vec3(0.55, -0.6, 0.58) * cos(dot(p, vec3(0.55, -0.6, 0.58)) * 0.93 + t * 2.9) * 0.93 * 0.025;
            g += vec3(-0.7, -0.2, 0.68) * cos(dot(p, vec3(-0.7, -0.2, 0.68)) * 2.3 + t * 4.1) * 2.3 * 0.008;
            return g;
          }`,
        )
        .replace(
          '#include <color_fragment>',
          `#include <color_fragment>
          float wDeep = 1.0 - exp(-max(vDepth, 0.0) / uDepthScale);
          diffuseColor.rgb = mix(uShallow, uDeep, wDeep);`,
        )
        .replace(
          '#include <normal_fragment_maps>',
          `#include <normal_fragment_maps>
          vec3 wUp = normalize(vWaterUp);
          vec3 wg = waveGrad(vWaterTile, uWaterTime);
          wg -= wUp * dot(wg, wUp);
          // Waves fade with distance so far water does not shimmer.
          float wFade = 1.0 - smoothstep(150.0, 1500.0, length(vViewPosition));
          vec3 wN = normalize(wUp - wg * wFade);
          normal = normalize((viewMatrix * vec4(wN, 0.0)).xyz);`,
        )
        .replace(
          '#include <emissivemap_fragment>',
          `#include <emissivemap_fragment>
          {
            vec3 wV = normalize(vAtmoWorld - cameraPosition);
            vec3 wNr = normalize((vec4(normal, 0.0) * viewMatrix).xyz);
            vec3 wR = reflect(wV, wNr);
            wR = normalize(wR + wUp * max(0.0, -dot(wR, wUp)) * 1.02); // never below the horizon
            float cosT = clamp(dot(-wV, wNr), 0.0, 1.0);
            float fres = 0.02 + 0.98 * pow(1.0 - cosT, 5.0);
            vec3 skyR;
            #ifdef WATER_LOW
              skyR = mix(vec3(0.08, 0.12, 0.2), vec3(0.18, 0.3, 0.5), wR.y * 0.5 + 0.5) * uAtmoOn;
            #else
              vec3 rT;
              skyR = uAtmoOn > 0.5 ? atmoScatter(vAtmoWorld - uPlanetCenter + wUp * 2.0, wR, 1e9, 4, rT) : vec3(0.0);
            #endif
            totalEmissiveRadiance += fres * skyR;
          }`,
        );
    },
    `water${low ? 'L' : ''}`,
  );
  return { material: m, uniforms };
}
