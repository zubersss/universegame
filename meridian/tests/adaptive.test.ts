import { describe, expect, it } from 'vitest';
import { ADAPTIVE_LEVELS, AdaptiveQuality } from '../src/render/Adaptive';

const run = (a: AdaptiveQuality, seconds: number, dt: number) => {
  let changes = 0;
  for (let t = 0; t < seconds; t += dt) if (a.frame(dt)) changes++;
  return changes;
};

describe('adaptive quality', () => {
  it('steps down on sustained slow frames with a cooldown, never per frame', () => {
    const a = new AdaptiveQuality(16.7);
    expect(run(a, 3.9, 0.025)).toBe(0); // cooldown and two slow windows not yet met
    run(a, 2.5, 0.025);
    expect(a.level).toBe(1);
    // Many more slow seconds: at most one step per 4 s cooldown.
    const changes = run(a, 12, 0.025);
    expect(changes).toBeLessThanOrEqual(3);
    expect(a.level).toBeGreaterThan(1);
    expect(a.current.resolutionScale).toBeLessThan(1);
  });

  it('degrades resolution before decorative density and distant detail', () => {
    const a = new AdaptiveQuality(16.7);
    run(a, 120, 0.05);
    expect(a.level).toBe(ADAPTIVE_LEVELS.length - 1);
    const firstProp = ADAPTIVE_LEVELS.findIndex((l) => l.propScale < 1);
    const firstSplit = ADAPTIVE_LEVELS.findIndex((l) => l.splitScale > 1);
    const minRes = ADAPTIVE_LEVELS.findIndex((l) => l.resolutionScale === 0.6);
    expect(minRes).toBeLessThan(firstProp);
    expect(firstProp).toBeLessThan(firstSplit);
  });

  it('recovers only after a long run of clearly fast frames', () => {
    const a = new AdaptiveQuality(16.7);
    run(a, 10, 0.03);
    const degraded = a.level;
    expect(degraded).toBeGreaterThan(0);
    run(a, 8, 0.008); // fast, but not yet for long enough
    expect(a.level).toBe(degraded);
    run(a, 10, 0.008);
    expect(a.level).toBe(degraded - 1);
  });

  it('ignores hitches and pauses, and holds steady near the target', () => {
    const a = new AdaptiveQuality(33.3);
    for (let i = 0; i < 2000; i++) a.frame(i % 50 === 0 ? 2.0 : 0.033);
    expect(a.level).toBe(0);
  });
});
