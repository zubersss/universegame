// PLAYER-owned extension point (charter D): boot calls installPlayer(game) once,
// right after the Game exists. PLAYER installs its ON_FOOT hooks here with
// game.onFoot.install(...) (contract: src/game/onFoot.ts).

import type { Game } from '../game/Game';
import type { OnFootContext, OnFootExitReason, OnFootHooks } from '../game/onFoot';
import { BODIES, type BodyId } from '../world/bodies';
import { AbilityController } from '../abilities/AbilityController';
import { bodyPower } from '../abilities/catalog';
import { SIM_DT } from '../game/config';

/**
 * Everything PLAYER adds on foot: the visible explorer and the character
 * camera (frame), the camera toggle binding and the ability controller
 * (step), with powers deactivated when ON_FOOT ends.
 */
export class PlayerRuntime implements OnFootHooks {
  readonly abilities: AbilityController;
  /** Simulation time of the last rendered frame's interpolated state (null after enter). */
  private lastVisTime: number | null = null;

  constructor(private readonly game: Game) {
    this.abilities = new AbilityController(game.hud, (id) => {
      const def = (BODIES as Record<string, (typeof BODIES)[BodyId] | undefined>)[id];
      return def ? bodyPower(def) : 'walk';
    });
  }

  enter(ctx: OnFootContext): void {
    this.game.player?.attachVisual(this.game.render.scene);
    this.lastVisTime = null;
    this.abilities.enter(ctx);
  }

  step(dt: number): boolean {
    const p = this.game.player;
    if (p && this.game.input.consume('KeyC')) p.view.toggle();
    return this.abilities.step(dt);
  }

  frame(_dt: number, alpha: number): boolean {
    const g = this.game;
    const p = g.player;
    if (!p) return false;
    // Animate on simulation time: the rendered state is interpolated between
    // fixed steps, so its time is simTime - (1 - alpha) * SIM_DT. Pause,
    // loading and open panels stop the simulation and so freeze the
    // character; slow frames that drop steps never desynchronise the gait.
    const t = g.simTime + (alpha - 1) * SIM_DT;
    const dt = this.lastVisTime === null ? 0 : Math.min(0.25, Math.max(0, t - this.lastVisTime));
    this.lastVisTime = t;
    p.renderView(dt, alpha, g.cameraRig, g.lighting.envMap, g.settings.reducedMotion);
    return true;
  }

  exit(reason: OnFootExitReason): void {
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
