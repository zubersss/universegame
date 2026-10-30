import type { OnFootContext, OnFootExitReason } from '../game/onFoot';
import type { AbilitySlot, WarningSeverity } from '../ui/Hud';
import { abilityFor, isAbilityId } from './catalog';
import { isAbilityState, transitionBlocked, type AbilityConfig, type AbilityId, type AbilityState, type BodyPower, type Primitive, type TransitionContext } from './types';

/** The two HUD slot calls the controller makes (LEAD's HUD slot API). */
export interface AbilityHud {
  setAbility(slot: AbilitySlot | null): void;
  setWarning(text: string | null, severity?: WarningSeverity): void;
}

/** Ability fields of the schema-2 save (player.abilityState and unlocked). */
export interface AbilitySave {
  abilityState: AbilityState;
  unlocked: AbilityId[];
}

/**
 * Validate the ability fields of a save record. Unknown power ids are
 * dropped; a missing or invalid state reads as walking. A save never resumes
 * a power mid-use: a character restored in flight is restored walking at the
 * saved (ground-snapped) spot, which is the safe reading of "flight never
 * ends mid-air" for a reload.
 */
export function readAbilitySave(raw: unknown): AbilitySave {
  const r = (raw ?? {}) as { abilityState?: unknown; unlocked?: unknown };
  const unlocked = Array.isArray(r.unlocked) ? [...new Set(r.unlocked.filter(isAbilityId))] : [];
  return { abilityState: isAbilityState(r.abilityState) ? r.abilityState : 'walk', unlocked };
}

/**
 * Owns AbilityState inside ON_FOOT. The power on the current body comes from
 * its BodyDef.power; it is usable only there, only once unlocked. Primitives
 * plug in as they are built (charter M2: flight, speed, blink; M3: drift);
 * until then the controller keeps the character walking and Game's walk
 * controller moves it.
 */
export class AbilityController {
  state: AbilityState = 'walk';
  /** Power on the current body (null: walking only). */
  power: AbilityConfig | null = null;
  bodyId: string | null = null;
  readonly unlocked = new Set<AbilityId>();
  /** Why the last transition request was refused (HUD feedback, tests). */
  lastRefusal: string | null = null;
  /** Transitions taken, for diagnostics: "from>to". */
  readonly log: string[] = [];
  /** Primitives that have a working implementation. */
  private readonly built = new Set<Primitive>();

  constructor(
    private readonly hud: AbilityHud,
    private readonly powerOf: (bodyId: string) => BodyPower,
  ) {}

  /** ON_FOOT entered: the character exists and is placed. */
  enter(ctx: OnFootContext): void {
    this.bodyId = ctx.body;
    this.power = abilityFor(this.powerOf(ctx.body));
    this.state = 'walk';
    this.lastRefusal = null;
    this.showHud();
  }

  /**
   * One fixed step. Returns true when an active power moved the character
   * (Game's walk step is then skipped); false keeps walking.
   */
  step(_dt: number): boolean {
    return this.state !== 'walk';
  }

  /** Ask for a state change under the charter J rules. */
  request(to: AbilityState, c: TransitionContext): boolean {
    const why = to !== 'walk' && !this.built.has(to) ? 'not built yet' : transitionBlocked(this.state, to, c);
    if (why) {
      this.lastRefusal = why;
      return false;
    }
    if (to !== this.state) this.log.push(`${this.state}>${to}`);
    this.state = to;
    this.lastRefusal = null;
    this.showHud();
    return true;
  }

  /** ON_FOOT is ending: powers deactivate (boarding) or the character is re-placed. */
  exit(_reason: OnFootExitReason): void {
    if (this.state !== 'walk') this.log.push(`${this.state}>walk`);
    this.state = 'walk';
    this.power = null;
    this.bodyId = null;
  }

  /** Arriving at a destination unlocks its power (journal, L9). */
  unlock(id: AbilityId): void {
    this.unlocked.add(id);
    this.showHud();
  }

  snapshot(): AbilitySave {
    return { abilityState: this.state, unlocked: [...this.unlocked].sort() };
  }

  restore(raw: unknown): void {
    const s = readAbilitySave(raw);
    this.unlocked.clear();
    for (const id of s.unlocked) this.unlocked.add(id);
    // Powers are never resumed mid-use (see readAbilitySave).
    this.state = 'walk';
  }

  /** Ability slot: shown only where a power exists and is unlocked. */
  private showHud(): void {
    const p = this.power;
    if (!p || !this.unlocked.has(p.id) || !this.built.has(p.primitive)) {
      this.hud.setAbility(null);
      return;
    }
    this.hud.setAbility({ name: p.name, state: this.state, charge: 1, cooldown: 0, hint: p.feedback.hint });
  }
}
