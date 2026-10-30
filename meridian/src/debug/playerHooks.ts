// PLAYER-owned test hooks (charter D), exposed as window.__meridian.player in
// test builds only. Like the rest of the test API they inject input and read
// state; they never set gameplay state directly.

import { Vector3 } from 'three';
import type { Game } from '../game/Game';
import { playerRuntime } from '../player/install';
import { GROUPS } from '../physics/Physics';
import type { AbilityLogEntry, AbilityView } from '../abilities/AbilityController';

const _v = new Vector3();

export interface PlayerTestApi {
  /** Read-only snapshot of the explorer, its camera and the ability controller (null when not on foot). */
  state(): Record<string, unknown> | null;
  /** Press C (camera view toggle) as an edge input. */
  pressView(): void;
  /** Start a fresh planted-foot slip measurement (diagnostic counters only). */
  resetSlip(): void;
  /** The active ability: {id, state, active, charge, cooldown, preview} (null when not on foot). */
  ability(): AbilityView | null;
  /** The last ability state changes {t, from, to} (bounded), oldest first. */
  abilityLog(): AbilityLogEntry[];
}

export function playerTestHooks(game: Game): PlayerTestApi & Record<string, unknown> {
  return {
    state() {
      const p = game.player;
      const rt = playerRuntime(game);
      if (!p) return null;
      const a = p.avatar;
      const v = p.view;
      const cam = game.render.camera.position;
      // Camera height above the analytic terrain, measured independently of the camera code.
      const toCam = new Vector3().copy(cam).sub(game.bodyCenterLocal);
      const r = toCam.length();
      const cameraAltitude = r - (game.ref.radius + game.terrainHeightAt(toCam.divideScalar(r)));
      const eye = p.eye(1, _v);
      // Camera height above the collision geometry (terrain, props, ship) below it, by ray.
      const up = toCam.copy(cam).sub(game.bodyCenterLocal).normalize();
      const from = new Vector3().copy(cam).addScaledVector(up, 50);
      const hit = game.physics.castRay(from.x, from.y, from.z, -up.x, -up.y, -up.z, 100, GROUPS.queryWalk);
      // The ray starts 50 m above the camera: the ground lies (toi - 50) m below it.
      const groundGap = hit ? hit.toi - 50 : null;
      return {
        avatar: a
          ? {
              attached: !!a.rig.root.parent,
              visible: a.visible,
              state: a.anim.state,
              entries: { ...a.anim.entries },
              phase: a.anim.phase,
              speed: a.anim.speed,
              maxSlip: a.maxSlip,
              slipSamples: a.slipSamples,
              slipSamplesMoving: a.slipSamplesMoving,
              settleSteps: a.anim.settleSteps,
              overreach: a.anim.overreach,
              hipsDrop: a.anim.hipsDrop,
              facing: a.facing.toArray(),
              rootToFeet: a.rig.root.position.distanceTo(p.feet(new Vector3())),
            }
          : null,
        camera: {
          mode: v.mode,
          arm: v.arm,
          shoulder: v.shoulder,
          bodyVisible: v.bodyVisible,
          minTerrainClearance: v.minTerrainClearance,
          pushedFrames: v.pushedFrames,
          distanceToEye: cam.distanceTo(eye),
          altitude: cameraAltitude,
          groundGap,
        },
        ability: rt
          ? { state: rt.abilities.state, power: rt.abilities.power?.id ?? null, body: rt.abilities.bodyId, unlocked: [...rt.abilities.unlocked], lastRefusal: rt.abilities.lastRefusal }
          : null,
      };
    },
    pressView() {
      game.input.press('KeyC');
    },
    ability() {
      const rt = playerRuntime(game);
      return rt && game.player ? rt.abilities.view() : null;
    },
    abilityLog() {
      const rt = playerRuntime(game);
      return rt ? rt.abilities.log.map((e) => ({ ...e })) : [];
    },
    resetSlip() {
      const a = game.player?.avatar;
      if (a) {
        a.maxSlip = 0;
        a.slipSamples = 0;
        a.slipSamplesMoving = 0;
      }
    },
  };
}
