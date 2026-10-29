// Test-only profiling helpers: frame-interval statistics and an estimate of
// GPU allocations from the actual buffers, textures and render targets in use.

import type { BufferGeometry, InstancedMesh, Material, Mesh, Texture, WebGLRenderTarget } from 'three';
import type { Game } from '../game/Game';

export interface FrameStats {
  frames: number;
  medianMs: number;
  p95Ms: number;
  p99Ms: number;
  maxMs: number;
  stalls100: number;
}

export function frameStats(game: Game, last = 4096): FrameStats {
  const n = Math.min(game.frameIntervalCount, game.frameIntervals.length, last);
  const out: number[] = [];
  const end = game.frameIntervalCount;
  for (let i = end - n; i < end; i++) out.push(game.frameIntervals[((i % game.frameIntervals.length) + game.frameIntervals.length) % game.frameIntervals.length]);
  out.sort((a, b) => a - b);
  const q = (p: number) => (out.length ? out[Math.min(out.length - 1, Math.floor(p * out.length))] : 0);
  return { frames: n, medianMs: q(0.5), p95Ms: q(0.95), p99Ms: q(0.99), maxMs: out.length ? out[out.length - 1] : 0, stalls100: out.filter((x) => x > 100).length };
}

function textureBytes(t: Texture): number {
  const img = t.image as { width?: number; height?: number; data?: ArrayBufferView } | undefined;
  if (!img) return 0;
  if (img.data && 'byteLength' in img.data) return img.data.byteLength * (t.generateMipmaps ? 1.33 : 1);
  const w = img.width ?? 0;
  const h = img.height ?? 0;
  return w * h * 4 * (t.generateMipmaps ? 1.33 : 1);
}

function targetBytes(rt: WebGLRenderTarget): number {
  const t = rt.texture;
  const bpp = t.type === 1016 /* HalfFloatType */ ? 8 : t.type === 1015 /* FloatType */ ? 16 : 4;
  return rt.width * rt.height * (bpp + (rt.depthBuffer ? 4 : 0));
}

/** Estimated GPU allocations (MB): geometry buffers, textures and render targets. */
export function gpuEstimate(game: Game): { geometryMB: number; texturesMB: number; targetsMB: number; totalMB: number; geometries: number; textures: number } {
  const r = game.render;
  const geos = new Set<BufferGeometry>();
  const textures = new Set<Texture>();
  let instanceBytes = 0;
  const addMat = (m: Material) => {
    for (const v of Object.values(m)) if (v && (v as Texture).isTexture) textures.add(v as Texture);
    const uniforms = (m as unknown as { uniforms?: Record<string, { value: unknown }> }).uniforms;
    if (uniforms) for (const u of Object.values(uniforms)) if (u && u.value && (u.value as Texture).isTexture) textures.add(u.value as Texture);
  };
  for (const scene of [r.bgScene, r.skyScene, r.scene]) {
    scene.traverse((o) => {
      const mesh = o as Mesh;
      if (mesh.geometry) geos.add(mesh.geometry);
      const mats = Array.isArray(mesh.material) ? mesh.material : mesh.material ? [mesh.material] : [];
      for (const m of mats) addMat(m);
      const im = o as InstancedMesh;
      if (im.isInstancedMesh) instanceBytes += im.instanceMatrix.array.byteLength + (im.instanceColor ? im.instanceColor.array.byteLength : 0);
    });
  }
  let geometryBytes = instanceBytes;
  for (const g of geos) {
    for (const a of Object.values(g.attributes)) geometryBytes += (a as { array: ArrayBufferView }).array.byteLength;
    if (g.index) geometryBytes += g.index.array.byteLength;
  }
  // Chunk index buffers are shared; counted once via the Set.
  let texBytes = 0;
  for (const t of textures) texBytes += textureBytes(t);
  let targets = 0;
  for (const rt of r.composerTargets()) targets += targetBytes(rt);
  const shadow = game.lighting.sun.shadow;
  if (shadow.map) targets += shadow.mapSize.x * shadow.mapSize.y * 4 * 2;
  const env = game.lighting.envRenderTarget;
  if (env) targets += targetBytes(env);
  // Default framebuffer (color + depth) at the internal resolution.
  targets += r.size.x * r.size.y * 8 * (r.antialiasContext ? 4 : 1);
  const MB = 1048576;
  return {
    geometryMB: geometryBytes / MB,
    texturesMB: texBytes / MB,
    targetsMB: targets / MB,
    totalMB: (geometryBytes + texBytes + targets) / MB,
    geometries: geos.size,
    textures: textures.size,
  };
}
