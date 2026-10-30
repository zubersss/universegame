import { describe, expect, it } from 'vitest';
import { ABILITIES, abilityFor, bodyPower, isAbilityId, primitivesOf } from '../src/abilities/catalog';
import { ABILITY_STATES, PRIMITIVES, SPEED_EXIT_MAX, transitionBlocked, type AbilityState, type Primitive, type TransitionContext } from '../src/abilities/types';
import { AbilityController, readAbilitySave, validateAbilityFields, type AbilityHud } from '../src/abilities/AbilityController';
import { OnFootHost } from '../src/game/onFoot';
import type { AbilitySlot } from '../src/ui/Hud';

function fakeHud() {
  const calls: (AbilitySlot | null)[] = [];
  const hud: AbilityHud & { calls: typeof calls } = {
    calls,
    setAbility: (s) => calls.push(s),
    setWarning: () => {},
  };
  return hud;
}

const CTX: TransitionContext = { grounded: true, speed: 0, primitivesHere: [], unlocked: false, inZone: false };

describe('ability contracts', () => {
  it('has exactly walk plus the four primitives', () => {
    expect([...ABILITY_STATES].sort()).toEqual(['blink', 'drift', 'flight', 'speed', 'walk']);
    expect(PRIMITIVES.length).toBe(4);
  });

  it('spells power ids as BodyDef.power does, and every power uses one of the four primitives', () => {
    // WORLDS' BodyDef.power values (IFACE W8).
    const worlds = ['skyborne-flight', 'lunar-step', 'redline', 'sunline-dash', 'pressure-glide', 'anchor-blink', 'wing-glide', 'storm-lift', 'ring-skate', 'cold-drift', 'gale-rider'];
    for (const id of worlds) expect(isAbilityId(id)).toBe(true);
    for (const [id, a] of Object.entries(ABILITIES)) {
      expect(a.id).toBe(id);
      expect(PRIMITIVES).toContain(a.primitive);
      expect(a.bodyIds.length).toBeGreaterThan(0);
      expect(a.controls.length).toBeGreaterThan(0);
      for (const v of Object.values(a.params)) expect(Number.isFinite(v)).toBe(true);
    }
    expect(isAbilityId('walk')).toBe(false);
    expect(isAbilityId('toString')).toBe(false);
  });

  it('starts the M2 powers from the charter K tunables', () => {
    const f = ABILITIES['skyborne-flight'];
    expect(f.primitive === 'flight' && f.params).toMatchObject({ accel: 25, cruise: 90, boost: 220, climb: 30, brake: 60, turn: 1.5, ceiling: 2000, takeoffHold: 0.6, landHeight: 1.5, landSpeed: 4 });
    const r = ABILITIES.redline;
    expect(r.primitive === 'speed' && r.params).toMatchObject({ accel: 40, top: 110, yawLow: 3, yawHigh: 0.8, maxSlopeDeg: 35, brake: 50, lookaheadTime: 2, lookaheadMargin: 50 });
    const b = ABILITIES['lunar-step'];
    expect(b.primitive === 'blink' && b.params).toMatchObject({ range: 60, cooldown: 1.2, groundWithin: 2, airborneWithin: 3 });
    expect(f.bodyIds).toEqual(['earth']);
    expect(r.bodyIds).toEqual(['mars']);
    expect(b.bodyIds).toEqual(['moon']);
  });

  it('lists every control a flight variant uses, and offers Terminator Step as flight plus blink', () => {
    for (const a of Object.values(ABILITIES)) {
      if (a.primitive !== 'flight') continue;
      const keys = a.controls.map((c) => c.keys).join(' | ');
      if (a.params.boost > a.params.cruise && a.params.flapImpulse === undefined) expect(keys, a.id).toMatch(/Shift/);
      if (a.params.flapImpulse === undefined) expect(keys, a.id).toMatch(/X/);
    }
    const t = ABILITIES['terminator-step'];
    expect(primitivesOf(t)).toEqual(['flight', 'blink']);
    const ctx: TransitionContext = { ...CTX, primitivesHere: primitivesOf(t), unlocked: true };
    expect(transitionBlocked('walk', 'blink', ctx)).toBeNull();
    expect(transitionBlocked('walk', 'flight', ctx)).toBeNull();
    expect(primitivesOf(null)).toEqual([]);
  });

  it('reads BodyDef.power when present and falls back to walking', () => {
    expect(bodyPower({ id: 'mars', power: 'redline' })).toBe('redline');
    expect(bodyPower({ id: 'sun', power: null })).toBeNull();
    expect(bodyPower({ id: 'ilex' })).toBe('walk');
    expect(bodyPower({ id: 'x', power: 'teleport-anywhere' })).toBe('walk');
    expect(abilityFor('walk')).toBeNull();
    expect(abilityFor(null)).toBeNull();
    expect(abilityFor('lunar-step')?.name).toBe('Lunar Step');
  });
});

describe('transition rules (charter J)', () => {
  const here = (p: Primitive, extra: Partial<TransitionContext> = {}): TransitionContext => ({ ...CTX, primitivesHere: [p], unlocked: true, ...extra });

  it('starts a power only from walking, only where it lives, only once unlocked', () => {
    expect(transitionBlocked('walk', 'flight', here('flight'))).toBeNull();
    expect(transitionBlocked('walk', 'flight', here('speed'))).toMatch(/not available/);
    expect(transitionBlocked('walk', 'flight', { ...here('flight'), unlocked: false })).toMatch(/unlocked/);
    expect(transitionBlocked('speed', 'flight', here('flight'))).toMatch(/one power/);
    expect(transitionBlocked('walk', 'speed', here('speed', { grounded: false }))).toMatch(/ground/);
    expect(transitionBlocked('walk', 'drift', here('drift'))).toMatch(/zone/);
    expect(transitionBlocked('walk', 'drift', here('drift', { inZone: true }))).toBeNull();
  });

  it('never ends flight mid-air, always brakes out of superspeed', () => {
    expect(transitionBlocked('flight', 'walk', { ...CTX, grounded: false })).toMatch(/mid-air/);
    expect(transitionBlocked('flight', 'walk', { ...CTX, grounded: true })).toBeNull();
    expect(transitionBlocked('speed', 'walk', { ...CTX, speed: 60 })).toMatch(/brake/);
    expect(transitionBlocked('speed', 'walk', { ...CTX, speed: SPEED_EXIT_MAX })).toBeNull();
    expect(transitionBlocked('blink', 'walk', { ...CTX, grounded: false })).toBeNull();
    expect(transitionBlocked('drift', 'walk', { ...CTX, grounded: false, inZone: true })).toMatch(/drifting/);
    // Leaving the zone in the air does not end drift: the boundary pushes back and recalls to the ship.
    expect(transitionBlocked('drift', 'walk', { ...CTX, grounded: false, inZone: false })).toMatch(/drifting/);
    expect(transitionBlocked('drift', 'walk', { ...CTX, grounded: true, inZone: true })).toBeNull();
    for (const s of ABILITY_STATES) expect(transitionBlocked(s, s, CTX)).toBeNull();
  });
});

describe('ability controller (walk only in M1)', () => {
  it('walks everywhere, hides the ability slot and refuses unbuilt powers', () => {
    const hud = fakeHud();
    const c = new AbilityController(hud, (id) => (id === 'ilex' ? 'walk' : 'redline'));
    c.enter({ body: 'ilex' });
    expect(c.state).toBe('walk');
    expect(c.power).toBeNull();
    expect(hud.calls.at(-1)).toBeNull();
    expect(c.step(1 / 60)).toBe(false);
    c.exit('board');
    c.enter({ body: 'vesper' as never });
    expect(c.power?.id).toBe('redline');
    c.unlock('redline');
    // No placeholder: the slot stays hidden and the power cannot start until speed is built.
    expect(hud.calls.at(-1)).toBeNull();
    expect(c.request('speed', { ...CTX, primitivesHere: ['speed'], unlocked: true })).toBe(false);
    expect(c.lastRefusal).toMatch(/not built/);
    expect(c.state).toBe('walk');
    expect(c.step(1 / 60)).toBe(false);
  });

  it('pairs with the ON_FOOT host: enter, steps, exit on boarding', () => {
    const hud = fakeHud();
    const c = new AbilityController(hud, () => 'walk');
    const host = new OnFootHost();
    host.install(c);
    host.transition('LANDED', 'ON_FOOT', { body: 'cairn' }, 'relocate');
    expect(c.bodyId).toBe('cairn');
    expect(host.step(1 / 60, { forward: 0, right: 0, sprint: false, jump: false, yaw: 0, pitch: 0 })).toBe(false); // walking: Game's walk controller keeps the character
    host.transition('ON_FOOT', 'LANDED', null, 'board');
    expect(c.bodyId).toBeNull();
    expect(c.state).toBe('walk');
  });

  it('saves and restores unlocked powers; never resumes a power mid-use', () => {
    const c = new AbilityController(fakeHud(), () => 'walk');
    c.unlock('lunar-step');
    c.unlock('redline');
    const snap = c.snapshot();
    expect(snap).toEqual({ abilityState: 'walk', unlocked: ['lunar-step', 'redline'] });
    const d = new AbilityController(fakeHud(), () => 'walk');
    d.restore(JSON.parse(JSON.stringify({ ...snap, abilityState: 'flight' })));
    expect(d.state).toBe('walk');
    expect([...d.unlocked].sort()).toEqual(['lunar-step', 'redline']);
    // Junk is dropped, not trusted.
    expect(readAbilitySave({ abilityState: 'teleport', unlocked: ['redline', 'redline', 'x', 7, null] })).toEqual({ abilityState: 'walk', unlocked: ['redline'] });
    expect(readAbilitySave(null)).toEqual({ abilityState: 'walk', unlocked: [] });
    // The strict validator for saves rejects malformed fields instead of coercing them.
    expect(validateAbilityFields('flight', ['redline'])).toEqual({ abilityState: 'flight', unlocked: ['redline'] });
    expect(validateAbilityFields(null, [])).toEqual({ abilityState: 'walk', unlocked: [] });
    for (const [st, un] of [['teleport', []], ['walk', {}], ['walk', 'redline'], ['walk', ['redline', 'redline']], ['walk', ['x']], ['walk', Array(13).fill('redline')], ['walk', undefined]] as [unknown, unknown][]) {
      expect(typeof validateAbilityFields(st, un)).toBe('string');
    }
    const states: AbilityState[] = ['walk', 'flight', 'speed', 'blink', 'drift'];
    for (const s of states) expect(readAbilitySave({ abilityState: s }).abilityState).toBe(s);
  });
});
