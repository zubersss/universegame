import { describe, expect, it } from 'vitest';
import { Color, Group, Mesh, MeshBasicMaterial, Vector3 } from 'three';
import { PowerVfx, rushStrength, trailStrength } from '../src/abilities/vfx';

const UP = new Vector3(0, 1, 0);
const CAM = new Vector3(0, 2, 5);

/** The quad's front face (+z, the side a FrontSide material draws) looks toward the camera. */
function facesCamera(m: Mesh, cam: Vector3): boolean {
  m.updateMatrixWorld(true);
  const at = new Vector3().setFromMatrixPosition(m.matrixWorld);
  const n = new Vector3(0, 0, 1).transformDirection(m.matrixWorld);
  return n.dot(cam.clone().sub(at)) > 0;
}

function meshes(v: PowerVfx): Mesh[] {
  const out: Mesh[] = [];
  v.root.traverse((o) => {
    if ((o as Mesh).isMesh) out.push(o as Mesh);
  });
  return out;
}

describe('power effects', () => {
  it('marks the blink target in the power colour, red when refused, hidden when not aiming', () => {
    const parent = new Group();
    const v = new PowerVfx(parent, '#c8b6ff');
    const feet = new Vector3(3, 0, -20);
    v.update(1 / 60, { up: UP, camera: CAM, aim: { feet, ok: true }, rush: null, trails: null }, false);
    const ring = meshes(v).find((m) => m.parent !== v.root)!;
    expect(ring.parent!.visible).toBe(true);
    expect(ring.parent!.position.distanceTo(feet)).toBeLessThan(1e-9);
    expect((ring.material as MeshBasicMaterial).color.getHexString()).toBe(new Color('#c8b6ff').getHexString());
    v.update(1 / 60, { up: UP, camera: CAM, aim: { feet, ok: false }, rush: null, trails: null }, false);
    expect((ring.material as MeshBasicMaterial).color.getHexString()).toBe('ff4a4a');
    v.update(1 / 60, { up: UP, camera: CAM, aim: null, rush: null, trails: null }, false);
    expect(ring.parent!.visible).toBe(false);
    v.dispose();
    expect(parent.children.length).toBe(0);
  });

  it('flashes briefly where a blink leaves and lands', () => {
    const v = new PowerVfx(new Group(), '#c8b6ff');
    v.flash(new Vector3(0, 1, 0));
    v.flash(new Vector3(0, 1, -30));
    const flashes = meshes(v).filter((m) => m.parent === v.root && m.visible);
    expect(flashes.length).toBe(2);
    for (let i = 0; i < 30; i++) v.update(1 / 60, { up: UP, camera: CAM, aim: null, rush: null, trails: null }, false);
    expect(meshes(v).filter((m) => m.parent === v.root && m.visible).length).toBe(0);
    v.dispose();
  });

  it('draws speed lines at superspeed and in fast flight, never with reduced motion', () => {
    const v = new PowerVfx(new Group(), '#ff7a3d');
    const rush = { center: new Vector3(0, 0.9, 0), dir: new Vector3(0, 0, -1), speed: 100, strength: rushStrength('dash', 100) };
    // Seen from the side, well away from every line.
    const side = new Vector3(14, 1.5, -2);
    v.update(1 / 60, { up: UP, camera: side, aim: null, rush, trails: null }, false);
    const streaks = meshes(v).filter((m) => m.parent === v.root && (m.geometry as unknown as { parameters?: { height?: number } }).parameters?.height === 3.2);
    expect(streaks.length).toBe(10);
    expect(streaks.every((m) => m.visible && m.scale.x === 1)).toBe(true);
    // Drawn, not culled: the front face of every streak turns to the camera.
    expect(streaks.every((m) => facesCamera(m, side))).toBe(true);
    expect((streaks[0].material as MeshBasicMaterial).opacity).toBeGreaterThan(0.2);
    // From the chase camera too.
    v.update(1 / 60, { up: UP, camera: CAM, aim: null, rush, trails: null }, false);
    expect(streaks.filter((m) => m.visible).every((m) => facesCamera(m, CAM))).toBe(true);
    v.update(1 / 60, { up: UP, camera: side, aim: null, rush: { ...rush, speed: 10, strength: rushStrength('dash', 10) }, trails: null }, false);
    expect(streaks.some((m) => m.visible)).toBe(false);
    v.update(1 / 60, { up: UP, camera: side, aim: null, rush, trails: null }, true);
    expect(streaks.some((m) => m.visible)).toBe(false);
    // Superspeed shows them from 20 m/s; flight from 60, faint at the 90 m/s cruise, full with boost.
    expect(rushStrength('dash', 20)).toBe(0);
    expect(rushStrength('dash', 110)).toBe(1);
    expect(rushStrength('flight', 50)).toBe(0);
    expect(rushStrength('flight', 90)).toBeGreaterThan(0.15);
    expect(rushStrength('flight', 90)).toBeLessThan(0.3);
    expect(rushStrength('flight', 220)).toBe(1);
    // Lines near the camera thin out and vanish instead of smearing across the view.
    v.update(1 / 60, { up: UP, camera: new Vector3(0, 1.2, 2), aim: null, rush, trails: null }, false);
    for (const m of streaks) {
      const d = m.position.distanceTo(new Vector3(0, 1.2, 2));
      if (d < 3) expect(m.visible).toBe(false);
      if (m.visible) expect(m.scale.x).toBeCloseTo(Math.min(1, (d - 3) / 3), 6);
    }
    // Climbing straight up (travel along up): still a valid frame, no NaN.
    v.update(1 / 60, { up: UP, camera: side, aim: null, rush: { ...rush, dir: new Vector3(0, 1, 0), speed: 150, strength: 1 }, trails: null }, false);
    for (const m of streaks) {
      expect(m.visible).toBe(true);
      expect([m.position.x, m.position.y, m.position.z, m.quaternion.x, m.quaternion.w].every(Number.isFinite)).toBe(true);
    }
    v.dispose();
  });

  it('draws two thin boot trails only at flight boost, never near the camera', () => {
    const v = new PowerVfx(new Group(), '#7fd4ff');
    const trails = meshes(v).filter((m) => (m.geometry as { index: unknown }).index && (m.geometry.getAttribute('color') ?? null) !== null);
    expect(trails.length).toBe(2);
    // Flying along -Z; the boots trail behind the body; the camera 7 m behind and 2 m up.
    const dir = new Vector3(0, 0, -1);
    const from = [new Vector3(-0.1, 0, 0.9), new Vector3(0.1, 0, 0.9)] as const;
    const cam = new Vector3(0, 2, 7);
    const frame = (speed: number, camera = cam, reduced = false) =>
      v.update(1 / 60, { up: UP, camera, aim: null, rush: null, trails: trailStrength(speed) > 0 ? { from, dir, strength: trailStrength(speed) } : null }, reduced);
    // Cruise: none.
    expect(trailStrength(90)).toBe(0);
    frame(90);
    expect(trails.some((m) => m.visible)).toBe(false);
    // Boost: both, starting at the boot tips and running back along the travel direction.
    frame(220);
    expect(trails.every((m) => m.visible)).toBe(true);
    for (let i = 0; i < 2; i++) {
      const m = trails[i];
      m.updateMatrixWorld(true);
      const head = new Vector3(0, 0, 0).applyMatrix4(m.matrixWorld);
      const tail = new Vector3(0, -1, 0).applyMatrix4(m.matrixWorld);
      expect(head.distanceTo(from[i])).toBeLessThan(1e-6);
      expect(facesCamera(m, cam)).toBe(true);
      const back = tail.clone().sub(head);
      expect(back.clone().normalize().dot(dir)).toBeLessThan(-0.999);
      // Seen from the chase camera it stops 4 m short of the camera: no part comes nearer.
      for (let k = 0; k <= 20; k++) expect(head.clone().lerp(tail, k / 20).distanceTo(cam)).toBeGreaterThanOrEqual(4 - 1e-6);
      expect(back.length()).toBeLessThan(5);
    }
    // Seen from the side the whole trail shows.
    frame(220, new Vector3(9, 1, 0));
    expect(trails.every((m) => m.visible)).toBe(true);
    expect(trails[0].scale.y).toBeCloseTo(14, 6);
    // Static, so they stay with reduced motion; a camera ahead looking back sees them run away from it, whole.
    frame(220, cam, true);
    expect(trails.every((m) => m.visible)).toBe(true);
    frame(220, new Vector3(0, 2, -5));
    expect(trails.every((m) => m.visible && Math.abs(m.scale.y - 14) < 1e-6)).toBe(true);
    // Seen exactly end-on: nothing to draw, and no NaN.
    frame(220, new Vector3(-0.1, 0, 30));
    expect(trails[0].visible).toBe(false);
    v.dispose();
  });
});
