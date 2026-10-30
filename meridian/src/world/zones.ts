// Exploration zones for bodies without walkable ground (charter section I,
// ZoneDef). Types only for now; the zone data and wind fields land with W10.
// Pure data: no Three.js, shared with the worker.

export type V3 = [number, number, number];

export interface ZonePlatform {
  /** Center in the body frame [m]. */
  center: V3;
  /** Disc radius [m] and thickness [m]; a flat collision slab facing radial up. */
  radius: number;
  thickness: number;
}

export interface ZoneHazard {
  kind: 'heat' | 'cold' | 'pressure' | 'lightning' | 'liquid';
  /** Seconds before the suit recalls the explorer to the ship. */
  timer: number;
}

export interface ZoneDef {
  /** Zone center in the body frame [m]. */
  center: V3;
  /** Horizontal radius of the zone bubble [m]. */
  radius: number;
  /** Altitudes above the body datum [m]: the floor recalls, the ceiling pushes back. */
  floorAlt: number;
  ceilingAlt: number;
  /** Wind at a body-frame position [m] written into `out` [m/s]. Pure and deterministic. */
  wind(p: V3, out: V3): V3;
  hazards: ZoneHazard[];
  platforms: ZonePlatform[];
}
