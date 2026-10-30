import { describe, expect, it } from 'vitest';
import { Color, Scene, Vector3, type WebGLRenderer } from 'three';
import { Lighting, lightScale, starLight, starOf, type StarLight } from '../src/render/Lighting';
import { atmoUniforms } from '../src/render/Atmosphere';
import { BODIES, SUN_DIR, SYSTEM_BODY_IDS, sunDirFor, type BodyId } from '../src/world/bodies';
import { LIGHT } from '../src/game/config';

const DEG = Math.PI / 180;
const SOL = SYSTEM_BODY_IDS.sol.map((id) => BODIES[id]);
const blank = (): StarLight => ({ dir: new Vector3(), distance: 0, angularRadius: null, flux: 0 });
const center = (id: BodyId) => new Vector3(...BODIES[id].center);
const flux = (id: BodyId) => starLight(BODIES[id], new Vector3(), true, blank()).flux;

describe('starLight', () => {
  it('keeps the Quiet System on the fixed SUN_DIR at full brightness', () => {
    for (const id of SYSTEM_BODY_IDS.quiet) {
      const def = BODIES[id];
      expect(starOf(def)).toBeNull();
      for (const perBody of [true, false]) {
        for (const rel of [new Vector3(), new Vector3(def.radius + 500, 0, 0), new Vector3(4e5, -2e5, 3e5)]) {
          const l = starLight(def, rel, perBody, blank());
          expect(l.dir.toArray()).toEqual([...SUN_DIR]);
          expect(l.distance).toBe(Infinity);
          expect(l.angularRadius).toBeNull();
          expect(l.flux).toBe(1);
          expect(lightScale(l.flux)).toBe(1);
        }
      }
    }
    expect(starLight(null, new Vector3(), false, blank()).dir.toArray()).toEqual([...SUN_DIR]);
  });

  it('finds the Sun as the star of every Sol body', () => {
    for (const def of SOL) expect(starOf(def)).toBe(BODIES.sun);
  });

  it('lights a whole Sol body from sunDirFor, with its day side toward the Sun', () => {
    for (const def of SOL) {
      if (def.kind === 'star') continue;
      const v = sunDirFor(def);
      const l = starLight(def, new Vector3(), true, blank());
      expect(Math.abs(l.dir.x - v[0]), def.id).toBeLessThan(1e-12);
      expect(Math.abs(l.dir.y - v[1]), def.id).toBeLessThan(1e-12);
      expect(Math.abs(l.dir.z - v[2]), def.id).toBeLessThan(1e-12);
      expect(l.dir.dot(center(def.id)), def.id).toBeLessThan(0);
      // Every point on the body shares the direction.
      const rel = new Vector3(def.radius, -def.radius, 0.5 * def.radius);
      expect(starLight(def, rel, true, blank()).dir.toArray()).toEqual(l.dir.toArray());
    }
  });

  it('differs from the true direction by at most atan(R/d) on the surface', () => {
    const earth = BODIES.earth;
    const toSun = new Vector3(...sunDirFor(earth));
    // A terminator point is the worst case.
    const rel = new Vector3(0, 1, 0).cross(toSun).normalize().multiplyScalar(earth.radius);
    const perBody = starLight(earth, rel, true, blank()).dir.clone();
    const actual = starLight(earth, rel, false, blank()).dir.clone();
    const bound = Math.atan(earth.radius / center('earth').length());
    expect(bound / DEG).toBeCloseTo(3.1, 1);
    expect(perBody.angleTo(actual)).toBeLessThanOrEqual(bound + 1e-9);
    expect(perBody.angleTo(actual)).toBeGreaterThan(0.99 * bound);
  });

  it('points at the Sun from open space, and from the Sun as the reference', () => {
    const rel = new Vector3(2e5, -3e5, 1e5);
    const focus = center('earth').add(rel);
    const l = starLight(BODIES.earth, rel, false, blank());
    expect(l.dir.distanceTo(focus.clone().negate().normalize())).toBeLessThan(1e-12);
    expect(l.distance).toBeCloseTo(focus.length(), 3);

    const sun = BODIES.sun;
    const near = new Vector3(3e5, 1e5, -2e5);
    for (const perBody of [true, false]) {
      const s = starLight(sun, near, perBody, blank());
      expect(s.dir.distanceTo(near.clone().negate().normalize())).toBeLessThan(1e-12);
      expect(s.distance).toBeCloseTo(near.length(), 6);
      expect(s.angularRadius).toBeCloseTo(Math.asin(sun.radius / near.length()), 12);
    }
  });

  it('shows the Sun about 3.89° in radius from Earth', () => {
    const l = starLight(BODIES.earth, new Vector3(), true, blank());
    expect(l.distance / 1000).toBeCloseTo(2950, 0);
    expect(l.angularRadius! / DEG).toBeCloseTo(3.89, 2);
    expect(starLight(BODIES.mercury, new Vector3(), true, blank()).angularRadius! / DEG).toBeCloseTo(8.29, 2);
  });

  it('falls off outward by the inverse square of the real distance', () => {
    expect(flux('earth')).toBeCloseTo(1.034, 3); // 0.983 AU at the epoch
    expect(flux('neptune')).toBeCloseTo(0.00112, 5);
    const planets = SOL.filter((b) => b.kind === 'planet');
    for (let i = 1; i < planets.length; i++) expect(flux(planets[i].id), planets[i].id).toBeLessThan(flux(planets[i - 1].id));
    // With the Sun as the reference, the scaled-up focus distance gives the same flux.
    expect(starLight(BODIES.sun, center('earth'), false, blank()).flux).toBeCloseTo(flux('earth'), 9);
  });

  it('scales brightness softly and clamps it', () => {
    expect(Math.abs(lightScale(flux('earth')) - 1)).toBeLessThan(0.01);
    expect(lightScale(flux('mercury'))).toBeCloseTo(1.26, 2);
    expect(lightScale(flux('mars'))).toBeCloseTo(0.9, 2);
    expect(lightScale(flux('neptune'))).toBeCloseTo(0.361, 3);
    expect(lightScale(1e6)).toBe(LIGHT.maxScale);
    expect(lightScale(Infinity)).toBe(LIGHT.maxScale);
    expect(lightScale(1e-9)).toBe(LIGHT.minScale);
  });
});

describe('Lighting', () => {
  // No GPU work happens unless the environment map is rebuilt (allowEnvRebuild = false here).
  const make = () => new Lighting({} as WebGLRenderer, new Scene(), 1024);
  const ground = new Color(0.3, 0.25, 0.2);

  it('lights the Quiet System exactly as before', () => {
    const lt = make();
    const ilex = BODIES.ilex;
    // Focus at the local origin 120 m above Ilex; then in open space near Vesper.
    lt.update(1 / 60, new Vector3(), ilex, new Vector3(0, -ilex.radius - 120, 0), ground, true, false);
    lt.update(1 / 60, new Vector3(), BODIES.vesper, new Vector3(2e5, 0, 0), ground, false, false);
    for (const v of [lt.sunDir, atmoUniforms.uSunDir.value]) expect(v.toArray()).toEqual([...SUN_DIR]);
    expect(lt.fluxScale).toBe(1);
    expect(lt.sun.intensity).toBe(5.2);
  });

  it('slews toward a new direction, and snaps on request or for large swings', () => {
    const lt = make();
    const earth = BODIES.earth;
    // 3.2 R from Earth's center, beside the Sun line: activation swings the light about 10°.
    const rel = new Vector3(0, 1, 0).cross(new Vector3(...sunDirFor(earth))).normalize().multiplyScalar(3.2 * earth.radius);
    const c = rel.clone().negate();
    lt.update(1 / 60, new Vector3(), earth, c, ground, false, false);
    const before = lt.sunDir.clone();
    expect(before.equals(lt.star.dir)).toBe(true); // the first update snaps
    lt.update(LIGHT.slewTau, new Vector3(), earth, c, ground, true, false);
    const target = lt.star.dir.clone();
    const a0 = before.angleTo(target);
    expect(a0 / DEG).toBeGreaterThan(8);
    expect(lt.sunDir.angleTo(target) / a0).toBeCloseTo(Math.exp(-1), 1);
    expect(atmoUniforms.uSunDir.value.equals(lt.sunDir)).toBe(true);
    for (let i = 0; i < 600; i++) lt.update(1 / 60, new Vector3(), earth, c, ground, true, false);
    expect(lt.sunDir.equals(target)).toBe(true);

    // Mars is lit from about 176° away: a swing that large snaps.
    lt.update(1 / 60, new Vector3(), BODIES.mars, new Vector3(0, -BODIES.mars.radius - 50, 0), ground, true, false);
    expect(lt.sunDir.toArray()).toEqual(lt.star.dir.toArray());
    expect(lt.sun.intensity).toBeCloseTo(LIGHT.sunIntensity * lightScale(flux('mars')), 12);

    // snap() skips the slew for a small change too.
    lt.snap();
    lt.update(1 / 60, new Vector3(), earth, c, ground, false, false);
    expect(lt.sunDir.toArray()).toEqual(lt.star.dir.toArray());
    expect(lt.fluxScale).toBe(lightScale(flux('earth')));
  });

  it('lights the space around the Sun as open space', () => {
    const lt = make();
    const near = new Vector3(3e5, 0, 0);
    lt.update(1 / 60, new Vector3(), BODIES.sun, near.clone().negate(), ground, false, false);
    expect(lt.sunColor.toArray()).toEqual([1, 1, 1]);
    expect(lt.sun.intensity).toBe(LIGHT.sunIntensity * LIGHT.maxScale);
    expect(lt.sunDir.distanceTo(new Vector3(-1, 0, 0))).toBeLessThan(1e-12);
  });
});
