// Adaptive quality: when sustained frame intervals miss the preset's target,
// step down — first internal resolution, then decorative prop density, then
// distant terrain detail — and step back up only after a long run of fast
// frames. Hysteresis and a cooldown prevent oscillation; collision and
// gameplay are never touched.

export interface AdaptiveLevel {
  resolutionScale: number;
  propScale: number;
  splitScale: number;
}

export const ADAPTIVE_LEVELS: readonly AdaptiveLevel[] = [
  { resolutionScale: 1, propScale: 1, splitScale: 1 },
  { resolutionScale: 0.85, propScale: 1, splitScale: 1 },
  { resolutionScale: 0.72, propScale: 1, splitScale: 1 },
  { resolutionScale: 0.6, propScale: 1, splitScale: 1 },
  { resolutionScale: 0.6, propScale: 0.6, splitScale: 1 },
  { resolutionScale: 0.6, propScale: 0.6, splitScale: 1.4 },
];

export class AdaptiveQuality {
  level = 0;
  /** Seconds since the last change. */
  private cooldown = 0;
  private window: number[] = [];
  private windowTime = 0;
  private slowWindows = 0;
  private fastTime = 0;
  /** Median frame interval of the last evaluated window (ms). */
  lastMedianMs = 0;

  constructor(public targetMs: number) {}

  reset(targetMs: number): void {
    this.targetMs = targetMs;
    this.level = 0;
    this.cooldown = 0;
    this.window = [];
    this.windowTime = 0;
    this.slowWindows = 0;
    this.fastTime = 0;
  }

  get current(): AdaptiveLevel {
    return ADAPTIVE_LEVELS[this.level];
  }

  /**
   * Feed one frame interval (s). Returns true when the level changed.
   * Evaluates 2-second windows: two slow windows in a row step down; 12 s of
   * clearly fast frames step up. At least 4 s between changes.
   */
  frame(dt: number): boolean {
    if (dt <= 0 || dt > 0.5) return false; // pauses and hitches are not load
    this.cooldown += dt;
    this.window.push(dt * 1000);
    this.windowTime += dt;
    if (this.windowTime < 2) return false;
    const sorted = [...this.window].sort((a, b) => a - b);
    const median = sorted[Math.floor(sorted.length / 2)];
    this.lastMedianMs = median;
    this.window = [];
    const span = this.windowTime;
    this.windowTime = 0;
    if (median > this.targetMs * 1.15) {
      this.slowWindows++;
      this.fastTime = 0;
    } else {
      this.slowWindows = 0;
      this.fastTime = median < this.targetMs * 0.7 ? this.fastTime + span : 0;
    }
    if (this.cooldown < 4) return false;
    if (this.slowWindows >= 2 && this.level < ADAPTIVE_LEVELS.length - 1) {
      this.level++;
      this.slowWindows = 0;
      this.cooldown = 0;
      return true;
    }
    if (this.fastTime >= 12 && this.level > 0) {
      this.level--;
      this.fastTime = 0;
      this.cooldown = 0;
      return true;
    }
    return false;
  }
}
