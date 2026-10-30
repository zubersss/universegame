// Latitude/longitude helpers for bodies with a body frame (Earth's is its real
// orientation at EPOCH). Pure: no Three.js, usable in workers.

import { sunDirFor, type BodyDef } from './bodies';
import { earthData, latLonOf, sampleCubic, sincosd, type CubicSample } from './earthData';

const RAD = 3.141592653589793 / 180;
const _la = { s: 0, c: 0 };
const _lo = { s: 0, c: 0 };

/**
 * Unit direction (system axes) of a latitude/longitude in degrees on `def`.
 * Arithmetic only (deterministic sin/cos), so site selection that starts from
 * geographic coordinates picks the same place in every thread and browser.
 */
export function geoToDir(def: BodyDef, latDeg: number, lonDeg: number): [number, number, number] {
  const f = def.frame;
  sincosd(latDeg * RAD, _la);
  sincosd(lonDeg * RAD, _lo);
  const c = _la.c;
  const x = c * _lo.c * f.meridian[0] + c * _lo.s * f.east[0] + _la.s * f.north[0];
  const y = c * _lo.c * f.meridian[1] + c * _lo.s * f.east[1] + _la.s * f.north[1];
  const z = c * _lo.c * f.meridian[2] + c * _lo.s * f.east[2] + _la.s * f.north[2];
  const l = Math.sqrt(x * x + y * y + z * z);
  return [x / l, y / l, z / l];
}

/** Latitude/longitude in degrees of a direction (need not be unit length) on `def`. Deterministic. */
export function dirToGeo(def: BodyDef, x: number, y: number, z: number): { lat: number; lon: number } {
  const l = Math.sqrt(x * x + y * y + z * z);
  const f = def.frame;
  return latLonOf(x / l, y / l, z / l, f.north, f.meridian, f.east, { lat: 0, lon: 0 });
}

/** Where the Sun stands at the zenith on `def` (bodies are static at EPOCH). */
export function subsolarPoint(def: BodyDef): { lat: number; lon: number } {
  const s = sunDirFor(def);
  return dirToGeo(def, s[0], s[1], s[2]);
}

const cs: CubicSample = { v: 0, dLon: 0, dLat: 0 };

/** Earth's data elevation (real metres above mean sea level, before infill and shore shaping); null until the data is loaded. */
export function earthElevationM(latDeg: number, lonDeg: number): number | null {
  const ed = earthData();
  return ed ? sampleCubic(ed.elevation, latDeg, lonDeg, cs).v : null;
}

/**
 * Largest seeded infill deviation from the data in real metres (mountains;
 * plains stay within tens of metres). Gameplay height = real / ELEVATION_DIVISOR.
 */
export const EARTH_INFILL_MAX_M = 900;
