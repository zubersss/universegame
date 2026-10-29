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

// stats() is compiled out of unit tests (__TEST_HOOKS__ is false); read the pool directly.
const voiceStats = (a: GameAudio) => (a as unknown as { pool: VoicePool }).pool.snapshot();

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
    const st = voiceStats(audio);
    expect(st.active).toBe(0);
    expect(st.releasing).toBe(0);
    expect(st.liveNodes).toBe(0);
    expect(st.nodesDisconnected).toBe(st.nodesCreated);
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
    expect(audio.suitMode).toBe(true);
    expect(inner(audio).suit.g.gain.value).toBeGreaterThan(0.005);
    expect((inner(audio).wind.g as unknown as { gain: { value: number } }).gain.value).toBeLessThan(1e-6);
    expect(pool.snapshot().started).toBeGreaterThanOrEqual(2);
    for (let i = 0; i < 600; i++) {
      audio.update(1 / 60, frame({ body: 'ilex', density: 1 }));
      ctx.advance(1 / 60);
    }
    expect(audio.suitMode).toBe(false);
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
    audio.dispose();
    expect(ctx.nodes.filter((n) => n !== ctx.destination).every((n) => n.disconnected)).toBe(true);
    expect(ctx.state).toBe('closed');
  });
});

describe('volume settings', () => {
  it('defaults music and effects for old settings records and clamps new ones', async () => {
    const { sanitizeSettings, DEFAULT_SETTINGS } = await import('../src/game/settings');
    const old = sanitizeSettings({ preset: 'low', volume: 0.5 });
    expect(old.music).toBe(DEFAULT_SETTINGS.music);
    expect(old.effects).toBe(DEFAULT_SETTINGS.effects);
    expect(old.volume).toBe(0.5);
    const s = sanitizeSettings({ music: 2, effects: -1 });
    expect(s.music).toBe(1);
    expect(s.effects).toBe(0);
    expect(sanitizeSettings({ music: 'loud', effects: NaN }).music).toBe(DEFAULT_SETTINGS.music);
  });
});

describe('ship layers', () => {
  it('plays mode and gear cues once per change, never per frame', () => {
    const { ctx, audio } = setup();
    const pool = (audio as unknown as { pool: VoicePool }).pool;
    const run = (n: number, over: Partial<AudioFrame>) => {
      for (let i = 0; i < n; i++) {
        audio.update(1 / 60, frame({ onFoot: false, shipActive: true, ...over }));
        ctx.advance(1 / 60);
      }
    };
    (audio as unknown as { ambientTimer: number }).ambientTimer = 1e9;
    run(60, { mode: 'LANDED', gear: 1 });
    expect(pool.snapshot().started).toBe(0);
    run(120, { mode: 'PILOTING', gear: 1 });
    const takeoff = pool.snapshot().started;
    expect(takeoff).toBe(1);
    run(120, { mode: 'PILOTING', gear: 0 });
    expect(pool.snapshot().started).toBe(takeoff + 2);
    run(120, { mode: 'CRUISING', gear: 0 });
    expect(pool.snapshot().started).toBe(takeoff + 4);
    run(600, { mode: 'CRUISING', gear: 0 });
    expect(pool.snapshot().started).toBe(takeoff + 4);
    const drone = (audio as unknown as { drone: { g: { gain: { value: number } } } }).drone;
    expect(drone.g.gain.value).toBeGreaterThan(0.015);
    run(600, { mode: 'PILOTING', gear: 0 });
    expect(drone.g.gain.value).toBeLessThan(0.001);
  });

  it('buffets in thick air at speed and not in vacuum', () => {
    const { ctx, audio } = setup();
    const buffet = (audio as unknown as { buffet: { g: { gain: { value: number } } } }).buffet;
    for (let i = 0; i < 300; i++) {
      audio.update(1 / 60, frame({ onFoot: false, shipActive: true, airspeed: 400, density: 1, mode: 'PILOTING' }));
      ctx.advance(1 / 60);
    }
    expect(buffet.g.gain.value).toBeGreaterThan(0.05);
    for (let i = 0; i < 300; i++) {
      audio.update(1 / 60, frame({ onFoot: false, shipActive: true, airspeed: 400, density: 0, mode: 'PILOTING' }));
      ctx.advance(1 / 60);
    }
    expect(buffet.g.gain.value).toBeLessThan(0.001);
  });

  it('scales touchdown with impact speed and disconnects every cue node', () => {
    const { ctx, audio } = setup();
    const pool = (audio as unknown as { pool: VoicePool }).pool;
    audio.touchdown(0.5);
    const soft = pool.active[0].peak;
    audio.touchdown(4);
    const hard = pool.active[2].peak;
    expect(hard).toBeGreaterThan(soft);
    audio.completeExtended();
    ctx.advance(20);
    expect(pool.snapshot().liveNodes).toBe(0);
  });
});

describe('creatures and discovery', () => {
  it('spatializes fauna events through equal-power panners on the creatures bus and frees them', () => {
    const { ctx, audio } = setup();
    const mix = inner(audio).mix;
    const persistent = new Set(ctx.nodes);
    audio.creature('call', 'ilex-trine', { x: 10, y: 0, z: -5 }, 0.6);
    const panners = ctx.nodes.filter((n) => n.kind === 'panner') as unknown as { panningModel: string; positionX: { value: number }; outputs: Set<MockNode> }[];
    expect(panners.length).toBeGreaterThan(0);
    for (const p of panners) {
      expect(p.panningModel).toBe('equalpower');
      expect(p.positionX.value).toBe(10);
      expect([...p.outputs]).toEqual([mix.buses.creatures.input]);
    }
    ctx.advance(10);
    expect(ctx.nodes.filter((n) => !persistent.has(n)).every((n) => n.disconnected)).toBe(true);
  });

  it('keeps fauna under their sub-cap, ignores far creatures and unknown species fall back', () => {
    const { audio } = setup();
    const pool = (audio as unknown as { pool: VoicePool }).pool;
    for (let i = 0; i < 40; i++) audio.creature('alarm', 'ilex-trine', { x: 1, y: 0, z: -3 }, 1);
    expect(pool.count('creature')).toBeLessThanOrEqual(12 + 5);
    expect(pool.snapshot().active).toBeLessThanOrEqual(32);
    const before = pool.snapshot().started;
    audio.creature('call', 'ilex-trine', { x: 0, y: 0, z: -500 }, 1);
    expect(pool.snapshot().started).toBe(before);
    const { audio: a2 } = setup();
    a2.creature('step', 'no-such-species', { x: 0, y: 0, z: -2 }, 0.5);
    expect((a2 as unknown as { pool: VoicePool }).pool.snapshot().started).toBe(1);
  });

  it('does not double the logged chime after scanDone and plays swells on the music bus', () => {
    const { ctx, audio } = setup();
    const pool = (audio as unknown as { pool: VoicePool }).pool;
    audio.scanDone();
    const n = pool.snapshot().started;
    audio.discovery('logged');
    expect(pool.snapshot().started).toBe(n);
    ctx.advance(1);
    audio.discovery('logged');
    expect(pool.snapshot().started).toBe(n + 2);
    audio.discovery('firstSpecies');
    const mix = inner(audio).mix;
    expect(ctx.reaches(pool.active.at(-1)!.out as unknown as MockNode, mix.buses.music.input as unknown as MockNode)).toBe(true);
    audio.discovery('worldComplete');
    audio.discovery('scanStart');
    ctx.advance(30);
    expect(pool.snapshot().liveNodes).toBe(0);
  });
});

describe('surface footsteps and fauna voices', () => {
  it('maps the surface under foot to a ground kind per body, falling back to the body default', async () => {
    const { groundAt, ambienceFor } = await import('../src/audio/profiles');
    const info = (o: Partial<{ biome: number; special: number; rockiness: number }>) => ({ height: 0, biome: 0, variation: 0.5, special: 0, rockiness: 0, ...o });
    expect(groundAt('ilex', info({ rockiness: 0.8 }))).toBe('rock');
    expect(groundAt('ilex', info({ special: 0.9 }))).toBe('moss');
    expect(groundAt('ilex', info({}))).toBe(ambienceFor('ilex').ground);
    expect(groundAt('vesper', info({ biome: 0.9 }))).toBe('sand');
    expect(groundAt('vesper', info({ biome: 0.1 }))).toBe('rock');
    expect(groundAt('cairn', info({ special: 0.8 }))).toBe('ice');
    expect(groundAt('cairn', info({}))).toBe('rock');
    expect(groundAt('orrin', info({ biome: 1 }))).toBe(ambienceFor('orrin').ground);
    expect(groundAt('saro', info({}))).toBe(ambienceFor('saro').ground);
  });

  it('plays a footstep for an explicit surface and frees its nodes', () => {
    const { ctx, audio } = setup();
    const pool = (audio as unknown as { pool: VoicePool }).pool;
    const n = pool.snapshot().started;
    audio.footstep('ilex', false, 'rock');
    audio.footstep('saro', true, 'salt');
    expect(pool.snapshot().started).toBeGreaterThan(n);
    ctx.advance(5);
    expect(pool.snapshot().liveNodes).toBe(0);
  });

  it('every fauna species has its own voice; fliers and floaters have no footfalls', async () => {
    const { FAUNA } = await import('../src/fauna/faunaSpecies');
    const { creatureVoice, DEFAULT_CREATURE } = await import('../src/audio/creatures');
    for (const sp of FAUNA) {
      const v = creatureVoice(sp.id);
      expect(v, sp.id).not.toBe(DEFAULT_CREATURE);
      expect(v.call.length + v.alarm.length, sp.id).toBeGreaterThan(0);
      if (sp.hover) expect(v.step, sp.id).toHaveLength(0);
      for (const l of [...v.call, ...v.alarm, ...v.step]) {
        expect(l.peak, sp.id).toBeLessThanOrEqual(0.08);
        expect(l.attack + l.decay + (l.delay ?? 0) + (l.repeat ?? 1) * (l.every ?? 0), sp.id).toBeLessThan(6);
      }
    }
  });
});
