// LEAD IFACE G: the journal pages follow the play set. Quiet System: species
// per world and the relay survey as before. Sol: the First Light survey bodies
// (Earth, Moon, Mars) with their route waypoints and landmarks.
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { SOL_M2_BODIES, SYSTEM_BODY_IDS, setPlaySystem } from '../src/world/bodies';
import { Expedition, newExpedition, type ExpeditionState } from '../src/game/Expedition';
import { journalBodies, renderJournal, renderSurvey } from '../src/ui/Journal';

/** Just enough DOM for the journal: elements with class, text and children. */
class FakeEl {
  className = '';
  textContent = '';
  children: FakeEl[] = [];
  constructor(readonly tag: string) {}
  append(...c: FakeEl[]): void {
    this.children.push(...c);
  }
  replaceChildren(...c: FakeEl[]): void {
    this.children = c;
  }
  /** Text of this element and its descendants, one line per element with text. */
  lines(): string[] {
    const own = this.textContent ? [this.textContent] : [];
    return [...own, ...this.children.flatMap((c) => c.lines())];
  }
}

beforeAll(() => {
  (globalThis as unknown as { document: unknown }).document = { createElement: (tag: string) => new FakeEl(tag) };
});
afterAll(() => {
  setPlaySystem(SYSTEM_BODY_IDS.quiet);
  delete (globalThis as unknown as { document?: unknown }).document;
});

function render(f: (root: HTMLElement) => void): string[] {
  const root = new FakeEl('div');
  f(root as unknown as HTMLElement);
  return root.lines();
}

describe('journal (G)', () => {
  it('lists the Quiet System worlds with species and the relay survey', () => {
    setPlaySystem(SYSTEM_BODY_IDS.quiet);
    expect(journalBodies()).toEqual(['ilex', 'vesper', 'cairn']);
    const j = render((r) => renderJournal(r, newExpedition()));
    expect(j[0]).toMatch(/^0 of \d+ species logged · 0 objects scanned\./);
    expect(j.filter((l) => l.startsWith('Route'))).toEqual([]);
    expect(j.some((l) => l.startsWith('Ilex'))).toBe(true);
    const e = new Expedition();
    const sv = render((r) => renderSurvey(r, e));
    expect(sv[0]).toMatch(/0 of 3 relays active/);
    expect(sv.filter((l) => l.endsWith(' relay'))).toEqual(['Ilex relay', 'Vesper relay', 'Cairn relay']);
  });

  it('lists Earth, the Moon and Mars with First Light routes and landmarks in Sol', () => {
    setPlaySystem(SOL_M2_BODIES);
    expect(journalBodies()).toEqual(['earth', 'moon', 'mars']);
    const s: ExpeditionState & { route: string[] } = { ...newExpedition(), scanned: ['earth:poi:0'], route: ['earth:route:0', 'moon:route:2'] };
    const j = render((r) => renderJournal(r, s));
    expect(j[0]).toMatch(/1 of 9 landmarks · 1 objects scanned/);
    // Route waypoints with their state, then the landmarks (named once scanned).
    const i = j.indexOf('Route 1 of 3 · Tasman coast at Hokitika');
    expect(i).toBeGreaterThan(0);
    expect(j[i + 1]).toBe('Reached');
    expect(j[j.indexOf('Route 2 of 3 · Franz Josef Glacier valley') + 1]).toBe('Ahead');
    expect(j[j.indexOf('Route 3 of 3 · North rim beacon') + 1]).toBe('Reached');
    const a = j.indexOf('Aoraki / Mount Cook');
    expect(j[a + 1]).toBe('Scanned');
    expect(j[a + 2]).toMatch(/highest mountain/);
    expect(j.filter((l) => l === 'Unscanned landmark').length).toBe(8);
    expect(j).not.toContain('Tranquility Base');
    // Survey tab: progress per survey body instead of relays.
    const e = new Expedition();
    e.reset(s);
    const sv = render((r) => renderSurvey(r, e));
    expect(sv[0]).toMatch(/^First Light survey/);
    expect(sv).toContain('Waypoints reached: 1 of 3 · landmarks scanned: 1 of 3');
    expect(sv.filter((l) => l.endsWith(' route'))).toEqual(['Earth route', 'Moon route', 'Mars route']);
    expect(sv.some((l) => /relay/.test(l))).toBe(false);
  });

  it('tolerates progress saved before route tracking existed', () => {
    setPlaySystem(SOL_M2_BODIES);
    const j = render((r) => renderJournal(r, newExpedition()));
    expect(j.filter((l) => l === 'Ahead').length).toBe(9);
  });
});
