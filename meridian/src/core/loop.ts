/**
 * Fixed-timestep accumulator. Simulation always advances in `dt` increments,
 * at most `maxSteps` per frame; incoming gaps are clamped so a long pause never
 * produces a burst of catch-up simulation.
 */
export class FixedStepper {
  private acc = 0;
  /** Steps dropped because the frame budget was exceeded (diagnostics). */
  droppedSteps = 0;

  constructor(
    readonly dt: number,
    readonly maxSteps: number,
    readonly maxGap: number,
  ) {}

  advance(frameDt: number, step: (dt: number) => void): { steps: number; alpha: number } {
    const d = Number.isFinite(frameDt) ? Math.min(Math.max(frameDt, 0), this.maxGap) : 0;
    this.acc += d;
    let steps = 0;
    while (this.acc >= this.dt && steps < this.maxSteps) {
      step(this.dt);
      this.acc -= this.dt;
      steps++;
    }
    if (this.acc >= this.dt) {
      // Frame budget exhausted: drop the backlog instead of spiraling.
      const drop = Math.floor(this.acc / this.dt);
      this.droppedSteps += drop;
      this.acc -= drop * this.dt;
    }
    return { steps, alpha: this.acc / this.dt };
  }

  reset(): void {
    this.acc = 0;
  }
}
