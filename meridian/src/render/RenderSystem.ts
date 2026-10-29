import {
  ACESFilmicToneMapping,
  Camera,
  HalfFloatType,
  PCFShadowMap,
  PerspectiveCamera,
  Scene,
  SRGBColorSpace,
  Vector2,
  WebGLRenderer,
  WebGLRenderTarget,
} from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { Pass } from 'three/addons/postprocessing/Pass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { FXAAPass } from 'three/addons/postprocessing/FXAAPass.js';
import { PRESETS, type PresetSpec, type QualityPreset } from '../game/config';

/**
 * Draws the three world layers into the current target:
 * 1. scaled celestial background (stars, sun, distant body proxies) — clears color+depth
 * 2. atmosphere sky (full-screen, blends over the background)
 * 3. local scene after clearing depth only.
 */
export class WorldLayers {
  constructor(
    readonly bgScene: Scene,
    readonly bgCamera: Camera,
    readonly skyScene: Scene,
    readonly skyCamera: Camera,
    readonly scene: Scene,
    readonly camera: Camera,
  ) {}
  skyEnabled = true;

  draw(renderer: WebGLRenderer, target: WebGLRenderTarget | null): void {
    const oldAuto = renderer.autoClear;
    renderer.autoClear = false;
    renderer.setRenderTarget(target);
    renderer.setClearColor(0x000000, 1);
    renderer.clear(true, true, false);
    renderer.render(this.bgScene, this.bgCamera);
    if (this.skyEnabled) {
      renderer.clearDepth();
      renderer.render(this.skyScene, this.skyCamera);
    }
    renderer.clearDepth();
    renderer.render(this.scene, this.camera);
    renderer.autoClear = oldAuto;
  }
}

class WorldPass extends Pass {
  constructor(private layers: WorldLayers) {
    super();
    this.needsSwap = false;
  }
  override render(renderer: WebGLRenderer, _write: WebGLRenderTarget, read: WebGLRenderTarget): void {
    this.layers.draw(renderer, this.renderToScreen ? null : read);
  }
}

export interface RenderStats {
  calls: number;
  triangles: number;
  geometries: number;
  textures: number;
  width: number;
  height: number;
}

export class RenderSystem {
  readonly renderer: WebGLRenderer;
  readonly bgScene = new Scene();
  readonly skyScene = new Scene();
  readonly scene = new Scene();
  readonly camera: PerspectiveCamera;
  readonly bgCamera: PerspectiveCamera;
  readonly skyCamera: PerspectiveCamera;
  readonly layers: WorldLayers;
  readonly hdrSupported: boolean;
  readonly antialiasContext: boolean;
  private composer: EffectComposer | null = null;
  private bloomPass: UnrealBloomPass | null = null;
  private fxaaPass: FXAAPass | null = null;
  preset: QualityPreset;
  spec: PresetSpec;
  /** Adaptive resolution multiplier (0.5..1). */
  resolutionScale = 1;
  readonly size = new Vector2();
  readonly stats: RenderStats = { calls: 0, triangles: 0, geometries: 0, textures: 0, width: 0, height: 0 };

  constructor(readonly canvas: HTMLCanvasElement, preset: QualityPreset) {
    this.preset = preset;
    this.spec = PRESETS[preset];
    this.antialiasContext = preset === 'low';
    const context = canvas.getContext('webgl2', {
      antialias: this.antialiasContext,
      alpha: false,
      depth: true,
      stencil: false,
      powerPreference: 'high-performance',
      preserveDrawingBuffer: false,
    });
    if (!context) throw new WebGL2UnavailableError();
    this.renderer = new WebGLRenderer({
      canvas,
      context,
      antialias: this.antialiasContext,
      logarithmicDepthBuffer: true,
      powerPreference: 'high-performance',
    });
    const r = this.renderer;
    r.toneMapping = ACESFilmicToneMapping;
    r.toneMappingExposure = 1.05;
    r.outputColorSpace = SRGBColorSpace;
    r.shadowMap.enabled = true;
    r.shadowMap.type = PCFShadowMap;
    r.info.autoReset = false;
    this.hdrSupported =
      r.extensions.has('EXT_color_buffer_half_float') || r.extensions.has('EXT_color_buffer_float');

    this.camera = new PerspectiveCamera(70, 1, 0.1, 50000);
    this.bgCamera = new PerspectiveCamera(70, 1, 0.5, 4000);
    this.skyCamera = new PerspectiveCamera(70, 1, 0.1, 10);
    this.layers = new WorldLayers(this.bgScene, this.bgCamera, this.skyScene, this.skyCamera, this.scene, this.camera);
    this.applyPreset(preset);
  }

  get usingComposer(): boolean {
    return this.composer !== null;
  }

  /** Render targets owned by the post-processing chain (for memory estimates). */
  composerTargets(): WebGLRenderTarget[] {
    if (!this.composer) return [];
    const out = [this.composer.renderTarget1, this.composer.renderTarget2];
    const bloom = this.bloomPass as unknown as { renderTargetsHorizontal?: WebGLRenderTarget[]; renderTargetsVertical?: WebGLRenderTarget[]; renderTargetBright?: WebGLRenderTarget } | null;
    if (bloom) out.push(...(bloom.renderTargetsHorizontal ?? []), ...(bloom.renderTargetsVertical ?? []), ...(bloom.renderTargetBright ? [bloom.renderTargetBright] : []));
    return out;
  }

  applyPreset(preset: QualityPreset): void {
    this.preset = preset;
    this.spec = PRESETS[preset];
    this.disposeComposer();
    if (this.spec.composer && this.hdrSupported) {
      const target = new WebGLRenderTarget(4, 4, { type: HalfFloatType, depthBuffer: true, stencilBuffer: false });
      const composer = new EffectComposer(this.renderer, target);
      composer.addPass(new WorldPass(this.layers));
      if (this.spec.bloom) {
        this.bloomPass = new UnrealBloomPass(new Vector2(256, 256), 0.28, 0.4, 3.0);
        composer.addPass(this.bloomPass);
      }
      composer.addPass(new OutputPass());
      this.fxaaPass = new FXAAPass();
      composer.addPass(this.fxaaPass);
      this.composer = composer;
    }
    this.resize();
  }

  private disposeComposer(): void {
    if (!this.composer) return;
    for (const p of this.composer.passes) p.dispose();
    this.composer.renderTarget1.dispose();
    this.composer.renderTarget2.dispose();
    this.composer = null;
    this.bloomPass = null;
    this.fxaaPass = null;
  }

  /** Resize to the canvas' CSS size, honoring the preset's internal resolution ceiling. */
  resize(): void {
    const cssW = Math.max(1, this.canvas.clientWidth || window.innerWidth);
    const cssH = Math.max(1, this.canvas.clientHeight || window.innerHeight);
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = cssW * dpr;
    const h = cssH * dpr;
    const ceilingArea = this.spec.maxWidth * this.spec.maxHeight;
    let scale = Math.min(1, Math.sqrt(ceilingArea / (w * h)));
    scale *= this.resolutionScale;
    const ratio = dpr * scale;
    this.renderer.setPixelRatio(ratio);
    this.renderer.setSize(cssW, cssH, false);
    this.renderer.getDrawingBufferSize(this.size);
    const aspect = cssW / cssH;
    for (const cam of [this.camera, this.bgCamera, this.skyCamera]) {
      cam.aspect = aspect;
      cam.updateProjectionMatrix();
    }
    if (this.composer) {
      this.composer.setPixelRatio(ratio);
      this.composer.setSize(cssW, cssH);
    }
  }

  setBloomStrength(s: number): void {
    if (this.bloomPass) this.bloomPass.strength = s;
  }

  render(): void {
    this.renderer.info.reset();
    if (this.composer) this.composer.render();
    else this.layers.draw(this.renderer, null);
    const info = this.renderer.info;
    this.stats.calls = info.render.calls;
    this.stats.triangles = info.render.triangles;
    this.stats.geometries = info.memory.geometries;
    this.stats.textures = info.memory.textures;
    this.stats.width = this.size.x;
    this.stats.height = this.size.y;
  }
}

export class WebGL2UnavailableError extends Error {
  constructor() {
    super('WebGL 2 is not available in this browser or on this device.');
    this.name = 'WebGL2UnavailableError';
  }
}
