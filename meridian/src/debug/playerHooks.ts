// PLAYER-owned test hooks (charter D), exposed as window.__meridian.player in
// test builds only. Like the rest of the test API they inject input and read
// state; they never set gameplay state directly.

import { Vector3 } from 'three';
import type { Game } from '../game/Game';
import { playerRuntime } from '../player/install';

const _v = new Vector3();

export interface PlayerTestApi {
  /** Read-only snapshot of the explorer, its camera and the ability controller (null when not on foot). */
  state(): Record<string, unknown> | null;
  /** Press C (camera view toggle) as an edge input. */
  pressView(): void;
  /** Start a fresh planted-foot slip measurement (diagnostic counters only). */
  resetSlip(): void;
}

export function playerTestHooks(game: Game): PlayerTestApi & Record<string, unknown> {
  return {
    state() {
      const p = game.player;
      const rt = playerRuntime(game);
      if (!p) return null;
      const a = p.avatar;
      const v = p.view;
      const eye = p.eye(1, _v);
      const cam = game.render.camera.position;
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
        },
        ability: rt
          ? { state: rt.abilities.state, power: rt.abilities.power?.id ?? null, body: rt.abilities.bodyId, unlocked: [...rt.abilities.unlocked], lastRefusal: rt.abilities.lastRefusal }
          : null,
      };
    },
    pressView() {
      game.input.press('KeyC');
    },
    resetSlip() {
      const a = game.player?.avatar;
      if (a) {
        a.maxSlip = 0;
        a.slipSamples = 0;
      }
    },
  };
}
