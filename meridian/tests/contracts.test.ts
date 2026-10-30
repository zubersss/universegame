import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { OnFootHost, onFootEdge, type OnFootHooks } from '../src/game/onFoot';
import type { Mode } from '../src/game/Game';
import { abilityView, pickWarning } from '../src/ui/Hud';
import { Input } from '../src/core/input';
import type { WalkInput } from '../src/player/Player';

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
