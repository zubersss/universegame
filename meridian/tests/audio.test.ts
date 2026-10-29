import { afterEach, describe, expect, it, vi } from 'vitest';
import { GameAudio, type AudioFrame } from '../src/audio/GameAudio';
import { BUS_NAMES, Mixer } from '../src/audio/Mixer';
import { VOICE_CAP, VoicePool } from '../src/audio/VoicePool';
import { MockContext, MockNode, type MockOsc } from './audioMock';

function setup(): { ctx: MockContext; audio: GameAudio } {
  const ctx = new MockContext();
  const audio = new GameAudio(() => ctx as unknown as AudioContext);
  audio.start(0.8);
  return { ctx, audio };
}

function frame(over: Partial<AudioFrame> = {}): AudioFrame {
  return { thrust: 0, boost: false, airspeed: 0, density: 1, shipDistance: 0, shipActive: false, onFoot: true, body: 'ilex', ...over };
}

// Internals reached for routing checks.
type Inner = { mix: Mixer; eng: { o1: MockNode; hg: MockNode }; wind: { g: MockNode }; suit: { g: { gain: { value: number } } } };
const inner = (a: GameAudio) => a as unknown as Inner;

afterEach(() => {
  vi.useRealTimers();
});

describe('mix buses', () => {
  it('routes every bus through master, pause fade, compressor and limiter to the destination', () => {
    const { ctx, audio } = setup();
    const mix = inner(audio).mix;
    for (const name of BUS_NAMES) {
      const b = mix.buses[name];
      expect(ctx.reaches(b.input as unknown as MockNode, mix.master as unknown as MockNode)).toBe(true);
    }
    const chain = [mix.master, mix.pause, mix.glue, mix.limiter] as unknown as MockNode[];
    for (let i = 0; i < chain.length - 1; i++) expect([...chain[i].outputs]).toEqual([chain[i + 1]]);
    expect([...chain[3].outputs]).toEqual([ctx.destination]);
  });

  it('sends each layer and cue to its own bus', () => {
    const { ctx, audio } = setup();
    const mix = inner(audio).mix;
    const bus = (n: (typeof BUS_NAMES)[number]) => mix.buses[n].input as unknown as MockNode;
    const it = inner(audio);
    expect(ctx.reaches(it.eng.o1, bus('ship'))).toBe(true);
    expect(ctx.reaches(it.eng.hg, bus('ship'))).toBe(true);
    expect(ctx.reaches(it.wind.g, bus('ambience'))).toBe(true);
    expect(ctx.reaches(it.eng.o1, bus('ambience'))).toBe(false);
    // One-shot cues: the newest voice's envelope gain is connected to the right bus.
    const lastOut = () => (audio as unknown as { pool: VoicePool }).pool.active.at(-1)!.out as unknown as MockNode;
    audio.footstep('ilex', false);
    expect(ctx.reaches(lastOut(), bus('effects'))).toBe(true);
    audio.ui();
    expect(ctx.reaches(lastOut(), bus('ui'))).toBe(true);
    audio.collect();
    expect(ctx.reaches(lastOut(), bus('effects'))).toBe(true);
    expect(ctx.reaches(lastOut(), bus('music'))).toBe(false);
  });

  it('scales music and effects buses by their group volume', () => {
    const { audio } = setup();
    const mix = inner(audio).mix;
    audio.setMix(0.5, 0.25);
    expect(mix.buses.music.gain.gain.value).toBeCloseTo(0.9 * 0.5);
    expect(mix.buses.effects.gain.gain.value).toBeCloseTo(0.9 * 0.25);
    expect(mix.buses.ship.gain.gain.value).toBeCloseTo(0.25);
    audio.setVolume(0.3);
    expect(mix.master.gain.value).toBeCloseTo(0.3);
  });
});

describe('voice pool', () => {
  it('never exceeds the cap and steals instead of dropping', () => {
    const { audio } = setup();
    const pool = (audio as unknown as { pool: VoicePool }).pool;
    for (let i = 0; i < 100; i++) audio.collect();
    const s = pool.snapshot();
    expect(s.active).toBeLessThanOrEqual(VOICE_CAP);
    expect(s.active).toBe(VOICE_CAP);
    expect(s.started).toBe(200);
    expect(s.stolen).toBe(200 - VOICE_CAP);
    expect(s.dropped).toBe(0);
  });

  it('steals the quietest voice, then the oldest among equals', () => {
    const ctx = new MockContext();
    const pool = new VoicePool(ctx as unknown as AudioContext, 4);
    const dest = ctx.createGain() as unknown as AudioNode;
    const mk = (peak: number) => {
      const v = pool.voice(dest, peak, 0.01, 2)!;
      pool.source(v, ctx.createOscillator() as unknown as OscillatorNode);
      return v;
    };
    const loud1 = mk(0.5);
    ctx.advance(0.001);
    const quiet = mk(0.01);
    ctx.advance(0.001);
    const loud2 = mk(0.5);
    const loud3 = mk(0.5);
    ctx.advance(0.1);
    mk(0.5);
    expect(pool.active.includes(quiet)).toBe(false);
    expect(quiet.stolen).toBe(true);
    // All remaining equal-peak voices: loud1 is the oldest and has decayed most.
    mk(0.5);
    expect(pool.active.includes(loud1)).toBe(false);
    expect(pool.active.includes(loud2)).toBe(true);
    expect(pool.active.includes(loud3)).toBe(true);
    expect(pool.active.length).toBe(4);
  });

  it('fades a stolen voice instead of cutting it', () => {
    const ctx = new MockContext();
    const pool = new VoicePool(ctx as unknown as AudioContext, 1);
    const dest = ctx.createGain() as unknown as AudioNode;
    const a = pool.voice(dest, 0.3, 0.01, 1)!;
    const osc = ctx.createOscillator();
    pool.source(a, osc as unknown as OscillatorNode);
    ctx.advance(0.2);
    pool.voice(dest, 0.3, 0.01, 1);
    expect(osc.stopAt).toBeGreaterThan(ctx.currentTime + 0.01);
    expect(osc.stopAt).toBeLessThan(ctx.currentTime + 0.05);
  });

  it('disconnects every node of finished and stolen voices', () => {
    const { ctx, audio } = setup();
    const persistent = new Set(ctx.nodes);
    for (let i = 0; i < 60; i++) {
      audio.footstep(i % 2 ? 'vesper' : 'cairn', i % 3 === 0);
      audio.scanTick(1);
      audio.collect();
      if (i % 10 === 0) {
        audio.relay();
        audio.thump(1);
        audio.scanDone();
      }
    }
    audio.complete();
    ctx.advance(10);
    const voiceNodes = ctx.nodes.filter((n) => !persistent.has(n));
    expect(voiceNodes.length).toBeGreaterThan(100);
    expect(voiceNodes.every((n) => n.disconnected && n.outputs.size === 0)).toBe(true);
    const st = audio.stats()!;
    expect(st.voices.active).toBe(0);
    expect(st.voices.releasing).toBe(0);
    expect(st.voices.liveNodes).toBe(0);
    expect(st.liveNodes).toBe(st.persistentNodes);
  });

  it('releases voices whose end event never fired (sweep)', () => {
    const { ctx, audio } = setup();
    const pool = (audio as unknown as { pool: VoicePool }).pool;
    audio.collect();
    for (const v of pool.active) for (const s of v.sources) s.onended = null;
    ctx.currentTime += 5;
    audio.update(1 / 60, frame());
    expect(pool.snapshot().active).toBe(0);
    expect(pool.snapshot().liveNodes).toBe(0);
  });
});

describe('no per-frame automation (A8.1)', () => {
  it('queues no automation events on long-lived params across 20,000 frames', () => {
    const { ctx, audio } = setup();
    const persistent = [...ctx.nodes];
    const before = persistent.reduce((c, n) => c + n.params().reduce((a, p) => a + p.automation, 0), 0);
    const pool = (audio as unknown as { pool: VoicePool }).pool;
    const bodies = ['ilex', 'vesper', 'cairn'] as const;
    for (let i = 0; i < 20000; i++) {
      const phase = Math.floor(i / 2000);
      audio.update(1 / 60, frame({
        thrust: (i % 300) / 300, boost: i % 500 < 50, airspeed: (i % 900) * 0.4, density: phase % 3 === 2 ? 0 : 1,
        shipActive: phase % 2 === 0, onFoot: phase % 2 === 1, shipDistance: 20, body: bodies[phase % 3],
      }));
      ctx.advance(1 / 60);
    }
    const after = persistent.reduce((c, n) => c + n.params().reduce((a, p) => a + p.automation, 0), 0);
    expect(after).toBe(before);
    // Event-driven voices only: ambient tones and breaths, a few per minute.
    const s = pool.snapshot();
    expect(s.started).toBeGreaterThan(5);
    expect(s.started).toBeLessThan(400);
    expect(s.liveNodes).toBeLessThan(40);
    // Continuous layers really moved (assigned directly).
    expect((inner(audio).eng.o1 as unknown as MockOsc).frequency.directSets).toBeGreaterThan(1000);
  });
});

describe('pause, suit mode and failure', () => {
  it('fades out before suspending and fades back in on resume', () => {
    vi.useFakeTimers();
    const { ctx, audio } = setup();
    const mix = inner(audio).mix;
    audio.suspend();
    expect(ctx.state).toBe('running');
    expect(mix.pause.gain.value).toBe(0);
    vi.advanceTimersByTime(200);
    expect(ctx.state).toBe('suspended');
    audio.resume();
    expect(ctx.state).toBe('running');
    expect(mix.pause.gain.value).toBe(1);
    // A resume right after a suspend cancels the pending suspend.
    audio.suspend();
    audio.resume();
    vi.advanceTimersByTime(200);
    expect(ctx.state).toBe('running');
  });

  it('makes no sound and no voices while suspended', () => {
    const { ctx, audio } = setup();
    ctx.state = 'suspended';
    const n = ctx.nodes.length;
    audio.collect();
    audio.footstep('ilex', true);
    audio.update(1 / 60, frame());
    expect(ctx.nodes.length).toBe(n);
  });

  it('switches to suit sounds on airless ground: no wind, breathing, helmet hush', () => {
    const { ctx, audio } = setup();
    const pool = (audio as unknown as { pool: VoicePool }).pool;
    for (let i = 0; i < 600; i++) {
      audio.update(1 / 60, frame({ body: 'cairn', density: 0 }));
      ctx.advance(1 / 60);
    }
    expect(audio.stats()!.suit).toBe(true);
    expect(inner(audio).suit.g.gain.value).toBeGreaterThan(0.005);
    expect((inner(audio).wind.g as unknown as { gain: { value: number } }).gain.value).toBeLessThan(1e-6);
    expect(pool.snapshot().started).toBeGreaterThanOrEqual(2);
    for (let i = 0; i < 600; i++) {
      audio.update(1 / 60, frame({ body: 'ilex', density: 1 }));
      ctx.advance(1 / 60);
    }
    expect(audio.stats()!.suit).toBe(false);
    expect(inner(audio).suit.g.gain.value).toBeLessThan(0.001);
    expect((inner(audio).wind.g as unknown as { gain: { value: number } }).gain.value).toBeGreaterThan(0.01);
  });

  it('plays on silently when the AudioContext cannot be created', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const audio = new GameAudio(() => {
      throw new Error('no audio device');
    });
    expect(() => audio.start(1)).not.toThrow();
    expect(audio.ready).toBe(false);
    expect(() => {
      audio.update(1 / 60, frame());
      audio.footstep('ilex', false);
      audio.relay();
      audio.complete();
      audio.suspend();
      audio.resume();
    }).not.toThrow();
    expect(audio.stats()).toBeNull();
    expect(warn).toHaveBeenCalled();
  });

  it('disposes every node', () => {
    const { ctx, audio } = setup();
    audio.collect();
    audio.meter();
    audio.dispose();
    expect(ctx.nodes.filter((n) => n !== ctx.destination).every((n) => n.disconnected)).toBe(true);
    expect(ctx.state).toBe('closed');
  });
});
