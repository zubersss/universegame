import { Vector3 } from 'three';
import type { OnFootContext, OnFootExitReason } from '../game/onFoot';
import type { AbilitySlot, WarningSeverity } from '../ui/Hud';
import { abilityFor, primitivesOf } from './catalog';
import { createPower, FlightPower, SpeedPower, type Power, type PowerWorld } from './powers';
import type { PowerMotion } from '../avatar/AvatarAnimator';
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

const _feet = new Vector3();

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
  private readonly built = new Set<Primitive>(['flight', 'speed', 'blink']);
  /** The power's runtime on this body (null: walking only). */
  runtime: Power | null = null;
  /** A reloaded power waits for the first step with a world to resume. */
  private resumePending = false;
  private shownRefusal: string | null = null;

  constructor(
    private readonly hud: AbilityHud,
    private readonly powerOf: (bodyId: string) => BodyPower,
    private readonly clock: () => number = () => 0,
  ) {}

  /** ON_FOOT entered: the character exists and is placed. Activates exactly the given power (else the body's). */
  enter(ctx: AbilityEnterContext): void {
    this.bodyId = ctx.body;
    this.power = abilityFor(ctx.power !== undefined ? ctx.power : this.powerOf(ctx.body));
    const saved = ctx.restored ? this.restore(ctx.restored) : 'walk';
    // Game passes a power only once its destination unlocked it.
    if (ctx.power !== undefined && this.power) this.unlocked.add(this.power.id);
    this.runtime = this.power ? createPower(this.power) : null;
    this.state = 'walk';
    this.resumePending = false;
    // A reload resumes the saved power where it has a rule for it (LEAD M2
    // plan C): flight hovers where it was saved (it never ends mid-air),
    // superspeed resumes braking. The first step with a world starts it.
    if (saved !== 'walk' && this.usable && this.runtime!.primitive === saved && this.runtime!.resume) {
      this.state = saved;
      this.resumePending = true;
    }
    this.lastRefusal = null;
    this.showHud();
  }

  /** The power can be used here now (exists, built, unlocked). */
  get usable(): boolean {
    const p = this.power;
    return !!p && !!this.runtime && this.built.has(p.primitive) && this.unlocked.has(p.id);
  }

  /**
   * One fixed step with the game's view (null in headless tests: walking
   * only). Returns true when an active power moved the character (Game's
   * walk step is then skipped); false keeps walking.
   */
  step(dt: number, w: PowerWorld | null = null): boolean {
    const rt = this.runtime;
    if (!rt || !w) return this.state !== 'walk';
    if (this.resumePending) {
      this.resumePending = false;
      rt.resume!(w);
    }
    rt.tick(dt, this.usable ? w : null);
    if (this.state === 'walk') {
      if (!this.usable || !rt.wants(dt, w)) {
        this.showHud();
        return false;
      }
      if (!this.request(rt.primitive, this.context(w))) {
        this.showHud();
        return false;
      }
      rt.start(w);
    }
    if (rt.step(dt, w) === 'done') this.request('walk', this.context(w));
    this.showHud();
    return true;
  }

  /** Facts for the transition rules. A flier below the landing height counts as down (its landing flare). */
  private context(w: PowerWorld): TransitionContext {
    const pl = w.player;
    const p = this.power;
    let grounded = pl.grounded;
    if (!grounded && this.state === 'flight' && p && p.primitive === 'flight') {
      const g = pl.groundAt(pl.feet(_feet), 0.5, p.params.landHeight + 0.5);
      grounded = !!g && -g.h <= p.params.landHeight + 0.1;
    }
    return { grounded, speed: pl.vel.length(), primitivesHere: primitivesOf(p), unlocked: !!p && this.unlocked.has(p.id), inZone: false };
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
    this.resumePending = false;
    this.power = null;
    this.runtime = null;
    this.bodyId = null;
    if (this.shownRefusal !== null) {
      this.hud.setWarning(null);
      this.shownRefusal = null;
    }
  }

  /** Arriving at a destination unlocks its power (journal, L9). */
  unlock(id: AbilityId): void {
    this.unlocked.add(id);
    this.showHud();
  }

  snapshot(): AbilitySave {
    return { abilityState: this.state, unlocked: [...this.unlocked].sort() };
  }

  /** How a power is moving the body (avatar pose, camera), or null when walking. */
  motion(): PowerMotion | null {
    const rt = this.runtime;
    if (!rt || this.state === 'walk') return null;
    if (rt instanceof FlightPower) return { mode: 'flight', speed: rt.flight.vel.length() };
    if (rt instanceof SpeedPower) return { mode: 'dash', speed: rt.speed.speed };
    return null;
  }

  /** The readout for tests (LEAD's M2 journeys) and diagnostics. */
  view(): AbilityView {
    const r = this.runtime?.readout();
    const blink = this.runtime && this.runtime.primitive === 'blink' ? (this.runtime as Power & { aiming: boolean; target: { ok: boolean; reason: string | null } }) : null;
    return {
      id: this.power?.id ?? null,
      state: this.state,
      active: this.state !== 'walk',
      charge: r ? r.charge : 1,
      cooldown: r ? r.cooldown : 0,
      preview: blink && blink.aiming ? { ok: blink.target.ok, reason: blink.target.reason } : null,
    };
  }

  /** State changes so far (the log is bounded; this counts all). */
  changes = 0;

  private note(from: AbilityState, to: AbilityState): void {
    this.changes++;
    this.log.push({ t: this.clock(), from, to });
    if (this.log.length > LOG_MAX) this.log.splice(0, this.log.length - LOG_MAX);
  }

  /** Restore the unlocked powers; returns the saved state, which enter() resumes where a rule allows (the character walks until then). */
  restore(raw: unknown): AbilityState {
    const s = readAbilitySave(raw);
    this.unlocked.clear();
    for (const id of s.unlocked) this.unlocked.add(id);
    this.state = 'walk';
    this.resumePending = false;
    return s.abilityState;
  }

  /** Ability slot: shown only where a power exists, is built and unlocked; refusals as a caution line. */
  private showHud(): void {
    const p = this.power;
    if (!p || !this.usable) {
      this.hud.setAbility(null);
      return;
    }
    const r = this.runtime!.readout();
    this.hud.setAbility({ name: p.name, state: this.state === 'walk' ? r.status : `${this.state} · ${r.status}`, charge: r.charge, cooldown: r.cooldown, hint: r.hint });
    const refusal = this.runtime!.refusal;
    if (refusal !== this.shownRefusal) {
      this.hud.setWarning(refusal ? `${p.name}: ${refusal}` : null, 'caution');
      this.shownRefusal = refusal;
    }
  }
}
