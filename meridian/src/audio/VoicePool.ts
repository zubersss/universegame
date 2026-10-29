// One-shot voices with a hard cap. A voice is a group of nodes ending in one
// envelope gain; when the cap is reached the quietest voice (oldest on a tie)
// is faded out over a few milliseconds and stolen. Every node of a finished
// voice is disconnected, whether it ended normally or was stolen.

export const VOICE_CAP = 32;
/** Envelope floor (exponential ramps cannot reach 0). */
const FLOOR = 0.0001;
/** Fade applied to a stolen voice, long enough not to click. */
const STEAL_FADE = 0.015;

export interface Voice {
  readonly id: number;
  /** Envelope gain; connect the voice's sound into it. */
  readonly out: GainNode;
  readonly nodes: AudioNode[];
  readonly sources: AudioScheduledSourceNode[];
  start: number;
  attack: number;
  decay: number;
  peak: number;
  /** Time the last source stops. */
  end: number;
  ended: number;
  stolen: boolean;
}

export interface VoiceStats {
  active: number;
  releasing: number;
  started: number;
  stolen: number;
  finished: number;
  /** Nodes created by voices that are not yet disconnected. */
  liveNodes: number;
  nodesCreated: number;
  nodesDisconnected: number;
  dropped: number;
}

export class VoicePool {
  /** Voices that count toward the cap. */
  readonly active: Voice[] = [];
  /** Stolen voices fading out (not counted toward the cap). */
  readonly releasing: Voice[] = [];
  private nextId = 1;
  private sweepTimer = 0;
  readonly stats: VoiceStats = {
    active: 0, releasing: 0, started: 0, stolen: 0, finished: 0, liveNodes: 0, nodesCreated: 0, nodesDisconnected: 0, dropped: 0,
  };

  constructor(private readonly ctx: BaseAudioContext, readonly cap = VOICE_CAP) {}

  /**
   * Begin a voice whose envelope rises to `peak` over `attack` and decays over
   * `decay`, starting at `start` (seconds, context time). Returns null if
   * nothing can be stolen (cap 0).
   */
  voice(dest: AudioNode, peak: number, attack: number, decay: number, start = this.ctx.currentTime): Voice | null {
    if (this.active.length >= this.cap && !this.stealOne()) {
      this.stats.dropped++;
      return null;
    }
    const out = this.ctx.createGain();
    attack = Math.max(0.003, attack);
    const g = out.gain;
    g.setValueAtTime(FLOOR, start);
    g.exponentialRampToValueAtTime(Math.max(FLOOR * 2, peak), start + attack);
    g.exponentialRampToValueAtTime(FLOOR, start + attack + decay);
    out.connect(dest);
    const v: Voice = {
      id: this.nextId++, out, nodes: [out], sources: [], start, attack, decay, peak,
      end: start + attack + decay + 0.05, ended: 0, stolen: false,
    };
    this.active.push(v);
    this.stats.started++;
    this.stats.nodesCreated++;
    return v;
  }

  /** Register an intermediate node (filter, gain) so it is disconnected with the voice. */
  node<T extends AudioNode>(v: Voice, n: T): T {
    v.nodes.push(n);
    this.stats.nodesCreated++;
    return n;
  }

  /** Register, start and schedule the stop of a source (`offset` for buffer sources). */
  source<T extends AudioScheduledSourceNode>(v: Voice, s: T, offset?: number): T {
    v.nodes.push(s);
    v.sources.push(s);
    this.stats.nodesCreated++;
    s.onended = () => this.onSourceEnded(v);
    if (offset === undefined) s.start(v.start);
    else (s as unknown as AudioBufferSourceNode).start(v.start, offset);
    s.stop(v.end);
    return s;
  }

  /** Estimated envelope level of a voice at time t. */
  level(v: Voice, t: number): number {
    if (v.stolen) return 0;
    const age = t - v.start;
    // Scheduled or still rising: it is about to be as loud as it gets.
    if (age < v.attack) return v.peak;
    const d = (age - v.attack) / v.decay;
    if (d >= 1) return 0;
    return v.peak * Math.pow(FLOOR / Math.max(FLOOR * 2, v.peak), d);
  }

  /** Fade out and release the quietest active voice (oldest first on ties). */
  private stealOne(): boolean {
    const t = this.ctx.currentTime;
    let best = -1;
    let bestLevel = Infinity;
    for (let i = 0; i < this.active.length; i++) {
      const v = this.active[i];
      const l = this.level(v, t);
      if (l < bestLevel - 1e-9 || (Math.abs(l - bestLevel) <= 1e-9 && best >= 0 && v.start < this.active[best].start)) {
        best = i;
        bestLevel = l;
      }
    }
    if (best < 0) return false;
    const v = this.active[best];
    this.active.splice(best, 1);
    const g = v.out.gain;
    g.cancelScheduledValues(t);
    g.setValueAtTime(Math.max(FLOOR, Math.min(v.peak, bestLevel)), t);
    g.linearRampToValueAtTime(0, t + STEAL_FADE);
    v.end = Math.min(v.end, t + STEAL_FADE + 0.005);
    for (const s of v.sources) {
      try {
        s.stop(v.end);
      } catch {
        // Already stopped.
      }
    }
    v.stolen = true;
    this.releasing.push(v);
    this.stats.stolen++;
    return true;
  }

  private onSourceEnded(v: Voice): void {
    v.ended++;
    if (v.ended >= v.sources.length) this.release(v);
  }

  /** Disconnect every node of a voice and forget it. Idempotent. */
  private release(v: Voice): void {
    let i = this.active.indexOf(v);
    if (i >= 0) this.active.splice(i, 1);
    else {
      i = this.releasing.indexOf(v);
      if (i < 0) return;
      this.releasing.splice(i, 1);
    }
    for (const s of v.sources) s.onended = null;
    for (const n of v.nodes) n.disconnect();
    this.stats.nodesDisconnected += v.nodes.length;
    this.stats.finished++;
  }

  /**
   * Safety net for `onended` not firing (it does not while the context is
   * suspended, and some engines drop it): release voices well past their end.
   * Cheap enough to call every frame; it only scans twice a second.
   */
  sweep(dt: number): void {
    this.sweepTimer -= dt;
    if (this.sweepTimer > 0) return;
    this.sweepTimer = 0.5;
    const t = this.ctx.currentTime;
    for (let i = this.active.length - 1; i >= 0; i--) if (t > this.active[i].end + 0.5) this.release(this.active[i]);
    for (let i = this.releasing.length - 1; i >= 0; i--) if (t > this.releasing[i].end + 0.5) this.release(this.releasing[i]);
  }

  /** Stop and release everything now. */
  clear(): void {
    for (const v of [...this.active, ...this.releasing]) {
      for (const s of v.sources) {
        try {
          s.stop();
        } catch {
          // Already stopped.
        }
      }
      this.release(v);
    }
  }

  snapshot(): VoiceStats {
    const s = this.stats;
    s.active = this.active.length;
    s.releasing = this.releasing.length;
    s.liveNodes = s.nodesCreated - s.nodesDisconnected;
    return { ...s };
  }
}
