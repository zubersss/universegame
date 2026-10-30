// PLAYER-owned test hooks (charter D), exposed as window.__meridian.player in
// test builds only. Like the rest of the test API they inject input and read
// state; they never set gameplay state directly.

import { Vector3 } from 'three';
import type { Game } from '../game/Game';
import { playerRuntime } from '../player/install';
import { GROUPS } from '../physics/Physics';
import type { AbilityLogEntry, AbilityView } from '../abilities/AbilityController';
import { BlinkPower, FlightPower, SpeedPower } from '../abilities/powers';

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
  /**
   * The active power's motion and checks, with the walker's height measured
   * independently of the power (null when not on foot or without a power):
   * flight setpoint and readiness limit; superspeed run speed, braking and the
   * hazard ahead; blink aim target and jumps.
   */
  power(): Record<string, unknown> | null;
  /** Free distance for the walker's capsule moved straight toward the ship's centre (m; null when not on foot). */
  shipGap(): number | null;
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
        // The ladder climb in progress ('exit' / 'board'): the walker is held and powers wait until it ends.
        transition: rt?.transition?.kind ?? null,
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
    power() {
      const rt = playerRuntime(game);
      const p = game.player;
      const r = rt?.abilities.runtime;
      if (!p || !r) return null;
      // Feet above whatever the walker stands on (terrain, props, ship), by a ray from 2 m above them.
      const feet = p.feet(new Vector3());
      const from = new Vector3().copy(feet).addScaledVector(p.up, 2);
      const hit = game.physics.castRay(from.x, from.y, from.z, -p.up.x, -p.up.y, -p.up.z, 5000, GROUPS.queryWalk);
      // Feet above the generator's terrain (negative: below the ground), independent of collision.
      const rel = feet.sub(game.bodyCenterLocal);
      const rr = rel.length();
      const base = {
        primitive: r.primitive,
        state: rt.abilities.state,
        // The power's own refusal line (a refused step, take-off or run), while it shows.
        refusal: r.refusal,
        speed: Math.hypot(p.vel.length(), p.vVert),
        vVert: p.vVert,
        grounded: p.grounded,
        height: hit ? hit.toi - 2 : null,
        terrainClearance: rr - (game.ref.radius + game.terrainHeightAt(rel.divideScalar(rr))),
        hitWall: p.hitWall,
        // The walker's capsule intersects nothing where it stands (never inside solid).
        clear: p.fitsAt(p.feet(new Vector3())),
      };
      if (r instanceof FlightPower) return { ...base, setpoint: r.flight.speed, limit: Number.isFinite(r.flight.limit) ? r.flight.limit : null };
      if (r instanceof SpeedPower) {
        const sp = r.speed;
        return { ...base, run: sp.speed, braking: sp.braking, obstacle: Number.isFinite(sp.obstacle) ? sp.obstacle : null, obstacleKind: sp.obstacleKind };
      }
      if (r instanceof BlinkPower) {
        const t = r.target;
        return { ...base, aiming: r.aiming, target: { ok: t.ok, reason: t.reason, distance: t.distance }, jumps: r.lastJump.count, jumpFrom: r.lastJump.from.toArray(), jumpTo: r.lastJump.to.toArray() };
      }
      return base;
    },
    shipGap() {
      const p = game.player;
      if (!p) return null;
      const to = new Vector3().copy(game.ship.currPos).sub(p.pos);
      const d = to.length();
      if (d < 1e-6) return 0;
      const gap = p.sweepCapsule(to.divideScalar(d), d, 0);
      return Number.isFinite(gap) ? gap : d;
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
