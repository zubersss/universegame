// Terrain generation worker (module worker). Generates chunk meshes and proxy
// globes with the same pure surface functions used on the main thread.

import { BODIES, type BodyId } from '../world/bodies';
import { computeSites } from '../world/sites';
import { getSurface } from '../world/surface';
import { chunkTransfers, generateChunk } from './chunkGen';

export interface GenRequest {
  type: 'gen';
  id: number;
  bodyId: BodyId;
  face: number;
  level: number;
  x: number;
  y: number;
  token: number;
}

export type WorkerRequest = GenRequest;

interface WorkerScope {
  onmessage: ((e: MessageEvent<WorkerRequest>) => void) | null;
  postMessage(msg: unknown, transfer: Transferable[]): void;
}

const scope = self as unknown as WorkerScope;

function surfaceFor(bodyId: BodyId) {
  const def = BODIES[bodyId];
  return { def, gen: getSurface(def, computeSites(def).clearings) };
}

scope.onmessage = (e) => {
  const msg = e.data;
  if (msg.type === 'gen') {
    try {
      const { def, gen } = surfaceFor(msg.bodyId);
      const data = generateChunk(def, gen, msg.face, msg.level, msg.x, msg.y, msg.token);
      scope.postMessage({ type: 'chunk', id: msg.id, data }, chunkTransfers(data));
    } catch (err) {
      scope.postMessage({ type: 'error', id: msg.id, message: err instanceof Error ? err.message : String(err) }, []);
    }
  }
};
