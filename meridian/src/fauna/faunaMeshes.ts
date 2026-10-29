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
