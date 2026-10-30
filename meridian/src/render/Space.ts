import {
  AdditiveBlending,
  BackSide,
  BufferGeometry,
  Color,
  Float32BufferAttribute,
  Group,
  Mesh,
  PlaneGeometry,
  Points,
  ShaderMaterial,
  SphereGeometry,
  Vector3,
} from 'three';
import { mulberry32, hashCombine } from '../core/rng';
import { SUN_DIR, WORLD_SEED } from '../world/bodies';
import { BG_SCALE } from './BodyProxies';

const STAR_RADIUS = 3000;
const SUN_DISTANCE = 2600;
/** Disc angular radius of the fixed far-away sun (its original look) [rad]. */
const SUN_THETA = (0.085 * 150) / SUN_DISTANCE;
/** The glare reaches this far beyond the limb [rad]; the billboard covers it. */
const SUN_GLARE = 0.06;

const PLANE_NORMAL = new Vector3(0, 0, 1);
const NEG = new Vector3();

/** Seeded starfield, faint galactic band and sun disk for the scaled background scene. */
export class Space {
  readonly group = new Group();
  readonly stars: Points;
  readonly sun: Mesh;
  private readonly starMat: ShaderMaterial;
  private readonly sunMat: ShaderMaterial;

  constructor(starCount = 7000) {
    const rand = mulberry32(hashCombine(WORLD_SEED, 'stars'));
    const pos: number[] = [];
    const col: number[] = [];
    const size: number[] = [];
    // A gently tilted galactic plane concentrates a share of the stars.
    const galN = new Vector3(0.32, 0.86, -0.4).normalize();
    const tmp = new Vector3();
    const c = new Color();
    for (let i = 0; i < starCount; i++) {
      // Uniform direction.
      let z = rand() * 2 - 1;
      let phi = rand() * Math.PI * 2;
      let r = Math.sqrt(1 - z * z);
      tmp.set(r * Math.cos(phi), z, r * Math.sin(phi));
      if (i % 3 === 0) {
        // Pull toward the galactic plane.
        const d = tmp.dot(galN);
        tmp.addScaledVector(galN, -d * 0.85).normalize();
      }
      pos.push(tmp.x * STAR_RADIUS, tmp.y * STAR_RADIUS, tmp.z * STAR_RADIUS);
      const t = rand();
      // Mostly white, a few warm and cool stars.
      if (t < 0.12) c.setRGB(1.0, 0.78, 0.58);
      else if (t < 0.22) c.setRGB(0.7, 0.82, 1.0);
      else c.setRGB(1.0, 0.97, 0.92);
      const mag = rand();
      const b = 0.25 + mag * mag * mag * 2.2;
      col.push(c.r * b, c.g * b, c.b * b);
      size.push(1.1 + mag * mag * 2.4);
    }
    const g = new BufferGeometry();
    g.setAttribute('position', new Float32BufferAttribute(pos, 3));
    g.setAttribute('color', new Float32BufferAttribute(col, 3));
    g.setAttribute('size', new Float32BufferAttribute(size, 1));
    this.starMat = new ShaderMaterial({
      uniforms: {
        uPixelRatio: { value: 1 },
        uFade: { value: 1 },
        uSunDir: { value: new Vector3(SUN_DIR[0], SUN_DIR[1], SUN_DIR[2]) },
        uGlareCos: { value: new Vector3(2, 3, 0) }, // cos of the outer and inner glare angles (> 1: no glare)
      },
      vertexShader: /* glsl */ `
        attribute float size;
        attribute vec3 color;
        varying vec3 vColor;
        uniform float uPixelRatio;
        uniform vec3 uSunDir;
        uniform vec3 uGlareCos;
        #include <common>
        #include <logdepthbuf_pars_vertex>
        void main() {
          // Glare: stars close to the Sun are lost in its light.
          float cs = dot(normalize((modelMatrix * vec4(position, 1.0)).xyz - cameraPosition), uSunDir);
          vColor = color * (1.0 - smoothstep(uGlareCos.x, uGlareCos.y, cs));
          vec4 mv = modelViewMatrix * vec4(position, 1.0);
          gl_Position = projectionMatrix * mv;
          gl_PointSize = size * uPixelRatio;
          #include <logdepthbuf_vertex>
        }`,
      fragmentShader: /* glsl */ `
        varying vec3 vColor;
        uniform float uFade;
        #include <common>
        #include <logdepthbuf_pars_fragment>
        void main() {
          #include <logdepthbuf_fragment>
          vec2 d = gl_PointCoord - 0.5;
          float a = smoothstep(0.5, 0.05, length(d));
          gl_FragColor = vec4(vColor * a * uFade, 1.0);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,
      blending: AdditiveBlending,
      depthWrite: false,
      transparent: true,
    });
    this.stars = new Points(g, this.starMat);
    this.stars.frustumCulled = false;
    this.stars.renderOrder = -10;

    // Faint galactic band / color field.
    const bandMat = new ShaderMaterial({
      uniforms: { uGalN: { value: galN } },
      vertexShader: /* glsl */ `
        varying vec3 vDir;
        #include <common>
        #include <logdepthbuf_pars_vertex>
        void main() {
          vDir = normalize(position);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          #include <logdepthbuf_vertex>
        }`,
      fragmentShader: /* glsl */ `
        varying vec3 vDir;
        uniform vec3 uGalN;
        #include <common>
        #include <logdepthbuf_pars_fragment>
        float h31(vec3 p){ p = fract(p*0.3183099+0.1); p*=17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
        float vnoise(vec3 x){ vec3 i=floor(x); vec3 f=fract(x); f=f*f*(3.0-2.0*f);
          return mix(mix(mix(h31(i),h31(i+vec3(1,0,0)),f.x),mix(h31(i+vec3(0,1,0)),h31(i+vec3(1,1,0)),f.x),f.y),
                     mix(mix(h31(i+vec3(0,0,1)),h31(i+vec3(1,0,1)),f.x),mix(h31(i+vec3(0,1,1)),h31(i+vec3(1,1,1)),f.x),f.y),f.z); }
        void main() {
          #include <logdepthbuf_fragment>
          float lat = dot(vDir, uGalN);
          float band = exp(-lat*lat*18.0);
          float n = vnoise(vDir*6.0)*0.6 + vnoise(vDir*13.0)*0.3 + vnoise(vDir*29.0)*0.1;
          vec3 c = mix(vec3(0.010,0.012,0.020), vec3(0.030,0.024,0.020), n) * band * (0.5 + n);
          c += vec3(0.0025,0.003,0.005);
          gl_FragColor = vec4(c, 1.0);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,
      side: BackSide,
      depthWrite: false,
    });
    const band = new Mesh(new SphereGeometry(STAR_RADIUS * 1.1, 48, 24), bandMat);
    band.renderOrder = -20;
    band.frustumCulled = false;

    // Sun: HDR core with soft corona, always facing the camera.
    this.sunMat = new ShaderMaterial({
      uniforms: {
        uIntensity: { value: 1 },
        uTanHalf: { value: 150 / SUN_DISTANCE }, // billboard half-size over its distance
        uTheta: { value: SUN_THETA }, // disc angular radius [rad]
        uSoft: { value: SUN_THETA * 0.18 }, // width of the disc's soft edge [rad]
      },
      vertexShader: /* glsl */ `
        varying vec2 vUv;
        #include <common>
        #include <logdepthbuf_pars_vertex>
        void main() {
          vUv = uv * 2.0 - 1.0;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          #include <logdepthbuf_vertex>
        }`,
      fragmentShader: /* glsl */ `
        varying vec2 vUv;
        uniform float uIntensity;
        uniform float uTanHalf;
        uniform float uTheta;
        uniform float uSoft;
        #include <common>
        #include <logdepthbuf_pars_fragment>
        void main() {
          #include <logdepthbuf_fragment>
          float r = length(vUv);
          float th = atan(r * uTanHalf); // angle from the Sun's centre [rad]
          float core = smoothstep(uTheta, uTheta - uSoft, th);
          // Linear limb darkening (u = 0.6) across the disc.
          float q = min(th / uTheta, 1.0);
          float limb = 1.0 - 0.6 * (1.0 - sqrt(1.0 - q * q));
          // Glare beyond the limb, in absolute angle so it does not swell with the disc.
          float e = max(th - uTheta, 0.0);
          float glow = (0.42 * exp(-e * 156.0) + 0.09 * exp(-e * 55.5)) * smoothstep(1.0, 0.8, r);
          vec3 c = vec3(1.0, 0.95, 0.86) * (core * limb * 40.0 + glow * 3.0) * uIntensity;
          gl_FragColor = vec4(c, 1.0);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,
      blending: AdditiveBlending,
      depthWrite: false,
      transparent: true,
    });
    this.sun = new Mesh(new PlaneGeometry(2, 2), this.sunMat);
    this.sun.scale.setScalar(150);
    this.sun.position.set(SUN_DIR[0], SUN_DIR[1], SUN_DIR[2]).multiplyScalar(SUN_DISTANCE);
    this.sun.renderOrder = -5;
    this.sun.frustumCulled = false;

    this.group.add(band, this.stars, this.sun);
  }

  /**
   * Keep the sun billboard facing the background camera. With `sun`, the
   * billboard sits along `dir` (unit, from the camera) at min(distance·BG_SCALE,
   * 2600) scene units, faces the camera along that ray, and its disc subtends
   * `angularRadius` (radians; the glare around it keeps a fixed angular size);
   * null keeps the fixed far-away look. Stars within the glare fade out.
   */
  update(
    bgCameraQuat: { x: number; y: number; z: number; w: number },
    pixelRatio: number,
    starFade: number,
    sun?: { dir: Vector3; angularRadius: number | null; distance: number },
  ): void {
    this.sun.quaternion.set(bgCameraQuat.x, bgCameraQuat.y, bgCameraQuat.z, bgCameraQuat.w);
    const su = this.starMat.uniforms;
    su.uPixelRatio.value = pixelRatio;
    su.uFade.value = starFade;
    if (!sun) return;
    const u = this.sunMat.uniforms;
    su.uSunDir.value.copy(sun.dir);
    if (sun.angularRadius === null) {
      this.sun.position.copy(sun.dir).multiplyScalar(SUN_DISTANCE);
      this.sun.scale.setScalar(150);
      u.uTanHalf.value = 150 / SUN_DISTANCE;
      u.uTheta.value = SUN_THETA;
      u.uSoft.value = SUN_THETA * 0.18;
      su.uGlareCos.value.set(Math.cos(SUN_THETA + 0.2), Math.cos(SUN_THETA + 0.02), 0);
      return;
    }
    const theta = Math.min(Math.max(sun.angularRadius, 1e-4), 1.2);
    const dist = Math.min(sun.distance * BG_SCALE, SUN_DISTANCE);
    const tanHalf = Math.tan(theta + SUN_GLARE);
    this.sun.position.copy(sun.dir).multiplyScalar(dist);
    // Perpendicular to the ray, so billboard radius maps to angle exactly (atan).
    this.sun.quaternion.setFromUnitVectors(PLANE_NORMAL, NEG.copy(sun.dir).negate());
    this.sun.scale.setScalar(dist * tanHalf);
    u.uTanHalf.value = tanHalf;
    u.uTheta.value = theta;
    u.uSoft.value = Math.min(theta * 0.18, 0.003);
    su.uGlareCos.value.set(Math.cos(theta + 0.2), Math.cos(theta + 0.02), 0);
  }
}
