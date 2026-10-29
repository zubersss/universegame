import { BODIES } from '../src/world/bodies';
import { computeSites } from '../src/world/sites';
import { getSurface } from '../src/world/surface';
import { generateChunk, type ChunkData } from '../src/terrain/chunkGen';
import type { ChunkBackend, ChunkRequest } from '../src/terrain/ChunkStore';
import { mulberry32 } from '../src/core/rng';

/**
 * In-process chunk backend for Node tests. Results can be delayed and
 * delivered out of order to emulate a slow/reordering worker.
 */
export class FakeBackend implements ChunkBackend {
  onResult: ((id: number, data: ChunkData | null, error?: string) => void) | null = null;
  private pending: { id: number; data: ChunkData; due: number }[] = [];
  private tickN = 0;
  private readonly rnd: () => number;

  constructor(
    private readonly maxDelayTicks = 0,
    private readonly shuffle = false,
    seed = 1,
  ) {
    this.rnd = mulberry32(seed);
  }

  post(id: number, req: ChunkRequest, token: number): void {
    const def = BODIES[req.bodyId];
    const gen = getSurface(def, computeSites(def).clearings);
    const data = generateChunk(def, gen, req.face, req.level, req.x, req.y, token);
    if (this.maxDelayTicks === 0 && !this.shuffle) {
      // Deliver asynchronously-but-immediately on the next flush.
      this.pending.push({ id, data, due: this.tickN });
      return;
    }
    const delay = Math.floor(this.rnd() * (this.maxDelayTicks + 1));
    this.pending.push({ id, data, due: this.tickN + delay });
  }

  /** Deliver due results (optionally in shuffled order). */
  tick(): number {
    this.tickN++;
    let due = this.pending.filter((p) => p.due <= this.tickN);
    this.pending = this.pending.filter((p) => p.due > this.tickN);
    if (this.shuffle) {
      for (let i = due.length - 1; i > 0; i--) {
        const j = Math.floor(this.rnd() * (i + 1));
        [due[i], due[j]] = [due[j], due[i]];
      }
    }
    for (const p of due) this.onResult?.(p.id, p.data);
    return due.length;
  }

  get backlog(): number {
    return this.pending.length;
  }

  dispose(): void {
    this.pending = [];
  }
}
