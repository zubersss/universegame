// Mix graph: six buses → master (user volume) → pause duck → glue
// compressor → limiter → destination. Every gain change here is scheduled
// once per *change* (settings, pause, cue ducking), never per frame (A8.1).

export type BusName = 'ambience' | 'ship' | 'creatures' | 'effects' | 'ui' | 'music';
export const BUS_NAMES: readonly BusName[] = ['ambience', 'ship', 'creatures', 'effects', 'ui', 'music'];

/** Mix levels of each bus before user volume (linear). */
export const BUS_LEVELS: Readonly<Record<BusName, number>> = {
  ambience: 1,
  ship: 1,
  creatures: 0.8,
  effects: 0.9,
  ui: 0.8,
  music: 0.9,
};

/** Which user volume slider scales a bus (besides master). */
const BUS_GROUP: Readonly<Record<BusName, 'music' | 'effects'>> = {
  ambience: 'effects',
  ship: 'effects',
  creatures: 'effects',
  effects: 'effects',
  ui: 'effects',
  music: 'music',
};

export interface Bus {
  /** Sources connect here. */
  input: GainNode;
  /** Level × user group volume. */
  gain: GainNode;
  /** Cue ducking (1 = none). */
  duck: GainNode;
}

/**
 * Replace whatever is scheduled on `param` with one short linear ramp. The
 * timeline never holds more than two events per param, however often this runs.
 */
export function rampTo(ctx: BaseAudioContext, param: AudioParam, value: number, time: number): void {
  const t = ctx.currentTime;
  param.cancelScheduledValues(t);
  param.setValueAtTime(param.value, t);
  param.linearRampToValueAtTime(value, t + Math.max(0.005, time));
}

export class Mixer {
  readonly buses = {} as Record<BusName, Bus>;
  readonly master: GainNode;
  /** Pause/hidden fade, separate from the user volume. */
  readonly pause: GainNode;
  readonly glue: DynamicsCompressorNode;
  readonly limiter: DynamicsCompressorNode;
  private groups = { music: 1, effects: 1 };
  /** Persistent nodes owned by the mixer. */
  readonly nodeCount: number;

  constructor(private readonly ctx: BaseAudioContext, volume: number) {
    this.limiter = ctx.createDynamicsCompressor();
    this.limiter.threshold.value = -2;
    this.limiter.knee.value = 0;
    this.limiter.ratio.value = 20;
    this.limiter.attack.value = 0.002;
    this.limiter.release.value = 0.12;
    this.limiter.connect(ctx.destination);
    this.glue = ctx.createDynamicsCompressor();
    this.glue.threshold.value = -14;
    this.glue.ratio.value = 3;
    this.glue.connect(this.limiter);
    this.pause = ctx.createGain();
    this.pause.gain.value = 0;
    this.pause.connect(this.glue);
    this.master = ctx.createGain();
    this.master.gain.value = volume;
    this.master.connect(this.pause);
    for (const name of BUS_NAMES) {
      const input = ctx.createGain();
      const gain = ctx.createGain();
      const duck = ctx.createGain();
      gain.gain.value = BUS_LEVELS[name];
      input.connect(gain);
      gain.connect(duck);
      duck.connect(this.master);
      this.buses[name] = { input, gain, duck };
    }
    this.nodeCount = 4 + BUS_NAMES.length * 3;
    // Fade in from silence so the first frame never clicks.
    rampTo(ctx, this.pause.gain, 1, 0.3);
  }

  bus(name: BusName): GainNode {
    return this.buses[name].input;
  }

  setMaster(v: number): void {
    rampTo(this.ctx, this.master.gain, v, 0.05);
  }

  /** User volume of the music or effects group (0..1). */
  setGroup(group: 'music' | 'effects', v: number): void {
    this.groups[group] = v;
    for (const name of BUS_NAMES) {
      if (BUS_GROUP[name] === group) rampTo(this.ctx, this.buses[name].gain.gain, BUS_LEVELS[name] * v, 0.05);
    }
  }

  /** Fade the whole mix out (pause) or back in. */
  fadePause(on: boolean, time: number): void {
    rampTo(this.ctx, this.pause.gain, on ? 0 : 1, time);
  }

  /** Dip a bus to `depth` for `hold` seconds under an important cue, then recover. */
  duck(name: BusName, depth: number, hold: number): void {
    const p = this.buses[name].duck.gain;
    const t = this.ctx.currentTime;
    p.cancelScheduledValues(t);
    p.setValueAtTime(p.value, t);
    p.linearRampToValueAtTime(depth, t + 0.12);
    p.setValueAtTime(depth, t + 0.12 + hold);
    p.linearRampToValueAtTime(1, t + 0.12 + hold + 1.2);
  }

  dispose(): void {
    for (const name of BUS_NAMES) {
      const b = this.buses[name];
      b.input.disconnect();
      b.gain.disconnect();
      b.duck.disconnect();
    }
    this.master.disconnect();
    this.pause.disconnect();
    this.glue.disconnect();
    this.limiter.disconnect();
  }
}
