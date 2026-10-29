import type { BodyId } from '../world/bodies';
import { chunkBytes, type ChunkData } from './chunkGen';
import { BUDGETS } from '../game/config';

export interface ChunkRequest {
  key: string;
  bodyId: BodyId;
  face: number;
  level: number;
  x: number;
  y: number;
  /** Lower = more urgent. Collision-critical work uses class 0. */
  priority: number;
}

/** Something that turns requests into ChunkData asynchronously (worker, or a test fake). */
export interface ChunkBackend {
  post(id: number, req: ChunkRequest, token: number): void;
  onResult: ((id: number, data: ChunkData | null, error?: string) => void) | null;
  dispose(): void;
}

/** Module-worker backend. */
export class WorkerBackend implements ChunkBackend {
  private readonly worker: Worker;
  onResult: ((id: number, data: ChunkData | null, error?: string) => void) | null = null;

  constructor(name = 'terrain') {
    this.worker = new Worker(new URL('./terrain.worker.ts', import.meta.url), { type: 'module', name });
    this.worker.onmessage = (e: MessageEvent) => {
      const m = e.data as { type: string; id: number; data?: ChunkData; message?: string };
      if (m.type === 'chunk') this.onResult?.(m.id, m.data ?? null);
      else if (m.type === 'error') this.onResult?.(m.id, null, m.message);
    };
    this.worker.onerror = (e) => {
      console.error('Terrain worker error', e.message);
    };
  }

  post(id: number, req: ChunkRequest, token: number): void {
    this.worker.postMessage({ type: 'gen', id, bodyId: req.bodyId, face: req.face, level: req.level, x: req.x, y: req.y, token });
  }

  dispose(): void {
    this.worker.terminate();
  }
}

/**
 * Job scheduling + LRU cache. Demand is replaced every LOD update (never
 * accumulated); stale results from a previous body/token are discarded.
 */
export class ChunkStore {
  private readonly cache = new Map<string, ChunkData>(); // insertion order = LRU order
  private bytes = 0;
  private queue: ChunkRequest[] = [];
  private readonly inFlight = new Map<number, { req: ChunkRequest; token: number }>();
  private readonly inFlightKeys = new Set<string>();
  private nextId = 1;
  token = 1;
  bodyId: BodyId;
  maxInFlight: number = BUDGETS.maxInFlightJobs;
  /** Keys that must not be evicted (rendered or collider-backed). */
  pinned: Set<string> = new Set();
  /** Called when new data enters the cache. */
  onData: ((d: ChunkData) => void) | null = null;
  // Stats
  generated = 0;
  seeded = 0;
  discarded = 0;
  errors = 0;
  genMsTotal = 0;
  genMsMax = 0;

  constructor(private readonly backend: ChunkBackend, bodyId: BodyId) {
    this.bodyId = bodyId;
    backend.onResult = (id, data, err) => this.onResult(id, data, err);
  }

  /** Switch bodies: invalidate in-flight work and clear demand (cache is kept per key+body). */
  setBody(bodyId: BodyId): void {
    if (bodyId === this.bodyId) return;
    this.bodyId = bodyId;
    this.token++;
    this.queue = [];
  }

  get(key: string): ChunkData | undefined {
    const d = this.cache.get(`${this.bodyId}:${key}`);
    if (d) {
      // touch for LRU
      this.cache.delete(`${this.bodyId}:${key}`);
      this.cache.set(`${this.bodyId}:${key}`, d);
    }
    return d;
  }

  has(key: string): boolean {
    return this.cache.has(`${this.bodyId}:${key}`);
  }

  isPending(key: string): boolean {
    return this.inFlightKeys.has(`${this.bodyId}:${key}`) || this.queue.some((q) => q.key === key);
  }

  /**
   * Replace the demand queue with the most urgent requests (at most
   * BUDGETS.maxQueuedJobs beyond in-flight work), then dispatch.
   */
  setDemand(reqs: ChunkRequest[]): void {
    const fresh: ChunkRequest[] = [];
    for (const r of reqs) {
      if (this.has(r.key) || this.inFlightKeys.has(`${this.bodyId}:${r.key}`)) continue;
      fresh.push(r);
    }
    fresh.sort((a, b) => a.priority - b.priority);
    // Deduplicate by key, keep the most urgent.
    const seen = new Set<string>();
    this.queue = [];
    for (const r of fresh) {
      if (seen.has(r.key)) continue;
      seen.add(r.key);
      this.queue.push(r);
      if (this.queue.length >= BUDGETS.maxQueuedJobs) break;
    }
    this.pump();
  }

  get queued(): number {
    return this.queue.length;
  }

  get inFlightCount(): number {
    return this.inFlight.size;
  }

  pump(): void {
    while (this.inFlight.size < this.maxInFlight && this.queue.length > 0) {
      const req = this.queue.shift()!;
      const id = this.nextId++;
      this.inFlight.set(id, { req, token: this.token });
      this.inFlightKeys.add(`${req.bodyId}:${req.key}`);
      this.backend.post(id, req, this.token);
    }
  }

  private onResult(id: number, data: ChunkData | null, err?: string): void {
    const job = this.inFlight.get(id);
    if (!job) return;
    this.inFlight.delete(id);
    this.inFlightKeys.delete(`${job.req.bodyId}:${job.req.key}`);
    if (!data) {
      this.errors++;
      if (err) console.error('Chunk generation failed', job.req.key, err);
    } else if (data.token !== this.token || data.bodyId !== this.bodyId) {
      // Stale (body switched since the request): discard.
      this.discarded++;
    } else {
      this.insert(data);
      this.onData?.(data);
    }
    this.pump();
  }

  insert(data: ChunkData): void {
    const k = `${data.bodyId}:${data.key}`;
    const old = this.cache.get(k);
    if (old) this.bytes -= chunkBytes(old);
    this.cache.delete(k);
    this.cache.set(k, data);
    this.bytes += chunkBytes(data);
    this.generated++;
    this.genMsTotal += data.genMs;
    this.genMsMax = Math.max(this.genMsMax, data.genMs);
    this.evict();
  }

  /**
   * Insert a chunk generated elsewhere (the proxy worker's level-0 roots) for
   * any body, without counting it as generated work. Existing entries win.
   */
  seed(data: ChunkData): void {
    const k = `${data.bodyId}:${data.key}`;
    if (this.cache.has(k)) return;
    this.cache.set(k, data);
    this.bytes += chunkBytes(data);
    this.seeded++;
  }

  private evict(): void {
    if (this.bytes <= BUDGETS.chunkCacheBytes) return;
    for (const [k, d] of this.cache) {
      if (this.bytes <= BUDGETS.chunkCacheBytes * 0.9) break;
      // Level-0 roots of every body stay resident: they back the coarse planet and the proxies.
      if (d.level === 0) continue;
      const local = k.slice(k.indexOf(':') + 1);
      if (d.bodyId === this.bodyId && this.pinned.has(local)) continue;
      this.cache.delete(k);
      this.bytes -= chunkBytes(d);
    }
  }

  /** Drop cached chunks of other bodies (on body release); their level-0 roots are kept. */
  releaseOtherBodies(): void {
    for (const [k, d] of this.cache) {
      if (d.bodyId !== this.bodyId && d.level > 0) {
        this.cache.delete(k);
        this.bytes -= chunkBytes(d);
      }
    }
  }

  get cacheBytes(): number {
    return this.bytes;
  }

  get cacheCount(): number {
    return this.cache.size;
  }

  dispose(): void {
    this.backend.dispose();
    this.cache.clear();
    this.bytes = 0;
  }
}
