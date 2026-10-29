import { describe, expect, it } from 'vitest';
import { newScanTrack, stepScanTrack, SCAN_GRACE } from '../src/game/scan';
import { Expedition } from '../src/game/Expedition';
import { validateSave } from '../src/save/SaveSystem';
import { DEFAULT_SETTINGS } from '../src/game/settings';
import { GENERATOR_VERSION, SAVE_SCHEMA_VERSION, WORLD_SEED } from '../src/world/bodies';

const HOLD = 1.2;
const dt = 0.1;

describe('scan tracking', () => {
  it('completes after the hold time, exactly once per hold', () => {
    const st = newScanTrack();
    const phases: string[] = [];
    for (let i = 0; i < 20; i++) phases.push(stepScanTrack(st, true, 'a', dt, HOLD));
    expect(phases.filter((p) => p === 'complete')).toHaveLength(1);
    expect(phases.indexOf('complete')).toBe(Math.ceil(HOLD / dt) - 1);
    expect(phases.at(-1)).toBe('done');
  });

  it('pauses (does not reset) while a moving target briefly leaves the cone', () => {
    const st = newScanTrack();
    for (let i = 0; i < 6; i++) stepScanTrack(st, true, 'a', dt, HOLD);
    const kept = st.progress;
    for (let i = 0; i < 5; i++) expect(stepScanTrack(st, true, null, dt, HOLD)).toBe('paused');
    expect(st.progress).toBeCloseTo(kept, 9);
    // Another object in the cone does not steal the scan during the grace period.
    expect(stepScanTrack(st, true, 'b', dt, HOLD)).toBe('paused');
    expect(stepScanTrack(st, true, 'a', dt, HOLD)).toBe('scanning');
    expect(st.progress).toBeCloseTo(kept + dt, 9);
    expect(st.lost).toBe(0);
  });

  it('resets after the grace period, then can switch targets', () => {
    const st = newScanTrack();
    for (let i = 0; i < 6; i++) stepScanTrack(st, true, 'a', dt, HOLD);
    let t = 0;
    let phase = '';
    while ((phase = stepScanTrack(st, true, null, dt, HOLD)) === 'paused') t += dt;
    expect(phase).toBe('idle');
    expect(t).toBeLessThanOrEqual(SCAN_GRACE + 1e-9);
    expect(st.progress).toBe(0);
    expect(stepScanTrack(st, true, 'b', dt, HOLD)).toBe('scanning');
    expect(st.id).toBe('b');
  });

  it('releasing F resets; a finished target is not rescanned while F stays held', () => {
    const st = newScanTrack();
    for (let i = 0; i < 13; i++) stepScanTrack(st, true, 'a', dt, HOLD);
    expect(st.done).toBe(true);
    expect(stepScanTrack(st, true, null, dt, HOLD)).toBe('idle');
    expect(stepScanTrack(st, true, 'a', dt, HOLD)).toBe('done');
    expect(stepScanTrack(st, false, 'a', dt, HOLD)).toBe('idle');
    expect(st).toEqual({ id: '', progress: 0, done: false, lost: 0 });
    expect(stepScanTrack(st, true, 'a', dt, HOLD)).toBe('scanning');
  });
});

describe('creature journal entries', () => {
  it('a creature scan adds one journal entry and one object, idempotently', () => {
    const e = new Expedition();
    const id = 'ilex:fauna:ilex-trine:3/45/67:0:2';
    expect(e.scan(id, 'ilex-trine')).toEqual({ newObject: true, newSpecies: true });
    expect(e.scan(id, 'ilex-trine')).toEqual({ newObject: false, newSpecies: false });
    expect(e.scan('ilex:fauna:ilex-trine:3/45/67:0:3', 'ilex-trine')).toEqual({ newObject: true, newSpecies: false });
    expect(e.state.species).toEqual(['ilex-trine']);
    expect(e.state.scanned).toHaveLength(2);
    expect(e.scan('ilex:fauna:x:0', 'ilex-unknown').newSpecies).toBe(false);
  });

  it('a state with creature entries passes save validation', () => {
    const e = new Expedition();
    e.scan('ilex:fauna:ilex-trine:3/45/67:0:2', 'ilex-trine');
    const r = validateSave({
      schema: SAVE_SCHEMA_VERSION, generator: GENERATOR_VERSION, seed: WORLD_SEED, savedAt: '2026-10-29T12:00:00.000Z', playTime: 1, mode: 'LANDED', body: 'ilex',
      ship: { sys: [1, 2, 60000], quat: [0, 0, 0, 1], vel: [0, 0, 0], gear: 1, throttle: 0 },
      player: null, cruise: null, lastSafeLanding: null, navTarget: null,
      settings: { ...DEFAULT_SETTINGS },
      expedition: e.state,
    });
    expect(r.ok ? null : r.error).toBeNull();
  });
});
