import {
  AdditiveBlending,
  BoxGeometry,
  BufferGeometry,
  CanvasTexture,
  Color,
  ConeGeometry,
  CylinderGeometry,
  ExtrudeGeometry,
  Float32BufferAttribute,
  Group,
  LatheGeometry,
  Mesh,
  MeshStandardMaterial,
  Object3D,
  ShaderMaterial,
  Shape,
  SphereGeometry,
  SRGBColorSpace,
  TorusGeometry,
  Vector2,
  Vector3,
  type Material,
} from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// Ship-local frame: forward = -Z, right = +X, up = +Y. Origin = fuselage center.

/** Bottom of the landing pads in ship-local Y when the gear is deployed. */
export const GEAR_PAD_BOTTOM_Y = -2.85;
export const GEAR_PAD_RADIUS = 0.3;
/** Foot positions (pad bottom centers) in ship-local coordinates. */
export const GEAR_FEET: readonly Vector3[] = [
  new Vector3(0, GEAR_PAD_BOTTOM_Y, -4.7),
  new Vector3(-2.75, GEAR_PAD_BOTTOM_Y, 2.7),
  new Vector3(2.75, GEAR_PAD_BOTTOM_Y, 2.7),
];
/** Boarding point (bottom of the ladder) in ship-local coordinates. */
export const BOARDING_POINT = new Vector3(-2.25, -2.6, -1.2);
/** Engine nozzle exit centers (exhaust exits toward +Z). */
export const NOZZLES: readonly Vector3[] = [new Vector3(-2.55, -0.05, 7.6), new Vector3(2.55, -0.05, 7.6)];

const NACELLE_SCALE = 0.8;

// z, rx, ry, yc — Catmull-Rom interpolated fuselage cross-sections (closed boat tail).
const FUSELAGE_PROFILE: number[][] = [
  [-8.3, 0.02, 0.02, -0.18],
  [-7.7, 0.5, 0.36, -0.12],
  [-6.8, 0.98, 0.66, -0.05],
  [-5.4, 1.42, 0.92, 0.04],
  [-3.6, 1.76, 1.1, 0.12],
  [-1.2, 1.94, 1.18, 0.15],
  [1.4, 1.96, 1.16, 0.13],
  [3.6, 1.8, 1.05, 0.1],
  [5.3, 1.5, 0.93, 0.08],
  [6.5, 1.12, 0.78, 0.08],
  [7.3, 0.62, 0.5, 0.1],
  [7.7, 0.04, 0.04, 0.12],
];

/** Points used to build the hull's convex collider (slightly inset from visuals). */
export function hullColliderPoints(): Float32Array {
  const pts: number[] = [];
  for (const s of FUSELAGE_PROFILE) {
    for (let k = 0; k < 8; k++) {
      const a = (k / 8) * Math.PI * 2;
      pts.push(Math.cos(a) * s[1] * 0.98, s[3] + Math.sin(a) * s[2] * 0.98, s[0]);
    }
  }
  pts.push(-5.7, -0.25, 3.6, 5.7, -0.25, 3.6, -5.7, 0.05, 4.4, 5.7, 0.05, 4.4);
  pts.push(-3.2, -0.65, 7.4, 3.2, -0.65, 7.4, -3.2, 0.55, 7.4, 3.2, 0.55, 7.4);
  pts.push(-3.2, -0.65, 1.8, 3.2, -0.65, 1.8);
  return new Float32Array(pts);
}

function catmull(p0: number, p1: number, p2: number, p3: number, t: number): number {
  const t2 = t * t;
  const t3 = t2 * t;
  return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3);
}

function sampleProfile(u: number): number[] {
  const n = FUSELAGE_PROFILE.length - 1;
  const f = Math.min(u * n, n - 1e-9);
  const i = Math.floor(f);
  const t = f - i;
  const P = (k: number) => FUSELAGE_PROFILE[Math.min(Math.max(k, 0), n)];
  const out: number[] = [];
  for (let c = 0; c < 4; c++) out.push(catmull(P(i - 1)[c], P(i)[c], P(i + 1)[c], P(i + 2)[c], t));
  return out;
}

/** Superellipse loft of the fuselage with UVs (u around, v along). */
function fuselageGeometry(): BufferGeometry {
  const segAlong = 80;
  const segAround = 48;
  const exp = 2.7;
  const pos: number[] = [];
  const uv: number[] = [];
  const idx: number[] = [];
  for (let i = 0; i <= segAlong; i++) {
    const u = i / segAlong;
    const [z, rx, ry, yc] = sampleProfile(u);
    for (let j = 0; j <= segAround; j++) {
      const a = (j / segAround) * Math.PI * 2;
      const ca = Math.cos(a);
      const sa = Math.sin(a);
      const x = rx * Math.sign(ca) * Math.pow(Math.abs(ca), 2 / exp);
      const yy = ry * Math.sign(sa) * Math.pow(Math.abs(sa), 2 / exp) * (sa < 0 ? 0.86 : 1);
      pos.push(x, yc + yy, z);
      uv.push(j / segAround, u);
    }
  }
  const row = segAround + 1;
  for (let i = 0; i < segAlong; i++) {
    for (let j = 0; j < segAround; j++) {
      const a = i * row + j;
      const b = a + row;
      idx.push(a, a + 1, b, b, a + 1, b + 1);
    }
  }
  const g = new BufferGeometry();
  g.setAttribute('position', new Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

/** Painted ceramic/graphite livery with panel lines; plus an ORM map (G=roughness, B=metalness). */
function liveryTextures(): { map: CanvasTexture; orm: CanvasTexture } {
  const W = 1024;
  const H = 512;
  const c = document.createElement('canvas');
  c.width = W;
  c.height = H;
  const g = c.getContext('2d')!;
  const o = document.createElement('canvas');
  o.width = W;
  o.height = H;
  const go = o.getContext('2d')!;
  // u = angle around (0 = +X side, 0.25 = top, 0.5 = -X, 0.75 = belly), v = along (0 nose .. 1 tail)
  const xOf = (u: number) => u * W;
  const yOf = (v: number) => v * H;
  g.fillStyle = '#e8e3d8';
  g.fillRect(0, 0, W, H);
  go.fillStyle = 'rgb(255,110,0)';
  go.fillRect(0, 0, W, H);
  // Graphite belly band and nose tip.
  g.fillStyle = '#2b2e33';
  g.fillRect(xOf(0.6), 0, xOf(0.3), H);
  go.fillStyle = 'rgb(255,150,60)';
  go.fillRect(xOf(0.6), 0, xOf(0.3), H);
  g.fillRect(0, 0, W, yOf(0.03));
  // Graphite tail cone.
  g.fillRect(0, yOf(0.94), W, yOf(0.06));
  // Warm metal pinstripes bordering the belly band and the tail ring.
  g.fillStyle = '#b07a45';
  go.fillStyle = 'rgb(255,80,255)';
  for (const u of [0.585, 0.9]) {
    g.fillRect(xOf(u), 0, 7, yOf(0.94));
    go.fillRect(xOf(u), 0, 7, yOf(0.94));
  }
  g.fillRect(0, yOf(0.935), W, 5);
  go.fillRect(0, yOf(0.935), W, 5);
  // Dorsal accent band running aft from the canopy.
  g.fillStyle = '#c98a45';
  g.fillRect(xOf(0.236), yOf(0.43), xOf(0.028), yOf(0.48));
  // Panel lines.
  g.strokeStyle = 'rgba(40,36,30,0.55)';
  g.lineWidth = 1.6;
  for (const v of [0.14, 0.26, 0.38, 0.52, 0.66, 0.8, 0.9]) {
    g.beginPath();
    g.moveTo(0, yOf(v));
    g.lineTo(W, yOf(v));
    g.stroke();
  }
  for (const u of [0.08, 0.17, 0.33, 0.42, 0.5, 0.75]) {
    g.beginPath();
    g.moveTo(xOf(u), yOf(0.14));
    g.lineTo(xOf(u), yOf(0.93));
    g.stroke();
  }
  g.strokeStyle = 'rgba(40,36,30,0.6)';
  g.lineWidth = 1.2;
  const rects: [number, number, number, number][] = [
    [0.04, 0.55, 0.06, 0.07], [0.44, 0.55, 0.06, 0.07], [0.1, 0.3, 0.04, 0.05], [0.37, 0.3, 0.04, 0.05],
    [0.02, 0.7, 0.05, 0.12], [0.46, 0.7, 0.05, 0.12],
  ];
  for (const [u, v, w, h] of rects) g.strokeRect(xOf(u), yOf(v), xOf(w), yOf(h));
  // Registration along each flank. The loft's (u, v) parameterization is mirrored
  // relative to canvas axes, and u has ~3x the texel density of v, hence the
  // reflection matrices with a 1/3 squash along the text direction.
  g.fillStyle = 'rgba(48,44,38,0.85)';
  g.font = '600 30px sans-serif';
  const label = 'MRD-07  SURVEYOR';
  g.setTransform(0, -0.33, -1, 0, xOf(0.035), yOf(0.6)); // right flank: reads toward the nose
  g.fillText(label, 0, 0);
  g.setTransform(0, 0.33, 1, 0, xOf(0.465), yOf(0.3)); // left flank: reads toward the tail
  g.fillText(label, 0, 0);
  g.setTransform(1, 0, 0, 1, 0, 0);
  // Subtle grime/variation for albedo and roughness.
  const img = g.getImageData(0, 0, W, H);
  const oimg = go.getImageData(0, 0, W, H);
  let seed = 1337;
  const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
  for (let y = 0; y < H; y++) {
    const streak = 0.5 + 0.5 * Math.sin(y * 0.05);
    for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 4;
      const n = (rnd() - 0.5) * 10 + (Math.sin(x * 0.013 + y * 0.002) + Math.sin(x * 0.0041 - y * 0.009)) * 3;
      const aft = (y / H) * (y / H) * 18 * streak;
      img.data[i] = Math.max(0, Math.min(255, img.data[i] + n - aft));
      img.data[i + 1] = Math.max(0, Math.min(255, img.data[i + 1] + n - aft));
      img.data[i + 2] = Math.max(0, Math.min(255, img.data[i + 2] + n - aft * 1.1));
      oimg.data[i + 1] = Math.max(0, Math.min(255, oimg.data[i + 1] + n * 2.2 + aft * 0.8));
    }
  }
  g.putImageData(img, 0, 0);
  go.putImageData(oimg, 0, 0);
  const map = new CanvasTexture(c);
  map.colorSpace = SRGBColorSpace;
  map.anisotropy = 4;
  const orm = new CanvasTexture(o);
  orm.anisotropy = 4;
  return { map, orm };
}

/** Radial glow texture for the engine cores (sRGB color). */
function coreGlowTexture(): CanvasTexture {
  const s = 128;
  const c = document.createElement('canvas');
  c.width = s;
  c.height = s;
  const g = c.getContext('2d')!;
  const grad = g.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
  grad.addColorStop(0, '#fff6e6');
  grad.addColorStop(0.25, '#ffd08a');
  grad.addColorStop(0.6, '#c2551c');
  grad.addColorStop(0.85, '#3a1406');
  grad.addColorStop(1, '#0a0503');
  g.fillStyle = grad;
  g.fillRect(0, 0, s, s);
  const t = new CanvasTexture(c);
  t.colorSpace = SRGBColorSpace;
  return t;
}

function wingGeometry(side: 1 | -1): BufferGeometry {
  // Planform in (span, chord): span along +x, chord along +y (mapped to +z aft).
  const s = new Shape();
  s.moveTo(1.4, -0.4);
  s.lineTo(5.6, 2.3);
  s.lineTo(5.95, 2.55);
  s.lineTo(5.95, 4.3);
  s.lineTo(5.3, 4.55);
  s.lineTo(1.4, 4.4);
  s.closePath();
  const g = new ExtrudeGeometry(s, {
    depth: 0.18,
    bevelEnabled: true,
    bevelThickness: 0.07,
    bevelSize: 0.07,
    bevelSegments: 3,
    curveSegments: 4,
  });
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i);
    const y = p.getY(i);
    const z = p.getZ(i);
    const t = Math.min(1, Math.max(0, (x - 1.4) / 4.6));
    p.setXYZ(i, x * side, (z - 0.09) * (1 - 0.45 * t) - 0.38 - 0.18 * t, y);
  }
  // The (x,y,z) -> (side*x, z, y) remap has determinant -side: fix winding.
  if (side === 1) flipWinding(g);
  g.computeVertexNormals();
  return g;
}

/** Reverse triangle winding for indexed or non-indexed geometry. */
function flipWinding(g: BufferGeometry): void {
  if (g.index) {
    const idx = g.index;
    for (let i = 0; i < idx.count; i += 3) {
      const a = idx.getX(i + 1);
      idx.setX(i + 1, idx.getX(i + 2));
      idx.setX(i + 2, a);
    }
    return;
  }
  for (const name of Object.keys(g.attributes)) {
    const at = g.attributes[name];
    const n = at.itemSize;
    const arr = at.array as Float32Array;
    for (let t = 0; t < at.count; t += 3) {
      const b = (t + 1) * n;
      const c = (t + 2) * n;
      for (let k = 0; k < n; k++) {
        const tmp = arr[b + k];
        arr[b + k] = arr[c + k];
        arr[c + k] = tmp;
      }
    }
    at.needsUpdate = true;
  }
}

function nacelleGeometry(): BufferGeometry {
  // Lathe profile (radius, length) around Y, rotated so Y -> +Z (aft).
  const k = NACELLE_SCALE;
  const pts = [
    new Vector2(0.0, -2.9), new Vector2(0.52 * k, -2.88), new Vector2(0.72 * k, -2.75), new Vector2(0.84 * k, -2.45),
    new Vector2(0.9 * k, -1.6), new Vector2(0.92 * k, 0.6), new Vector2(0.9 * k, 1.6), new Vector2(0.84 * k, 2.05),
    new Vector2(0.74 * k, 2.3), new Vector2(0.7 * k, 2.32), new Vector2(0.66 * k, 2.1),
  ];
  const g = new LatheGeometry(pts, 40);
  g.rotateX(Math.PI / 2);
  return g;
}

function nozzleGeometry(): BufferGeometry {
  const k = NACELLE_SCALE;
  const pts = [new Vector2(0.68 * k, 0.0), new Vector2(0.64 * k, 0.3), new Vector2(0.58 * k, 0.55), new Vector2(0.52 * k, 0.6)];
  const g = new LatheGeometry(pts, 40);
  g.rotateX(Math.PI / 2);
  return g;
}

/** Additive exhaust plume material (scaled along +Z by thrust). */
function plumeMaterial(): ShaderMaterial {
  return new ShaderMaterial({
    uniforms: { uIntensity: { value: 0 }, uBoost: { value: 0 } },
    vertexShader: /* glsl */ `
      varying float vAlong;
      varying float vEdge;
      #include <common>
      #include <logdepthbuf_pars_vertex>
      void main() {
        vAlong = uv.y;
        vec3 n = normalize(normalMatrix * normal);
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        vEdge = abs(dot(n, normalize(-mv.xyz)));
        gl_Position = projectionMatrix * mv;
        #include <logdepthbuf_vertex>
      }`,
    fragmentShader: /* glsl */ `
      varying float vAlong;
      varying float vEdge;
      uniform float uIntensity;
      uniform float uBoost;
      #include <common>
      #include <logdepthbuf_pars_fragment>
      void main() {
        #include <logdepthbuf_fragment>
        float t = vAlong; // cone uv.y: 0 at the nozzle (base), 1 at the tip
        float core = pow(vEdge, 2.5);
        float fall = pow(1.0 - t, 1.6);
        vec3 hot = mix(vec3(1.0, 0.78, 0.5), vec3(0.75, 0.85, 1.0), uBoost);
        vec3 c = mix(vec3(1.0, 0.42, 0.14), hot, core) * (core * 1.4 + 0.15) * fall * uIntensity;
        gl_FragColor = vec4(c, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
    transparent: true,
    depthWrite: false,
    blending: AdditiveBlending,
  });
}

export interface ShipVisual {
  root: Group;
  gearLegs: Object3D[];
  ladder: Group;
  engineMaterial: MeshStandardMaterial;
  plumes: Mesh[];
  plumeMaterial: ShaderMaterial;
  navLights: Mesh[];
  materials: Material[];
  triangleCount: number;
}

/** Build the ship's visual model; static parts are merged per material. */
export function buildShipModel(): ShipVisual {
  const root = new Group();
  root.name = 'ship';
  const { map, orm } = liveryTextures();
  const ceramic = new MeshStandardMaterial({ map, roughnessMap: orm, metalnessMap: orm, roughness: 1, metalness: 1, envMapIntensity: 0.9 });
  const ceramicPlain = new MeshStandardMaterial({ color: 0xe6e1d6, roughness: 0.46, metalness: 0.0, envMapIntensity: 0.9 });
  const graphite = new MeshStandardMaterial({ color: 0x2a2d32, roughness: 0.56, metalness: 0.3, envMapIntensity: 0.8 });
  const warmMetal = new MeshStandardMaterial({ color: 0xb98250, roughness: 0.3, metalness: 1.0, envMapIntensity: 1.0 });
  const canopy = new MeshStandardMaterial({ color: 0x06090c, roughness: 0.07, metalness: 0.6, envMapIntensity: 1.4 });
  const dark = new MeshStandardMaterial({ color: 0x15171a, roughness: 0.7, metalness: 0.2 });
  const engine = new MeshStandardMaterial({
    color: 0x0a0604, emissive: new Color(1, 1, 1), emissiveMap: coreGlowTexture(), emissiveIntensity: 0.2, roughness: 0.6, metalness: 0,
  });
  const lightRed = new MeshStandardMaterial({ color: 0x220000, emissive: new Color(1, 0.08, 0.04), emissiveIntensity: 4 });
  const lightGreen = new MeshStandardMaterial({ color: 0x002200, emissive: new Color(0.1, 1, 0.35), emissiveIntensity: 4 });
  const lightWhite = new MeshStandardMaterial({ color: 0x222222, emissive: new Color(1, 0.95, 0.85), emissiveIntensity: 5 });

  // Static parts are collected per material and merged at the end.
  const parts = new Map<Material, BufferGeometry[]>();
  const add = (geo: BufferGeometry, mat: Material): void => {
    const g = geo.index ? geo.toNonIndexed() : geo;
    for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal' && k !== 'uv') g.deleteAttribute(k);
    if (!g.attributes.normal) g.computeVertexNormals();
    let list = parts.get(mat);
    if (!list) parts.set(mat, (list = []));
    list.push(g);
  };

  add(fuselageGeometry(), ceramic);

  // Canopy and frame.
  const canopyGeo = new SphereGeometry(1, 40, 20, 0, Math.PI * 2, 0, Math.PI / 2);
  canopyGeo.scale(1.08, 0.62, 2.5);
  canopyGeo.translate(0, 0.86, -4.25);
  add(canopyGeo, canopy);
  const frame = new TorusGeometry(1, 0.045, 8, 48);
  frame.rotateX(Math.PI / 2);
  frame.scale(1.1, 1, 2.53);
  frame.translate(0, 0.9, -4.25);
  add(frame, warmMetal);
  const strut = new BoxGeometry(0.07, 0.07, 4.6);
  strut.translate(0, 1.47, -4.25);
  add(strut, warmMetal);

  // Wings, fairings and tip fins.
  add(wingGeometry(1), ceramicPlain);
  add(wingGeometry(-1), ceramicPlain);
  for (const side of [-1, 1]) {
    const fair = new BoxGeometry(0.9, 0.42, 4.4);
    fair.translate(side * 1.62, -0.42, 2.0);
    add(fair, graphite);
    const fs = new Shape();
    fs.moveTo(0, 0);
    fs.lineTo(1.2, 0);
    fs.lineTo(1.0, 0.95);
    fs.lineTo(0.55, 1.0);
    fs.closePath();
    const fg = new ExtrudeGeometry(fs, { depth: 0.08, bevelEnabled: true, bevelSize: 0.03, bevelThickness: 0.03, bevelSegments: 2 });
    fg.rotateY(-Math.PI / 2);
    fg.translate(side * 5.92 + 0.04, -0.62, 3.2);
    add(fg, warmMetal);
  }

  // Engine nacelles, rings, nozzles, glowing cores and pylons.
  const nac = nacelleGeometry();
  const ring = new TorusGeometry(0.86 * NACELLE_SCALE, 0.06, 10, 40);
  const ring2 = new TorusGeometry(0.93 * NACELLE_SCALE, 0.04, 8, 40);
  const noz = nozzleGeometry();
  const coreGeo = new CylinderGeometry(0.5 * NACELLE_SCALE, 0.5 * NACELLE_SCALE, 0.04, 32);
  coreGeo.rotateX(Math.PI / 2);
  const engineCores: BufferGeometry[] = [];
  for (const n of NOZZLES) {
    const z0 = n.z - 0.6; // nozzle start
    add(nac.clone().translate(n.x, n.y, z0 - 2.32), graphite);
    add(ring.clone().translate(n.x, n.y, z0 - 4.95), warmMetal);
    add(ring2.clone().translate(n.x, n.y, z0 - 1.2), warmMetal);
    add(noz.clone().translate(n.x, n.y, z0), dark);
    engineCores.push(coreGeo.clone().translate(n.x, n.y, z0 + 0.45));
    const py = new BoxGeometry(0.9, 0.24, 2.6);
    py.translate(n.x * 0.74, n.y + 0.1, z0 - 3.0);
    add(py, graphite);
  }

  // Dorsal sensor fin.
  const dfs = new Shape();
  dfs.moveTo(0, 0);
  dfs.lineTo(2.6, 0);
  dfs.lineTo(2.2, 0.85);
  dfs.lineTo(1.2, 0.9);
  dfs.closePath();
  const dfg = new ExtrudeGeometry(dfs, { depth: 0.1, bevelEnabled: true, bevelSize: 0.04, bevelThickness: 0.04, bevelSegments: 2 });
  dfg.rotateY(-Math.PI / 2);
  dfg.translate(0.05, 1.08, 2.0);
  add(dfg, ceramicPlain);
  const finEdge = new BoxGeometry(0.06, 0.05, 1.0);
  finEdge.translate(0, 1.98, 3.15);
  add(finEdge, warmMetal);

  // Sensor dish under the nose; small tail vent.
  const dish = new SphereGeometry(0.34, 20, 10, 0, Math.PI * 2, 0, Math.PI / 2);
  dish.rotateX(Math.PI);
  dish.translate(0, -0.8, -5.8);
  add(dish, warmMetal);

  // Gear bay plates.
  for (const f of GEAR_FEET) {
    const bay = new BoxGeometry(0.55, 0.05, 1.5);
    bay.translate(f.x, f === GEAR_FEET[0] ? -0.97 : -0.79, f.z - 0.55);
    add(bay, dark);
  }

  for (const [mat, list] of parts) {
    const merged = mergeGeometries(list, false);
    if (!merged) throw new Error('Ship geometry merge failed');
    const m = new Mesh(merged, mat);
    m.castShadow = true;
    m.receiveShadow = true;
    root.add(m);
    for (const g of list) g.dispose();
  }
  const cores = new Mesh(mergeGeometries(engineCores, false)!, engine);
  root.add(cores);

  // Exhaust plumes: unit-length cones pointing +Z from each nozzle; scaled by thrust.
  const plumeMat = plumeMaterial();
  const plumeGeo = new ConeGeometry(0.42 * NACELLE_SCALE, 1, 20, 6, true);
  plumeGeo.rotateX(Math.PI / 2); // tip toward +Z
  plumeGeo.translate(0, 0, 0.5);
  const plumes: Mesh[] = [];
  for (const n of NOZZLES) {
    const p = new Mesh(plumeGeo, plumeMat);
    p.position.copy(n).add(new Vector3(0, 0, -0.1));
    p.renderOrder = 6;
    p.frustumCulled = false;
    root.add(p);
    plumes.push(p);
  }

  // Nav lights (kept separate: distinct emissive materials).
  const lamp = new SphereGeometry(0.09, 10, 8);
  const mk = (x: number, y: number, z: number, mat: Material) => {
    const m = new Mesh(lamp, mat);
    m.position.set(x, y, z);
    root.add(m);
    return m;
  };
  const navLights = [mk(-5.95, -0.42, 3.4, lightRed), mk(5.95, -0.42, 3.4, lightGreen), mk(0, 1.95, 3.65, lightWhite)];

  // Ladder at the boarding point (visible when landed).
  const ladderParts: BufferGeometry[] = [];
  for (let k = 0; k < 5; k++) {
    // Rungs span the rails, which stand 0.5 m apart along z.
    ladderParts.push(new BoxGeometry(0.04, 0.04, 0.5).translate(BOARDING_POINT.x, BOARDING_POINT.y + 0.35 + k * 0.42, BOARDING_POINT.z).toNonIndexed());
  }
  for (const dz of [-0.25, 0.25]) {
    ladderParts.push(new BoxGeometry(0.05, 2.2, 0.05).translate(BOARDING_POINT.x, BOARDING_POINT.y + 1.1, BOARDING_POINT.z + dz).toNonIndexed());
  }
  const ladder = new Group();
  const ladderMesh = new Mesh(mergeGeometries(ladderParts, false)!, warmMetal);
  ladderMesh.castShadow = true;
  ladder.add(ladderMesh);
  root.add(ladder);

  // Landing gear: hinge groups (merged per material inside each leg) that rotate to retract.
  const gearLegs: Object3D[] = [];
  for (let i = 0; i < GEAR_FEET.length; i++) {
    const foot = GEAR_FEET[i];
    const hingeY = i === 0 ? -0.95 : -0.75;
    const len = hingeY - (GEAR_PAD_BOTTOM_Y + 0.14);
    const strutG = new CylinderGeometry(0.11, 0.13, len - 0.3, 12).translate(0, -(len - 0.3) / 2, 0);
    const padG = new CylinderGeometry(0.5, 0.56, 0.14, 24).translate(0, -len - 0.07, 0);
    const oleoG = new CylinderGeometry(0.17, 0.17, 0.55, 14).translate(0, -len + 0.45, 0);
    const kneeG = new SphereGeometry(0.19, 12, 8).translate(0, -len + 0.05, 0);
    const hinge = new Group();
    hinge.position.set(foot.x, hingeY, foot.z);
    const darkPart = new Mesh(mergeGeometries([strutG.toNonIndexed(), padG.toNonIndexed()], false)!, graphite);
    const metalPart = new Mesh(mergeGeometries([oleoG.toNonIndexed(), kneeG.toNonIndexed()], false)!, warmMetal);
    for (const m of [darkPart, metalPart]) {
      m.castShadow = true;
      m.receiveShadow = true;
      hinge.add(m);
    }
    root.add(hinge);
    gearLegs.push(hinge);
  }

  let triangleCount = 0;
  root.traverse((o) => {
    const m = o as Mesh;
    if (m.isMesh) {
      const g = m.geometry;
      triangleCount += (g.index ? g.index.count : g.attributes.position.count) / 3;
    }
  });

  return {
    root,
    gearLegs,
    ladder,
    engineMaterial: engine,
    plumes,
    plumeMaterial: plumeMat,
    navLights,
    materials: [ceramic, ceramicPlain, graphite, warmMetal, canopy, dark, engine, lightRed, lightGreen, lightWhite],
    triangleCount,
  };
}

/** Animate gear: t = 1 deployed, 0 retracted. */
export function setGearDeploy(legs: Object3D[], t: number): void {
  const e = t * t * (3 - 2 * t);
  for (let i = 0; i < legs.length; i++) {
    const leg = legs[i];
    leg.rotation.set(i === 0 ? -(1 - e) * 1.62 : (1 - e) * 1.62, 0, 0);
    leg.visible = t > 0.02;
  }
}

/** Update plume length/intensity from normalized thrust (0..1). */
export function setPlumes(v: ShipVisual, thrust: number, boost: boolean, dt: number): void {
  const u = v.plumeMaterial.uniforms;
  const targetI = thrust > 0.01 ? 0.6 + thrust * 2.2 + (boost ? 1.4 : 0) : 0;
  u.uIntensity.value += (targetI - u.uIntensity.value) * (1 - Math.exp(-dt / 0.1));
  u.uBoost.value += ((boost ? 1 : 0) - u.uBoost.value) * (1 - Math.exp(-dt / 0.2));
  const len = 0.6 + thrust * 4.2 + (boost ? 3.5 : 0);
  for (const p of v.plumes) {
    p.scale.z += (len - p.scale.z) * (1 - Math.exp(-dt / 0.08));
    p.visible = u.uIntensity.value > 0.02;
  }
}
