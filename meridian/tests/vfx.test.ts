import { describe, expect, it } from 'vitest';
import { Color, Group, Mesh, MeshBasicMaterial, Vector3 } from 'three';
import { PowerVfx } from '../src/abilities/vfx';

const UP = new Vector3(0, 1, 0);
const CAM = new Vector3(0, 2, 5);

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
    v.update(1 / 60, { up: UP, camera: CAM, aim: { feet, ok: true }, dash: null }, false);
    const ring = meshes(v).find((m) => m.parent !== v.root)!;
    expect(ring.parent!.visible).toBe(true);
    expect(ring.parent!.position.distanceTo(feet)).toBeLessThan(1e-9);
    expect((ring.material as MeshBasicMaterial).color.getHexString()).toBe(new Color('#c8b6ff').getHexString());
    v.update(1 / 60, { up: UP, camera: CAM, aim: { feet, ok: false }, dash: null }, false);
    expect((ring.material as MeshBasicMaterial).color.getHexString()).toBe('ff4a4a');
    v.update(1 / 60, { up: UP, camera: CAM, aim: null, dash: null }, false);
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
    for (let i = 0; i < 30; i++) v.update(1 / 60, { up: UP, camera: CAM, aim: null, dash: null }, false);
    expect(meshes(v).filter((m) => m.parent === v.root && m.visible).length).toBe(0);
    v.dispose();
  });

  it('draws speed streaks only at superspeed and never with reduced motion', () => {
    const v = new PowerVfx(new Group(), '#ff7a3d');
    const dash = { center: new Vector3(0, 0.9, 0), dir: new Vector3(0, 0, -1), speed: 100 };
    v.update(1 / 60, { up: UP, camera: CAM, aim: null, dash }, false);
    const streaks = meshes(v).filter((m) => m.parent === v.root && (m.geometry as unknown as { parameters: { height?: number } }).parameters.height === 3.2);
    expect(streaks.length).toBe(10);
    expect(streaks.every((m) => m.visible)).toBe(true);
    expect((streaks[0].material as MeshBasicMaterial).opacity).toBeGreaterThan(0.2);
    v.update(1 / 60, { up: UP, camera: CAM, aim: null, dash: { ...dash, speed: 10 } }, false);
    expect(streaks.some((m) => m.visible)).toBe(false);
    v.update(1 / 60, { up: UP, camera: CAM, aim: null, dash }, true);
    expect(streaks.some((m) => m.visible)).toBe(false);
    v.dispose();
  });
});
