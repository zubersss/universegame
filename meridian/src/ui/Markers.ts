import { Vector3, type PerspectiveCamera } from 'three';

export type MarkerKind = 'nav' | 'ship' | 'sample' | 'relay';

export interface MarkerSpec {
  id: string;
  label: string;
  /** Draw as a small unlabeled glyph (secondary targets). */
  minor?: boolean;
  /** Position in local (render) coordinates. */
  pos: Vector3;
  kind: MarkerKind;
  /** Distance shown under the label (m); omitted when undefined. */
  distance?: number;
}

const _v = new Vector3();
const _cam = new Vector3();

function fmtDist(d: number): string {
  if (d >= 100000) return `${(d / 1000).toFixed(0)} km`;
  if (d >= 1000) return `${(d / 1000).toFixed(1)} km`;
  return `${d.toFixed(0)} m`;
}

/** DOM markers anchored to world positions, clamped to the screen edge when off-screen. */
export class Markers {
  private readonly root: HTMLElement;
  private readonly els = new Map<string, { el: HTMLElement; lbl: HTMLElement; dist: HTMLElement; key: string; tf: string }>();

  constructor() {
    const r = document.getElementById('markers');
    if (!r) throw new Error('Missing #markers');
    this.root = r;
  }

  update(camera: PerspectiveCamera, specs: MarkerSpec[], width: number, height: number): void {
    const seen = new Set<string>();
    camera.getWorldPosition(_cam);
    const margin = 36;
    // Labels already placed this frame (earlier specs have priority).
    const placed: { x: number; y: number; above: boolean }[] = [];
    for (const s of specs) {
      seen.add(s.id);
      let m = this.els.get(s.id);
      if (!m) {
        const el = document.createElement('div');
        const glyph = document.createElement('div');
        glyph.className = 'glyph';
        const lbl = document.createElement('div');
        lbl.className = 'lbl';
        const dist = document.createElement('div');
        dist.className = 'dist';
        el.append(glyph, lbl, dist);
        this.root.appendChild(el);
        m = { el, lbl, dist, key: '', tf: '' };
        this.els.set(s.id, m);
      }
      // Project a point a bounded distance along the direction to the target:
      // destinations can lie far beyond the camera's far plane.
      _v.copy(s.pos).sub(_cam);
      const len = _v.length();
      if (len > 1000) _v.multiplyScalar(1000 / len);
      _v.add(_cam).applyMatrix4(camera.matrixWorldInverse);
      // Behind the camera: mirror to the front and push to the edge.
      const behind = _v.z > -0.01;
      if (behind) _v.z = -Math.max(Math.abs(_v.z), 0.01);
      _v.applyMatrix4(camera.projectionMatrix);
      const x = _v.x;
      const y = _v.y;
      let edge = behind || x < -1 || x > 1 || y < -1 || y > 1;
      let px = (x * 0.5 + 0.5) * width;
      let py = (-y * 0.5 + 0.5) * height;
      if (edge) {
        // Clamp along the ray from the screen center.
        const cx = width / 2;
        const cy = height / 2;
        let dx = px - cx;
        let dy = py - cy;
        if (behind && Math.abs(dx) < 1 && Math.abs(dy) < 1) dy = 1;
        const sx = (cx - margin) / Math.max(Math.abs(dx), 1e-6);
        const sy = (cy - margin) / Math.max(Math.abs(dy), 1e-6);
        const k = Math.min(sx, sy);
        px = cx + dx * k;
        py = cy + dy * k;
        edge = true;
      }
      // Targets close together on screen (a relay and its samples): the second
      // label goes above its glyph, further ones are reduced to glyphs.
      // Clamped to the bottom edge: the label goes above so it stays on screen.
      let above = edge && py > height / 2;
      let minor = !!s.minor;
      if (!minor) {
        const near = placed.filter((p) => Math.abs(p.x - px) < 96 && Math.abs(p.y - py) < 34);
        if (near.length > 0) {
          if (above || near.some((p) => p.above)) minor = true;
          else above = true;
        }
        if (!minor) placed.push({ x: px, y: py, above });
      }
      const cls = `marker ${s.kind === 'sample' || s.kind === 'relay' ? 'teal' : s.kind === 'ship' ? 'ship' : ''}${edge ? ' edge' : ''}${minor ? ' minor' : ''}${above ? ' above' : ''}`;
      if (m.el.className !== cls) m.el.className = cls;
      // The glyph's center sits on the target; the label hangs below (or above) it.
      // Style writes only on change: per-frame CSS parsing is garbage for the DOM heap.
      const glyphHalf = minor ? 4.5 : s.kind === 'ship' ? 5 : 7;
      const ty = above ? `calc(-100% + ${glyphHalf}px)` : `${-glyphHalf}px`;
      const tf = `translate(${px.toFixed(1)}px, ${py.toFixed(1)}px) translate(-50%, ${ty})`;
      if (tf !== m.tf) {
        m.tf = tf;
        m.el.style.transform = tf;
      }
      const d = s.distance !== undefined ? fmtDist(s.distance) : '';
      const key = `${s.label}|${d}`;
      if (key !== m.key) {
        m.key = key;
        m.lbl.textContent = s.label;
        m.dist.textContent = d;
      }
    }
    for (const [id, m] of this.els) {
      if (!seen.has(id)) {
        m.el.remove();
        this.els.delete(id);
      }
    }
  }

  clear(): void {
    for (const m of this.els.values()) m.el.remove();
    this.els.clear();
  }
}
