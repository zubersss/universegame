import {
  Color,
  DoubleSide,
  Group,
  Matrix3,
  Mesh,
  ShaderMaterial,
  SphereGeometry,
  Vector3,
} from 'three';
import type { BodyDef, CloudLayerDef } from '../world/bodies';
import { ATMO_GLSL, atmoUniforms } from './Atmosphere';
import { hashCombine, mulberry32 } from '../core/rng';

const NOISE_GLSL = /* glsl */ `
float cHash(vec3 p) { p = fract(p * 0.3183099 + vec3(0.71, 0.113, 0.419)); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float cNoise(vec3 x) {
  vec3 i = floor(x); vec3 f = fract(x); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(cHash(i), cHash(i + vec3(1,0,0)), f.x), mix(cHash(i + vec3(0,1,0)), cHash(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(cHash(i + vec3(0,0,1)), cHash(i + vec3(1,0,1)), f.x), mix(cHash(i + vec3(0,1,1)), cHash(i + vec3(1,1,1)), f.x), f.y), f.z);
}
float cFbm(vec3 p) {
  float s = 0.0; float a = 0.5; float n = 0.0;
  for (int i = 0; i < CLOUD_OCTAVES; i++) { s += cNoise(p) * a; n += a; a *= 0.5; p = p * 2.07 + vec3(1.7, 9.2, 3.1); }
  return s / n;
}
`;

interface Layer {
  mesh: Mesh;
  mat: ShaderMaterial;
  def: CloudLayerDef;
  axis: Vector3;
  angle: number;
}

/**
 * Seeded, slowly advected cloud shells for one atmospheric body. The local
 * scene uses one instance with the shared atmosphere uniforms (unit = 1 m);
 * each distant body proxy uses its own instance in the scaled background
 * scene (unit = meters per scene unit). Advection is a function of a shared
 * clock, so the proxy and local shells always show the same clouds.
 */
export class Clouds {
  readonly group = new Group();
  private layers: Layer[] = [];
  private bodyId: string | null = null;

  constructor(
    private readonly atmo: typeof atmoUniforms = atmoUniforms,
    private readonly unit = 1,
    private readonly segments: [number, number] = [128, 64],
  ) {}

  setBody(def: BodyDef | null, quality: number): void {
    const key = def ? `${def.id}:${quality}` : null;
    if (key === this.bodyId) return;
    this.bodyId = key;
    for (const l of this.layers) {
      l.mesh.geometry.dispose();
      l.mat.dispose();
      this.group.remove(l.mesh);
    }
    this.layers = [];
    if (!def || !def.atmosphere) return;
    const defs = quality === 0 ? def.clouds.slice(0, 1) : def.clouds;
    const rnd = mulberry32(hashCombine(def.seed, 'clouds'));
    defs.forEach((cd, i) => {
      const r = def.radius + cd.altitude;
      const geo = new SphereGeometry(r, this.segments[0], this.segments[1]);
      const mat = new ShaderMaterial({
        uniforms: {
          ...this.atmo,
          uUnit: { value: this.unit },
          uRot: { value: new Matrix3() },
          uScale: { value: r / cd.scale },
          uCoverage: { value: cd.coverage },
          uOpacity: { value: cd.opacity },
          uStreak: { value: cd.streak },
          uTint: { value: new Color(cd.tint[0], cd.tint[1], cd.tint[2]) },
          uAmbient: { value: new Color(0.1, 0.12, 0.14) },
          uShellR: { value: r },
          uThickness: { value: cd.thickness },
          uOffset: { value: new Vector3(rnd() * 100, rnd() * 100, rnd() * 100) },
        },
        defines: { CLOUD_OCTAVES: quality >= 2 ? 5 : quality === 1 ? 4 : 3, CLOUD_SHADOW: quality >= 1 ? 1 : 0 },
        vertexShader: /* glsl */ `
          varying vec3 vObj;
          varying vec3 vWorld;
          #include <common>
          #include <logdepthbuf_pars_vertex>
          void main() {
            vObj = position;
            vec4 w = modelMatrix * vec4(position, 1.0);
            vWorld = w.xyz;
            gl_Position = projectionMatrix * viewMatrix * w;
            #include <logdepthbuf_vertex>
          }`,
        fragmentShader: /* glsl */ `
          varying vec3 vObj;
          varying vec3 vWorld;
          uniform mat3 uRot;
          uniform float uScale, uCoverage, uOpacity, uStreak, uShellR, uThickness, uUnit;
          uniform vec3 uTint, uAmbient, uOffset;
          ${ATMO_GLSL}
          ${NOISE_GLSL}
          #include <common>
          #include <logdepthbuf_pars_fragment>
          float density(vec3 n) {
            vec3 p = uRot * n * uScale + uOffset;
            // Streaky layers stretch features along one axis.
            p *= vec3(1.0, 1.0 + uStreak * 3.0, 1.0);
            float f = cFbm(p);
            float big = cNoise(p * 0.23 + 4.1);
            float cov = uCoverage * (0.65 + 0.7 * big);
            return smoothstep(1.0 - cov, 1.0 - cov + 0.22 + uStreak * 0.1, f);
          }
          void main() {
            #include <logdepthbuf_fragment>
            vec3 n = normalize(vObj);
            float d = density(n);
            if (d < 0.01) discard;
            float light = 1.0;
            #if CLOUD_SHADOW == 1
              float dS = density(normalize(n + uSunDir * 0.006));
              light = 1.0 - 0.55 * smoothstep(0.1, 0.9, dS);
            #endif
            vec3 V = normalize(vWorld - cameraPosition);
            float mu = dot(n, uSunDir);
            float alt = uShellR - uPlanetRadius;
            vec3 sunT = atmoSunTrans(alt, mu);
            float c = dot(V, uSunDir);
            float g = 0.6;
            float phase = 0.0795775 * (1.0 - g * g) / pow(max(1.0 + g * g - 2.0 * g * c, 1e-3), 1.5);
            // Sunlit deck dims toward the terminator (softer than Lambert: thick clouds scatter many times).
            float onset = smoothstep(-0.06, 0.12, mu);
            float diffuse = onset * (0.35 + 0.65 * max(mu, 0.0));
            vec3 col = uTint * (sunT * (light * 0.62 * diffuse + phase * (1.2 - d) * 1.6 * onset) * 3.2 + uAmbient * 1.4);
            float dist = length(vWorld - cameraPosition) * uUnit;
            // Soft when the camera is inside or near the layer.
            float fade = smoothstep(uThickness * 0.15, uThickness * 1.2, dist);
            float a = d * uOpacity * fade;
            vec3 aT;
            vec3 aS = atmoScatter((cameraPosition - uPlanetCenter) * uUnit, V, dist, 3, aT);
            col = col * aT + aS;
            gl_FragColor = vec4(col, a);
            #include <tonemapping_fragment>
            #include <colorspace_fragment>
          }`,
        transparent: true,
        depthWrite: false,
        side: DoubleSide,
      });
      const mesh = new Mesh(geo, mat);
      mesh.renderOrder = 2 + i;
      mesh.frustumCulled = false;
      this.group.add(mesh);
      const axis = new Vector3(rnd() - 0.5, 1, rnd() - 0.5).normalize();
      this.layers.push({ mesh, mat, def: cd, axis, angle: rnd() * 6.28 });
    });
  }

  /**
   * @param time shared cloud clock (s)
   * @param planetPos body center in this scene's units
   * @param scale scene units per meter (1 locally)
   */
  update(time: number, planetPos: Vector3, ambient: Color, scale = 1): void {
    this.group.position.copy(planetPos);
    this.group.scale.setScalar(scale);
    for (const l of this.layers) {
      const angle = l.angle + l.def.speed * time;
      const c = Math.cos(angle);
      const s = Math.sin(angle);
      const a = l.axis;
      const t = 1 - c;
      // Axis-angle rotation matrix (advection of the noise field).
      l.mat.uniforms.uRot.value.set(
        t * a.x * a.x + c, t * a.x * a.y - s * a.z, t * a.x * a.z + s * a.y,
        t * a.x * a.y + s * a.z, t * a.y * a.y + c, t * a.y * a.z - s * a.x,
        t * a.x * a.z - s * a.y, t * a.y * a.z + s * a.x, t * a.z * a.z + c,
      );
      (l.mat.uniforms.uAmbient.value as Color).copy(ambient);
    }
  }
}
