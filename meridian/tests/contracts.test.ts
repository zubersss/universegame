import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { OnFootHost, onFootEdge, type OnFootContext, type OnFootHooks } from '../src/game/onFoot';
import type { Mode } from '../src/game/Game';
import { abilityView, pickWarning } from '../src/ui/Hud';
import { Input } from '../src/core/input';
import type { WalkInput } from '../src/player/Player';
import { Expedition } from '../src/game/Expedition';
import type { AbilitySave } from '../src/abilities/save';
import { AbilityController } from '../src/abilities/AbilityController';
import { bodyPower } from '../src/abilities/catalog';
import { BODIES } from '../src/world/bodies';

const IDLE: WalkInput = { forward: 0, right: 0, sprint: false, jump: false, yaw: 0, pitch: 0 };

const MODES: Mode[] = ['PILOTING', 'CRUISING', 'LANDED', 'ON_FOOT'];

/** Hooks that record every call; step returns `owns`. */
function recorder(owns = false): OnFootHooks & { log: string[] } {
  const log: string[] = [];
  return {
    log,
    enter: (ctx) => log.push(`enter:${ctx.body}`),
    step: (dt) => {
      log.push(`step:${dt}`);
      return owns;
    },
    exit: (reason) => log.push(`exit:${reason}`),
  };
}

describe('ON_FOOT hook points (Mode unchanged)', () => {
  it('fires enter/exit exactly on the ON_FOOT boundary', () => {
    for (const a of MODES) {
      for (const b of MODES) {
        const want = a === b ? null : b === 'ON_FOOT' ? 'enter' : a === 'ON_FOOT' ? 'exit' : null;
        expect(onFootEdge(a, b), `${a} -> ${b}`).toBe(want);
      }
    }
  });

  it('pairs enter and exit and steps only in between', () => {
    const host = new OnFootHost();
    const h = recorder();
    host.install(h);
    expect(host.step(1 / 60, IDLE)).toBe(false); // not on foot: no step
    host.transition('LANDED', 'ON_FOOT', { body: 'ilex' }, 'relocate');
    expect(host.active).toBe(true);
    host.step(1 / 60, IDLE);
    host.step(1 / 60, IDLE);
    host.transition('ON_FOOT', 'LANDED', null, 'board');
    host.step(1 / 60, IDLE);
    host.transition('LANDED', 'PILOTING', null, 'relocate');
    expect(h.log).toEqual(['enter:ilex', `step:${1 / 60}`, `step:${1 / 60}`, 'exit:board']);
    expect(host.active).toBe(false);
  });

  it('hands the step the walk input', () => {
    const host = new OnFootHost();
    const seen: WalkInput[] = [];
    host.install({ ...recorder(), step: (_dt, input) => (seen.push(input), false) });
    host.transition('LANDED', 'ON_FOOT', { body: 'ilex' }, 'relocate');
    const w = { ...IDLE, forward: 1, yaw: 0.2, jump: true };
    host.step(1 / 60, w);
    expect(seen).toEqual([w]);
  });

  it('lets an ability own the character only when its step says so', () => {
    const host = new OnFootHost();
    host.transition('LANDED', 'ON_FOOT', { body: 'cairn' }, 'relocate');
    expect(host.step(1 / 60, IDLE)).toBe(false); // no hooks installed: the walk controller runs
    host.install(recorder(true));
    expect(host.step(1 / 60, IDLE)).toBe(true);
    host.install(recorder(false));
    expect(host.step(1 / 60, IDLE)).toBe(false);
  });

  it('keeps ordering when hooks are swapped or the character is re-placed', () => {
    const host = new OnFootHost();
    const a = recorder();
    const b = recorder();
    host.transition('LANDED', 'ON_FOOT', { body: 'vesper' }, 'relocate');
    host.install(a); // installed while on foot: enters immediately
    host.install(b); // replaced: the old hooks exit, the new ones enter
    host.transition('ON_FOOT', 'LANDED', null, 'restore');
    expect(a.log).toEqual(['enter:vesper', 'exit:replaced']);
    expect(b.log).toEqual(['enter:vesper', 'exit:restore']);
    expect(() => host.transition('LANDED', 'ON_FOOT', null, 'relocate')).toThrow();
  });

  it('forwards frames only on foot and lets the hooks take the camera', () => {
    const host = new OnFootHost();
    let frames = 0;
    host.install({ ...recorder(), frame: () => (frames++, true) });
    expect(host.frame(1 / 60, 0.5)).toBe(false); // not on foot
    host.transition('LANDED', 'ON_FOOT', { body: 'ilex' }, 'relocate');
    expect(host.frame(1 / 60, 0.5)).toBe(true);
    host.install(recorder()); // hooks without frame(): Game keeps its camera
    expect(host.frame(1 / 60, 0.5)).toBe(false);
    host.transition('ON_FOOT', 'LANDED', null, 'board');
    expect(host.frame(1 / 60, 0.5)).toBe(false);
    expect(frames).toBe(1);
  });

  it('reads input before the hooks, never boards mid-air, and leaves the FOV to a hook camera', () => {
    const src = readFileSync(new URL('../src/game/Game.ts', import.meta.url), 'utf8');
    expect(src).toMatch(/const w = this\.state === 'playing' \? this\.readWalk\(\) : [^\n]+\n\s*if \(this\.onFoot\.step\(dt, w\)\)/);
    expect(src).toMatch(/if \(t\.kind === 'ship'\) \{[^}]*if \(this\.player\?\.grounded\) this\.boardShip\(\);/);
    expect(src).toMatch(/if \(!hookCamera\) this\.cameraRig\.updateFov\(/);
  });

  it('tracks C and mouse buttons as input codes while the pointer is locked', () => {
    // Node has no DOM: the key handler only needs HTMLElement for its text-field check.
    const g = globalThis as unknown as { HTMLElement?: unknown };
    g.HTMLElement ??= class {};
    const inp = new Input();
    // The DOM handlers are private; drive them directly with minimal event objects.
    const h = inp as unknown as Record<'onMouseDown' | 'onMouseUp' | 'onKeyDown', (e: unknown) => void>;
    inp.active = true;
    const ev = (button: number) => ({ button, preventDefault() {} });
    h.onMouseDown(ev(2)); // not locked: the click only requests the lock
    expect(inp.isDown('MouseRight')).toBe(false);
    inp.pointerLocked = true;
    h.onMouseDown(ev(2));
    h.onMouseDown(ev(0));
    expect(inp.isDown('MouseRight')).toBe(true);
    expect(inp.consume('MouseLeft')).toBe(true);
    expect(inp.consume('MouseLeft')).toBe(false);
    h.onMouseUp(ev(2));
    expect(inp.isDown('MouseRight')).toBe(false);
    h.onKeyDown({ code: 'KeyC', repeat: false, target: null, preventDefault() {} });
    expect(inp.consume('KeyC')).toBe(true);
  });

  it('gives PLAYER its extension point and test hooks', () => {
    const src = (f: string) => readFileSync(new URL(`../src/${f}`, import.meta.url), 'utf8');
    expect(src('game/boot.ts')).toMatch(/game = new Game\(render, settings\);\s*installPlayer\(game\);/);
    expect(src('game/Game.ts')).toMatch(/hookCamera = this\.onFoot\.frame\(dt, alpha\);\s*if \(!hookCamera\) this\.cameraRig\.firstPerson\(/);
    expect(src('debug/testHooks.ts')).toMatch(/player: playerTestHooks\(game\),/);
  });

  it('routes every Game mode change through setMode', () => {
    const src = readFileSync(new URL('../src/game/Game.ts', import.meta.url), 'utf8');
    const assigns = src.match(/this\.mode\s*=[^=]/g) ?? [];
    expect(assigns).toHaveLength(1);
    expect(src).toMatch(/private setMode\(next: Mode[^)]*\): void \{\s*const prev = this\.mode;\s*if \(prev === next\) return;\s*this\.mode = next;/);
    // Boarding reports the exit before the character is removed.
    expect(src).toMatch(/this\.setMode\('LANDED', 'board'\);\s*this\.player\.dispose\(\);/);
  });

  it('enters with the body power only once unlocked, and with the restored ability fields', () => {
    const exp = new Expedition();
    const host = new OnFootHost();
    const log: string[] = [];
    host.install({
      enter: (ctx) => log.push(`enter:${ctx.body}:${ctx.power}:${ctx.restored ? ctx.restored.abilityState : '-'}`),
      step: () => false,
      exit: (reason) => log.push(`exit:${reason}`),
    });
    // The context exactly as Game.setMode builds it (checked against its source below).
    const ctx = (body: string, restored: AbilitySave | null = null) => ({ body, power: exp.activePower(body), restored });
    host.transition('LANDED', 'ON_FOOT', ctx('moon'), 'relocate'); // not arrived: walking only
    host.transition('ON_FOOT', 'LANDED', null, 'board');
    exp.arrive('earth');
    host.transition('LANDED', 'ON_FOOT', ctx('moon'), 'relocate'); // Earth's unlock is not the Moon's power
    host.transition('ON_FOOT', 'LANDED', null, 'board');
    exp.arrive('moon');
    host.transition('LANDED', 'ON_FOOT', ctx('moon', { abilityState: 'blink', unlocked: [...exp.unlocked] }), 'relocate');
    expect(log).toEqual(['enter:moon:null:-', 'exit:board', 'enter:moon:null:-', 'exit:board', 'enter:moon:lunar-step:blink']);
    const ilex = new Expedition();
    ilex.arrive('ilex');
    expect(ilex.activePower('ilex')).toBeNull(); // Quiet bodies: walking only, as before

    const src = readFileSync(new URL('../src/game/Game.ts', import.meta.url), 'utf8');
    const setMode = src.slice(src.indexOf('private setMode('), src.indexOf('private fixedUpdate('));
    expect(setMode).toMatch(/const ctx = next === 'ON_FOOT' && id \? \{ body: id, power: this\.expedition\.activePower\(id\), restored \} : null;\s*this\.onFoot\.transition\(prev, next, ctx, reason\);/);
    // Only the restored placement passes saved ability fields.
    expect(src.match(/this\.setMode\('ON_FOOT'[^)]*\)/g)).toEqual(["this.setMode('ON_FOOT')", "this.setMode('ON_FOOT', 'relocate', restored)"]);
    expect(src).toMatch(/placeRestoredPlayer\(feet, new Vector3\(\.\.\.pl\.heading\), pl\.pitch, \{ abilityState: pl\.abilityState, unlocked: \[\.\.\.this\.expedition\.unlocked\] \}\)/);
  });

  it('fails closed: a context without a power reaches the hooks as null, never as the body\'s catalog power', () => {
    const host = new OnFootHost();
    const seen: OnFootContext[] = [];
    host.install({ ...recorder(), enter: (ctx) => seen.push(ctx) });
    host.transition('LANDED', 'ON_FOOT', { body: 'earth' }, 'relocate');
    expect(seen).toEqual([{ body: 'earth', power: null, restored: null }]);
    // PLAYER's controller reads an absent power as the body's own (IFACE pending);
    // through the host it gets null and stays walking until an arrival unlocks the power.
    expect(bodyPower(BODIES.earth)).toBe('skyborne-flight');
    const c = new AbilityController({ setAbility() {}, setWarning() {} }, (id) => bodyPower(BODIES[id]));
    host.install(c); // installed while on foot: enters with the host's context
    expect(c.power).toBeNull();
    host.transition('ON_FOOT', 'LANDED', null, 'board');
    host.transition('LANDED', 'ON_FOOT', { body: 'earth' }, 'relocate');
    expect(c.power).toBeNull();
    host.transition('ON_FOOT', 'LANDED', null, 'board');
    // The context Game builds activates exactly the unlocked power.
    const exp = new Expedition();
    host.transition('LANDED', 'ON_FOOT', { body: 'earth', power: exp.activePower('earth') }, 'relocate');
    expect(c.power).toBeNull();
    host.transition('ON_FOOT', 'LANDED', null, 'board');
    exp.arrive('earth');
    host.transition('LANDED', 'ON_FOOT', { body: 'earth', power: exp.activePower('earth') }, 'relocate');
    expect(c.power?.id).toBe('skyborne-flight');
  });

  it('asks the hooks for the ability state of a save only while on foot', () => {
    const host = new OnFootHost();
    const state: AbilitySave = { abilityState: 'flight', unlocked: ['skyborne-flight'] };
    host.install({ ...recorder(), saveState: () => state });
    expect(host.saveState()).toBeNull(); // not on foot
    host.transition('LANDED', 'ON_FOOT', { body: 'earth', power: 'skyborne-flight' }, 'relocate');
    expect(host.saveState()).toBe(state);
    host.install(recorder()); // hooks without saveState
    expect(host.saveState()).toBeNull();
    host.transition('ON_FOOT', 'LANDED', null, 'board');
    expect(host.saveState()).toBeNull();
    const src = readFileSync(new URL('../src/game/Game.ts', import.meta.url), 'utf8');
    const snapshot = src.slice(src.indexOf('  snapshot(): SaveData {'), src.indexOf('  restore(data: SaveData): void {'));
    expect(snapshot).toMatch(/const abilityState = this\.onFoot\.saveState\(\)\?\.abilityState \?\? 'walk';\s*player = \{[^}]*abilityState \};/);
    expect(snapshot).toMatch(/unlocked: \[\.\.\.e\.unlocked\],/);
  });

  it('records arrivals where the ship comes to rest, never inside setMode', () => {
    const src = readFileSync(new URL('../src/game/Game.ts', import.meta.url), 'utf8');
    const setMode = src.slice(src.indexOf('private setMode('), src.indexOf('private fixedUpdate('));
    expect(setMode).not.toMatch(/noteArrival|arrive\(/);
    expect(src).toMatch(/this\.counters\.landings\+\+;[^]*?this\.noteArrival\(def\);\s*this\.onNotice\?\.\('Landed'/);
    expect(src).toMatch(/placeShipLanded\(bodyId[^]*?this\.setMode\('LANDED'\);\s*this\.noteArrival\(def\);/);
    expect(src).toMatch(/this\.markSaved\(data\);[^]*?this\.noteArrival\(this\.body!\.def\);[^]*?this\.setState\('loading'\);/);
  });
});

describe('HUD slot API', () => {
  it('sanitizes ability readouts', () => {
    const base = { name: 'Lunar Step', state: 'blink', charge: 1, cooldown: 0, hint: 'Q commit' };
    expect(abilityView(base)).toEqual({ name: 'Lunar Step', state: 'blink', chargePct: 100, cooldownText: '', hint: 'Q commit', ready: true });
    expect(abilityView({ ...base, charge: NaN }).chargePct).toBe(0);
    expect(abilityView({ ...base, charge: 1.7 }).chargePct).toBe(100);
    expect(abilityView({ ...base, charge: 0.333 }).chargePct).toBe(33);
    expect(abilityView({ ...base, cooldown: 1.24 })).toMatchObject({ cooldownText: '1.2 s', ready: false });
    expect(abilityView({ ...base, cooldown: 12.6 }).cooldownText).toBe('13 s');
    expect(abilityView({ ...base, cooldown: -3 })).toMatchObject({ cooldownText: '', ready: true });
    expect(abilityView({ ...base, cooldown: Infinity })).toMatchObject({ cooldownText: '', ready: true });
    expect(abilityView({ ...base, charge: 0 }).ready).toBe(false);
  });

  it('shows the more severe warning, the game winning ties', () => {
    const game = { text: 'Slowing: Vesper ahead', severity: 'caution' as const };
    expect(pickWarning(null, null)).toBeNull();
    expect(pickWarning(game, null)).toBe(game);
    const heat = { text: 'Heat 80%', severity: 'danger' as const };
    expect(pickWarning(null, heat)).toBe(heat);
    expect(pickWarning(game, heat)).toBe(heat);
    expect(pickWarning(game, { text: 'Zone edge', severity: 'caution' })).toBe(game);
    expect(pickWarning(game, { text: 'Thermal', severity: 'info' })).toBe(game);
    const danger = { text: 'Too fast to land', severity: 'danger' as const };
    expect(pickWarning(danger, heat)).toBe(danger);
  });
});
