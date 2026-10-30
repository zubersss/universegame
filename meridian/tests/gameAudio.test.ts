import { afterEach, describe, expect, it } from 'vitest';
import { GameAudio } from '../src/audio/GameAudio';

// Node has no Web Audio: a minimal stand-in that records the graph's connections.
interface FakeNode {
  kind: string;
  to: FakeNode[];
  connect(n: FakeNode): FakeNode;
  [k: string]: unknown;
}

function node(kind: string): FakeNode {
  const param = () => ({
    value: 0,
    setTargetAtTime(v: number) {
      this.value = v;
    },
  });
  const n: FakeNode = {
    kind,
    to: [],
    gain: param(), frequency: param(), Q: param(), threshold: param(), ratio: param(),
    connect(m: FakeNode) {
      n.to.push(m);
      return m;
    },
    start() {},
  };
  return n;
}

class FakeAudioContext {
  sampleRate = 8000;
  currentTime = 0;
  destination = node('destination');
  state = 'running';
  createDynamicsCompressor = () => node('compressor');
  createGain = () => node('gain');
  createOscillator = () => node('oscillator');
  createBiquadFilter = () => node('filter');
  createBufferSource = () => node('source');
  createBuffer = (channels: number, length: number, sampleRate: number) => {
    const data = new Float32Array(length);
    return { numberOfChannels: channels, length, sampleRate, duration: length / sampleRate, getChannelData: () => data };
  };
  resume = async () => {};
}

const g = globalThis as unknown as { window?: unknown };

describe('GameAudio effects bus', () => {
  afterEach(() => {
    delete g.window;
  });

  it('has no bus before start() (no audio context without a user gesture)', () => {
    expect(new GameAudio().bus()).toBeNull();
  });

  it('stays null where Web Audio is missing', () => {
    g.window = {};
    const a = new GameAudio();
    a.start(0.5);
    expect(a.bus()).toBeNull();
  });

  it('after start() exposes the context, the effects gain that feeds the master volume and the noise buffer', () => {
    g.window = { AudioContext: FakeAudioContext };
    const a = new GameAudio();
    a.start(0.5);
    const bus = a.bus();
    expect(bus).not.toBeNull();
    const ctx = bus!.ctx as unknown as FakeAudioContext;
    expect(ctx).toBeInstanceOf(FakeAudioContext);
    // out → master gain (the volume setting) → compressor → speakers.
    const out = bus!.out as unknown as FakeNode;
    expect(out.kind).toBe('gain');
    const master = out.to[0];
    expect(master.kind).toBe('gain');
    expect((master.gain as { value: number }).value).toBe(0.5);
    expect(master.to[0].kind).toBe('compressor');
    expect(master.to[0].to[0]).toBe(ctx.destination);
    // Shared white noise: 2 s, already filled.
    const noise = bus!.noise as unknown as ReturnType<FakeAudioContext['createBuffer']>;
    expect(noise.duration).toBe(2);
    expect(noise.getChannelData().some((v) => v !== 0)).toBe(true);
    // The same bus on every call; a repeated start() keeps the context.
    a.start(0.7);
    expect(a.bus()!.ctx).toBe(bus!.ctx);
    expect(a.bus()!.out).toBe(bus!.out);
  });
});
