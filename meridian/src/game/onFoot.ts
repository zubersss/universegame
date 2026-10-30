// ON_FOOT hook points for the ability system (charter section I: AbilityState
// lives inside ON_FOOT). PLAYER implements OnFootHooks and installs it with
// game.onFoot.install() from src/player/install.ts; Game routes every mode
// change through setMode(), so enter/exit always pair and step/frame only run
// in between. Mode stays unchanged.

import type { BodyId } from '../world/bodies';
import type { AbilityId, AbilitySave } from '../abilities/save';
import type { WalkInput } from '../player/Player';
import type { Mode } from './Game';

/** Why the character left ON_FOOT. Powers deactivate on 'board'; the others re-place the character. */
export type OnFootExitReason = 'board' | 'restore' | 'relocate' | 'replaced';

export interface OnFootContext {
  body: BodyId;
  /**
   * The power active while exploring this body: its own, once an arrival
   * unlocked it (charter K), else null (walking only). Game always sets it;
   * the hooks activate exactly this power and nothing else. Optional in the
   * type only so contexts built without a power (tests) still type-check.
   */
  power?: AbilityId | null;
  /** The ability fields of the save being restored, on the enter that follows a restore only. */
  restored?: AbilitySave | null;
}

export interface OnFootHooks {
  /** The character has just been placed outside the ship (or restored on foot). */
  enter(ctx: OnFootContext): void;
  /**
   * One fixed step (SIM_DT) while ON_FOOT, before the walk controller, with this
   * step's walk input (look, move, jump, sprint; all idle unless playing).
   * Return true when an active ability moved the character this step: the walk
   * controller is then skipped, so the character has exactly one position owner.
   */
  step(dt: number, input: WalkInput): boolean;
  /** The character is leaving ON_FOOT. */
  exit(reason: OnFootExitReason): void;
  /**
   * Once per rendered frame while on foot (also paused or loading), with the
   * interpolation alpha. Return true when the hooks placed the camera (character
   * camera); otherwise Game keeps its first-person camera.
   */
  frame?(dt: number, alpha: number): boolean;
  /** The ability fields for a save snapshot while on foot (schema 2: player.abilityState). */
  saveState?(): AbilitySave | null;
}

/** 'enter' / 'exit' when a mode change crosses the ON_FOOT boundary, else null. */
export function onFootEdge(prev: Mode, next: Mode): 'enter' | 'exit' | null {
  if (prev === next) return null;
  if (next === 'ON_FOOT') return 'enter';
  if (prev === 'ON_FOOT') return 'exit';
  return null;
}

/** Holds the installed hooks and guarantees enter/step/exit ordering. */
export class OnFootHost {
  private hooks: OnFootHooks | null = null;
  private ctx: OnFootContext | null = null;

  /** True between enter and exit. */
  get active(): boolean {
    return this.ctx !== null;
  }

  /** Install (or remove with null) the hooks; while on foot the old ones exit and the new ones enter. */
  install(hooks: OnFootHooks | null): void {
    if (this.ctx) this.hooks?.exit('replaced');
    this.hooks = hooks;
    if (this.ctx) this.hooks?.enter(this.ctx);
  }

  /** Report a mode change; ctx is required when entering ON_FOOT. */
  transition(prev: Mode, next: Mode, ctx: OnFootContext | null, reason: OnFootExitReason): void {
    const edge = onFootEdge(prev, next);
    if (edge === 'enter') {
      if (!ctx) throw new Error('Entering ON_FOOT needs a context');
      if (this.ctx) this.hooks?.exit('relocate');
      this.ctx = ctx;
      this.hooks?.enter(ctx);
    } else if (edge === 'exit' && this.ctx) {
      this.ctx = null;
      this.hooks?.exit(reason);
    }
  }

  /** Per fixed step while on foot; true when an ability owned the character's motion. */
  step(dt: number, input: WalkInput): boolean {
    if (!this.ctx || !this.hooks) return false;
    return this.hooks.step(dt, input) === true;
  }

  /** Per rendered frame while on foot; true when the hooks placed the camera. */
  frame(dt: number, alpha: number): boolean {
    if (!this.ctx || !this.hooks?.frame) return false;
    return this.hooks.frame(dt, alpha) === true;
  }

  /** The hooks' ability fields for a save while on foot; null otherwise or when they keep none. */
  saveState(): AbilitySave | null {
    if (!this.ctx || !this.hooks?.saveState) return null;
    return this.hooks.saveState() ?? null;
  }
}
