// Small synthesized Web Audio soundscape. Created only from a user gesture
// (the Play click); suspended while paused or hidden.

import type { BodyId } from '../world/bodies';

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

const PENTA = [0, 2, 4, 7, 9, 12, 14];

export class GameAudio {
  private ctx: AudioContext | null = null;
  private master!: GainNode;
  private sfx!: GainNode;
  private noiseBuf!: AudioBuffer;
  private eng!: { o1: OscillatorNode; o2: OscillatorNode; lp: BiquadFilterNode; g: GainNode; hiss: BiquadFilterNode; hg: GainNode };
  private wind!: { bp: BiquadFilterNode; g: GainNode };
  private ambientTimer = 6;
  private gust = 0;
  private time = 0;
  ready = false;

  /** Must be called from a user gesture. Safe to call repeatedly. */
  start(volume: number): void {
    if (this.ctx) {
      this.setVolume(volume);
      void this.ctx.resume();
      return;
    }
    const Ctx = window.AudioContext ?? (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    if (!Ctx) return;
    const ctx = new Ctx();
    this.ctx = ctx;
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -14;
    comp.ratio.value = 3;
    comp.connect(ctx.destination);
    this.master = ctx.createGain();
    this.master.gain.value = volume;
    this.master.connect(comp);
    this.sfx = ctx.createGain();
    this.sfx.gain.value = 0.9;
    this.sfx.connect(this.master);
    // 2 s of white noise, looped by sources.
    const len = ctx.sampleRate * 2;
    this.noiseBuf = ctx.createBuffer(1, len, ctx.sampleRate);
    const d = this.noiseBuf.getChannelData(0);
    let seed = 1;
    for (let i = 0; i < len; i++) {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      d[i] = (seed / 4294967296) * 2 - 1;
    }
    // Engine: two detuned saws through a lowpass, plus a thrust hiss.
    const o1 = ctx.createOscillator();
    const o2 = ctx.createOscillator();
    o1.type = 'sawtooth';
    o2.type = 'sawtooth';
    o1.frequency.value = 52;
    o2.frequency.value = 52.7;
    const lp = ctx.createBiquadFilter();
    lp.type = 'lowpass';
    lp.frequency.value = 260;
    lp.Q.value = 0.7;
    const g = ctx.createGain();
    g.gain.value = 0;
    o1.connect(lp);
    o2.connect(lp);
    lp.connect(g);
    g.connect(this.master);
    const hissSrc = this.noiseSource(true);
    const hiss = ctx.createBiquadFilter();
    hiss.type = 'bandpass';
    hiss.frequency.value = 900;
    hiss.Q.value = 0.8;
    const hg = ctx.createGain();
    hg.gain.value = 0;
    hissSrc.connect(hiss);
    hiss.connect(hg);
    hg.connect(this.master);
    o1.start();
    o2.start();
    hissSrc.start();
    this.eng = { o1, o2, lp, g, hiss, hg };
    // Wind: band-passed noise driven by airspeed and density.
    const wsrc = this.noiseSource(true);
    const bp = ctx.createBiquadFilter();
    bp.type = 'bandpass';
    bp.frequency.value = 500;
    bp.Q.value = 0.6;
    const wg = ctx.createGain();
    wg.gain.value = 0;
    wsrc.connect(bp);
    bp.connect(wg);
    wg.connect(this.master);
    wsrc.start();
    this.wind = { bp, g: wg };
    this.ready = true;
  }

  /**
   * The effects bus for sounds made elsewhere (PLAYER's ability sounds): the
   * audio context, the effects gain that feeds the master volume, and the
   * shared 2 s white-noise buffer. Null until start() has created the context.
   */
  bus(): { ctx: AudioContext; out: GainNode; noise: AudioBuffer } | null {
    return this.ctx ? { ctx: this.ctx, out: this.sfx, noise: this.noiseBuf } : null;
  }

  private noiseSource(loop: boolean): AudioBufferSourceNode {
    const s = this.ctx!.createBufferSource();
    s.buffer = this.noiseBuf;
    s.loop = loop;
    return s;
  }

  setVolume(v: number): void {
    if (this.ctx) this.master.gain.setTargetAtTime(v, this.ctx.currentTime, 0.05);
  }

  suspend(): void {
    if (this.ctx && this.ctx.state === 'running') void this.ctx.suspend();
  }

  resume(): void {
    if (this.ctx && this.ctx.state === 'suspended') void this.ctx.resume();
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
    if (!this.ctx || this.ctx.state !== 'running') return;
    this.time += dt;
    const att = f.onFoot ? Math.max(0, 1 - f.shipDistance / 60) : 1;
    const thrust = f.shipActive ? f.thrust : 0;
    const idle = f.shipActive ? 0.05 : f.onFoot ? 0.015 : 0.02;
    const e = this.eng;
    this.glide(e.g.gain, (idle + thrust * 0.16 + (f.boost ? 0.05 : 0)) * att, 0.12, dt);
    this.glide(e.o1.frequency, 48 + thrust * 46 + (f.boost ? 18 : 0), 0.2, dt);
    this.glide(e.o2.frequency, 48.8 + thrust * 47 + (f.boost ? 18 : 0), 0.2, dt);
    this.glide(e.lp.frequency, 220 + thrust * 900 + (f.boost ? 500 : 0), 0.15, dt);
    this.glide(e.hg.gain, (thrust * 0.05 + (f.boost ? 0.04 : 0)) * att, 0.1, dt);
    this.glide(e.hiss.frequency, 700 + thrust * 1400, 0.2, dt);
    // Wind: only where there is air.
    this.gust += (Math.random() - 0.5) * dt * 0.8;
    this.gust = Math.max(-0.4, Math.min(0.4, this.gust * 0.995));
    const flow = f.onFoot ? 0.18 + this.gust * 0.3 : Math.min(1, f.airspeed / 260);
    const wv = f.density * (f.onFoot ? 0.06 : 0.02 + 0.2 * flow * flow);
    this.glide(this.wind.g.gain, Math.max(0, wv), 0.25, dt);
    this.glide(this.wind.bp.frequency, 300 + flow * 1500, 0.3, dt);
    // Sparse ambient tones.
    this.ambientTimer -= dt;
    if (this.ambientTimer <= 0) {
      this.ambientTimer = 9 + Math.random() * 14;
      this.ambientTone(f.body);
    }
  }

  private env(g: GainNode, peak: number, attack: number, decay: number): void {
    const t = this.ctx!.currentTime;
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, t + attack + decay);
  }

  private tone(freq: number, type: OscillatorType, peak: number, attack: number, decay: number, dest: AudioNode = this.sfx): void {
    const ctx = this.ctx!;
    const o = ctx.createOscillator();
    o.type = type;
    o.frequency.value = freq;
    const g = ctx.createGain();
    o.connect(g);
    g.connect(dest);
    this.env(g, peak, attack, decay);
    o.start();
    o.stop(ctx.currentTime + attack + decay + 0.05);
  }

  private ambientTone(body: BodyId): void {
    if (!this.ctx) return;
    const base = body === 'ilex' ? 220 : body === 'vesper' ? 196 : 261.6;
    const step = PENTA[Math.floor(Math.random() * PENTA.length)];
    const f = base * 2 ** (step / 12);
    const type: OscillatorType = body === 'cairn' ? 'sine' : 'triangle';
    this.tone(f, type, 0.028, 1.2, 5.5);
    if (Math.random() < 0.4) this.tone(f * 1.5, 'sine', 0.012, 1.8, 6);
  }

  footstep(body: BodyId, sprint: boolean): void {
    if (!this.ctx || this.ctx.state !== 'running') return;
    const ctx = this.ctx;
    const s = this.noiseSource(false);
    const f = ctx.createBiquadFilter();
    f.type = body === 'vesper' ? 'highpass' : 'lowpass';
    f.frequency.value = body === 'ilex' ? 900 : body === 'vesper' ? 1800 : 500;
    const g = ctx.createGain();
    s.connect(f);
    f.connect(g);
    g.connect(this.sfx);
    this.env(g, sprint ? 0.12 : 0.08, 0.005, body === 'vesper' ? 0.11 : 0.07);
    s.start(ctx.currentTime, Math.random() * 1.5);
    s.stop(ctx.currentTime + 0.2);
  }

  thump(strength = 1): void {
    if (!this.ctx || this.ctx.state !== 'running') return;
    const ctx = this.ctx;
    const o = ctx.createOscillator();
    o.type = 'sine';
    o.frequency.setValueAtTime(70, ctx.currentTime);
    o.frequency.exponentialRampToValueAtTime(28, ctx.currentTime + 0.35);
    const g = ctx.createGain();
    o.connect(g);
    g.connect(this.sfx);
    this.env(g, 0.35 * strength, 0.01, 0.45);
    o.start();
    o.stop(ctx.currentTime + 0.5);
  }

  /** Continuous scan feedback (call with progress 0..1 while scanning). */
  scanTick(progress: number): void {
    if (!this.ctx || this.ctx.state !== 'running') return;
    if (Math.random() < 0.12) this.tone(500 + progress * 900, 'sine', 0.025, 0.01, 0.08);
  }

  scanDone(): void {
    if (!this.ctx) return;
    this.tone(659.3, 'sine', 0.08, 0.01, 0.35);
    window.setTimeout(() => this.ctx && this.tone(987.8, 'sine', 0.07, 0.01, 0.6), 110);
  }

  collect(): void {
    if (!this.ctx) return;
    this.tone(880, 'triangle', 0.09, 0.005, 0.25);
    this.tone(1320, 'sine', 0.04, 0.005, 0.4);
  }

  relay(): void {
    if (!this.ctx) return;
    for (const [f, d] of [[261.6, 0], [329.6, 0.12], [392, 0.24], [523.3, 0.36]] as const) {
      window.setTimeout(() => this.ctx && this.tone(f, 'sine', 0.07, 0.3, 2.6), d * 1000);
    }
  }

  ui(): void {
    if (!this.ctx) return;
    this.tone(1200, 'sine', 0.03, 0.002, 0.06);
  }

  complete(): void {
    if (!this.ctx) return;
    const chord = [196, 293.7, 392, 493.9, 587.3];
    chord.forEach((f, i) => window.setTimeout(() => this.ctx && this.tone(f, 'sine', 0.06, 0.6, 4.5), i * 180));
  }
}
