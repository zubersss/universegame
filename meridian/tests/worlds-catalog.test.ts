import { describe, expect, it } from 'vitest';
import sol from '../src/data/sol.json';
import { BODIES, BODY_IDS, GENERATOR_VERSION, PLAY_SYSTEM, SOL_M2_BODIES, SOL_TRAVEL_ORDER, SYSTEM_BODY_IDS, SYSTEM_EXTENT, WORLD_SEED, isBodyId, setPlaySystem, sunDirFor } from '../src/world/bodies';
import { BELTS } from '../src/world/catalog';
import { AU_KM, EPOCH, POSITION_DIVISOR, gameRadius, moonDistance, moonOffset, systemPosition } from '../src/world/scale';
import { hashCombine } from '../src/core/rng';
import { computeSites } from '../src/world/sites';

const dist = (a: readonly number[], b: readonly number[]) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);

describe('sol.json (W1)', () => {
  it('records epoch, frame and sources, and tags every field', () => {
    expect(sol.epoch.jdTdb).toBe(EPOCH.jdTdb);
    expect(sol.epoch.iso).toBe(EPOCH.iso);
    expect(sol.sources.positions.url).toBeTruthy();
    expect(sol.sources.positions.accessed).toBeTruthy();
    const ids = sol.bodies.map((b) => b.id);
    expect(ids).toEqual(['sun', 'mercury', 'venus', 'earth', 'moon', 'mars', 'jupiter', 'europa', 'saturn', 'titan', 'uranus', 'neptune']);
    for (const b of sol.bodies) {
      for (const k of ['radiusKm', 'gravity', 'massKg', 'rotationHours', 'hasAtmosphere', 'positionKm'] as const) {
        expect(['measured', 'estimated', 'fictional'], `${b.id}.${k}`).toContain(b[k].tag);
      }
      // Unverified physical constants are never presented as measured.
      if (!b.verified) {
        const physical = b as unknown as Record<string, { tag: string } | undefined>;
        for (const k of ['radiusKm', 'gravity', 'massKg', 'rotationHours', 'hasAtmosphere', 'semiMajorAxisKm', 'luminosityW', 'effectiveTempK']) {
          if (physical[k]) expect(physical[k]!.tag, `${b.id}.${k}`).not.toBe('measured');
        }
      }
    }
    expect(sol.belts.map((b) => b.id)).toEqual(['asteroid-belt', 'kuiper-belt']);
    // Belts carry a source record (pending) and a tagged half-thickness.
    expect(sol.sources.belts.note).toMatch(/PENDING/);
    for (const b of sol.belts) expect(b.halfThicknessAu.tag).toBe('estimated');
  });

  it('has plausible heliocentric distances at the epoch (AU)', () => {
    const au = (id: string) => Math.hypot(...sol.bodies.find((b) => b.id === id)!.positionKm.value) / AU_KM;
    // Perihelion is 2026-01-03, so Earth is near 0.983 AU on 1 January.
    expect(au('earth')).toBeCloseTo(0.9833, 3);
    expect(au('mercury')).toBeGreaterThan(0.307);
    expect(au('mercury')).toBeLessThan(0.467);
    expect(au('venus')).toBeGreaterThan(0.718);
    expect(au('venus')).toBeLessThan(0.729);
    expect(au('mars')).toBeGreaterThan(1.38);
    expect(au('mars')).toBeLessThan(1.67);
    expect(au('jupiter')).toBeGreaterThan(4.95);
    expect(au('jupiter')).toBeLessThan(5.46);
    expect(au('neptune')).toBeGreaterThan(29.8);
    expect(au('neptune')).toBeLessThan(30.4);
    const e = sol.bodies.find((b) => b.id === 'earth')!.positionKm.value;
    const m = sol.bodies.find((b) => b.id === 'moon')!.positionKm.value;
    expect(dist(e, m)).toBeGreaterThan(356000);
    expect(dist(e, m)).toBeLessThan(407000);
  });
});

describe('scale.ts (W2)', () => {
  it('maps radius ÷ 40 clamped to 12–200 km', () => {
    expect(gameRadius(6371)).toBeCloseTo(159275, 6);
    expect(gameRadius(69911)).toBe(200000);
    expect(gameRadius(100)).toBe(12000);
    expect(BODIES.earth.radius).toBeCloseTo(159275, 6);
    expect(BODIES.moon.radius).toBeCloseTo(43435, 6);
    expect(BODIES.sun.radius).toBe(200000);
  });

  it('puts 1 AU at 3,000 km and keeps the ecliptic horizontal (Y up)', () => {
    expect(AU_KM * 1000 / POSITION_DIVISOR).toBeCloseTo(3_000_000, 6);
    const p = systemPosition([AU_KM, 0, 0]);
    expect(p[0]).toBeCloseTo(3_000_000, 3);
    // North ecliptic pole → +Y; +Y ecliptic → −Z (proper rotation).
    expect(systemPosition([0, 0, AU_KM])[1]).toBeCloseTo(3_000_000, 3);
    expect(systemPosition([0, AU_KM, 0])[2]).toBeCloseTo(-3_000_000, 3);
    const earthKm = Math.hypot(...BODIES.earth.center) / 1000;
    expect(earthKm).toBeGreaterThan(2900);
    expect(earthKm).toBeLessThan(3100);
  });

  it('places moons by the sqrt rule with a minimum separation, in their real direction', () => {
    const e = BODIES.earth;
    const m = BODIES.moon;
    const d = dist(e.center, m.center);
    const realKm = dist(e.real!.positionKm, m.real!.positionKm);
    expect(d).toBeCloseTo(e.radius * Math.sqrt(realKm / e.real!.radiusKm), 3);
    const off = moonOffset([1, 0, 0], 1, 1, 10);
    expect(Math.hypot(...off)).toBeCloseTo(4.5 * 11, 9);
    const rel = [0, 1, 2].map((i) => (m.real!.positionKm[i] - e.real!.positionKm[i]) / realKm);
    const dir = [0, 1, 2].map((i) => (m.center[i] - e.center[i]) / d);
    expect(dir[0]).toBeCloseTo(rel[0], 9);
    expect(dir[1]).toBeCloseTo(rel[2], 9);
    expect(dir[2]).toBeCloseTo(-rel[1], 9);
  });

  it('keeps every pair of Sol bodies outside each other’s 4R envelope', () => {
    const ids = SYSTEM_BODY_IDS.sol;
    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) {
        const a = BODIES[ids[i]];
        const b = BODIES[ids[j]];
        expect(dist(a.center, b.center), `${a.id}-${b.id}`).toBeGreaterThan(4 * (a.radius + b.radius));
      }
    }
  });
});

describe('catalog BodyDef (W2)', () => {
  it('keeps the Quiet System unchanged and playable', () => {
    expect(BODY_IDS).toEqual(['ilex', 'vesper', 'cairn']);
    expect(GENERATOR_VERSION).toBe(1);
    for (const id of BODY_IDS) {
      const d = BODIES[id];
      expect(d.system).toBe('quiet');
      expect(d.seed).toBe(hashCombine(WORLD_SEED, GENERATOR_VERSION, id));
      expect(d.real).toBeNull();
      expect(d.fiction.length).toBeGreaterThan(0);
      expect(computeSites(d).landing.dir.length).toBe(3);
    }
    expect(BODIES.ilex.center).toEqual([0, 0, 0]);
    expect(BODIES.vesper.center).toEqual([800000, 0, -600000]);
    expect(BODIES.cairn.center).toEqual([450000, 120000, 300000]);
    expect(sunDirFor(BODIES.ilex)[0]).toBeLessThan(0);
  });

  it('builds Sol bodies with real values, tags, powers and catalog-checked ids', () => {
    expect(isBodyId('earth')).toBe(true);
    expect(isBodyId('ilex')).toBe(true);
    expect(isBodyId('toString')).toBe(false);
    expect(isBodyId('pluto')).toBe(false);
    expect(isBodyId(3)).toBe(false);
    const e = BODIES.earth;
    expect(e.surface).toBe('data');
    expect(e.gravity).toBeCloseTo(9.8, 2);
    expect(e.power).toBe('skyborne-flight');
    expect(BODIES.mars.power).toBe('redline');
    expect(BODIES.moon.power).toBe('lunar-step');
    expect(BODIES.sun.kind).toBe('star');
    expect(BODIES.sun.explore).toBe('none');
    expect(BODIES.sun.real!.luminosityW).toBeCloseTo(3.828e26, -22);
    expect(BODIES.sun.real!.effectiveTempK).toBe(5772);
    expect(BODIES.jupiter.explore).toBe('zone');
    expect(BODIES.europa.real!.tags.positionKm).toBe('fictional');
    // Light comes from the Sun at the origin.
    const s = sunDirFor(e);
    const c = e.center;
    expect(s[0] * c[0] + s[1] * c[1] + s[2] * c[2]).toBeLessThan(0);
    const seeds = new Set(Object.values(BODIES).map((b) => b.seed));
    expect(seeds.size).toBe(Object.keys(BODIES).length);
    const indices = Object.values(BODIES).map((b) => b.index).sort((a, b) => a - b);
    expect(indices).toEqual(indices.map((_, i) => i));
  });

  it('labels moon placement by the rule actually applied and marks invented directions', () => {
    const rule = (moon: string) => {
      const m = BODIES[moon];
      const p = BODIES[m.parent!];
      const km = Math.hypot(...[0, 1, 2].map((i) => m.real!.positionKm[i] - p.real!.positionKm[i]));
      return moonDistance(km, p.real!.radiusKm, p.radius, m.radius).rule;
    };
    expect(rule('moon')).toBe('sqrt');
    expect(rule('europa')).toBe('minimum');
    expect(rule('titan')).toBe('minimum');
    expect(BODIES.moon.fiction.join(' ')).toMatch(/square-root rule/);
    for (const id of ['europa', 'titan']) {
      const f = BODIES[id].fiction.join(' ');
      expect(f).toMatch(/minimum separation/);
      expect(f).not.toMatch(/square-root/);
      expect(f).toMatch(/direction from its parent invented/);
      expect(BODIES[id].real!.positionSource).toMatch(/^fictional/);
    }
    expect(BODIES.moon.real!.positionSource).not.toMatch(/fictional/);
  });

  it('switches the played body set with setPlaySystem', () => {
    expect(PLAY_SYSTEM).toBe('quiet');
    expect(BODY_IDS).toEqual(['ilex', 'vesper', 'cairn']);
    expect(() => setPlaySystem([])).toThrow();
    expect(() => setPlaySystem(['earth', 'pluto'])).toThrow(/unknown/);
    expect(() => setPlaySystem(['earth', 'ilex'])).toThrow(/several systems/);
    expect(() => setPlaySystem(['earth', 'earth'])).toThrow(/duplicate/);
    expect(SOL_M2_BODIES.every((id) => BODIES[id].system === 'sol')).toBe(true);
    setPlaySystem(SOL_M2_BODIES);
    expect(PLAY_SYSTEM).toBe('sol');
    expect(BODY_IDS).toEqual(SOL_M2_BODIES);
    expect(Object.isFrozen(BODY_IDS)).toBe(true);
    setPlaySystem(SYSTEM_BODY_IDS.quiet);
    expect(PLAY_SYSTEM).toBe('quiet');
    expect(BODY_IDS).toEqual(['ilex', 'vesper', 'cairn']);
  });

  it('exports travel order, belts and the system extent', () => {
    const order = SOL_TRAVEL_ORDER.map((x) => ('body' in x ? x.body : x.belt));
    for (const id of SYSTEM_BODY_IDS.sol) expect(order).toContain(id);
    for (const b of BELTS) {
      expect(order).toContain(b.id);
      expect(b.outer).toBeGreaterThan(b.inner);
      expect(b.halfThickness).toBeGreaterThan(0);
      expect(b.real.source).toMatch(/PENDING/);
    }
    expect(BELTS[0].inner).toBeCloseTo(2.1 * 3_000_000, 3);
    expect(SYSTEM_EXTENT).toBeGreaterThan(50 * 3_000_000);
    for (const b of Object.values(BODIES)) expect(Math.hypot(...b.center)).toBeLessThan(SYSTEM_EXTENT);
  });
});
