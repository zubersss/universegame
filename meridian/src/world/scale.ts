// Documented mapping from scientific values (src/data/*.json) to gameplay
// values (charter section H). Pure arithmetic, no Three.js: shared by the main
// thread and the terrain worker. Nothing here is a physical simulation: the
// system is compressed so that a flight between planets takes about a minute.

/** The one epoch at which every Sol position in src/data/sol.json is given. Bodies are static at it. */
export const EPOCH = { iso: '2026-01-01T00:00:00 TDB', jdTdb: 2461041.5 } as const;

/** Astronomical unit (IAU 2012 Resolution B2), km. */
export const AU_KM = 149597870.7;

/** Body radius: real ÷ 40, clamped to 12–200 km. */
export const RADIUS_DIVISOR = 40;
export const RADIUS_MIN_KM = 12;
export const RADIUS_MAX_KM = 200;

/** Earth's gameplay distance from the Sun for 1 AU, m. */
export const AU_GAME_M = 3_000_000;
/** Heliocentric positions: real ÷ POSITION_DIVISOR (≈ 49,866), so 1 AU → 3,000 km. */
export const POSITION_DIVISOR = (AU_KM * 1000) / AU_GAME_M;

/**
 * Terrain relief: real elevation ÷ ELEVATION_DIVISOR. Relief scaled like the
 * radius (÷ 40) would make Everest a 221 m bump on a 159 km sphere, too flat to
 * read from the ground, so relief is exaggerated 8× relative to the radius
 * (Everest ≈ 1,770 m, Olympus Mons ≈ 4,400 m above the Martian datum).
 */
export const VERTICAL_EXAGGERATION = 8;
export const ELEVATION_DIVISOR = RADIUS_DIVISOR / VERTICAL_EXAGGERATION;

/** Cruise: max speed = max(15 km/s, hop distance ÷ 45 s). */
export const CRUISE_MIN_MAX_SPEED = 15_000;
export const CRUISE_HOP_SECONDS = 45;
/** Interstellar travel is a jump sequence of about this many seconds. */
export const JUMP_SECONDS = 6;

/** Gameplay radius [m] for a real mean radius [km]. */
export function gameRadius(realRadiusKm: number): number {
  const km = Math.min(Math.max(realRadiusKm / RADIUS_DIVISOR, RADIUS_MIN_KM), RADIUS_MAX_KM);
  return km * 1000;
}

/**
 * Real J2000-ecliptic vector [km] (x vernal equinox, z north ecliptic pole) to
 * the game's system frame [m], which is Y-up: game (x, y, z) = (x, z, −y)·k.
 * This is a proper rotation (−90° about x), so handedness is preserved.
 */
export function eclipticToSystem(v: readonly number[], kmToM: number): [number, number, number] {
  return [v[0] * kmToM, v[2] * kmToM, -v[1] * kmToM];
}

/** Heliocentric real position [km] → gameplay system position [m]. */
export function systemPosition(realKm: readonly number[]): [number, number, number] {
  return eclipticToSystem(realKm, 1000 / POSITION_DIVISOR);
}

/**
 * Moons: the single position factor would put the Moon 7.7 km from Earth's
 * center, inside Earth's 159 km gameplay radius. A moon therefore keeps its
 * real direction from its parent, with distance compressed separately:
 *   d = parentGameRadius × sqrt(realDistance ÷ parentRealRadius)
 * but never closer than MOON_MIN_SEPARATION × (sum of both gameplay radii),
 * so the two bodies' 4R envelopes (gravity taper, proxy hand-off) never
 * overlap. Moon ≈ 1,240 km from Earth (sqrt rule); Europa ≈ 1,080 km from
 * Jupiter and Titan ≈ 1,190 km from Saturn (minimum applies; the sqrt rule
 * alone gives 620 and 920 km). Returned offset is in the game system frame [m].
 */
export const MOON_MIN_SEPARATION = 4.5;

export function moonOffset(
  realOffsetKm: readonly number[],
  parentRealRadiusKm: number,
  parentGameRadiusM: number,
  moonGameRadiusM: number,
): [number, number, number] {
  const len = Math.hypot(realOffsetKm[0], realOffsetKm[1], realOffsetKm[2]);
  const d = Math.max(parentGameRadiusM * Math.sqrt(len / parentRealRadiusKm), MOON_MIN_SEPARATION * (parentGameRadiusM + moonGameRadiusM));
  return eclipticToSystem(realOffsetKm, d / len);
}

/** Heliocentric distance in AU → gameplay distance from the Sun [m]. */
export function auToGame(au: number): number {
  return au * AU_GAME_M;
}

/** Gameplay cruise speed cap [m/s] for a hop of `distance` meters. */
export function cruiseMaxSpeed(distance: number): number {
  return Math.max(CRUISE_MIN_MAX_SPEED, distance / CRUISE_HOP_SECONDS);
}

/** Real elevation [m] → gameplay relief [m]. */
export function gameElevation(realMeters: number): number {
  return realMeters / ELEVATION_DIVISOR;
}

/** Contact/max-detail quadtree level for a gameplay radius: ceil(log2(2R/128)). */
export function maxLevelFor(radius: number): number {
  return Math.ceil(Math.log2((2 * radius) / 128));
}
