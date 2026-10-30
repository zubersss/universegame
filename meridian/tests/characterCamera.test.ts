import { beforeAll, describe, expect, it } from 'vitest';
import { Group, PerspectiveCamera, Vector3 } from 'three';
import { CHAR_CAMERA, CharacterCamera, type ArmCast } from '../src/player/CharacterCamera';
import { initPhysics, Physics, RAPIER, GROUPS } from '../src/physics/Physics';
import { Player, FOOT_OFFSET } from '../src/player/Player';
import { CameraRig } from '../src/render/CameraRig';
import { WALK } from '../src/game/config';

const UP = new Vector3(0, 1, 0);
const FWD = new Vector3(0, 0, -1);
const dt = 1 / 60;

beforeAll(async () => {
  await initPhysics();
});

function look(cam: PerspectiveCamera): Vector3 {
  cam.updateMatrixWorld();
  return cam.getWorldDirection(new Vector3());
}

describe('character camera (spring arm)', () => {
  it('sits behind and above the shoulder and looks exactly along the aim', () => {
    const cc = new CharacterCamera();
    const cam = new PerspectiveCamera();
    const feet = new Vector3(0, 0, 0);
    cc.update(dt, cam, feet, UP, FWD, -0.2, 0, null, null, false);
    const aim = FWD.clone().multiplyScalar(Math.cos(-0.2)).addScaledVector(UP, Math.sin(-0.2));
    expect(look(cam).distanceTo(aim)).toBeLessThan(1e-6);
    // Behind (+Z), to the right (+X), above the eye.
    expect(cam.position.z).toBeGreaterThan(3.5);
    expect(cam.position.x).toBeCloseTo(CHAR_CAMERA.shoulder, 5);
    expect(cam.position.y).toBeGreaterThan(CHAR_CAMERA.pivotUp);
    expect(cc.bodyVisible).toBe(true);
  });

  it('pulls in at once when something is behind and eases back out when clear', () => {
    const cc = new CharacterCamera();
    const cam = new PerspectiveCamera();
    const feet = new Vector3();
    let wall = 1.5; // distance to an obstacle along the arm
    const cast: ArmCast = (_from, dir, max) => (dir.z > 0.5 && wall < max ? wall : null);
    for (let i = 0; i < 30; i++) cc.update(dt, cam, feet, UP, FWD, 0, 0, null, null, false);
    expect(cc.arm).toBeCloseTo(CHAR_CAMERA.arm, 3);
    cc.update(dt, cam, feet, UP, FWD, 0, 0, cast, null, false);
    // Same frame: never through the obstacle.
    expect(cc.arm).toBeLessThanOrEqual(wall - CHAR_CAMERA.margin + 1e-9);
    expect(cc.pushedFrames).toBe(1);
    wall = 100;
    const arms: number[] = [];
    for (let i = 0; i < 90; i++) {
      cc.update(dt, cam, feet, UP, FWD, 0, 0, cast, null, false);
      arms.push(cc.arm);
    }
    // Eases out monotonically, reaching the rest length within 1.5 s and not snapping.
    for (let i = 1; i < arms.length; i++) expect(arms[i]).toBeGreaterThanOrEqual(arms[i - 1] - 1e-12);
    expect(arms[0] - (1.5 - CHAR_CAMERA.margin)).toBeLessThan(0.5);
    expect(arms[arms.length - 1]).toBeGreaterThan(CHAR_CAMERA.arm - 0.01);
  });

  it('keeps the minimum height above the analytic terrain where no collider is loaded', () => {
    const cc = new CharacterCamera();
    const cam = new PerspectiveCamera();
    // Terrain rising behind the character: height = 0.8 * z (z > 0 is behind).
    const terrain = (p: Vector3) => {
      const ground = Math.max(0, 0.8 * p.z);
      const need = ground + 1.6 - p.y;
      return need > 0 ? need : null;
    };
    cc.update(dt, cam, new Vector3(), UP, FWD, 0.3, 0, null, terrain, false);
    const ground = Math.max(0, 0.8 * cam.position.z);
    expect(cam.position.y - ground).toBeGreaterThanOrEqual(CHAR_CAMERA.minGround - 1e-9);
    expect(cc.minTerrainClearance).toBeGreaterThanOrEqual(CHAR_CAMERA.minGround - 1e-9);
  });

  it('pulls back with speed unless reduced motion is on', () => {
    const a = new CharacterCamera();
    const b = new CharacterCamera();
    const cam = new PerspectiveCamera();
    for (let i = 0; i < 200; i++) {
      a.update(dt, cam, new Vector3(), UP, FWD, 0, 7.5, null, null, false);
      b.update(dt, cam, new Vector3(), UP, FWD, 0, 7.5, null, null, true);
    }
    expect(a.arm).toBeGreaterThan(CHAR_CAMERA.arm + 0.3);
    expect(b.arm).toBeCloseTo(CHAR_CAMERA.arm, 6);
  });

  it('C toggles first person at eye height with the body hidden, and back', () => {
    const cc = new CharacterCamera();
    const cam = new PerspectiveCamera();
    cc.toggle();
    cc.update(dt, cam, new Vector3(0, 0, 0), UP, FWD, 0.1, 0, null, null, false);
    expect(cc.mode).toBe('first');
    expect(cam.position.distanceTo(new Vector3(0, CHAR_CAMERA.pivotUp, 0))).toBeLessThan(1e-9);
    expect(cc.bodyVisible).toBe(false);
    cc.toggle();
    for (let i = 0; i < 120; i++) cc.update(dt, cam, new Vector3(), UP, FWD, 0, 0, null, null, false);
    expect(cc.mode).toBe('third');
    expect(cc.bodyVisible).toBe(true);
  });
});

describe('player with the explorer and camera on real colliders', () => {
  function world() {
    const physics = new Physics();
    // Ground slab (terrain group) with its top at y = 0.
    const ground = physics.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(0, -1, 0));
    physics.world.createCollider(RAPIER.ColliderDesc.cuboid(50, 1, 50).setCollisionGroups(GROUPS.terrain), ground);
    physics.refreshQueries();
    const center = new Vector3(0, FOOT_OFFSET + WALK.skin + 0.01, 0);
    const player = new Player(physics, center, UP, FWD);
    const scene = new Group();
    player.attachVisual(scene);
    // Settle on the ground.
    const idle = { forward: 0, right: 0, sprint: false, jump: false, yaw: 0, pitch: 0 };
    for (let i = 0; i < 30; i++) {
      player.step(dt, idle, new Vector3(0, -1e7, 0), 9.8);
      physics.step();
    }
    const rig = new CameraRig(new PerspectiveCamera());
    return { physics, player, scene, rig };
  }

  it('renders the explorer at the capsule feet and keeps the camera above the ground and outside a wall', () => {
    const { physics, player, scene, rig } = world();
    expect(player.avatar).not.toBeNull();
    expect(scene.children.length).toBe(1);
    player.renderView(dt, 1, rig, null, false);
    const root = player.avatar!.rig.root.position;
    const feet = player.feet(new Vector3());
    expect(root.distanceTo(feet)).toBeLessThan(0.03); // lowered by the controller skin
    expect(rig.camera.position.y).toBeGreaterThan(1.5);
    expect(player.view.arm).toBeCloseTo(CHAR_CAMERA.arm, 2);
    // A wall 2 m behind the character (props group).
    const wall = physics.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(0, 2, 2.2));
    physics.world.createCollider(RAPIER.ColliderDesc.cuboid(5, 3, 0.2).setCollisionGroups(GROUPS.props), wall);
    physics.refreshQueries();
    player.renderView(dt, 1, rig, null, false);
    expect(rig.camera.position.z).toBeLessThan(2.0 - CHAR_CAMERA.probe + 1e-3);
    expect(player.view.arm).toBeLessThan(2.2);
    // Aim ray: along the camera's view, starting level with the eye.
    const o = new Vector3();
    const d = new Vector3();
    player.aim(o, d);
    expect(d.distanceTo(look(rig.camera))).toBeLessThan(1e-6);
    expect(Math.abs(o.z - player.eye(1, new Vector3()).z)).toBeLessThan(0.05);
    player.dispose();
    expect(scene.children.length).toBe(0);
  });

  it('C pressed while walking switches to first person through the step input', () => {
    const { player, rig } = world();
    player.step(dt, { forward: 0, right: 0, sprint: false, jump: false, yaw: 0, pitch: 0, view: true }, new Vector3(0, -1e7, 0), 9.8);
    player.renderView(dt, 1, rig, null, false);
    expect(player.view.mode).toBe('first');
    expect(player.avatar!.visible).toBe(false);
    expect(rig.camera.position.distanceTo(player.eye(1, new Vector3()))).toBeLessThan(0.01);
    player.dispose();
  });
});
