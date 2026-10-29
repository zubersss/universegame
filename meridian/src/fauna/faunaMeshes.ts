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
