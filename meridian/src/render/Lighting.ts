import {
  BackSide,
  Color,
  DirectionalLight,
  HemisphereLight,
  Matrix4,
  Mesh,
  PMREMGenerator,
  Scene,
  ShaderMaterial,
  SphereGeometry,
  Texture,
  Vector3,
  type WebGLRenderer,
  type WebGLRenderTarget,
} from 'three';
import { LIGHT } from '../game/config';
import { BODIES, SUN_DIR, SYSTEM_BODY_IDS, sunDirFor, type BodyDef } from '../world/bodies';
import { AU_KM, POSITION_DIVISOR } from '../world/scale';
import { atmoUniforms, cpuScatter, sunTransCPU } from './Atmosphere';

const _m = new Matrix4();
const _mi = new Matrix4();
const _p = new Vector3();
const _up = new Vector3();
const _c = new Color();
const _ro = new Vector3();
const _rel = new Vector3();
const _toStar = new Vector3();

/** Flux is relative to the Sun's luminosity at 1 AU. */
const L_SUN = BODIES.sun.real!.luminosityW!;
/** A reference change that swings the light further than this snaps instead of slewing (rad). */
const SNAP_ANGLE = Math.PI / 4;
/** Below this the slewed direction takes the target exactly (rad). */
const SETTLED_ANGLE = 1e-5;

/** Where the light comes from at the focus (system frame; also the local frame, which is only translated). */
export interface StarLight {
  /** Unit direction toward the star. */
  readonly dir: Vector3;
  /** Focus to star center [m]; Infinity for the Quiet System's fixed, infinitely distant sun. */
  distance: number;
  /** Angular radius of the star's disc seen from the focus [rad]; null without a catalog star. */
  angularRadius: number | null;
  /** Irradiance relative to 1 AU from the Sun. */
  flux: number;
}

/** The star of a body's system (its kind-'star' catalog body), or null (the Quiet System has none). */
export function starOf(def: BodyDef): BodyDef | null {
  for (const id of SYSTEM_BODY_IDS[def.system]) {
    if (BODIES[id].kind === 'star') return BODIES[id];
  }
  return null;
}

/**
 * The light at a focus point `focusRel` (focus − ref center, m), written into `out`.
 * Without a star (Quiet System, or no reference) it is SUN_DIR at flux 1.
 * `perBody` (an active body): every point on the body shares sunDirFor(ref), so
 * local terrain, sky, proxy and landing sites agree. In open space, or with the
 * star itself as the reference, it is the true direction from the focus to the
 * star. Flux follows the inverse square of the real distance (the reference
 * body's heliocentric distance; the scaled-up focus distance near the star).
 */
export function starLight(ref: BodyDef | null, focusRel: Vector3, perBody: boolean, out: StarLight): StarLight {
  const star = ref ? starOf(ref) : null;
  if (!ref || !star) {
    out.dir.set(SUN_DIR[0], SUN_DIR[1], SUN_DIR[2]);
    out.distance = Infinity;
    out.angularRadius = null;
    out.flux = 1;
    return out;
  }
  const s = star.center;
  const c = ref.center;
  _toStar.set(s[0] - c[0], s[1] - c[1], s[2] - c[2]).sub(focusRel);
  const d = _toStar.length();
  out.distance = d;
  out.angularRadius = Math.asin(Math.min(1, star.radius / d));
  if (d > 0 && (ref === star || !perBody)) {
    out.dir.copy(_toStar).divideScalar(d);
  } else {
    const v = sunDirFor(ref);
    out.dir.set(v[0], v[1], v[2]);
  }
  let km = (d * POSITION_DIVISOR) / 1000;
  if (ref !== star && ref.real && star.real) {
    const a = ref.real.positionKm;
    const b = star.real.positionKm;
    km = Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
  }
  out.flux = ((star.real?.luminosityW ?? L_SUN) / L_SUN) * (AU_KM / km) ** 2;
  return out;
}

/** Display brightness for a relative flux: a soft power, clamped (adaptation, not physics). */
export function lightScale(flux: number): number {
  return Math.min(LIGHT.maxScale, Math.max(LIGHT.minScale, flux ** LIGHT.fluxGamma));
}

/**
 * Sun + ambient + environment reflections: direction and brightness from the
 * reference body's star (starLight), color and sky from its atmosphere.
 */
export class Lighting {
  readonly sun: DirectionalLight;
  readonly hemi: HemisphereLight;
  readonly sunColor = new Color(1, 1, 1);
  readonly skyColor = new Color();
  /** Unit direction toward the light; slews toward `star.dir` (LIGHT.slewTau). */
  readonly sunDir = new Vector3(SUN_DIR[0], SUN_DIR[1], SUN_DIR[2]);
  /** The target light at the focus from the last update. */
  readonly star: StarLight = { dir: new Vector3(SUN_DIR[0], SUN_DIR[1], SUN_DIR[2]), distance: Infinity, angularRadius: null, flux: 1 };
  /** Brightness scale (lightScale of the flux), slewed with the direction. */
  fluxScale = 1;
  private snapNext = true;
  extent = 70;
  private pmrem: PMREMGenerator;
  private envTarget: WebGLRenderTarget | null = null;
  private readonly envScene = new Scene();
  private readonly envMat: ShaderMaterial;
  private envKey = '';
  private envTimer = 0;
  private ambientTimer = 0;
  envMap: Texture | null = null;

  /** The PMREM render target behind the environment map (for memory estimates). */
  get envRenderTarget(): WebGLRenderTarget | null {
    return this.envTarget;
  }
  /** Called when the env map changes so materials can be updated. */
  onEnvChange: ((t: Texture) => void) | null = null;

  constructor(renderer: WebGLRenderer, scene: Scene, shadowSize: number) {
    this.sun = new DirectionalLight(0xffffff, 3);
    this.sun.castShadow = true;
    this.setShadowSize(shadowSize);
    const cam = this.sun.shadow.camera;
    cam.near = 1;
    cam.far = 1400;
    this.sun.shadow.bias = -0.00006;
    this.sun.shadow.normalBias = 0.05;
    scene.add(this.sun, this.sun.target);
    this.hemi = new HemisphereLight(0x9fc4cc, 0x3a2c1c, 0.5);
    scene.add(this.hemi);

    this.pmrem = new PMREMGenerator(renderer);
    this.envMat = new ShaderMaterial({
      uniforms: {
        uUp: { value: new Vector3(0, 1, 0) },
        uSun: { value: this.sunDir.clone() },
        uZenith: { value: new Color() },
        uHorizon: { value: new Color() },
        uGround: { value: new Color() },
        uSunCol: { value: new Color() },
      },
      vertexShader: /* glsl */ `varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
      fragmentShader: /* glsl */ `
        varying vec3 vDir;
        uniform vec3 uUp, uSun, uZenith, uHorizon, uGround, uSunCol;
        void main(){
          float h = dot(normalize(vDir), uUp);
          vec3 sky = mix(uHorizon, uZenith, smoothstep(0.0, 0.6, h));
          vec3 c = h > 0.0 ? sky : mix(uHorizon * 0.5, uGround, smoothstep(0.0, -0.25, h));
          float s = max(dot(normalize(vDir), uSun), 0.0);
          c += uSunCol * (pow(s, 600.0) * 30.0 + pow(s, 12.0) * 0.25);
          gl_FragColor = vec4(c, 1.0);
        }`,
      side: BackSide,
      depthWrite: false,
    });
    this.envScene.add(new Mesh(new SphereGeometry(10, 32, 16), this.envMat));
  }

  setShadowSize(n: number): void {
    const s = this.sun.shadow;
    if (s.mapSize.x === n) return;
    s.mapSize.set(n, n);
    if (s.map) {
      s.map.dispose();
      s.map = null;
    }
  }

  /** Take the target light on the next update instead of slewing to it (teleports, restores). */
  snap(): void {
    this.snapNext = true;
  }

  /**
   * @param focus local position the shadow box follows
   * @param ref the reference body (active, else dominant), or null in deep space
   * @param refCenter local position of the reference body's center (or null in deep space)
   * @param perBody true while a body is active: light the whole body from sunDirFor(ref)
   */
  update(
    dt: number,
    focus: Vector3,
    ref: BodyDef | null,
    refCenter: Vector3 | null,
    groundAlbedo: Color,
    perBody: boolean,
    allowEnvRebuild = true,
  ): void {
    // Direction and flux from the reference body's star. Lighting is the single
    // writer of the shared sun direction (sky, aerial perspective, clouds).
    if (refCenter) _rel.copy(focus).sub(refCenter);
    else _rel.set(0, 0, 0);
    starLight(ref, _rel, perBody, this.star);
    this.slew(dt);
    const sunDir = this.sunDir;
    atmoUniforms.uSunDir.value.copy(sunDir);

    // A star is lit like open space: no transmittance, no planetary shadow.
    const def = ref && ref.kind !== 'star' ? ref : null;
    const planetCenter = def ? refCenter : null;

    // Sun color/intensity from atmospheric transmittance at the focus.
    let altitude = 1e9;
    let mu = 1;
    if (def && planetCenter) {
      _up.copy(focus).sub(planetCenter);
      const r = _up.length();
      _up.divideScalar(r);
      altitude = r - def.radius;
      mu = _up.dot(sunDir);
    } else {
      _up.set(0, 1, 0);
    }
    if (def && def.atmosphere && altitude < def.atmosphereHeight * 1.5) {
      this.sunColor.setRGB(
        sunTransCPU(def, Math.max(altitude, 0), mu, 0),
        sunTransCPU(def, Math.max(altitude, 0), mu, 1),
        sunTransCPU(def, Math.max(altitude, 0), mu, 2),
      );
    } else if (def && planetCenter && !def.atmosphere) {
      // Airless: hard planetary shadow with a narrow penumbra. It is a single
      // light color, so it only applies near the surface (where everything in
      // view shares the focus's illumination); from orbit N.L shades the globe.
      const muH = -Math.sqrt(Math.max(0, 1 - (def.radius / (def.radius + Math.max(altitude, 0))) ** 2));
      const lit = Math.min(1, Math.max(0, (mu - muH + 0.006) / 0.012));
      const v = lit + (1 - lit) * Math.min(1, Math.max(0, (altitude - 2000) / 6000));
      this.sunColor.setRGB(v, v, v);
    } else {
      this.sunColor.setRGB(1, 1, 1);
    }
    this.sun.color.setRGB(1.0, 0.96, 0.9).multiply(this.sunColor);
    this.sun.intensity = LIGHT.sunIntensity * this.fluxScale;

    // Shadow box follows the focus; snap to shadow texels in light space.
    const texel = (2 * this.extent) / this.sun.shadow.mapSize.x;
    _m.lookAt(_p.set(0, 0, 0), sunDir.clone().negate(), _up);
    _mi.copy(_m).invert();
    _p.copy(focus).applyMatrix4(_mi);
    _p.x = Math.round(_p.x / texel) * texel;
    _p.y = Math.round(_p.y / texel) * texel;
    _p.applyMatrix4(_m);
    this.sun.target.position.copy(_p);
    this.sun.position.copy(_p).addScaledVector(sunDir, 700);
    const cam = this.sun.shadow.camera;
    if (cam.right !== this.extent) {
      cam.left = -this.extent;
      cam.right = this.extent;
      cam.top = this.extent;
      cam.bottom = -this.extent;
      cam.updateProjectionMatrix();
    }
    this.sun.target.updateMatrixWorld();

    // Ambient from the sky (throttled).
    this.ambientTimer -= dt;
    if (this.ambientTimer <= 0) {
      this.ambientTimer = 0.25;
      if (def && def.atmosphere && planetCenter && altitude < def.atmosphereHeight * 2) {
        _ro.copy(focus).sub(planetCenter);
        cpuScatter(def, _ro, _up, 10, _c);
        this.skyColor.copy(_c);
      } else {
        this.skyColor.setRGB(0.02, 0.022, 0.03);
      }
      const day = Math.max(0, Math.min(1, (mu + 0.08) / 0.4));
      const sky = this.skyColor.clone().multiplyScalar(3.2);
      sky.r = Math.max(sky.r, 0.035);
      sky.g = Math.max(sky.g, 0.04);
      sky.b = Math.max(sky.b, 0.05);
      this.hemi.color.copy(sky);
      this.hemi.groundColor.copy(groundAlbedo).multiplyScalar(0.22 * day + 0.02).multiply(this.sunColor.clone().addScalar(0.15));
      this.hemi.intensity = 1.35;
    }
    // Sky light comes from the local radial up, not the world +Y axis.
    this.hemi.position.copy(_up);

    // Environment map: regenerate when the sky state changes meaningfully.
    this.envTimer -= dt;
    if (this.envTimer <= 0 && allowEnvRebuild) {
      this.envTimer = 1.5;
      const key = [
        def?.id ?? 'space',
        Math.round(Math.min(altitude, 20000) / 2500),
        Math.round(mu * 8),
        Math.round(_up.x * 6), Math.round(_up.y * 6), Math.round(_up.z * 6),
        Math.round(sunDir.x * 6), Math.round(sunDir.y * 6), Math.round(sunDir.z * 6),
      ].join(',');
      if (key !== this.envKey) {
        this.envKey = key;
        this.rebuildEnv(_up, groundAlbedo);
      }
    }
  }

  /** Slew the light direction and brightness toward the target (snap on request or for large swings). */
  private slew(dt: number): void {
    const target = this.star.dir;
    const angle = this.sunDir.angleTo(target);
    const k = this.snapNext || angle > SNAP_ANGLE ? 1 : 1 - Math.exp(-dt / LIGHT.slewTau);
    this.snapNext = false;
    if (k === 1 || angle < SETTLED_ANGLE) this.sunDir.copy(target);
    else this.sunDir.lerp(target, k).normalize();
    const scale = lightScale(this.star.flux);
    this.fluxScale = k === 1 ? scale : this.fluxScale + (scale - this.fluxScale) * k;
  }

  private rebuildEnv(up: Vector3, ground: Color): void {
    const u = this.envMat.uniforms;
    u.uUp.value.copy(up);
    u.uSun.value.copy(this.sunDir);
    const zen = this.hemi.color.clone();
    u.uZenith.value.copy(zen);
    u.uHorizon.value.copy(zen).lerp(this.sunColor, 0.25).multiplyScalar(1.3);
    u.uGround.value.copy(ground).multiplyScalar(0.25).multiply(this.sunColor.clone().addScalar(0.1));
    u.uSunCol.value.copy(this.sunColor);
    const prev = this.envTarget;
    this.envTarget = this.pmrem.fromScene(this.envScene, 0.02);
    this.envMap = this.envTarget.texture;
    this.onEnvChange?.(this.envMap);
    prev?.dispose();
  }

  dispose(): void {
    this.envTarget?.dispose();
    this.pmrem.dispose();
  }
}

