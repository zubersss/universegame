// PLAYER-owned extension point (charter D): boot calls installPlayer(game) once,
// right after the Game exists. PLAYER installs its ON_FOOT hooks here with
// game.onFoot.install(...) (contract: src/game/onFoot.ts).

import type { Game } from '../game/Game';
import type { OnFootExitReason, OnFootHooks } from '../game/onFoot';
import type { Player, WalkInput } from './Player';
import { BlinkPower, type PowerWorld } from '../abilities/powers';
import { PowerVfx, rushStrength, trailStrength, type VfxFrame } from '../abilities/vfx';
import { AbilitySounds, type AudioBus } from '../audio/abilitySounds';
import { bodyGravity } from '../world/environment';
import { BODIES, isBodyId } from '../world/bodies';
import { AbilityController, type AbilityEnterContext } from '../abilities/AbilityController';
import type { AbilitySave } from '../abilities/save';
import { bodyPower } from '../abilities/catalog';
import { SIM_DT } from '../game/config';
import { GROUPS } from '../physics/Physics';
import { newScriptedPose, ShipTransition, type TransitionWorld } from './Transitions';
import { Vector3 } from 'three';

/**
 * Everything PLAYER adds on foot: the visible explorer and the character
 * camera (frame), the camera toggle binding and the ability controller
 * (step), with powers deactivated when ON_FOOT ends.
 */
export class PlayerRuntime implements OnFootHooks {
  readonly abilities: AbilityController;
  /** Simulation time of the last rendered frame's interpolated state (null after enter). */
  private lastVisTime: number | null = null;
  /** Ladder transition in progress (the walker is held; only the body moves) and its clock. */
  transition: ShipTransition | null = null;
  private transitionTime = 0;
  private readonly pose = newScriptedPose();
  private exitsSeen: number;
  private readonly world: TransitionWorld;
  private readonly world2: PowerWorld;

  constructor(private readonly game: Game) {
    this.abilities = new AbilityController(game.hud, (id) => (isBodyId(id) ? bodyPower(BODIES[id]) : 'walk'), () => game.simTime);
    this.exitsSeen = game.counters.exits;
    this.world = {
      shipToLocal: (v, out) => game.ship.localToWorld(v, out),
      upAt: (p, out) => out.copy(p).sub(game.bodyCenterLocal).normalize(),
      groundBelow: (p, up, out) => {
        const hit = game.physics.castRay(p.x, p.y, p.z, -up.x, -up.y, -up.z, 4, GROUPS.queryStatic);
        return hit ? out.copy(p).addScaledVector(up, -hit.toi) : null;
      },
    };
    this.world2 = {
      player: null as unknown as Player,
      held: (code) => game.input.isDown(code),
      pressed: (code) => game.input.consume(code),
      walk: { forward: 0, right: 0, sprint: false, jump: false, yaw: 0, pitch: 0 },
      center: game.bodyCenterLocal,
      gravity: 0,
      ready: (pt) => {
        const b = game.body;
        return !!b && b.collision.readyAt(_r.copy(pt).sub(game.bodyCenterLocal));
      },
    };
  }

  enter(ctx: AbilityEnterContext): void {
    this.game.player?.attachVisual(this.game.render.scene, () => this.game.lighting.envMap);
    this.lastVisTime = null;
    this.transition = null;
    this.abilities.enter(ctx);
    this.vfx?.dispose();
    const power = this.abilities.power;
    this.vfx = power && this.abilities.runtime ? new PowerVfx(this.game.render.scene, power.feedback.color) : null;
    this.blinksSeen = this.blinkCount();
  }

  /** Power effects (blink marker and flashes, superspeed streaks); null without a power. */
  private vfx: PowerVfx | null = null;
  private blinksSeen = 0;
  /** Power sounds through the game's effects bus (silent until GameAudio exposes bus()). */
  private readonly sounds = new AbilitySounds(() => {
    const audio = this.game.audio as unknown as { bus?: () => AudioBus | null };
    return typeof audio.bus === 'function' ? audio.bus() : null;
  });
  private logSeen = 0;
  private refusalSeen: string | null = null;

  private blinkCount(): number {
    const rt = this.abilities.runtime;
    return rt instanceof BlinkPower ? rt.lastJump.count : 0;
  }

  /** Effects for one rendered frame. */
  private updateVfx(dt: number, p: Player): void {
    const v = this.vfx;
    if (!v) return;
    const rt = this.abilities.runtime;
    let aim: VfxFrame['aim'] = null;
    if (rt instanceof BlinkPower) {
      if (rt.aiming && this.abilities.usable) aim = { feet: rt.target.feet, ok: rt.target.ok };
      if (rt.lastJump.count !== this.blinksSeen) {
        this.blinksSeen = rt.lastJump.count;
        v.flash(_fx.copy(rt.lastJump.from).addScaledVector(p.up, 1));
        v.flash(_fx.copy(rt.lastJump.to).addScaledVector(p.up, 1));
      }
    }
    // Speed lines and flight trails along the full velocity (a flier climbs and dives).
    const motion = this.abilities.motion();
    let rush: VfxFrame['rush'] = null;
    let trails: VfxFrame['trails'] = null;
    _fd.copy(p.vel);
    if (motion?.mode === 'flight') _fd.addScaledVector(p.up, p.vVert);
    if (motion && _fd.lengthSq() > 1) {
      _fd.normalize();
      rush = { center: p.pos, dir: _fd, speed: motion.speed, strength: rushStrength(motion.mode, motion.speed) };
      const ts = motion.mode === 'flight' ? trailStrength(motion.speed) : 0;
      if (ts > 0 && p.avatar?.visible) {
        p.avatar.bootTips(_tipL, _tipR);
        trails = { from: _tips, dir: _fd, strength: ts };
      }
    }
    v.update(dt, { up: p.up, camera: this.game.render.camera.position, aim, rush, trails }, this.game.settings.reducedMotion);
  }

  /** Sounds for one rendered frame: the rush by speed, cues on take-off, blinks and refusals. */
  private updateSounds(dt: number): void {
    const s = this.sounds;
    s.update(dt, this.abilities.motion());
    const log = this.abilities.log;
    const changes = this.abilities.changes;
    if (changes !== this.logSeen) {
      // Only the newest change can be new this frame (one power step per fixed step at most a few).
      const last = log[log.length - 1];
      if (last && last.to === 'flight') s.takeoff();
      if (last && (last.to === 'blink' || last.from === 'blink')) s.blink();
      this.logSeen = changes;
    }
    const refusal = this.abilities.runtime?.refusal ?? null;
    if (refusal && refusal !== this.refusalSeen) s.refuse();
    this.refusalSeen = refusal;
  }

  /**
   * A fresh exit from the ship (Game counts it just after entering ON_FOOT,
   * so this runs on the first step or frame after enter): climb down the
   * ladder. Restores and re-placements do not count as exits.
   */
  private checkExit(): void {
    if (this.game.counters.exits === this.exitsSeen) return;
    this.exitsSeen = this.game.counters.exits;
    this.start('exit');
  }

  step(dt: number, input: WalkInput): boolean {
    const g = this.game;
    const p = g.player;
    this.checkExit();
    if (this.transition) {
      this.transitionTime += dt;
      if (this.transitionTime < this.transition.duration) return true; // hold the walker
      const boarding = this.transition.kind === 'board';
      this.transition = null;
      if (boarding) {
        // The climb is done: hand the player's E back to Game, which boards.
        g.input.press('KeyE');
        return false;
      }
    }
    // E at the ship: climb the ladder first, then board.
    if (p && p.grounded && g.interactionTarget()?.kind === 'ship' && g.input.consume('KeyE')) {
      this.start('board');
      if (this.transition) return true;
      g.input.press('KeyE');
    }
    if (p && g.input.consume('KeyC')) p.view.toggle();
    return this.abilities.step(dt, p && g.body ? this.powerWorld(p, input) : null);
  }

  /** The game as the powers see it this step. */
  private powerWorld(p: Player, input: WalkInput): PowerWorld {
    const g = this.game;
    const body = g.body!;
    const c = body.def.center;
    const sys = _v.copy(p.pos).add(g.origin);
    const gravity = bodyGravity(body.def, sys.x - c[0], sys.y - c[1], sys.z - c[2], _g).length();
    const w = this.world2;
    w.player = p;
    w.walk = input;
    w.center = g.bodyCenterLocal;
    w.gravity = gravity;
    return w;
  }

  private start(kind: 'exit' | 'board'): void {
    const p = this.game.player;
    if (!p) return;
    const feet = p.feet(new Vector3());
    this.transition = kind === 'exit' ? ShipTransition.exit(this.world, feet, p.heading) : ShipTransition.board(this.world, feet);
    this.transitionTime = 0;
  }

  frame(_dt: number, alpha: number): boolean {
    const g = this.game;
    const p = g.player;
    if (!p) return false;
    this.checkExit();
    // Animate on simulation time: the rendered state is interpolated between
    // fixed steps, so its time is simTime - (1 - alpha) * SIM_DT. Pause,
    // loading and open panels stop the simulation and so freeze the
    // character; slow frames that drop steps never desynchronise the gait.
    const { t, alpha: a, dt } = visualClock(g.simTime, alpha, this.lastVisTime);
    this.lastVisTime = t;
    const scripted = this.transition ? this.transition.sample(this.transitionTime + (a - 1) * SIM_DT, this.pose) : null;
    p.renderView(dt, a, g.cameraRig, g.settings.reducedMotion, scripted, this.abilities.motion());
    this.updateVfx(dt, p);
    this.updateSounds(dt);
    return true;
  }

  exit(reason: OnFootExitReason): void {
    this.transition = null;
    this.abilities.exit(reason);
    this.vfx?.dispose();
    this.vfx = null;
    this.sounds.dispose();
  }

  /** The ability fields for a save snapshot (schema 2: player.abilityState and unlocked). */
  saveState(): AbilitySave {
    return this.abilities.snapshot();
  }
}

/**
 * The rendered moment on simulation time (the state shown is interpolated
 * between fixed steps: simTime - (1 - alpha) * SIM_DT) and the animation dt
 * since the last frame. It never runs backward: when the stepper restarts
 * (resume after pause or loading) with a smaller alpha, the last rendered
 * moment is held instead.
 */
export function visualClock(simTime: number, alpha: number, last: number | null): { t: number; alpha: number; dt: number } {
  let a = alpha;
  let t = simTime + (a - 1) * SIM_DT;
  if (last !== null && t < last) {
    a = Math.min(1, alpha + (last - t) / SIM_DT);
    t = simTime + (a - 1) * SIM_DT;
  }
  const dt = last === null ? 0 : Math.min(0.25, Math.max(0, t - last));
  return { t, alpha: a, dt };
}

const _v = new Vector3();
const _g = new Vector3();
const _r = new Vector3();
const _fx = new Vector3();
const _fd = new Vector3();
const _tipL = new Vector3();
const _tipR = new Vector3();
const _tips = [_tipL, _tipR] as const;

const runtimes = new WeakMap<Game, PlayerRuntime>();

export function installPlayer(game: Game): void {
  const r = new PlayerRuntime(game);
  runtimes.set(game, r);
  game.onFoot.install(r);
}

/** The runtime installed for a game (test hooks, diagnostics). */
export function playerRuntime(game: Game): PlayerRuntime | null {
  return runtimes.get(game) ?? null;
}
