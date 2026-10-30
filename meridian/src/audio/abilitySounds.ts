import type { PowerMotion } from '../avatar/AvatarAnimator';

// Power sounds (charter K: audio feedback). A continuous rush of air in
// flight and at superspeed, by speed, and short cues for a blink, a refused
// power and a take-off. Continuous parameters glide by direct per-frame
// assignment (PROGRESS.md: no per-frame automation events); one-shots use a
// few scheduled ramps each. Everything plays through the game's effects bus.

/** What the sounds need from the game's audio: its context, an effects input and a looping noise buffer. */
export interface AudioBus {
  ctx: BaseAudioContext;
  out: AudioNode;
  noise: AudioBuffer;
}

interface Rush {
  src: AudioBufferSourceNode;
  bp: BiquadFilterNode;
  g: GainNode;
}

export class AbilitySounds {
  private rush: Rush | null = null;
  /** Smoothed rush level 0..1. */
  level = 0;

  constructor(private readonly bus: () => AudioBus | null) {}

  /** Per rendered frame (dt 0 while paused): the rush follows the power's speed. */
  update(dt: number, motion: PowerMotion | null): void {
    const b = this.bus();
    if (!b) return;
    const target = motion ? Math.min(1, motion.speed / (motion.mode === 'flight' ? 160 : 110)) : 0;
    if (dt > 0) this.level += (target - this.level) * (1 - Math.exp(-dt / 0.25));
    if (!motion && this.level < 0.003) {
      this.stopRush();
      return;
    }
    if (!this.rush) {
      const src = b.ctx.createBufferSource();
      src.buffer = b.noise;
      src.loop = true;
      const bp = b.ctx.createBiquadFilter();
      bp.type = 'bandpass';
      bp.Q.value = 0.8;
      const g = b.ctx.createGain();
      g.gain.value = 0;
      src.connect(bp);
      bp.connect(g);
      g.connect(b.out);
      src.start();
      this.rush = { src, bp, g };
    }
    this.rush.g.gain.value = 0.16 * this.level;
    this.rush.bp.frequency.value = 280 + 1700 * this.level;
  }

  /** A blink: a quick falling sweep. */
  blink(): void {
    this.sweep(1500, 260, 0.22, 'sine', 0.12);
  }

  /** A refused power: a short low blip. */
  refuse(): void {
    this.sweep(170, 150, 0.12, 'square', 0.035);
  }

  /** Take-off: a rising sweep. */
  takeoff(): void {
    this.sweep(180, 620, 0.4, 'triangle', 0.08);
  }

  private sweep(f0: number, f1: number, dur: number, type: OscillatorType, peak: number): void {
    const b = this.bus();
    if (!b) return;
    const t = b.ctx.currentTime;
    const o = b.ctx.createOscillator();
    o.type = type;
    o.frequency.setValueAtTime(f0, t);
    o.frequency.exponentialRampToValueAtTime(f1, t + dur);
    const g = b.ctx.createGain();
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(peak, t + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0005, t + dur);
    o.connect(g);
    g.connect(b.out);
    o.start(t);
    o.stop(t + dur + 0.02);
  }

  private stopRush(): void {
    const r = this.rush;
    if (!r) return;
    r.src.stop();
    r.src.disconnect();
    r.bp.disconnect();
    r.g.disconnect();
    this.rush = null;
    this.level = 0;
  }

  dispose(): void {
    this.stopRush();
  }
}
