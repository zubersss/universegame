import { BufferGeometry, Color, ConeGeometry, CylinderGeometry, Float32BufferAttribute, Matrix4, SphereGeometry, Vector3 } from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// Procedural creature meshes, modeled in a unit frame (feet on y = 0, +Y up,
// +Z forward, height ~1) and scaled per instance. Besides vertex colors each
// vertex carries `aLeg` = (part, t): part -1 is the rigid body, -2 a swaying
// appendage (vanes), 0..2 a leg index; t runs 0 at the hip to 1 at the foot.
// The vertex shader in FaunaSystem animates the gait from these.

export interface FaunaGeometry {
  lod0: BufferGeometry;
  lod1: BufferGeometry;
}

const lin = (hex: number) => new Color(hex).convertSRGBToLinear();

function part(g: BufferGeometry, color: (p: Vector3, n: Vector3, c: Color) => void, leg: (p: Vector3) => [number, number]): BufferGeometry {
  const ng = g.index ? g.toNonIndexed() : g;
  for (const k of Object.keys(ng.attributes)) if (k !== 'position' && k !== 'normal') ng.deleteAttribute(k);
  ng.computeVertexNormals();
  const pos = ng.attributes.position;
  const nor = ng.attributes.normal;
  const cols = new Float32Array(pos.count * 3);
  const legs = new Float32Array(pos.count * 2);
  const p = new Vector3();
  const n = new Vector3();
  const c = new Color();
  for (let i = 0; i < pos.count; i++) {
    p.fromBufferAttribute(pos, i);
    n.fromBufferAttribute(nor, i);
    color(p, n, c);
    cols[i * 3] = c.r;
    cols[i * 3 + 1] = c.g;
    cols[i * 3 + 2] = c.b;
    const [a, b] = leg(p);
    legs[i * 2] = a;
    legs[i * 2 + 1] = b;
  }
  ng.setAttribute('color', new Float32BufferAttribute(cols, 3));
  ng.setAttribute('aLeg', new Float32BufferAttribute(legs, 2));
  return ng;
}

function merge(parts: BufferGeometry[]): BufferGeometry {
  const g = mergeGeometries(parts, false);
  if (!g) throw new Error('fauna merge failed');
  g.computeBoundingSphere();
  return g;
}

/** A tapered cylinder between two points (local +Y of the cylinder → a..b). */
function segment(a: Vector3, b: Vector3, r0: number, r1: number, radial: number): BufferGeometry {
  const len = a.distanceTo(b);
  const g = new CylinderGeometry(r1, r0, len, radial, 1, true);
  g.translate(0, len / 2, 0);
  const dir = b.clone().sub(a).normalize();
  const axis = new Vector3(0, 1, 0).cross(dir);
  const s = axis.length();
  if (s > 1e-6) g.applyMatrix4(new Matrix4().makeRotationAxis(axis.normalize(), Math.atan2(s, dir.y)));
  g.translate(a.x, a.y, a.z);
  return g;
}

/**
 * Grove trine (Ilex): a tripedal grazer. Pale ellipsoid carapace slung low
 * between three stilt legs whose knees rise above the body, a row of teal
 * dorsal vanes like a lantern-tree crown, and a browsing proboscis.
 */
export function groveTrine(): FaunaGeometry {
  const shell = lin(0xd9d0bb);
  const belly = lin(0xa88a5a);
  const legC = lin(0x4a3d30);
  const jointC = lin(0xcfc6b2);
  const vaneLo = lin(0x2a5a52);
  const vaneHi = lin(0x9fd8c4);
  const make = (detail: boolean) => {
    const parts: BufferGeometry[] = [];
    // Carapace.
    const body = new SphereGeometry(1, detail ? 14 : 7, detail ? 9 : 5);
    body.scale(0.15, 0.11, 0.33);
    body.translate(0, 0.74, 0);
    parts.push(part(body, (p, n, c) => {
      c.copy(belly).lerp(shell, Math.min(1, Math.max(0, n.y * 0.9 + 0.55)));
      // Faint transverse banding.
      const band = Math.sin(p.z * 40) * 0.5 + 0.5;
      c.multiplyScalar(0.94 + 0.06 * band);
    }, () => [-1, 0]));
    // Proboscis: hangs down and forward from the front of the carapace.
    const pro = segment(new Vector3(0, 0.7, 0.28), new Vector3(0, 0.2, 0.44), 0.025, 0.006, detail ? 5 : 3);
    parts.push(part(pro, (_p, _n, c) => c.copy(belly).multiplyScalar(0.8), () => [-1, 0]));
    // Dorsal vanes.
    const vanes = detail ? 5 : 3;
    for (let i = 0; i < vanes; i++) {
      const t = i / (vanes - 1);
      const h = 0.12 + 0.1 * Math.sin(t * Math.PI);
      const v = new ConeGeometry(0.045, h, detail ? 4 : 3, 1);
      v.scale(0.35, 1, 1.4);
      v.rotateX(-0.35);
      v.translate(0, 0.83 + h / 2, -0.2 + 0.4 * t);
      parts.push(part(v, (p, _n, c) => {
        c.copy(vaneLo).lerp(vaneHi, Math.min(1, Math.max(0, (p.y - 0.84) / h)));
      }, () => [-2, 0]));
    }
    // Three legs: one forward, two behind. Hip → knee (above the body) → foot.
    for (let k = 0; k < 3; k++) {
      const a = (k / 3) * Math.PI * 2;
      const sx = Math.sin(a);
      const cz = Math.cos(a);
      const hip = new Vector3(sx * 0.1, 0.7, cz * 0.18);
      const knee = new Vector3(sx * 0.38, 1.0, cz * 0.5);
      const foot = new Vector3(sx * 0.5, 0, cz * 0.68);
      const radial = detail ? 5 : 3;
      const upper = segment(hip, knee, 0.028, 0.02, radial);
      const lower = segment(knee, foot, 0.02, 0.008, radial);
      // Leg parameter: 0 at the hip, 0.5 at the knee, 1 at the foot.
      const along = (a0: Vector3, b0: Vector3, t0: number) => {
        const ab = b0.clone().sub(a0);
        const l2 = ab.lengthSq();
        return (p: Vector3): [number, number] => [k, t0 + 0.5 * Math.max(0, Math.min(1, p.clone().sub(a0).dot(ab) / l2))];
      };
      parts.push(part(upper, (_p, _n, c) => c.copy(legC), along(hip, knee, 0)));
      parts.push(part(lower, (p, _n, c) => c.copy(legC).lerp(jointC, Math.max(0, p.y - 0.9) * 6), along(knee, foot, 0.5)));
      if (detail) {
        const j = new SphereGeometry(0.03, 5, 3);
        j.translate(knee.x, knee.y, knee.z);
        parts.push(part(j, (_p, _n, c) => c.copy(jointC), () => [k, 0.5]));
      }
    }
    return merge(parts);
  };
  return { lod0: make(true), lod1: make(false) };
}

/**
 * Dune sledge (Vesper): a broad, low grazer under overlapping oxide-red
 * plates that hauls itself over the dunes on two heavy forelimbs; the
 * tapered rear drags. Height ~1, length ~2.4 (+Z forward).
 */
export function duneSledge(): FaunaGeometry {
  const plateA = lin(0x8e4126);
  const plateB = lin(0xb46a40);
  const belly = lin(0xd9c4a0);
  const limb = lin(0x5a2c1c);
  const make = (detail: boolean) => {
    const parts: BufferGeometry[] = [];
    // Body: a long, flattened shell, higher at the shoulders, tapering to the drag.
    const body = new SphereGeometry(1, detail ? 16 : 8, detail ? 9 : 5);
    body.scale(0.48, 0.34, 1.15);
    const bp = body.attributes.position;
    for (let i = 0; i < bp.count; i++) {
      const z = bp.getZ(i);
      const t = (z + 1.15) / 2.3; // 0 rear → 1 front
      bp.setY(i, bp.getY(i) * (0.55 + 0.6 * t));
      bp.setX(i, bp.getX(i) * (0.6 + 0.5 * t));
    }
    body.translate(0, 0.38, -0.2);
    parts.push(part(body, (p, n, c) => {
      // Overlapping plate bands across the back; pale underside.
      const band = Math.floor((p.z + 1.4) * 6) % 2;
      c.copy(band ? plateA : plateB);
      if (n.y < -0.2) c.copy(belly);
      c.multiplyScalar(0.85 + 0.15 * Math.max(0, n.y));
    }, () => [-1, 0]));
    // Head: low and blunt, set into the front of the shell.
    const head = new SphereGeometry(0.2, detail ? 10 : 6, detail ? 6 : 4);
    head.scale(1.2, 0.8, 1);
    head.translate(0, 0.42, 0.98);
    parts.push(part(head, (_p, n, c) => c.copy(plateA).lerp(belly, Math.max(0, -n.y)), () => [-1, 0]));
    // Two forelimbs: shoulder → elbow (raised, out) → broad hand planted forward.
    for (let k = 0; k < 2; k++) {
      const sx = k === 0 ? 1 : -1;
      const shoulder = new Vector3(sx * 0.32, 0.5, 0.55);
      const elbow = new Vector3(sx * 0.72, 0.7, 0.72);
      const hand = new Vector3(sx * 0.66, 0.02, 1.12);
      const radial = detail ? 6 : 3;
      const along = (a0: Vector3, b0: Vector3, t0: number) => {
        const ab = b0.clone().sub(a0);
        const l2 = ab.lengthSq();
        return (p: Vector3): [number, number] => [k, t0 + 0.5 * Math.max(0, Math.min(1, p.clone().sub(a0).dot(ab) / l2))];
      };
      parts.push(part(segment(shoulder, elbow, 0.09, 0.07, radial), (_p, _n, c) => c.copy(limb), along(shoulder, elbow, 0)));
      parts.push(part(segment(elbow, hand, 0.07, 0.05, radial), (_p, _n, c) => c.copy(limb), along(elbow, hand, 0.5)));
      const pad = new SphereGeometry(0.11, detail ? 6 : 4, 3);
      pad.scale(1.3, 0.4, 1.5);
      pad.translate(hand.x, 0.03, hand.z);
      parts.push(part(pad, (_p, _n, c) => c.copy(limb).multiplyScalar(0.8), () => [k, 1]));
    }
    return merge(parts);
  };
  return { lod0: make(true), lod1: make(false) };
}

// ------------------------------------------------------- shared builders

type Tag = (p: Vector3) => [number, number];
const rigid: Tag = () => [-1, 0];
const sway: Tag = () => [-2, 0];

/** A two-segment limb (hip → knee → foot) tagged with its leg index for the gait shader. */
function limb(parts: BufferGeometry[], k: number, hip: Vector3, knee: Vector3, foot: Vector3, r0: number, r1: number, radial: number, col: Color): void {
  const along = (a0: Vector3, b0: Vector3, t0: number): Tag => {
    const ab = b0.clone().sub(a0);
    const l2 = ab.lengthSq();
    return (p) => [k, t0 + 0.5 * Math.max(0, Math.min(1, p.clone().sub(a0).dot(ab) / l2))];
  };
  parts.push(part(segment(hip, knee, r0, (r0 + r1) / 2, radial), (_p, _n, c) => c.copy(col), along(hip, knee, 0)));
  parts.push(part(segment(knee, foot, (r0 + r1) / 2, r1, radial), (_p, _n, c) => c.copy(col), along(knee, foot, 0.5)));
}

function blob(sx: number, sy: number, sz: number, x: number, y: number, z: number, detail: boolean, w = 10, h = 6): BufferGeometry {
  const g = new SphereGeometry(1, detail ? w : Math.max(5, w >> 1), detail ? h : Math.max(3, h >> 1));
  g.scale(sx, sy, sz);
  g.translate(x, y, z);
  return g;
}

/** A flat, double-sided triangle fan (wings, plates, membranes) in the XZ plane at height y. */
function sheet(pts: [number, number][], y: number): BufferGeometry {
  const pos: number[] = [];
  for (let i = 1; i < pts.length - 1; i++) {
    const tri = [pts[0], pts[i], pts[i + 1]];
    for (const [x, z] of tri) pos.push(x, y, z);
    for (const [x, z] of [tri[0], tri[2], tri[1]]) pos.push(x, y - 0.001, z);
  }
  const g = new BufferGeometry();
  g.setAttribute('position', new Float32BufferAttribute(pos, 3));
  return g;
}

// ------------------------------------------------------------------ Ilex

/** Chalk skein: a paper-thin pale glider, long swept wings, tiny body. Unit span ~1 (+Z forward). */
export function chalkSkein(): FaunaGeometry {
  const pale = lin(0xf0ebe0);
  const edge = lin(0xb8ad96);
  const make = (detail: boolean) => {
    const parts: BufferGeometry[] = [];
    parts.push(part(blob(0.04, 0.03, 0.22, 0, 0.5, 0, detail, 6, 4), (_p, _n, c) => c.copy(edge), rigid));
    for (const sx of [1, -1]) {
      const w = sheet([[0, 0.12], [sx * 0.5, -0.05], [sx * 0.48, -0.16], [0, -0.12]], 0.5);
      parts.push(part(w, (p, _n, c) => c.copy(pale).lerp(edge, Math.min(1, Math.abs(p.x) * 1.6)), sway));
    }
    return merge(parts);
  };
  return { lod0: make(true), lod1: make(false) };
}

/** Ochre sounder: a flat disc that lies flush with the crust, a ring of fine tendrils on top. */
export function ochreSounder(): FaunaGeometry {
  const crust = lin(0xae9866);
  const dark = lin(0x6b5a3a);
  const tip = lin(0xe6d6a8);
  const make = (detail: boolean) => {
    const parts: BufferGeometry[] = [];
    parts.push(part(blob(0.5, 0.12, 0.45, 0, 0.08, 0, detail, 12, 5), (_p, n, c) => c.copy(dark).lerp(crust, Math.max(0, n.y)), rigid));
    const n = detail ? 12 : 6;
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2;
      const base = new Vector3(Math.cos(a) * 0.22, 0.16, Math.sin(a) * 0.2);
      const top = new Vector3(Math.cos(a) * 0.32, 0.95, Math.sin(a) * 0.3);
      parts.push(part(segment(base, top, 0.015, 0.004, 3), (p, _n, c) => c.copy(dark).lerp(tip, p.y), sway));
    }
    return merge(parts);
  };
  return { lod0: make(true), lod1: make(false) };
}

// ---------------------------------------------------------------- Vesper

/** Mesa kite: a long-winged glider with a narrow body and a forked tail. Unit span ~1. */
export function mesaKite(): FaunaGeometry {
  const upper = lin(0x5a2c1c);
  const under = lin(0xc07a4e);
  const make = (detail: boolean) => {
    const parts: BufferGeometry[] = [];
    parts.push(part(blob(0.035, 0.03, 0.2, 0, 0.5, 0.02, detail, 6, 4), (_p, _n, c) => c.copy(upper), rigid));
    for (const sx of [1, -1]) {
      const w = sheet([[0, 0.08], [sx * 0.25, 0.06], [sx * 0.5, -0.02], [sx * 0.3, -0.06], [0, -0.06]], 0.5);
      parts.push(part(w, (p, n, c) => c.copy(n.y > 0 ? upper : under).lerp(under, Math.abs(p.x) * 0.5), sway));
      const t = sheet([[0, -0.15], [sx * 0.06, -0.3], [sx * 0.02, -0.18]], 0.5);
      parts.push(part(t, (_p, _n, c) => c.copy(upper), rigid));
    }
    return merge(parts);
  };
  return { lod0: make(true), lod1: make(false) };
}

/** Glass tick: a glossy black bead on six short legs. Height ~1 (scaled to centimetres). */
export function glassTick(): FaunaGeometry {
  const shell = lin(0x0f0f12);
  const sheen = lin(0x3a2f45);
  const legC = lin(0x1a1a1e);
  const make = (detail: boolean) => {
    const parts: BufferGeometry[] = [];
    parts.push(part(blob(0.45, 0.32, 0.6, 0, 0.45, 0, detail, 8, 5), (_p, n, c) => c.copy(shell).lerp(sheen, Math.max(0, n.y) * 0.8), rigid));
    if (detail) {
      for (let k = 0; k < 3; k++) {
        for (const sx of [1, -1]) {
          const z = 0.3 - k * 0.3;
          limb(parts, k, new Vector3(sx * 0.3, 0.4, z), new Vector3(sx * 0.7, 0.55, z * 1.2), new Vector3(sx * 0.85, 0, z * 1.4), 0.05, 0.03, 3, legC);
        }
      }
    }
    return merge(parts);
  };
  return { lod0: make(true), lod1: make(false) };
}

// ----------------------------------------------------------------- Orrin

/** Fog wader: a tall, narrow biped; body high on two long legs, neck and small head held low and forward. */
export function fogWader(): FaunaGeometry {
  const hide = lin(0x4a4256);
  const pale = lin(0x8a8496);
  const legC = lin(0x2a2930);
  const make = (detail: boolean) => {
    const parts: BufferGeometry[] = [];
    parts.push(part(blob(0.09, 0.12, 0.16, 0, 0.78, 0, detail, 10, 6), (_p, n, c) => c.copy(hide).lerp(pale, Math.max(0, -n.y)), rigid));
    parts.push(part(segment(new Vector3(0, 0.82, 0.12), new Vector3(0, 0.55, 0.38), 0.03, 0.02, detail ? 5 : 3), (_p, _n, c) => c.copy(hide), rigid));
    parts.push(part(blob(0.035, 0.03, 0.07, 0, 0.53, 0.42, detail, 6, 4), (_p, _n, c) => c.copy(pale), rigid));
    for (let k = 0; k < 2; k++) {
      const sx = k === 0 ? 1 : -1;
      limb(parts, k, new Vector3(sx * 0.05, 0.72, 0), new Vector3(sx * 0.07, 0.4, -0.08), new Vector3(sx * 0.08, 0, 0.02), 0.022, 0.01, detail ? 5 : 3, legC);
    }
    return merge(parts);
  };
  return { lod0: make(true), lod1: make(false) };
}

/** Column drifter: a gas-filled bladder trailing long fine filaments (they sway). Height ~1 = bladder top. */
export function columnDrifter(): FaunaGeometry {
  const skin = lin(0x8a6ea4);
  const pale = lin(0xd8cce6);
  const make = (detail: boolean) => {
    const parts: BufferGeometry[] = [];
    parts.push(part(blob(0.22, 0.18, 0.22, 0, 0.82, 0, detail, 12, 8), (_p, n, c) => c.copy(skin).lerp(pale, Math.max(0, n.y) * 0.6), rigid));
    const n = detail ? 9 : 4;
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2;
      const top = new Vector3(Math.cos(a) * 0.12, 0.68, Math.sin(a) * 0.12);
      const bot = new Vector3(Math.cos(a) * 0.18, -1.2 - (i % 3) * 0.4, Math.sin(a) * 0.18);
      parts.push(part(segment(top, bot, 0.008, 0.003, 3), (p, _n, c) => c.copy(pale).lerp(skin, Math.max(0, -p.y) * 0.3), sway));
    }
    return merge(parts);
  };
  return { lod0: make(true), lod1: make(false) };
}

/** Moss creeper: three low segments on three pairs of short legs. Height ~1 (scaled small). */
export function mossCreeper(): FaunaGeometry {
  const seg = lin(0x5c5468);
  const back = lin(0x8a6ea4);
  const legC = lin(0x2a2930);
  const make = (detail: boolean) => {
    const parts: BufferGeometry[] = [];
    for (let i = 0; i < 3; i++) parts.push(part(blob(0.28, 0.22, 0.3, 0, 0.4, 0.45 - i * 0.45, detail, 8, 5), (_p, n, c) => c.copy(seg).lerp(back, Math.max(0, n.y)), rigid));
    if (detail) {
      for (let k = 0; k < 3; k++) {
        for (const sx of [1, -1]) {
          const z = 0.45 - k * 0.45;
          limb(parts, k, new Vector3(sx * 0.2, 0.3, z), new Vector3(sx * 0.45, 0.4, z), new Vector3(sx * 0.55, 0, z), 0.04, 0.025, 3, legC);
        }
      }
    }
    return merge(parts);
  };
  return { lod0: make(true), lod1: make(false) };
}

// ------------------------------------------------------------------ Saro

/** Brine skater: a flat oval body on six long splayed legs that rest on the surface film. */
export function brineSkater(): FaunaGeometry {
  const body = lin(0x5cc4bc);
  const dark = lin(0x2a5a56);
  const legC = lin(0x9ec9c0);
  const make = (detail: boolean) => {
    const parts: BufferGeometry[] = [];
    parts.push(part(blob(0.3, 0.1, 0.42, 0, 0.35, 0, detail, 10, 4), (_p, n, c) => c.copy(dark).lerp(body, Math.max(0, n.y)), rigid));
    for (let k = 0; k < 3; k++) {
      for (const sx of [1, -1]) {
        const z = 0.25 - k * 0.25;
        limb(parts, k, new Vector3(sx * 0.2, 0.33, z), new Vector3(sx * 0.6, 0.6, z * 1.6), new Vector3(sx * 1.0, 0, z * 2.4), 0.025, 0.01, detail ? 3 : 2, legC);
      }
    }
    return merge(parts);
  };
  return { lod0: make(true), lod1: make(false) };
}

/** Crust tilter: a low four-legged body under a broad, mirror-bright dorsal plate. */
export function crustTilter(): FaunaGeometry {
  const hide = lin(0xcf9fa0);
  const plate = lin(0xf3eee8);
  const plateEdge = lin(0x9a8e8c);
  const legC = lin(0x8a6a6a);
  const make = (detail: boolean) => {
    const parts: BufferGeometry[] = [];
    parts.push(part(blob(0.22, 0.16, 0.36, 0, 0.42, 0, detail, 10, 6), (_p, _n, c) => c.copy(hide), rigid));
    parts.push(part(blob(0.07, 0.06, 0.09, 0, 0.42, 0.38, detail, 6, 4), (_p, _n, c) => c.copy(hide), rigid));
    const pl = sheet([[0, 0.5], [0.45, 0.25], [0.5, -0.2], [0, -0.45], [-0.5, -0.2], [-0.45, 0.25]], 0);
    pl.rotateX(-0.35);
    pl.translate(0, 0.72, -0.05);
    parts.push(part(pl, (p, _n, c) => c.copy(plate).lerp(plateEdge, Math.min(1, Math.hypot(p.x, p.z + 0.05) * 1.6)), rigid));
    for (let k = 0; k < 2; k++) {
      for (const sz of [1, -1]) {
        const sx = (k === 0 ? 1 : -1) * sz; // diagonal pairs share a phase
        limb(parts, k, new Vector3(sx * 0.16, 0.36, sz * 0.22), new Vector3(sx * 0.3, 0.3, sz * 0.28), new Vector3(sx * 0.3, 0, sz * 0.3), 0.04, 0.025, detail ? 4 : 3, legC);
      }
    }
    return merge(parts);
  };
  return { lod0: make(true), lod1: make(false) };
}

/** Salt veil: a single minute translucent flier (shown in columns of many). */
export function saltVeil(): FaunaGeometry {
  const pale = lin(0xf3e1da);
  const tint = lin(0x9ec9c0);
  const make = () => {
    const parts: BufferGeometry[] = [];
    for (const sx of [1, -1]) parts.push(part(sheet([[0, 0.3], [sx * 0.5, 0], [0, -0.3]], 0.5), (p, _n, c) => c.copy(pale).lerp(tint, Math.abs(p.x)), sway));
    return merge(parts);
  };
  return { lod0: make(), lod1: make() };
}
