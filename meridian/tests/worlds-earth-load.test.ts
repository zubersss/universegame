// Robustness of lazy dataset loading: a failed Earth download backs off instead
// of re-downloading on every chunk job, failed chunk keys are not re-requested
// every LOD tick, and a later attempt succeeds. (Separate file: module state.)
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { EARTH_META, earthData, loadEarthData, type LayerName } from '../src/world/earthData';
import { ChunkStore, type ChunkBackend, type ChunkRequest } from '../src/terrain/ChunkStore';
import type { ChunkData } from '../src/terrain/chunkGen';

const dir = fileURLToPath(new URL('../src/data/earth/', import.meta.url));
const layers = EARTH_META.layers as Record<LayerName, { file: string }>;

afterEach(() => {
  vi.useRealTimers();
});

describe('Earth data loading', () => {
  it('backs off after a failed download, then loads once', async () => {
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(1_000_000);
    let calls = 0;
    const failing = async () => {
      calls++;
      throw new Error('offline');
    };
    await expect(loadEarthData(failing)).rejects.toThrow('offline');
    const afterFirst = calls;
    expect(afterFirst).toBeGreaterThan(0);
    // Inside the back-off window: rejected at once, nothing fetched.
    await expect(loadEarthData(failing)).rejects.toThrow(/unavailable/);
    vi.setSystemTime(1_001_500);
    await expect(loadEarthData(failing)).rejects.toThrow(/unavailable/);
    expect(calls).toBe(afterFirst);
    // After the window a new attempt is made; the second failure doubles the wait.
    vi.setSystemTime(1_002_100);
    await expect(loadEarthData(failing)).rejects.toThrow('offline');
    expect(calls).toBe(afterFirst * 2);
    vi.setSystemTime(1_005_000);
    await expect(loadEarthData(failing)).rejects.toThrow(/unavailable/);
    // Then a working fetch succeeds and is not repeated.
    vi.setSystemTime(1_007_000);
    let ok = 0;
    const real = async (name: LayerName) => {
      ok++;
      return readFileSync(dir + layers[name].file);
    };
    await loadEarthData(real);
    expect(earthData()).not.toBeNull();
    await loadEarthData(real);
    expect(ok).toBe(4);
  });
});

class FailingBackend implements ChunkBackend {
  onResult: ((id: number, data: ChunkData | null, error?: string) => void) | null = null;
  posts: ChunkRequest[] = [];
  private queue: number[] = [];
  post(id: number, req: ChunkRequest): void {
    this.posts.push(req);
    this.queue.push(id);
  }
  flush(): void {
    const q = this.queue;
    this.queue = [];
    for (const id of q) this.onResult?.(id, null, 'Earth data unavailable');
  }
  dispose(): void {}
}

describe('ChunkStore failures', () => {
  it('does not re-request a failed chunk on every tick', () => {
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(5_000_000);
    const err = vi.spyOn(console, 'error').mockImplementation(() => {});
    const backend = new FailingBackend();
    const store = new ChunkStore(backend, 'earth');
    const req: ChunkRequest = { key: '0/0/0/0', bodyId: 'earth', face: 0, level: 0, x: 0, y: 0, priority: 0 };
    store.setDemand([req]);
    backend.flush();
    expect(backend.posts.length).toBe(1);
    for (let t = 0; t < 20; t++) {
      store.setDemand([req]); // LOD updates keep asking
      backend.flush();
    }
    expect(backend.posts.length).toBe(1); // backed off
    vi.setSystemTime(5_001_100); // first back-off is 1 s
    store.setDemand([req]);
    backend.flush();
    expect(backend.posts.length).toBe(2);
    expect(store.errors).toBe(2);
    expect(err.mock.calls.length).toBe(1); // logged once, not per failure
    err.mockRestore();
  });
});
