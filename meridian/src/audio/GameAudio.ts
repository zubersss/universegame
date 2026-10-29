// Synthesized Web Audio soundscape. Created only from a user gesture (the
// Play click); faded out and suspended while paused or hidden. Continuous
// layers (engine, wind, suit) glide by direct per-frame assignment; one-shot
// sounds are pooled voices (VoicePool) routed through the Mixer's buses.

import type { BodyId } from '../world/bodies';
import { Mixer, type BusName } from './Mixer';
import { VoicePool, type Voice, type VoiceStats } from './VoicePool';
import { STEPS, ambienceFor, isAirless } from './profiles';
import { CREATURE_RANGE, CREATURE_VOICE_CAP, creatureVoice, type CreatureEvent, type CreatureLayer } from './creatures';

export type DiscoveryKind = 'scanStart' | 'logged' | 'firstSpecies' | 'worldComplete';

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
  /** Game mode; changes trigger cockpit chirps and the cruise drone. */
  mode?: 'PILOTING' | 'CRUISING' | 'LANDED' | 'ON_FOOT';
  /** Landing gear target (0 up, 1 down); changes run the gear motor. */
  gear?: number;
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
  private buffet!: { lp: BiquadFilterNode; g: GainNode };
  private drone!: { a: OscillatorNode; b: OscillatorNode; g: GainNode };
  private lastMode: AudioFrame['mode'] | null = null;
  private lastGear = -1;
  private body: BodyId = 'ilex';
  private lastChime = -10;
  private persistent: AudioNode[] = [];
  private loops: AudioScheduledSourceNode[] = [];
  private analyser: AnalyserNode | null = null;
  private meterBuf: Float32Array<ArrayBuffer> | null = null;
  private ambientTimer = 6;
  private breathTimer = 1;
  private exertion = 0;
  /** True while the on-foot mix is in airless suit mode. */
  suitMode = false;
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
    // Buffeting: low rumble of thick air against the hull at speed (none in vacuum).
    const bsrc = this.keep(this.noiseSource(true));
    const blp = this.keep(ctx.createBiquadFilter());
    blp.type = 'lowpass';
    blp.frequency.value = 120;
    blp.Q.value = 1.2;
    const bg = this.keep(ctx.createGain());
    bg.gain.value = 0;
    bsrc.connect(blp);
    blp.connect(bg);
    bg.connect(ship);
    this.buffet = { lp: blp, g: bg };
    // Cruise drone: two near-unison sines a twelfth apart; the slow beat is the shimmer.
    const da = this.keep(ctx.createOscillator());
    const db = this.keep(ctx.createOscillator());
    da.type = 'sine';
    db.type = 'sine';
    da.frequency.value = 73.4;
    db.frequency.value = 220.5;
    const dg = this.keep(ctx.createGain());
    dg.gain.value = 0;
    da.connect(dg);
    db.connect(dg);
    dg.connect(ship);
    this.drone = { a: da, b: db, g: dg };
    for (const s of [o1, o2, hissSrc, wsrc, ssrc, bsrc, da, db]) {
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
    this.body = f.body;
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
    // Buffeting grows with dynamic pressure; it fades out with the air.
    const q = f.onFoot || !f.shipActive ? 0 : f.density * Math.min(1, Math.max(0, (f.airspeed - 90) / 320)) ** 2;
    this.glide(this.buffet.g.gain, q * (0.16 + this.gust * 0.15), 0.18, dt);
    this.glide(this.buffet.lp.frequency, 90 + q * 160 + this.gust * 40, 0.25, dt);
    const cruising = f.mode === 'CRUISING';
    this.glide(this.drone.g.gain, cruising ? 0.022 : 0, cruising ? 1.5 : 0.6, dt);
    this.glide(this.drone.b.frequency, 220.5 + this.gust * 0.6, 0.5, dt);
    if (f.mode && f.mode !== this.lastMode) {
      if (this.lastMode) this.modeCue(this.lastMode, f.mode);
      this.lastMode = f.mode;
    }
    if (f.gear !== undefined) {
      const g = f.gear > 0.5 ? 1 : 0;
      if (this.lastGear >= 0 && g !== this.lastGear) this.gearMotor(g === 1);
      this.lastGear = g;
    }
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

  /** Cockpit chirps on mode changes (the HUD mode line is the visual cue). */
  private modeCue(from: NonNullable<AudioFrame['mode']>, to: NonNullable<AudioFrame['mode']>): void {
    if (to === 'CRUISING') {
      this.tone(660, 'sine', 0.035, 0.01, 0.18, 'ui');
      this.tone(990, 'sine', 0.03, 0.01, 0.3, 'ui', 0.09);
    } else if (from === 'CRUISING') {
      this.tone(990, 'sine', 0.03, 0.01, 0.18, 'ui');
      this.tone(660, 'sine', 0.03, 0.01, 0.3, 'ui', 0.09);
    } else if (from === 'LANDED' && to === 'PILOTING') {
      // Engine spool-up on take-off.
      const v = this.tone(90, 'sawtooth', 0.05, 0.25, 0.9, 'ship');
      if (v) {
        const o = v.sources[0] as OscillatorNode;
        o.frequency.setValueAtTime(70, v.start);
        o.frequency.exponentialRampToValueAtTime(150, v.start + 0.8);
        this.lowpass(v, o, 600);
      }
    } else if (to === 'ON_FOOT' || from === 'ON_FOOT') {
      // Hatch seal: a short pressure hiss.
      this.noise('bandpass', 2400, 0.7, 0.03, 0.02, 0.35, 'effects');
    }
  }

  /** Gear motor whine, then a clunk as it locks. */
  private gearMotor(down: boolean): void {
    const v = this.tone(down ? 180 : 220, 'sawtooth', 0.018, 0.08, 0.75, 'ship');
    if (v) {
      const o = v.sources[0] as OscillatorNode;
      o.frequency.setValueAtTime(o.frequency.value, v.start);
      o.frequency.linearRampToValueAtTime(down ? 140 : 260, v.start + 0.8);
      this.lowpass(v, o, 1100);
    }
    this.noise('lowpass', 500, 1, 0.07, 0.004, 0.12, 'ship', 0.85);
  }

  /** Reroute a voice's oscillator through a lowpass. */
  private lowpass(v: Voice, o: AudioNode, cutoff: number): void {
    const lp = this.pool.node(v, this.ctx!.createBiquadFilter());
    lp.type = 'lowpass';
    lp.frequency.value = cutoff;
    o.disconnect();
    o.connect(lp);
    lp.connect(v.out);
  }

  /** Ship touchdown: thump and gear creak scaled by vertical impact speed (m/s). */
  touchdown(impact: number): void {
    const k = Math.min(1.3, 0.45 + Math.abs(impact) / 5);
    this.thump(k);
    this.noise('bandpass', 700, 2, 0.03 * k, 0.03, 0.4, 'ship', 0.05);
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
    if (!this.running) return;
    this.lastChime = this.ctx!.currentTime;
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

  /**
   * A fauna sound event. `pos` is the creature relative to the camera in
   * camera space (x right, y up, −z forward; metres), e.g.
   * `world.applyMatrix4(camera.matrixWorldInverse)`. `intensity` 0..1.
   */
  creature(ev: CreatureEvent, speciesId: string, pos: { x: number; y: number; z: number }, intensity = 1): void {
    if (!this.running) return;
    const d = Math.hypot(pos.x, pos.y, pos.z);
    if (d > CREATURE_RANGE || intensity <= 0) return;
    const layers = creatureVoice(speciesId)[ev];
    // Fauna stay inside their own sub-cap so a herd never crowds out cues.
    if (this.pool.count('creature') >= CREATURE_VOICE_CAP) return;
    const k = Math.min(1, intensity) * (0.85 + Math.random() * 0.3);
    const detune = 0.94 + Math.random() * 0.12;
    for (const l of layers) {
      const n = l.repeat ?? 1;
      for (let i = 0; i < n; i++) this.creatureLayer(l, pos, k, detune, (l.delay ?? 0) + i * (l.every ?? 0));
    }
  }

  private creatureLayer(l: CreatureLayer, pos: { x: number; y: number; z: number }, k: number, detune: number, delay: number): void {
    const ctx = this.ctx!;
    const p = ctx.createPanner();
    p.panningModel = 'equalpower';
    p.distanceModel = 'inverse';
    p.refDistance = 6;
    p.rolloffFactor = 1;
    p.maxDistance = CREATURE_RANGE;
    p.positionX.value = pos.x;
    p.positionY.value = pos.y;
    p.positionZ.value = pos.z;
    p.connect(this.mix.bus('creatures'));
    const v = this.pool.voice(p, l.peak * k, l.attack, l.decay, ctx.currentTime + delay);
    if (!v) {
      p.disconnect();
      return;
    }
    v.tag = 'creature';
    this.pool.node(v, p);
    const f0 = l.freq * detune;
    if (l.src === 'noise') {
      const s = this.noiseSource(false);
      const fl = this.pool.node(v, ctx.createBiquadFilter());
      fl.type = l.filter ?? 'bandpass';
      fl.frequency.value = f0;
      fl.Q.value = l.q ?? 1;
      if (l.glide) {
        fl.frequency.setValueAtTime(f0, v.start);
        fl.frequency.exponentialRampToValueAtTime(l.glide * detune, v.start + l.attack + l.decay);
      }
      s.connect(fl);
      fl.connect(v.out);
      this.pool.source(v, s, Math.random() * 1.5);
    } else {
      const o = ctx.createOscillator();
      o.type = l.src;
      o.frequency.value = f0;
      if (l.glide) {
        o.frequency.setValueAtTime(f0, v.start);
        o.frequency.exponentialRampToValueAtTime(l.glide * detune, v.start + l.attack + l.decay);
      }
      o.connect(v.out);
      this.pool.source(v, o);
    }
  }

  /** Discovery moments. 'logged' is skipped if scanDone() already chimed. */
  discovery(kind: DiscoveryKind): void {
    if (!this.running) return;
    const t = this.ctx!.currentTime;
    if (kind === 'scanStart') this.tone(440, 'sine', 0.02, 0.04, 0.18);
    else if (kind === 'logged') {
      if (t - this.lastChime > 0.4) this.scanDone();
    } else if (kind === 'firstSpecies') this.swell(3, 0.022, 3.5, 2);
    else this.swell(5, 0.03, 6, 4);
  }

  /** Music swell on the current world's scale: `notes` rising, ambience ducked. */
  private swell(notes: number, peak: number, decay: number, hold: number): void {
    const p = ambienceFor(this.body);
    this.mix.duck('ambience', 0.6, hold);
    const start = Math.floor(Math.random() * 2);
    for (let i = 0; i < notes; i++) {
      const step = p.scale[Math.min(p.scale.length - 1, start + i * 2)];
      const f = p.tonic * 2 ** (step / 12);
      this.tone(f, p.timbre, peak, 0.8, decay, 'music', i * 0.4);
      this.tone(f * 2, 'sine', peak * 0.3, 1.2, decay, 'music', i * 0.4 + 0.2);
    }
  }

  /** Extended Survey transmitted: a slower, wider cue than the core transmission. */
  completeExtended(): void {
    if (!this.running) return;
    this.mix.duck('ambience', 0.4, 6);
    const notes = [146.8, 220, 329.6, 440, 554.4, 659.3];
    notes.forEach((f, i) => {
      this.tone(f, 'sine', 0.05, 0.9, 6, 'effects', i * 0.32);
      if (i % 2 === 1) this.tone(f * 2, 'triangle', 0.012, 1.2, 5, 'effects', i * 0.32 + 0.15);
    });
    this.noise('bandpass', 5200, 0.5, 0.01, 1.5, 4, 'effects', 0.4);
  }

  /** Node and voice counters for leak checks (dev and testhooks builds only). */
  stats(): AudioStats | null {
    if (!__TEST_HOOKS__ || !this.ctx) return null;
    const voices = this.pool.snapshot();
    const persistentNodes = this.mix.nodeCount + this.persistent.length + (this.analyser ? 1 : 0);
    return { state: this.ctx.state, voices, persistentNodes, liveNodes: persistentNodes + voices.liveNodes, suit: this.suitMode };
  }

  /** Peak and RMS of the final mix right now (lazily taps an analyser; dev and testhooks builds only). */
  meter(): { peak: number; rms: number } | null {
    if (!__TEST_HOOKS__ || !this.ctx) return null;
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
