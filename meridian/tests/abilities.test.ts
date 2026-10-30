import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { ABILITIES, abilityFor, bodyPower, isAbilityId, primitivesOf } from '../src/abilities/catalog';
import { ABILITY_STATES, PRIMITIVES, SPEED_EXIT_MAX, transitionBlocked, type AbilityState, type Primitive, type TransitionContext } from '../src/abilities/types';
import { AbilityController, type AbilityHud } from '../src/abilities/AbilityController';
import { readAbilitySave, validateAbilityFields } from '../src/abilities/save';
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
  it('walks where there is no power; a built power needs unlocking and shows in the slot once unlocked', () => {
    const hud = fakeHud();
    const c = new AbilityController(hud, (id) => (id === 'ilex' ? 'walk' : 'redline'));
    c.enter({ body: 'ilex' });
    expect(c.state).toBe('walk');
    expect(c.power).toBeNull();
    expect(c.runtime).toBeNull();
    expect(hud.calls.at(-1)).toBeNull();
    expect(c.step(1 / 60)).toBe(false);
    c.exit('board');
    c.enter({ body: 'mars' });
    expect(c.power?.id).toBe('redline');
    expect(c.runtime?.primitive).toBe('speed');
    // Locked: the slot stays hidden and the rules refuse.
    expect(c.usable).toBe(false);
    expect(hud.calls.at(-1)).toBeNull();
    expect(c.request('speed', { ...CTX, primitivesHere: ['speed'], unlocked: false })).toBe(false);
    expect(c.lastRefusal).toMatch(/unlocked/);
    c.unlock('redline');
    expect(c.usable).toBe(true);
    expect(hud.calls.at(-1)).toMatchObject({ name: 'Redline' });
    // Game passing the power means its destination unlocked it.
    const d = new AbilityController(fakeHud(), () => 'walk');
    d.enter({ body: 'moon', power: 'lunar-step' });
    expect(d.usable).toBe(true);
    // Drift is not built yet: no placeholder (charter B.7).
    const e = new AbilityController(fakeHud(), () => 'storm-lift');
    e.enter({ body: 'jupiter', power: 'storm-lift' });
    expect(e.runtime).toBeNull();
    expect(e.usable).toBe(false);
    expect(e.request('drift', { ...CTX, primitivesHere: ['drift'], unlocked: true, inZone: true })).toBe(false);
    expect(e.lastRefusal).toMatch(/not built/);
  });

  it('pairs with the ON_FOOT host: enter, steps, exit on boarding', () => {
    const hud = fakeHud();
    const c = new AbilityController(hud, () => 'walk');
    const host = new OnFootHost();
    host.install({ enter: (ctx) => c.enter(ctx), step: (dt) => c.step(dt), exit: (r) => c.exit(r) });
    host.transition('LANDED', 'ON_FOOT', { body: 'cairn' }, 'relocate');
    expect(c.bodyId).toBe('cairn');
    expect(host.step(1 / 60, { forward: 0, right: 0, sprint: false, jump: false, yaw: 0, pitch: 0 })).toBe(false); // walking: Game's walk controller keeps the character
    host.transition('ON_FOOT', 'LANDED', null, 'board');
    expect(c.bodyId).toBeNull();
    expect(c.state).toBe('walk');
  });

  it('saves and restores unlocked powers; restoring alone keeps walking; junk is dropped', () => {
    const c = new AbilityController(fakeHud(), () => 'walk');
    c.unlock('lunar-step');
    c.unlock('redline');
    const snap = c.snapshot();
    expect(snap).toEqual({ abilityState: 'walk', unlocked: ['lunar-step', 'redline'] });
    const d = new AbilityController(fakeHud(), () => 'walk');
    // The saved state is returned for enter() to resume; nothing resumes without a body and power.
    expect(d.restore(JSON.parse(JSON.stringify({ ...snap, abilityState: 'flight' })))).toBe('flight');
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

describe('save module and LEAD hook points (L8/L9)', () => {
  it('keeps the save shape, ids and validator free of Three.js (SaveSystem imports them in Node)', () => {
    for (const f of ['src/abilities/save.ts', 'src/abilities/catalog.ts', 'src/abilities/types.ts']) {
      const src = readFileSync(f, 'utf8');
      expect(src, f).not.toMatch(/from 'three'/);
      // Only these three modules in the chain.
      for (const m of src.matchAll(/from '([^']+)'/g)) expect(['./catalog', './types'], `${f} imports ${m[1]}`).toContain(m[1]);
    }
  });

  it('activates exactly the power Game passes, restores unlocks, logs state changes with time', () => {
    let t = 0;
    const hud = fakeHud();
    const c = new AbilityController(hud, () => 'walk', () => t);
    c.enter({ body: 'mars', power: 'redline', restored: { abilityState: 'speed', unlocked: ['redline'] } });
    expect(c.power?.id).toBe('redline');
    expect([...c.unlocked]).toEqual(['redline']);
    expect(c.state).toBe('speed'); // resumes braking (powers.test steps it)
    expect(c.view()).toEqual({ id: 'redline', state: 'speed', active: true, charge: 1, cooldown: 0, preview: null });
    expect(c.log).toEqual([]); // a reload is not a state change
    // power: null means none here, whatever the body says.
    c.enter({ body: 'mars', power: null });
    expect(c.power).toBeNull();
    // The log is bounded and time-stamped.
    for (let i = 0; i < 100; i++) {
      t = i;
      (c as unknown as { note(f: string, to: string): void }).note('walk', 'speed');
    }
    expect(c.log.length).toBe(64);
    expect(c.log[0].t).toBe(36);
    expect(c.log.at(-1)).toEqual({ t: 99, from: 'walk', to: 'speed' });
  });

  it('resumes a reloaded power only where it has a rule and is usable here (LEAD plan C)', () => {
    const cases: [string, string | null, AbilityState, string[], AbilityState][] = [
      ['earth', 'skyborne-flight', 'flight', ['skyborne-flight'], 'flight'], // hovers where saved
      ['mars', 'redline', 'speed', ['redline'], 'speed'], // resumes braking
      ['moon', 'lunar-step', 'blink', ['lunar-step'], 'walk'], // a blink is instant: nothing to resume
      ['earth', 'skyborne-flight', 'speed', ['skyborne-flight'], 'walk'], // not this body's primitive
      ['mars', null, 'speed', ['redline'], 'walk'], // no power here
      ['jupiter', 'storm-lift', 'drift', ['storm-lift'], 'walk'], // drift is not built yet
    ];
    for (const [body, power, saved, unlocked, expected] of cases) {
      const c = new AbilityController(fakeHud(), () => 'walk');
      c.enter({ body, power: power as never, restored: { abilityState: saved, unlocked: unlocked as never } });
      expect(c.state, `${body} ${saved}`).toBe(expected);
      expect(c.snapshot().abilityState).toBe(expected); // saving again before the first step keeps it
      // Boarding (or any exit) drops a pending resume.
      c.exit('board');
      expect(c.state).toBe('walk');
    }
    // A power the save does not list as unlocked never resumes (no ctx.power: the body's own, locked).
    const locked = new AbilityController(fakeHud(), () => 'skyborne-flight');
    locked.enter({ body: 'earth', restored: { abilityState: 'flight', unlocked: [] } });
    expect(locked.state).toBe('walk');
    // Without a world (headless), a resumed power holds the character in place (step returns true).
    const held = new AbilityController(fakeHud(), () => 'walk');
    held.enter({ body: 'earth', power: 'skyborne-flight', restored: { abilityState: 'flight', unlocked: ['skyborne-flight'] } });
    expect(held.step(1 / 60, null)).toBe(true);
  });
});
