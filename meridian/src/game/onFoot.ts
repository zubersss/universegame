// ON_FOOT hook points for the ability system (charter section I: AbilityState
// lives inside ON_FOOT). PLAYER implements OnFootHooks and installs it with
// game.onFoot.install() from src/player/install.ts; Game routes every mode
// change through setMode(), so enter/exit always pair and step/frame only run
// in between. Mode stays unchanged.

import type { BodyId } from '../world/bodies';
import type { Mode } from './Game';

/** Why the character left ON_FOOT. Powers deactivate on 'board'; the others re-place the character. */
export type OnFootExitReason = 'board' | 'restore' | 'relocate' | 'replaced';

export interface OnFootContext {
  body: BodyId;
}

export interface OnFootHooks {
  /** The character has just been placed outside the ship (or restored on foot). */
  enter(ctx: OnFootContext): void;
  /**
   * One fixed step (SIM_DT) while ON_FOOT and playing, before the walk controller.
   * Return true when an active ability moved the character this step: the walk
   * controller is then skipped, so the character has exactly one position owner.
   */
  step(dt: number): boolean;
  /** The character is leaving ON_FOOT. */
  exit(reason: OnFootExitReason): void;
  /**
   * Once per rendered frame while on foot (also paused or loading), with the
   * interpolation alpha. Return true when the hooks placed the camera (character
   * camera); otherwise Game keeps its first-person camera.
   */
  frame?(dt: number, alpha: number): boolean;
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
  step(dt: number): boolean {
    if (!this.ctx || !this.hooks) return false;
    return this.hooks.step(dt) === true;
  }

  /** Per rendered frame while on foot; true when the hooks placed the camera. */
  frame(dt: number, alpha: number): boolean {
    if (!this.ctx || !this.hooks?.frame) return false;
    return this.hooks.frame(dt, alpha) === true;
  }
}
