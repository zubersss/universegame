import type { OnFootContext, OnFootExitReason } from '../game/onFoot';
import type { AbilitySlot, WarningSeverity } from '../ui/Hud';
import { abilityFor } from './catalog';
import { readAbilitySave, type AbilitySave } from './save';
import { transitionBlocked, type AbilityConfig, type AbilityId, type AbilityState, type BodyPower, type Primitive, type TransitionContext } from './types';

/**
 * What enter() receives: Game's ON_FOOT context, optionally with the power
 * to activate (BodyDef.power of the body or zone) and a restored ability
 * save (LEAD L8/L9 plan; both optional until Game passes them).
 */
export type AbilityEnterContext = OnFootContext & { power?: AbilityId | 'walk' | null; restored?: AbilitySave | null };

/** One logged state change (simulation time, from, to). */
export interface AbilityLogEntry {
  t: number;
  from: AbilityState;
  to: AbilityState;
}

/** The ability readout for tests and diagnostics. */
export interface AbilityView {
  id: AbilityId | null;
  state: AbilityState;
  active: boolean;
  charge: number;
  cooldown: number;
  preview: { ok: boolean; reason: string | null } | null;
}

/** How many state changes the log keeps. */
const LOG_MAX = 64;

/** The two HUD slot calls the controller makes (LEAD's HUD slot API). */
export interface AbilityHud {
  setAbility(slot: AbilitySlot | null): void;
  setWarning(text: string | null, severity?: WarningSeverity): void;
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
  /** The last state changes, oldest first (bounded). */
  readonly log: AbilityLogEntry[] = [];
  /** Primitives that have a working implementation. */
  private readonly built = new Set<Primitive>();

  constructor(
    private readonly hud: AbilityHud,
    private readonly powerOf: (bodyId: string) => BodyPower,
    private readonly clock: () => number = () => 0,
  ) {}

  /** ON_FOOT entered: the character exists and is placed. Activates exactly the given power (else the body's). */
  enter(ctx: AbilityEnterContext): void {
    this.bodyId = ctx.body;
    this.power = abilityFor(ctx.power !== undefined ? ctx.power : this.powerOf(ctx.body));
    if (ctx.restored) this.restore(ctx.restored);
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
    if (to !== this.state) this.note(this.state, to);
    this.state = to;
    this.lastRefusal = null;
    this.showHud();
    return true;
  }

  /** ON_FOOT is ending: powers deactivate (boarding) or the character is re-placed. */
  exit(_reason: OnFootExitReason): void {
    if (this.state !== 'walk') this.note(this.state, 'walk');
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

  /** The readout for tests (LEAD's M2 journeys) and diagnostics. */
  view(): AbilityView {
    return { id: this.power?.id ?? null, state: this.state, active: this.state !== 'walk', charge: 1, cooldown: 0, preview: null };
  }

  private note(from: AbilityState, to: AbilityState): void {
    this.log.push({ t: this.clock(), from, to });
    if (this.log.length > LOG_MAX) this.log.splice(0, this.log.length - LOG_MAX);
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
