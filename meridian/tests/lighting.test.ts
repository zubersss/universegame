import { describe, expect, it } from 'vitest';
import { Color, Scene, Texture, Vector3, type WebGLRenderer } from 'three';
import { Lighting, lightScale, starLight, starOf, type StarLight } from '../src/render/Lighting';
import { atmoUniforms, sunTransCPU } from '../src/render/Atmosphere';
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

type Uniforms = Record<string, { value: { toArray(): number[] } }>;
const ENV_UNIFORMS = ['uUp', 'uSun', 'uZenith', 'uHorizon', 'uGround', 'uSunCol'] as const;

/** Replace the PMREM generator (GPU work) with a stub; count the environment rebuilds. */
function stubEnv(lt: Lighting): { rebuilds: number; u: Uniforms } {
  const priv = lt as unknown as { pmrem: unknown; envMat: { uniforms: Uniforms } };
  priv.pmrem = { fromScene: () => ({ texture: new Texture(), dispose() {} }), dispose() {} };
  const env = { rebuilds: 0, u: priv.envMat.uniforms };
  lt.onEnvChange = () => env.rebuilds++;
  return env;
}

/** Where the shadow-casting light actually comes from. */
const aim = (lt: Lighting) => lt.sun.position.clone().sub(lt.sun.target.position).normalize();
/** Weighted component sum, for tour digests. */
const wsum = (v: { toArray(): number[] }) => v.toArray().reduce((s, x, i) => s + x * (i + 1), 0);
/** Golden values are recorded to 12 significant digits. */
function expectGolden(actual: number[], golden: readonly number[], label: string): void {
  expect(actual.length, label).toBe(golden.length);
  actual.forEach((a, i) => expect(Math.abs(a - golden[i]), `${label}[${i}]`).toBeLessThanOrEqual(1e-11 * Math.max(1, Math.abs(golden[i]))));
}

// Quiet poses: the focus sits off the local origin (texel snapping), the body
// center where the pose puts it, the ground albedo as Game.setRef sets it.
const SUN = new Vector3(...SUN_DIR);
const E1 = SUN.clone().cross(new Vector3(0, 1, 0)).normalize();
const E2 = E1.clone().cross(SUN);
const FOCUS = new Vector3(37.25, -12.5, 5.75);
/** Unit direction from a body's center at cos(angle to SUN_DIR) = mu and azimuth az about it. */
function around(mu: number, az: number): Vector3 {
  const s = Math.sqrt(1 - mu * mu);
  return SUN.clone().multiplyScalar(mu).addScaledVector(E1, s * Math.cos(az)).addScaledVector(E2, s * Math.sin(az));
}
const albedo = (id: BodyId) => new Color().setHex(BODIES[id].palette.b1).convertSRGBToLinear();
const QUIET_POSES = {
  // Late afternoon 120 m above Ilex: reddened by the atmosphere.
  ilex: { mu: 0.2, az: 0.7, alt: 120, perBody: true },
  // Open space on Vesper's night side, beyond its activation radius (no active body).
  vesper: { mu: -0.3, az: 2.1, alt: 3.5 * BODIES.vesper.radius, perBody: false },
  // 300 m above airless Cairn, inside the penumbra past the geometric terminator.
  cairn: { mu: -Math.sqrt(1 - (BODIES.cairn.radius / (BODIES.cairn.radius + 300)) ** 2) + 0.002, az: -1.3, alt: 300, perBody: true },
} as const;

/** Recorded from the base Lighting (70f8217) at QUIET_POSES: the Quiet System lights exactly as before L6a. */
const QUIET_GOLDEN = {
  ilex: {
    sunColor: [0.731823529412, 0.472696470588, 0.337464705882],
    position: [-515.492429476, -162.948442206, -396.544759494],
    target: [37.2450825323, -12.5198788112, 5.76418911982],
    hemi: [0.2554067491, 0.511271031505, 0.61500066811],
    hemiGround: [0.0269881572114, 0.0119987480965, 0.00219816506024],
    env: {
      uUp: [0.173402359078, 0.573475179034, -0.800660877587],
      uSun: [-0.789625017154, -0.214897947707, -0.574727069448],
      uZenith: [0.2554067491, 0.511271031505, 0.61500066811],
      uHorizon: [0.486864227431, 0.658516706698, 0.72148790631],
      uGround: [0.0365774571185, 0.0158977537708, 0.0028574717932],
      uSunCol: [0.731823529412, 0.492392156863, 0.374960784314],
    },
  },
  vesper: {
    sunColor: [1, 0.96, 0.9],
    position: [-515.528697763, -162.918894454, -396.50597831],
    target: [37.2088142449, -12.4903310599, 5.80297030332],
    hemi: [0.064, 0.0704, 0.096],
    hemiGround: [0.0101041508959, 0.00610371671945, 0.00233211970075],
    env: {
      uUp: [-0.189590870784, 0.86867998953, 0.457657489292],
      uSun: [-0.789625017154, -0.214897947707, -0.574727069448],
      uZenith: [0.064, 0.0704, 0.096],
      uHorizon: [0.3874, 0.39364, 0.4186],
      uGround: [0.120810499843, 0.0729792216456, 0.0278840399003],
      uSunCol: [1, 1, 1],
    },
  },
  cairn: {
    sunColor: [0.666666666667, 0.64, 0.6],
    position: [-515.451030672, -162.975096498, -396.591671462],
    target: [37.2864813357, -12.5465331039, 5.71727715154],
    hemi: [0.064, 0.0704, 0.096],
    hemiGround: [0.000530937885371, 0.000624969098847, 0.000806353425515],
    env: {
      uUp: [0.460438517456, -0.887639897962, 0.00958035435479],
      uSun: [-0.789625017154, -0.214897947707, -0.574727069448],
      uZenith: [0.064, 0.0704, 0.096],
      uHorizon: [0.279066666667, 0.285306666667, 0.310266666667],
      uGround: [0.00623039355282, 0.0073338210579, 0.00946231060554],
      uSunCol: [0.666666666667, 0.666666666667, 0.666666666667],
    },
  },
} as const;

/** The same tour run on the base Lighting (70f8217): environment rebuilds and summed outputs. */
const QUIET_TOUR_GOLDEN = { rebuilds: 17, sun: 5049.810101126823, shadow: -2437219.427367606, hemi: 1152.9595042059336, env: 77.30463714239451 };

describe('Lighting', () => {
  // No GPU work happens unless the environment map is rebuilt (allowEnvRebuild = false, or stubEnv).
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

  it('matches the base Lighting at golden Quiet poses', () => {
    for (const id of ['ilex', 'vesper', 'cairn'] as const) {
      const p = QUIET_POSES[id];
      const g = QUIET_GOLDEN[id];
      const def = BODIES[id];
      const lt = make();
      const env = stubEnv(lt);
      const center = FOCUS.clone().addScaledVector(around(p.mu, p.az), -(def.radius + p.alt));
      lt.update(1 / 60, FOCUS.clone(), def, center, albedo(id), p.perBody, true);
      expect(env.rebuilds, id).toBe(1);
      expect(lt.sunDir.toArray(), id).toEqual([...SUN_DIR]);
      expect(lt.sun.intensity, id).toBe(5.2);
      expectGolden(lt.sun.color.toArray(), g.sunColor, `${id} sun.color`);
      expectGolden(lt.sun.position.toArray(), g.position, `${id} sun.position`);
      expectGolden(lt.sun.target.position.toArray(), g.target, `${id} sun.target`);
      expectGolden(lt.hemi.color.toArray(), g.hemi, `${id} hemi.color`);
      expectGolden(lt.hemi.groundColor.toArray(), g.hemiGround, `${id} hemi.groundColor`);
      expectGolden(lt.hemi.position.toArray(), g.env.uUp, `${id} hemi.position`);
      expect(lt.hemi.intensity, id).toBe(1.35);
      for (const k of ENV_UNIFORMS) expectGolden(env.u[k].value.toArray(), g.env[k], `${id} ${k}`);
    }
  });

  it('matches the base Lighting over a Quiet tour', () => {
    // 400 frames around each body through the terminator, from 50 m to 300 km up,
    // with throttled and undrawn frames: exercises the ambient and env timers and the env key.
    const lt = make();
    const env = stubEnv(lt);
    const d = { rebuilds: 0, sun: 0, shadow: 0, hemi: 0, env: 0 };
    lt.onEnvChange = () => {
      d.rebuilds++;
      for (const k of ENV_UNIFORMS) d.env += wsum(env.u[k].value);
    };
    for (const id of ['ilex', 'vesper', 'cairn'] as const) {
      const def = BODIES[id];
      for (let i = 0; i < 400; i++) {
        const a = (i / 400) * 2 * Math.PI;
        const dir = new Vector3(Math.cos(a), 0.3 * Math.sin(3 * a), Math.sin(a)).normalize().lerp(SUN, 0.1 * Math.sin(2 * a)).normalize();
        const alt = [50, 1500, 9000, 40000, 300000][i % 5];
        const center = FOCUS.clone().addScaledVector(dir, -(def.radius + alt));
        lt.update(i % 37 === 0 ? 0.25 : 1 / 60, FOCUS.clone(), def, center, albedo(id), alt < 2e5, i % 3 !== 0);
        expect(lt.sunDir.toArray()).toEqual([...SUN_DIR]);
        expect(aim(lt).angleTo(SUN)).toBeLessThan(1e-6);
        d.sun += wsum(lt.sun.color);
        d.shadow += wsum(lt.sun.position);
        d.hemi += wsum(lt.hemi.color) + wsum(lt.hemi.groundColor) + wsum(lt.hemi.position);
      }
    }
    expect(d.rebuilds).toBe(QUIET_TOUR_GOLDEN.rebuilds);
    for (const k of ['sun', 'shadow', 'hemi', 'env'] as const) {
      expect(Math.abs(d[k] - QUIET_TOUR_GOLDEN[k]), k).toBeLessThanOrEqual(1e-9 * Math.abs(QUIET_TOUR_GOLDEN[k]));
    }
  });

  it('slews toward a new direction, and snaps on request or for large swings', () => {
    const lt = make();
    const env = stubEnv(lt);
    const earth = BODIES.earth;
    // 3.2 R from Earth's center, beside the Sun line: activation swings the light about 10°.
    const rel = new Vector3(0, 1, 0).cross(new Vector3(...sunDirFor(earth))).normalize().multiplyScalar(3.2 * earth.radius);
    const c = rel.clone().negate();
    lt.update(1 / 60, new Vector3(), earth, c, ground, false, false);
    const before = lt.sunDir.clone();
    expect(before.equals(lt.star.dir)).toBe(true); // the first update snaps
    lt.update(LIGHT.slewTau, new Vector3(), earth, c, ground, true, true);
    const target = lt.star.dir.clone();
    const a0 = before.angleTo(target);
    expect(a0 / DEG).toBeGreaterThan(8);
    expect(lt.sunDir.angleTo(target) / a0).toBeCloseTo(Math.exp(-1), 1);
    expect(atmoUniforms.uSunDir.value.equals(lt.sunDir)).toBe(true);
    // The shadow-casting light and an environment rebuilt mid-slew follow the
    // slewed direction (what the sky shows), not the target.
    expect(aim(lt).angleTo(lt.sunDir)).toBeLessThan(1e-6);
    expect(env.rebuilds).toBe(1);
    expect(new Vector3().fromArray(env.u.uSun.value.toArray()).distanceTo(lt.sunDir)).toBeLessThan(1e-12);
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

  it('rebuilds the environment from the current light and aims the shadow light along it', () => {
    const lt = make();
    const env = stubEnv(lt);
    const texel = (2 * lt.extent) / lt.sun.shadow.mapSize.x;
    const uSun = () => new Vector3().fromArray(env.u.uSun.value.toArray());
    const check = (dir: Vector3, label: string) => {
      expect(lt.sunDir.distanceTo(dir), label).toBeLessThan(1e-12);
      expect(uSun().distanceTo(dir), label).toBeLessThan(1e-12);
      expect(aim(lt).angleTo(dir), label).toBeLessThan(1e-6);
      // The shadow box snaps to texels in light space: across the light only,
      // by at most half a texel diagonal (the focus is off the texel grid).
      const snap = lt.sun.target.position.clone().sub(FOCUS);
      expect(snap.length(), label).toBeGreaterThan(1e-3);
      expect(snap.length(), label).toBeLessThanOrEqual(texel * Math.SQRT1_2 + 1e-9);
      expect(Math.abs(snap.dot(dir)), label).toBeLessThan(1e-9);
    };
    const earth = BODIES.earth;
    const mars = BODIES.mars;
    const below = (r: number) => FOCUS.clone().add(new Vector3(0, -r, 0));
    lt.update(1 / 60, FOCUS.clone(), earth, below(earth.radius + 100), ground, true, true);
    expect(env.rebuilds).toBe(1);
    check(new Vector3(...sunDirFor(earth)), 'earth');
    // 100 m up (radial up +Y), the transmittance uses Earth's own light: mu = up · sunDirFor(earth).
    const mu = sunDirFor(earth)[1];
    lt.sunColor.toArray().forEach((v, ch) => expect(v, `earth sunColor[${ch}]`).toBeCloseTo(sunTransCPU(earth, 100, mu, ch), 9));

    // A hop to Mars: the next rebuild (env timer 1.5 s) takes Mars's light.
    lt.snap();
    for (let i = 0; i < 200; i++) lt.update(1 / 60, FOCUS.clone(), mars, below(mars.radius + 100), ground, true, true);
    expect(env.rebuilds).toBe(2);
    check(new Vector3(...sunDirFor(mars)), 'mars');

    // Around the Sun only the light direction changes the env key (no body, no up):
    // moving to another side of the Sun must still rebuild with the new direction.
    for (const p of [new Vector3(3e5, 0, 0), new Vector3(0, 3e5, 3e5)]) {
      lt.snap();
      for (let i = 0; i < 120; i++) lt.update(1 / 60, FOCUS.clone(), BODIES.sun, FOCUS.clone().sub(p), ground, false, true);
      check(p.clone().negate().normalize(), `sun ${p.toArray()}`);
    }
    expect(env.rebuilds).toBe(4);
  });
});
