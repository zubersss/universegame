// PLAYER-owned extension point (charter D): boot calls installPlayer(game) once,
// right after the Game exists. PLAYER installs its ON_FOOT hooks here with
// game.onFoot.install(...) (contract: src/game/onFoot.ts).

import type { Game } from '../game/Game';
import type { OnFootContext, OnFootExitReason, OnFootHooks } from '../game/onFoot';
import { BODIES, type BodyId } from '../world/bodies';
import { AbilityController } from '../abilities/AbilityController';
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

  constructor(private readonly game: Game) {
    this.abilities = new AbilityController(game.hud, (id) => {
      const def = (BODIES as Record<string, (typeof BODIES)[BodyId] | undefined>)[id];
      return def ? bodyPower(def) : 'walk';
    });
    this.exitsSeen = game.counters.exits;
    this.world = {
      shipToLocal: (v, out) => game.ship.localToWorld(v, out),
      upAt: (p, out) => out.copy(p).sub(game.bodyCenterLocal).normalize(),
      groundBelow: (p, up, out) => {
        const hit = game.physics.castRay(p.x, p.y, p.z, -up.x, -up.y, -up.z, 4, GROUPS.queryStatic);
        return hit ? out.copy(p).addScaledVector(up, -hit.toi) : null;
      },
    };
  }

  enter(ctx: OnFootContext): void {
    this.game.player?.attachVisual(this.game.render.scene);
    this.lastVisTime = null;
    this.transition = null;
    this.abilities.enter(ctx);
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

  step(dt: number): boolean {
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
    return this.abilities.step(dt);
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
    const t = g.simTime + (alpha - 1) * SIM_DT;
    const dt = this.lastVisTime === null ? 0 : Math.min(0.25, Math.max(0, t - this.lastVisTime));
    this.lastVisTime = t;
    const scripted = this.transition ? this.transition.sample(this.transitionTime + (alpha - 1) * SIM_DT, this.pose) : null;
    p.renderView(dt, alpha, g.cameraRig, g.lighting.envMap, g.settings.reducedMotion, scripted);
    return true;
  }

  exit(reason: OnFootExitReason): void {
    this.transition = null;
    this.abilities.exit(reason);
  }
}

const runtimes = new WeakMap<Game, PlayerRuntime>();

/** On-foot keys outside Game's own key set, latched into its input as edge presses. */
const EXTRA_KEYS = new Set(['KeyC']);

export function installPlayer(game: Game): void {
  const r = new PlayerRuntime(game);
  runtimes.set(game, r);
  game.onFoot.install(r);
  if (typeof window !== 'undefined') {
    window.addEventListener('keydown', (e) => {
      if (!EXTRA_KEYS.has(e.code) || e.repeat || !game.input.active) return;
      const t = e.target;
      if (t instanceof HTMLElement && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable)) return;
      game.input.press(e.code);
    });
  }
}

/** The runtime installed for a game (test hooks, diagnostics). */
export function playerRuntime(game: Game): PlayerRuntime | null {
  return runtimes.get(game) ?? null;
}
