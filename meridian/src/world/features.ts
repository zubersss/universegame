// Large surface features at their real coordinates (task W6): basins, maria,
// craters, shield volcanoes, crustal bulges, canyons and rilles, evaluated as
// smooth height profiles in real metres. Positions and sizes are reference
// values entered without a fetched source (tagged 'estimated'); the shapes are
// simplified. Arithmetic only (deterministic in every thread and browser).

import type { BodyDef, DataTag } from './bodies';
import { sincosd } from './earthData';
import { geoToDir } from './geo';

export type FeatureKind = 'crater' | 'basin' | 'mare' | 'shield' | 'bulge' | 'canyon' | 'fissures';

export interface FeatureSpec {
  kind: FeatureKind;
  name: string;
  /** Centre (canyon/fissures: unused, see path). */
  lat: number;
  lon: number;
  /** Radius in real km (canyon/fissures: half-width of the trough or field). */
  radiusKm: number;
  /** Real metres: depth for crater/basin/mare/canyon/fissures, height for shield/bulge. */
  amount: number;
  /** Canyon/fissures centre line as [lat, lon] points. */
  path?: [number, number][];
  /** Fissures: crack spacing in real km (crack width is about a third of it). */
  spacingKm?: number;
  tag: DataTag;
}

// Mars: planetocentric, east longitude. Depths/heights are relative to the
// surroundings (the profiles add up), so they are approximate shapes, not MOLA.
export const MARS_FEATURES: readonly FeatureSpec[] = [
  { kind: 'basin', name: 'Northern lowlands (Borealis)', lat: 67, lon: 208, radiusKm: 4300, amount: 4200, tag: 'estimated' },
  { kind: 'bulge', name: 'Tharsis rise', lat: 2, lon: 255, radiusKm: 2600, amount: 6000, tag: 'estimated' },
  { kind: 'shield', name: 'Olympus Mons', lat: 18.65, lon: 226.2, radiusKm: 310, amount: 21000, tag: 'estimated' },
  { kind: 'shield', name: 'Arsia Mons', lat: -8.4, lon: 239.9, radiusKm: 220, amount: 11000, tag: 'estimated' },
  { kind: 'shield', name: 'Pavonis Mons', lat: 1.5, lon: 247.5, radiusKm: 190, amount: 9000, tag: 'estimated' },
  { kind: 'shield', name: 'Ascraeus Mons', lat: 11.8, lon: 255.5, radiusKm: 230, amount: 11000, tag: 'estimated' },
  { kind: 'shield', name: 'Elysium Mons', lat: 25.0, lon: 147.0, radiusKm: 210, amount: 11500, tag: 'estimated' },
  { kind: 'shield', name: 'Apollinaris Mons', lat: -9.3, lon: 174.4, radiusKm: 150, amount: 4500, tag: 'estimated' },
  { kind: 'basin', name: 'Hellas Planitia', lat: -42.4, lon: 70.5, radiusKm: 1150, amount: 7000, tag: 'estimated' },
  { kind: 'basin', name: 'Argyre Planitia', lat: -49.7, lon: 316.0, radiusKm: 900, amount: 4500, tag: 'estimated' },
  { kind: 'basin', name: 'Isidis Planitia', lat: 12.9, lon: 87.0, radiusKm: 750, amount: 3000, tag: 'estimated' },
  { kind: 'crater', name: 'Gusev crater', lat: -14.57, lon: 175.47, radiusKm: 83, amount: 1500, tag: 'estimated' },
  { kind: 'crater', name: 'Gale crater', lat: -5.4, lon: 137.8, radiusKm: 77, amount: 4000, tag: 'estimated' },
  { kind: 'crater', name: 'Jezero crater', lat: 18.4, lon: 77.5, radiusKm: 24, amount: 500, tag: 'estimated' },
  {
    kind: 'canyon', name: 'Valles Marineris', lat: -10, lon: 290, radiusKm: 70, amount: 6000, tag: 'estimated',
    path: [[-6.5, 262], [-7.5, 272], [-8.5, 282], [-10.5, 289], [-12.5, 296], [-13.5, 302], [-14.5, 310], [-15, 318]],
  },
  {
    kind: 'canyon', name: "Ma'adim Vallis", lat: -21, lon: 177.5, radiusKm: 10, amount: 2000, tag: 'estimated',
    path: [[-28.5, 181.6], [-26.0, 180.6], [-23.5, 179.0], [-21.0, 177.5], [-18.8, 176.8], [-16.4, 176.1]],
  },
];

// Moon: selenographic, east longitude. Mare depths are the mean lowering of the
// basalt plains below the highlands.
export const MOON_FEATURES: readonly FeatureSpec[] = [
  { kind: 'mare', name: 'Oceanus Procellarum', lat: 18.4, lon: -57.4, radiusKm: 1100, amount: 1600, tag: 'estimated' },
  { kind: 'mare', name: 'Mare Imbrium', lat: 32.8, lon: -15.6, radiusKm: 570, amount: 2500, tag: 'estimated' },
  { kind: 'mare', name: 'Mare Serenitatis', lat: 28.0, lon: 17.5, radiusKm: 340, amount: 2200, tag: 'estimated' },
  { kind: 'mare', name: 'Mare Tranquillitatis', lat: 8.5, lon: 31.4, radiusKm: 430, amount: 1600, tag: 'estimated' },
  { kind: 'mare', name: 'Mare Crisium', lat: 17.0, lon: 59.1, radiusKm: 280, amount: 2800, tag: 'estimated' },
  { kind: 'mare', name: 'Mare Fecunditatis', lat: -7.8, lon: 51.3, radiusKm: 450, amount: 1400, tag: 'estimated' },
  { kind: 'mare', name: 'Mare Nectaris', lat: -15.2, lon: 35.5, radiusKm: 170, amount: 2000, tag: 'estimated' },
  { kind: 'mare', name: 'Mare Nubium', lat: -21.3, lon: -16.6, radiusKm: 360, amount: 1400, tag: 'estimated' },
  { kind: 'mare', name: 'Mare Humorum', lat: -24.4, lon: -38.6, radiusKm: 195, amount: 2000, tag: 'estimated' },
  { kind: 'mare', name: 'Mare Frigoris', lat: 56.0, lon: 1.4, radiusKm: 400, amount: 1000, tag: 'estimated' },
  { kind: 'mare', name: 'Mare Vaporum', lat: 13.3, lon: 3.6, radiusKm: 120, amount: 1000, tag: 'estimated' },
  { kind: 'basin', name: 'South Pole-Aitken basin', lat: -53, lon: 191, radiusKm: 1250, amount: 6000, tag: 'estimated' },
  { kind: 'crater', name: 'Tycho', lat: -43.3, lon: -11.2, radiusKm: 43, amount: 4800, tag: 'estimated' },
  { kind: 'crater', name: 'Copernicus', lat: 9.6, lon: -20.1, radiusKm: 47, amount: 3800, tag: 'estimated' },
  { kind: 'crater', name: 'Clavius', lat: -58.4, lon: -14.4, radiusKm: 113, amount: 3500, tag: 'estimated' },
  { kind: 'crater', name: 'Plato', lat: 51.6, lon: -9.4, radiusKm: 50, amount: 2000, tag: 'estimated' },
  { kind: 'crater', name: 'Theophilus', lat: -11.4, lon: 26.4, radiusKm: 50, amount: 4200, tag: 'estimated' },
  { kind: 'crater', name: 'Aristarchus', lat: 23.7, lon: -47.4, radiusKm: 20, amount: 2700, tag: 'estimated' },
  { kind: 'crater', name: 'Hyginus', lat: 7.8, lon: 6.3, radiusKm: 5, amount: 800, tag: 'estimated' },
  // Narrowed for play (real: about 5 km wide, 600 m deep): rim to rim about one Lunar Step (60 m).
  {
    kind: 'canyon', name: 'Rima Ariadaeus', lat: 6.4, lon: 14, radiusKm: 1.2, amount: 400, tag: 'estimated',
    path: [[5.6, 9.5], [6.0, 11.5], [6.4, 14.0], [6.8, 16.0], [7.2, 18.0]],
  },
  // Fictional detail for Lunar Step: parallel crevasses along the rille, about 55 m apart in play, crossed by the route.
  {
    kind: 'fissures', name: 'Ariadaeus crevasse field', lat: 6.4, lon: 13.95, radiusKm: 15, amount: 300, spacingKm: 2.2, tag: 'fictional',
    path: [[5.9, 11.0], [6.4, 13.95], [6.9, 16.8]],
  },
];

export const BODY_FEATURES: Readonly<Record<string, readonly FeatureSpec[]>> = { mars: MARS_FEATURES, moon: MOON_FEATURES };

interface Compiled {
  kind: FeatureKind;
  c: [number, number, number];
  /** Chord (unit sphere) at the feature radius, and its reciprocal. */
  chord: number;
  inv: number;
  /** Chord beyond which the feature has no effect. */
  reach: number;
  amount: number;
  /** Polyline vertices (unit vectors) for canyons and fissures. */
  path: [number, number, number][];
  /** Fissure spacing and width as fractions of the half-width chord. */
  spacing: number;
}

const sat = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x);
const sstep = (e0: number, e1: number, x: number) => {
  const t = sat((x - e0) / (e1 - e0));
  return t * t * (3 - 2 * t);
};
/** Smooth bump (1 - t^2)^2 on |t| < 1. */
const bump = (t: number) => (t > -1 && t < 1 ? (1 - t * t) * (1 - t * t) : 0);

/** Chord between two unit directions for an arc of `km` on a sphere of radius `rKm`. */
function chordOf(km: number, rKm: number): number {
  const half = sincosd(km / rKm / 2, { s: 0, c: 0 });
  return 2 * half.s;
}

/** Feature set compiled for a body (unit vectors in the system frame). */
export class FeatureField {
  readonly items: Compiled[];

  constructor(def: BodyDef, specs: readonly FeatureSpec[]) {
    const rKm = def.real ? def.real.radiusKm : def.radius / 1000;
    this.items = specs.map((f) => {
      const chord = chordOf(f.radiusKm, rKm);
      const reachMul = f.kind === 'crater' ? 2.2 : f.kind === 'basin' ? 1.45 : f.kind === 'mare' ? 1.1 : 1.05;
      const path = (f.path ?? []).map(([la, lo]) => geoToDir(def, la, lo));
      return {
        kind: f.kind,
        c: geoToDir(def, f.lat, f.lon),
        chord,
        inv: 1 / chord,
        reach: f.kind === 'canyon' || f.kind === 'fissures' ? chord * 1.3 : chord * reachMul,
        amount: f.amount,
        path,
        spacing: (f.spacingKm ?? f.radiusKm * 0.3) / f.radiusKm,
      };
    });
  }

  /**
   * Height contribution (real metres) at unit direction n, plus a 0..1 'mare'
   * weight (dark basalt plains) and a 0..1 'scar' weight (fresh crater walls
   * and rims, canyon walls) for shading.
   */
  sample(
    nx: number, ny: number, nz: number,
    out: { h: number; mare: number; scar: number },
    /** Seeded noise in [-1, 1] at ~1 km and ~250 m (gameplay) for meanders and crack detail (0 = straight). */
    w1 = 0,
    w2 = 0,
  ): { h: number; mare: number; scar: number } {
    let h = 0;
    let mare = 0;
    let scar = 0;
    for (let i = 0; i < this.items.length; i++) {
      const f = this.items[i];
      if (f.kind === 'canyon' || f.kind === 'fissures') {
        // Distance (chord) to the polyline; for fissures also the signed offset across it.
        let best = Infinity;
        let side = 0;
        const p = f.path;
        for (let k = 0; k + 1 < p.length; k++) {
          const a = p[k];
          const b = p[k + 1];
          const ex = b[0] - a[0], ey = b[1] - a[1], ez = b[2] - a[2];
          const wx = nx - a[0], wy = ny - a[1], wz = nz - a[2];
          const ee = ex * ex + ey * ey + ez * ez;
          let t = (wx * ex + wy * ey + wz * ez) / ee;
          t = t < 0 ? 0 : t > 1 ? 1 : t;
          const dx = wx - ex * t, dy = wy - ey * t, dz = wz - ez * t;
          const d2 = dx * dx + dy * dy + dz * dz;
          if (d2 < best) {
            best = d2;
            // Sign of the side: (e x n) . d
            const cx = ey * nz - ez * ny, cy = ez * nx - ex * nz, cz = ex * ny - ey * nx;
            side = cx * dx + cy * dy + cz * dz < 0 ? -1 : 1;
          }
        }
        const d = Math.sqrt(best);
        if (d >= f.reach * 1.4) continue;
        const sx = side * d * f.inv; // signed offset across the centre line, in half-widths
        if (f.kind === 'canyon') {
          // Meandering trough (seeded offset), width varying along it, flat floor, steep walls, low rim.
          const x0 = sx - 0.35 * w1;
          const x = (x0 < 0 ? -x0 : x0) / (1 + 0.2 * w2);
          const wall = 1 - sstep(0.5, 1.0, x);
          h += -f.amount * wall + 0.06 * f.amount * bump((x - 1.08) / 0.2);
          scar = Math.max(scar, sstep(0.4, 0.7, x) * (1 - sstep(0.95, 1.15, x)));
        } else {
          // Crevasse field: cracks roughly every `spacing` half-widths, wavering (seeded),
          // varying in width, breaking into segments, fading at the field edge.
          const x = sx < 0 ? -sx : sx;
          const u = (sx + 0.06 * w1) / f.spacing + 0.18 * w2;
          const ph = u - Math.floor(u) - 0.5; // -0.5..0.5 across each crack period
          const half = 0.11 + 0.05 * w1;
          const crack = 1 - sstep(half - 0.06, half, ph < 0 ? -ph : ph);
          const segment = sstep(-0.55, -0.25, w2 + 0.4 * w1); // gaps where the noise is low
          const field = (1 - sstep(0.8, 1.0, x)) * segment;
          h += -f.amount * crack * field;
          scar = Math.max(scar, crack * field);
        }
        continue;
      }
      const dx = nx - f.c[0], dy = ny - f.c[1], dz = nz - f.c[2];
      const d2 = dx * dx + dy * dy + dz * dz;
      if (d2 >= f.reach * f.reach) continue;
      const x = Math.sqrt(d2) * f.inv;
      switch (f.kind) {
        case 'crater': {
          // Bowl with a flat floor, a raised rim and, for large craters, a central peak.
          const bowl = x < 1 ? Math.min(0.85, 1 - x * x) : 0;
          h += -f.amount * bowl + 0.2 * f.amount * bump((x - 1) / 0.3) + (f.amount > 1500 ? 0.22 * f.amount * bump(x / 0.16) : 0);
          scar = Math.max(scar, sstep(0.55, 0.85, x) * (1 - sstep(1.1, 1.6, x)));
          break;
        }
        case 'basin': {
          // Broad flat floor, walls rising to a rim ring.
          h += -f.amount * (1 - sstep(0.55, 1.0, x)) + 0.1 * f.amount * bump((x - 1.05) / 0.3);
          break;
        }
        case 'mare': {
          // Lowered basalt plain with soft edges; dark.
          const w = 1 - sstep(0.7, 1.05, x);
          h += -f.amount * w;
          mare = Math.max(mare, 1 - sstep(0.8, 1.02, x));
          break;
        }
        case 'shield': {
          // Gentle dome, small summit caldera, basal escarpment.
          if (x < 1) {
            const s = 1 - x * x;
            h += f.amount * (0.75 * s * s + 0.25 * (1 - sstep(0.88, 0.98, x))) - 0.1 * f.amount * bump(x / 0.07);
            scar = Math.max(scar, sstep(0.86, 0.92, x) * (1 - sstep(0.96, 1.0, x)));
          }
          break;
        }
        case 'bulge': {
          if (x < 1) {
            const s = 1 - x * x;
            h += f.amount * s * s;
          }
          break;
        }
      }
    }
    out.h = h;
    out.mare = mare;
    out.scar = scar;
    return out;
  }
}
