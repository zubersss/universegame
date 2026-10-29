// Synthesized Web Audio soundscape. Created only from a user gesture (the
// Play click); faded out and suspended while paused or hidden. Continuous
// layers (engine, wind, suit) glide by direct per-frame assignment; one-shot
// sounds are pooled voices (VoicePool) routed through the Mixer's buses.

import type { BodyId } from '../world/bodies';
import { Mixer, type BusName } from './Mixer';
import { VoicePool, type Voice, type VoiceStats } from './VoicePool';
import { STEPS, ambienceFor, isAirless } from './profiles';

export interface AudioFrame {
  /** Engine thrust 0..1 (0 when parked or on foot). */
  thrust: number;
  boost: boolean;
  /** Ship speed relative to the air (m/s). */
  airspeed: number;
  /** Normalized air density at the listener. */
  density: number;
  /** Listener distance to the ship (engine attenuation). */
  shipDistance: number;
  shipActive: boolean;
  onFoot: boolean;
  body: BodyId;
}

export interface AudioStats {
  state: string;
  voices: VoiceStats;
  /** Long-lived nodes (mixer, engine, wind, suit, meter). */
  persistentNodes: number;
  /** All nodes created by this module and not yet disconnected. */
  liveNodes: number;
  suit: boolean;
}

type Ctor = new () => AudioContext;

export class GameAudio {
  private ctx: AudioContext | null = null;
  private mix!: Mixer;
  private pool!: VoicePool;
  private noiseBuf!: AudioBuffer;
  private eng!: { o1: OscillatorNode; o2: OscillatorNode; lp: BiquadFilterNode; g: GainNode; hiss: BiquadFilterNode; hg: GainNode };
  private wind!: { bp: BiquadFilterNode; g: GainNode };
  private suit!: { lp: BiquadFilterNode; g: GainNode };
  private persistent: AudioNode[] = [];
  private loops: AudioScheduledSourceNode[] = [];
  private analyser: AnalyserNode | null = null;
  private meterBuf: Float32Array<ArrayBuffer> | null = null;
  private ambientTimer = 6;
  private breathTimer = 1;
  private exertion = 0;
  private suitMode = false;
  private stepCount = 0;
  private gust = 0;
  private pauseToken = 0;
  ready = false;

  /** `createContext` replaces the browser AudioContext (unit tests). */
  constructor(private readonly createContext?: () => AudioContext) {}

  /** Must be called from a user gesture. Safe to call repeatedly. */
  start(volume: number): void {
    if (this.ctx) {
      this.setVolume(volume);
      this.resume();
      return;
    }
    try {
      this.init(volume);
    } catch (err) {
      // Audio is optional: the game plays on silently.
      console.warn('Audio unavailable; playing without sound.', err);
      this.ctx = null;
      this.ready = false;
    }
  }

  private init(volume: number): void {
    let ctx: AudioContext;
    if (this.createContext) ctx = this.createContext();
    else {
      const w = globalThis as unknown as { AudioContext?: Ctor; webkitAudioContext?: Ctor };
      const Ctx = w.AudioContext ?? w.webkitAudioContext;
      if (!Ctx) return;
      ctx = new Ctx();
    }
    this.ctx = ctx;
    this.mix = new Mixer(ctx, volume);
    this.pool = new VoicePool(ctx);
    // 2 s of white noise, looped by sources.
    const len = ctx.sampleRate * 2;
    this.noiseBuf = ctx.createBuffer(1, len, ctx.sampleRate);
    const d = this.noiseBuf.getChannelData(0);
    let seed = 1;
    for (let i = 0; i < len; i++) {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      d[i] = (seed / 4294967296) * 2 - 1;
    }
    const ship = this.mix.bus('ship');
    const amb = this.mix.bus('ambience');
    // Engine: two detuned saws through a lowpass, plus a thrust hiss.
    const o1 = this.keep(ctx.createOscillator());
    const o2 = this.keep(ctx.createOscillator());
    o1.type = 'sawtooth';
    o2.type = 'sawtooth';
    o1.frequency.value = 52;
    o2.frequency.value = 52.7;
    const lp = this.keep(ctx.createBiquadFilter());
    lp.type = 'lowpass';
    lp.frequency.value = 260;
    lp.Q.value = 0.7;
    const g = this.keep(ctx.createGain());
    g.gain.value = 0;
    o1.connect(lp);
    o2.connect(lp);
    lp.connect(g);
    g.connect(ship);
    const hissSrc = this.keep(this.noiseSource(true));
    const hiss = this.keep(ctx.createBiquadFilter());
    hiss.type = 'bandpass';
    hiss.frequency.value = 900;
    hiss.Q.value = 0.8;
    const hg = this.keep(ctx.createGain());
    hg.gain.value = 0;
    hissSrc.connect(hiss);
    hiss.connect(hg);
    hg.connect(ship);
    this.eng = { o1, o2, lp, g, hiss, hg };
    // Wind: band-passed noise driven by airspeed and density.
    const wsrc = this.keep(this.noiseSource(true));
    const bp = this.keep(ctx.createBiquadFilter());
    bp.type = 'bandpass';
    bp.frequency.value = 500;
    bp.Q.value = 0.6;
    const wg = this.keep(ctx.createGain());
    wg.gain.value = 0;
    wsrc.connect(bp);
    bp.connect(wg);
    wg.connect(amb);
    this.wind = { bp, g: wg };
    // Suit: the low hush of a sealed helmet (air recycler), only on airless ground.
    const ssrc = this.keep(this.noiseSource(true));
    const slp = this.keep(ctx.createBiquadFilter());
    slp.type = 'lowpass';
    slp.frequency.value = 320;
    slp.Q.value = 0.5;
    const sg = this.keep(ctx.createGain());
    sg.gain.value = 0;
    ssrc.connect(slp);
    slp.connect(sg);
    sg.connect(amb);
    this.suit = { lp: slp, g: sg };
    for (const s of [o1, o2, hissSrc, wsrc, ssrc]) {
      s.start();
      this.loops.push(s);
    }
    this.ready = true;
  }

  private keep<T extends AudioNode>(n: T): T {
    this.persistent.push(n);
    return n;
  }

  private noiseSource(loop: boolean): AudioBufferSourceNode {
    const s = this.ctx!.createBufferSource();
    s.buffer = this.noiseBuf;
    s.loop = loop;
    return s;
  }

  setVolume(v: number): void {
    if (this.ctx) this.mix.setMaster(v);
  }

  /** Music and effects group volumes (0..1); master is `setVolume`. */
  setMix(music: number, effects: number): void {
    if (!this.ctx) return;
    this.mix.setGroup('music', music);
    this.mix.setGroup('effects', effects);
  }

  /** Fade out, then suspend the context (pause, hidden tab). */
  suspend(): void {
    const ctx = this.ctx;
    if (!ctx || ctx.state !== 'running') return;
    this.mix.fadePause(true, 0.08);
    const token = ++this.pauseToken;
    globalThis.setTimeout(() => {
      if (this.ctx === ctx && token === this.pauseToken && ctx.state === 'running') void ctx.suspend();
    }, 120);
  }

  /** Resume the context and fade back in. */
  resume(): void {
    const ctx = this.ctx;
    if (!ctx) return;
    this.pauseToken++;
    if (ctx.state === 'suspended') void ctx.resume();
    this.mix.fadePause(false, 0.15);
  }

  private get running(): boolean {
    return !!this.ctx && this.ctx.state === 'running';
  }

  /**
   * Continuous parameters are smoothed here and assigned directly. Scheduling
   * an automation event per frame (setTargetAtTime) makes every AudioParam's
   * timeline grow without bound, which leaked memory and audio-thread time.
   */
  private glide(param: AudioParam, target: number, tau: number, dt: number): void {
    const k = 1 - Math.exp(-dt / tau);
    param.value += (target - param.value) * k;
  }

  update(dt: number, f: AudioFrame): void {
    if (!this.running) return;
    this.pool.sweep(dt);
    const prof = ambienceFor(f.body);
    const airless = isAirless(f.body);
    this.suitMode = f.onFoot && airless;
    // On foot in vacuum the ship is felt, not heard: only a dull trace through the ground.
    const vac = this.suitMode ? 0.18 : 1;
    const att = (f.onFoot ? Math.max(0, 1 - f.shipDistance / 60) : 1) * vac;
    const thrust = f.shipActive ? f.thrust : 0;
    const idle = f.shipActive ? 0.05 : f.onFoot ? 0.015 : 0.02;
    const e = this.eng;
    this.glide(e.g.gain, (idle + thrust * 0.16 + (f.boost ? 0.05 : 0)) * att, 0.12, dt);
    this.glide(e.o1.frequency, 48 + thrust * 46 + (f.boost ? 18 : 0), 0.2, dt);
    this.glide(e.o2.frequency, 48.8 + thrust * 47 + (f.boost ? 18 : 0), 0.2, dt);
    this.glide(e.lp.frequency, (220 + thrust * 900 + (f.boost ? 500 : 0)) * (this.suitMode ? 0.5 : 1), 0.15, dt);
    this.glide(e.hg.gain, (thrust * 0.05 + (f.boost ? 0.04 : 0)) * att * (this.suitMode ? 0 : 1), 0.1, dt);
    this.glide(e.hiss.frequency, 700 + thrust * 1400, 0.2, dt);
    // Wind: only where there is air.
    this.gust += (Math.random() - 0.5) * dt * 0.8;
    this.gust = Math.max(-0.4, Math.min(0.4, this.gust * 0.995));
    const flow = f.onFoot ? 0.18 + this.gust * 0.3 : Math.min(1, f.airspeed / 260);
    const wv = f.density * prof.wind * (f.onFoot ? 0.06 : 0.02 + 0.2 * flow * flow);
    this.glide(this.wind.g.gain, Math.max(0, wv), 0.25, dt);
    this.glide(this.wind.bp.frequency, prof.windTone + flow * 1500, 0.3, dt);
    // Suit: helmet hush and breathing that follows exertion.
    this.exertion = Math.max(0, this.exertion - dt / 14);
    this.glide(this.suit.g.gain, this.suitMode ? 0.012 + this.exertion * 0.006 : 0, 0.4, dt);
    if (this.suitMode) {
      this.breathTimer -= dt;
      if (this.breathTimer <= 0) {
        const pace = 1 - 0.45 * this.exertion;
        this.breathTimer = (3.6 + Math.random() * 0.8) * pace;
        this.breath(pace);
      }
    } else this.breathTimer = 1.5;
    // Sparse ambient tones.
    this.ambientTimer -= dt;
    if (this.ambientTimer <= 0) {
      this.ambientTimer = prof.toneGap * (0.55 + Math.random() * 0.9);
      this.ambientTone(f.body);
    }
  }

  /** A pooled oscillator voice into a bus (null when the context is not running). */
  private tone(freq: number, type: OscillatorType, peak: number, attack: number, decay: number, bus: BusName = 'effects', delay = 0): Voice | null {
    if (!this.running) return null;
    const ctx = this.ctx!;
    const v = this.pool.voice(this.mix.bus(bus), peak, attack, decay, ctx.currentTime + delay);
    if (!v) return null;
    const o = ctx.createOscillator();
    o.type = type;
    o.frequency.value = freq;
    o.connect(v.out);
    this.pool.source(v, o);
    return v;
  }

  /** A pooled filtered-noise voice. */
  private noise(filter: BiquadFilterType, cutoff: number, q: number, peak: number, attack: number, decay: number, bus: BusName, delay = 0): Voice | null {
    if (!this.running) return null;
    const ctx = this.ctx!;
    const v = this.pool.voice(this.mix.bus(bus), peak, attack, decay, ctx.currentTime + delay);
    if (!v) return null;
    const s = this.noiseSource(false);
    const fl = this.pool.node(v, ctx.createBiquadFilter());
    fl.type = filter;
    fl.frequency.value = cutoff;
    fl.Q.value = q;
    s.connect(fl);
    fl.connect(v.out);
    this.pool.source(v, s, Math.random() * 1.5);
    return v;
  }

  private ambientTone(body: BodyId): void {
    const p = ambienceFor(body);
    const step = p.scale[Math.floor(Math.random() * p.scale.length)];
    const f = p.tonic * 2 ** (step / 12);
    this.tone(f, p.timbre, 0.028, 1.2, 5.5, 'music');
    if (Math.random() < 0.4) this.tone(f * 1.5, 'sine', 0.012, 1.8, 6, 'music');
  }

  /** One breath in a sealed helmet: a soft inhale, then a longer exhale. */
  private breath(pace: number): void {
    const lvl = 0.016 + this.exertion * 0.014;
    this.noise('bandpass', 1150, 0.9, lvl, 0.55 * pace, 0.5 * pace, 'ambience');
    this.noise('bandpass', 650, 0.8, lvl * 1.15, 0.15, 1.1 * pace, 'ambience', 1.15 * pace);
  }

  /** Suit joint servo: a short, quiet whirr. */
  private servo(): void {
    const v = this.tone(330 + Math.random() * 60, 'sawtooth', 0.01, 0.03, 0.22, 'effects');
    if (!v) return;
    const ctx = this.ctx!;
    const o = v.sources[0] as OscillatorNode;
    o.frequency.setValueAtTime(o.frequency.value, v.start);
    o.frequency.linearRampToValueAtTime(o.frequency.value * 1.4, v.start + 0.2);
    const bp = this.pool.node(v, ctx.createBiquadFilter());
    bp.type = 'bandpass';
    bp.frequency.value = 900;
    bp.Q.value = 3;
    o.disconnect();
    o.connect(bp);
    bp.connect(v.out);
  }

  footstep(body: BodyId, sprint: boolean): void {
    if (!this.running) return;
    this.stepCount++;
    if (sprint) this.exertion = Math.min(1, this.exertion + 0.05);
    const ground = STEPS[ambienceFor(body).ground];
    if (isAirless(body)) {
      // No air to carry it: the step arrives through the boots, low and dull.
      this.noise('lowpass', 260, 0.7, (sprint ? 0.1 : 0.07) * ground.level, 0.005, 0.12, 'effects');
      this.tone(55 + Math.random() * 8, 'sine', sprint ? 0.09 : 0.06, 0.006, 0.12, 'effects');
      if (this.stepCount % 4 === 0 && Math.random() < 0.5) this.servo();
      return;
    }
    this.noise(ground.filter, ground.cutoff, 1, (sprint ? 0.12 : 0.08) * ground.level, 0.005, ground.decay, 'effects');
  }

  thump(strength = 1): void {
    const v = this.tone(70, 'sine', 0.35 * strength, 0.01, 0.45, 'effects');
    if (!v) return;
    const o = v.sources[0] as OscillatorNode;
    o.frequency.setValueAtTime(70, v.start);
    o.frequency.exponentialRampToValueAtTime(28, v.start + 0.35);
  }

  /** Continuous scan feedback (call with progress 0..1 while scanning). */
  scanTick(progress: number): void {
    if (Math.random() < 0.12) this.tone(500 + progress * 900, 'sine', 0.025, 0.01, 0.08);
  }

  scanDone(): void {
    this.tone(659.3, 'sine', 0.08, 0.01, 0.35);
    this.tone(987.8, 'sine', 0.07, 0.01, 0.6, 'effects', 0.11);
  }

  collect(): void {
    this.tone(880, 'triangle', 0.09, 0.005, 0.25);
    this.tone(1320, 'sine', 0.04, 0.005, 0.4);
  }

  relay(): void {
    if (!this.running) return;
    this.mix.duck('ambience', 0.5, 2.5);
    for (const [f, d] of [[261.6, 0], [329.6, 0.12], [392, 0.24], [523.3, 0.36]] as const) this.tone(f, 'sine', 0.07, 0.3, 2.6, 'effects', d);
  }

  ui(): void {
    this.tone(1200, 'sine', 0.03, 0.003, 0.06, 'ui');
  }

  complete(): void {
    if (!this.running) return;
    this.mix.duck('ambience', 0.4, 4);
    const chord = [196, 293.7, 392, 493.9, 587.3];
    chord.forEach((f, i) => this.tone(f, 'sine', 0.06, 0.6, 4.5, 'effects', i * 0.18));
  }

  /** Node and voice counters for leak checks. */
  stats(): AudioStats | null {
    if (!this.ctx) return null;
    const voices = this.pool.snapshot();
    const persistentNodes = this.mix.nodeCount + this.persistent.length + (this.analyser ? 1 : 0);
    return { state: this.ctx.state, voices, persistentNodes, liveNodes: persistentNodes + voices.liveNodes, suit: this.suitMode };
  }

  /** Peak and RMS of the final mix right now (lazily taps an analyser). */
  meter(): { peak: number; rms: number } | null {
    if (!this.ctx) return null;
    if (!this.analyser) {
      this.analyser = this.ctx.createAnalyser();
      this.analyser.fftSize = 2048;
      this.mix.limiter.connect(this.analyser);
      this.meterBuf = new Float32Array(this.analyser.fftSize);
    }
    const b = this.meterBuf!;
    this.analyser.getFloatTimeDomainData(b);
    let peak = 0;
    let sum = 0;
    for (let i = 0; i < b.length; i++) {
      const a = Math.abs(b[i]);
      if (a > peak) peak = a;
      sum += b[i] * b[i];
    }
    return { peak, rms: Math.sqrt(sum / b.length) };
  }

  dispose(): void {
    const ctx = this.ctx;
    if (!ctx) return;
    this.pool.clear();
    for (const s of this.loops) {
      try {
        s.stop();
      } catch {
        // Already stopped.
      }
    }
    for (const n of this.persistent) n.disconnect();
    this.analyser?.disconnect();
    this.mix.dispose();
    this.persistent = [];
    this.loops = [];
    this.analyser = null;
    this.ctx = null;
    this.ready = false;
    void ctx.close().catch(() => {});
  }
}
