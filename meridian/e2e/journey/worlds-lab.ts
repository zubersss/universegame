// WORLDS lab: renders one body with the game's own terrain, proxy, atmosphere
// and sky modules, from a camera given in the URL, so surfaces can be checked in
// a browser before they are wired into travel. Dev server only (see
// worlds-earth.spec.ts). Query: body, lat, lon (deg), alt (m above ground, or
// above the datum when `orbit` is set), heading (deg from north), pitch (deg
// below the horizon), fov, orbit (distance in body radii; looks at the body,
// or toward the Sun with look=sun).

import {
  ACESFilmicToneMapping,
  Color,
  DirectionalLight,
  Frustum,
  HemisphereLight,
  Matrix4,
  PerspectiveCamera,
  Quaternion,
  Scene,
  SRGBColorSpace,
  Vector3,
  WebGLRenderer,
} from 'three';
import { BODIES, sunDirFor } from '../../src/world/bodies';
import { ensureBodyData, getSurface } from '../../src/world/surface';
import { computeSites } from '../../src/world/sites';
import { ChunkStore, WorkerBackend } from '../../src/terrain/ChunkStore';
import { TerrainManager, type TerrainView } from '../../src/terrain/TerrainManager';
import { createTerrainMaterials, makeTerrainUniforms, setTerrainPalette } from '../../src/terrain/terrainMaterial';
import { createWaterMaterial, SEA_WATER } from '../../src/terrain/waterMaterial';
import { makeTerrainDetailTexture } from '../../src/render/terrainTextures';
import { atmoUniforms, createSkyMesh, setAtmosphereBody, updateSkyMesh } from '../../src/render/Atmosphere';
import { BodyProxies } from '../../src/render/BodyProxies';
import { Clouds } from '../../src/render/Clouds';
import { Space } from '../../src/render/Space';

interface LabState {
  ready: boolean;
  settled: boolean;
  frames: number;
  errors: string[];
  stats: Record<string, number>;
  /** Set true to read back the next frame: mean/std of luminance and the share of sea-blue and land pixels. */
  requestPixels: boolean;
  pixels: { mean: number; std: number; blue: number; land: number } | null;
}

const lab: LabState = { ready: false, settled: false, frames: 0, errors: [], stats: {}, requestPixels: false, pixels: null };
(window as unknown as { __lab: LabState }).__lab = lab;
window.addEventListener('error', (e) => lab.errors.push(String(e.message)));
window.addEventListener('unhandledrejection', (e) => lab.errors.push(String(e.reason)));

const q = new URLSearchParams(location.search);
const num = (k: string, d: number) => (q.has(k) ? Number(q.get(k)) : d);
const def = BODIES[q.get('body') ?? 'earth'];
/** Debug: which layers to draw (bg = proxies, sky, scene = terrain and lights, clouds). */
const layers = (q.get('layers') ?? 'bg,sky,scene,clouds').split(',');
if (!def) throw new Error(`Unknown body ${q.get('body')}`);

function dirOf(lat: number, lon: number): Vector3 {
  const f = def.frame;
  const a = (lat * Math.PI) / 180;
  const o = (lon * Math.PI) / 180;
  const c = Math.cos(a);
  return new Vector3(
    c * Math.cos(o) * f.meridian[0] + c * Math.sin(o) * f.east[0] + Math.sin(a) * f.north[0],
    c * Math.cos(o) * f.meridian[1] + c * Math.sin(o) * f.east[1] + Math.sin(a) * f.north[1],
    c * Math.cos(o) * f.meridian[2] + c * Math.sin(o) * f.east[2] + Math.sin(a) * f.north[2],
  ).normalize();
}

async function main(): Promise<void> {
  await ensureBodyData(def);
  const canvas = document.getElementById('c') as HTMLCanvasElement;
  const renderer = new WebGLRenderer({ canvas, antialias: true, logarithmicDepthBuffer: true });
  renderer.toneMapping = ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.setPixelRatio(1);
  renderer.setSize(canvas.clientWidth || innerWidth, canvas.clientHeight || innerHeight, false);
  const aspect = (canvas.clientWidth || innerWidth) / (canvas.clientHeight || innerHeight);
  const fov = num('fov', 60);
  const camera = new PerspectiveCamera(fov, aspect, 0.5, 2e7);
  const bgCamera = new PerspectiveCamera(fov, aspect, 0.5, 4000);
  const skyCamera = new PerspectiveCamera(fov, aspect, 0.1, 10);
  const scene = new Scene();
  const bgScene = new Scene();
  const skyScene = new Scene();

  // Camera placement (body frame -> system axes; the local scene is camera-centred).
  const R = def.radius;
  const gen = getSurface(def, computeSites(def).clearings);
  const lat = num('lat', 0);
  const lon = num('lon', 0);
  const up = dirOf(lat, lon);
  const orbit = num('orbit', 0);
  const camPlanet = new Vector3();
  const quat = new Quaternion();
  if (orbit > 0) {
    camPlanet.copy(up).multiplyScalar(R * orbit);
    // look=sun turns the orbit camera toward the Sun (checks the Space sun disc and eclipses).
    const target = q.get('look') === 'sun' ? camPlanet.clone().add(new Vector3(...sunDirFor(def))) : new Vector3();
    const m = new Matrix4().lookAt(camPlanet, target, new Vector3(...def.frame.north));
    quat.setFromRotationMatrix(m);
  } else {
    const ground = gen.height(up.x, up.y, up.z);
    camPlanet.copy(up).multiplyScalar(R + ground + num('alt', 500));
    const north = new Vector3(...def.frame.north);
    const n = north.clone().addScaledVector(up, -north.dot(up)).normalize();
    const e = new Vector3().crossVectors(n, up).normalize();
    const h = (num('heading', 0) * Math.PI) / 180;
    const fwd = n.clone().multiplyScalar(Math.cos(h)).addScaledVector(e, Math.sin(h));
    const p = (num('pitch', 10) * Math.PI) / 180;
    fwd.multiplyScalar(Math.cos(p)).addScaledVector(up, -Math.sin(p)).normalize();
    const m = new Matrix4().lookAt(new Vector3(), fwd, up);
    quat.setFromRotationMatrix(m);
  }
  camera.quaternion.copy(quat);
  camera.updateMatrixWorld();
  const planetLocal = camPlanet.clone().negate();

  // Lights: the Sun from its real direction relative to this body.
  const sunDir = new Vector3(...sunDirFor(def));
  const sun = new DirectionalLight(new Color(1.0, 0.96, 0.9), 5.2);
  sun.position.copy(sunDir).multiplyScalar(1000);
  scene.add(sun, sun.target);
  const hemi = new HemisphereLight(0x9fc4cc, 0x3a2c1c, 0.35);
  hemi.position.copy(up);
  scene.add(hemi);
  atmoUniforms.uSunDir.value.copy(sunDir);
  setAtmosphereBody(def);
  atmoUniforms.uPlanetCenter.value.copy(planetLocal);
  const sky = createSkyMesh(24);
  skyScene.add(sky);

  // Terrain, fed by the proxy worker's level-0 roots like the game.
  const store = new ChunkStore(new WorkerBackend(), def.id);
  const proxies = new BodyProxies(bgScene, new WorkerBackend('proxy'), 8, 16, 1, [def.id]);
  proxies.onRoot = (d) => store.seed(d);
  proxies.light.sunColor.setRGB(1.0, 0.96, 0.9).multiplyScalar(5.2);
  const uniforms = makeTerrainUniforms(makeTerrainDetailTexture(256));
  setTerrainPalette(uniforms, def);
  const terrainMaterials = createTerrainMaterials(uniforms, 8, false);
  if (q.get('debug') === 'wire') for (const m of terrainMaterials) m.wireframe = true;
  const terrain = new TerrainManager(def, store, terrainMaterials);
  const water = def.seaLevel != null ? createWaterMaterial(SEA_WATER, 8, false) : null;
  terrain.waterMaterial = water?.material ?? null;
  terrain.maxChunks = 260;
  terrain.splitPx = 4;
  store.onData = (d) => { if (d.level === 0) proxies.addRoot(d); };
  scene.add(terrain.root);
  const space = new Space();
  bgScene.add(space.group);
  const sunDef = def.system === 'sol' ? BODIES.sun : null;
  const clouds = new Clouds();
  clouds.setBody(def, 1);
  scene.add(clouds.group);
  // The game swaps proxy and terrain at 3 radii; force=proxy|terrain compares both at one distance.
  const force = q.get('force');
  const showTerrain = force === 'proxy' ? false : force === 'terrain' ? true : orbit === 0 || orbit < 3;
  if (!showTerrain) {
    // As in the game: a body not shown locally has no local sky or cloud shells (its proxy draws them).
    setAtmosphereBody(null);
    clouds.setBody(null, 0);
  }

  const frustum = new Frustum();
  const view: TerrainView = {
    camPlanet, frustum, planetLocal, fovY: (fov * Math.PI) / 180, viewportH: renderer.domElement.height,
    focusPlanet: camPlanet.clone(), contactRadius: 150,
  };
  const hud = document.getElementById('hud')!;
  let lastChange = performance.now();
  let lastSig = '';
  let t0 = performance.now();
  lab.ready = true;

  const frame = () => {
    const now = performance.now();
    const dt = Math.min(0.25, (now - t0) / 1000);
    t0 = now;
    terrain.root.position.copy(planetLocal);
    camera.updateMatrixWorld();
    frustum.setFromProjectionMatrix(new Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse));
    if (showTerrain) {
      terrain.update(view);
      terrain.updateMorphs(dt);
      if (water) water.uniforms.uWaterTime.value += dt;
      terrain.cullMeshes(view);
    }
    terrain.root.visible = showTerrain;
    bgCamera.quaternion.copy(camera.quaternion);
    bgCamera.updateMatrixWorld();
    const camSys = new Vector3(...def.center).add(camPlanet);
    // Stars fade in a daylit sky (the game does this from the sky luminance).
    const inAir = showTerrain && def.atmosphere != null && camPlanet.length() < R + def.atmosphereHeight;
    const sunUp = camPlanet.clone().normalize().dot(sunDir);
    const starFade = inAir ? 1 - Math.min(1, Math.max(0, (sunUp + 0.1) / 0.15)) : 1;
    if (sunDef) {
      const toSun = new Vector3(...sunDef.center).sub(camSys);
      const dist = toSun.length();
      space.update(bgCamera.quaternion, 1, starFade, { dir: toSun.normalize(), angularRadius: Math.asin(Math.min(1, sunDef.radius / dist)), distance: dist });
    } else space.update(bgCamera.quaternion, 1, starFade);
    proxies.update(camSys, showTerrain ? def.id : null, now / 1000);
    if (q.get('debug') === 'nowater') for (const p of proxies.proxies.values()) if (p.water) p.water.visible = false;
    if (q.get('debug') === 'noclouds') for (const p of proxies.proxies.values()) p.clouds.group.visible = false;
    if (q.get('debug') === 'noshell') for (const p of proxies.proxies.values()) if (p.shell) p.shell.visible = false;
    clouds.update(now / 1000, planetLocal, new Color(0.3, 0.4, 0.5));
    updateSkyMesh(sky, camera);
    renderer.autoClear = false;
    renderer.setClearColor(0x000000, 1);
    renderer.clear(true, true, false);
    if (layers.includes('bg')) renderer.render(bgScene, bgCamera);
    renderer.clearDepth();
    if (layers.includes('sky')) renderer.render(skyScene, skyCamera);
    renderer.clearDepth();
    clouds.group.visible = layers.includes('clouds');
    if (layers.includes('scene')) renderer.render(scene, camera);
    if (lab.requestPixels) {
      // Read back in the same task as the draw (the buffer is not preserved afterwards).
      const gl = renderer.getContext();
      const w = gl.drawingBufferWidth;
      const h = gl.drawingBufferHeight;
      const px = new Uint8Array(w * h * 4);
      gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
      let sum = 0;
      let sum2 = 0;
      let blue = 0;
      let land = 0;
      const n = w * h;
      for (let i = 0; i < n; i++) {
        const r = px[i * 4], g = px[i * 4 + 1], b = px[i * 4 + 2];
        const y = 0.2126 * r + 0.7152 * g + 0.0722 * b;
        sum += y;
        sum2 += y * y;
        if (b > r + 12 && b > g) blue++;
        else if (y > 25 && (g >= b || r >= b)) land++;
      }
      const mean = sum / n;
      lab.pixels = { mean, std: Math.sqrt(Math.max(0, sum2 / n - mean * mean)), blue: blue / n, land: land / n };
      lab.requestPixels = false;
    }
    lab.frames++;
    const s = terrain.stats;
    lab.stats = { leaves: s.leaves, rendered: s.rendered, morphing: s.morphing, maxLevel: s.maxLevel, queued: store.queued, inFlight: store.inFlightCount, proxies: proxies.readyCount, errors: store.errors, calls: renderer.info.render.calls };
    const sig = `${s.leaves}/${s.rendered}/${s.maxLevel}/${store.queued}/${store.inFlightCount}/${proxies.readyCount}`;
    if (sig !== lastSig) { lastSig = sig; lastChange = now; }
    lab.settled = proxies.readyCount > 0 && store.queued === 0 && store.inFlightCount === 0 && s.morphing === 0 && now - lastChange > 1500 && lab.frames > 5;
    hud.textContent = `${def.name}  lat ${lat.toFixed(2)}  lon ${lon.toFixed(2)}  ${orbit ? `orbit ${orbit} R` : `alt ${num('alt', 500)} m`}\nchunks ${s.rendered}  max level ${s.maxLevel}  queue ${store.queued}`;
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
}

main().catch((e: unknown) => {
  lab.errors.push(e instanceof Error ? `${e.message}\n${e.stack}` : String(e));
  console.error(e);
});
