import { describe, expect, it } from 'vitest';
import { AbilitySounds, type AudioBus } from '../src/audio/abilitySounds';

/** A minimal stand-in for the Web Audio graph: records node creation, starts and stops. */
function fakeBus() {
  const log: string[] = [];
  const param = () => ({ value: 0, setValueAtTime: () => log.push('set'), linearRampToValueAtTime: () => log.push('ramp'), exponentialRampToValueAtTime: () => log.push('ramp') });
  const node = (kind: string) => ({ kind, connect: () => {}, disconnect: () => {}, start: () => log.push(`start:${kind}`), stop: () => log.push(`stop:${kind}`), gain: param(), frequency: param(), Q: param(), type: '', buffer: null, loop: false });
  const ctx = {
    currentTime: 0,
    createBufferSource: () => node('noise'),
    createBiquadFilter: () => node('filter'),
    createGain: () => node('gain'),
    createOscillator: () => node('osc'),
  };
  const bus: AudioBus = { ctx: ctx as unknown as BaseAudioContext, out: node('out') as unknown as AudioNode, noise: {} as AudioBuffer };
  return { bus, log };
}

describe('power sounds', () => {
  it('is silent without a bus (until GameAudio exposes one)', () => {
    const s = new AbilitySounds(() => null);
    s.update(1 / 60, { mode: 'flight', speed: 100 });
    s.blink();
    expect(s.level).toBe(0);
  });

  it('rushes with speed in flight and at superspeed, and stops when the power ends', () => {
    const { bus, log } = fakeBus();
    const s = new AbilitySounds(() => bus);
    for (let i = 0; i < 120; i++) s.update(1 / 60, { mode: 'dash', speed: 110 });
    expect(s.level).toBeGreaterThan(0.95);
    expect(log.filter((l) => l === 'start:noise').length).toBe(1);
    // Per-frame changes are direct assignments: no automation events while it runs.
    expect(log.filter((l) => l === 'set' || l === 'ramp').length).toBe(0);
    for (let i = 0; i < 240; i++) s.update(1 / 60, null);
    expect(log).toContain('stop:noise');
    expect(s.level).toBe(0);
  });

  it('plays short cues with a few scheduled ramps each', () => {
    const { bus, log } = fakeBus();
    const s = new AbilitySounds(() => bus);
    s.blink();
    s.refuse();
    s.takeoff();
    expect(log.filter((l) => l === 'start:osc').length).toBe(3);
    expect(log.filter((l) => l === 'stop:osc').length).toBe(3);
    expect(log.filter((l) => l === 'set' || l === 'ramp').length).toBeLessThanOrEqual(15);
  });
});
