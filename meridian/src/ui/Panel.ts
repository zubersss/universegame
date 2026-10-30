import { BODIES, type BodyDef, type BodyId } from '../world/bodies';

// Navigation / journal / survey panel (Tab). The simulation is paused while it
// is open; buttons are ordinary focusable DOM buttons. Digits 1–9 and 0 pick
// the first ten navigation rows (the bodies in play; belts are not targets).

export type PanelTab = 'nav' | 'journal' | 'inventory';

export interface NavRow {
  id: BodyId;
  /** Distance from the ship to the body's surface (m). */
  distance: number;
  /** Short status text, e.g. "Survey pending" or "Relay active". */
  status: string;
}

export interface PanelView {
  rows: NavRow[];
  target: BodyId | null;
  /** Body the ship is at or nearest to. */
  here: BodyId;
}

const $ = (id: string): HTMLElement => {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing element #${id}`);
  return el;
};

/** Navigation row picked by a key code: Digit1–Digit9 are rows 0–8, Digit0 is row 9; null for any other key. */
export function navKeyIndex(code: string): number | null {
  const m = /^Digit([0-9])$/.exec(code);
  if (!m) return null;
  const d = Number(m[1]);
  return d === 0 ? 9 : d - 1;
}

/** The digit that picks navigation row `i` ('1'–'9', then '0'), or null past the tenth row. */
export function navKeyLabel(i: number): string | null {
  return i >= 0 && i < 9 ? String(i + 1) : i === 9 ? '0' : null;
}

/** Row kind label: Star, Planet or Moon. */
export function kindLabel(def: BodyDef): string {
  return def.kind === 'star' ? 'Star' : def.kind === 'moon' ? 'Moon' : 'Planet';
}

function fmt(d: number): string {
  if (d >= 100000) return `${(d / 1000).toFixed(0)} km`;
  if (d >= 1000) return `${(d / 1000).toFixed(1)} km`;
  return `${Math.max(0, d).toFixed(0)} m`;
}

export class Panel {
  private readonly root = $('panel-nav');
  private tab: PanelTab = 'nav';
  open = false;
  onSetCourse: ((id: BodyId | null) => void) | null = null;
  onClose: (() => void) | null = null;
  /** Supplies fresh data whenever the panel renders. */
  view: (() => PanelView) | null = null;
  /** Renders the journal/survey tabs (filled in by the exploration layer). */
  renderJournal: ((el: HTMLElement) => void) | null = null;
  renderSurvey: ((el: HTMLElement) => void) | null = null;

  constructor() {
    for (const b of Array.from(this.root.querySelectorAll<HTMLButtonElement>('.tab'))) {
      b.addEventListener('click', (e) => {
        e.preventDefault();
        this.select(b.dataset.tab as PanelTab);
      });
    }
    $('btn-panel-close').addEventListener('click', () => this.onClose?.());
    // Tab (open/close) is handled by the game input; digits pick a destination row.
    document.addEventListener('keydown', (e) => {
      if (!this.open || this.tab !== 'nav') return;
      const i = navKeyIndex(e.code);
      const row = i === null ? undefined : this.view?.().rows[i];
      if (row) this.setCourse(row.id);
    });
  }

  show(tab?: PanelTab): void {
    this.open = true;
    if (tab) this.tab = tab;
    this.root.classList.remove('hidden');
    this.select(this.tab);
  }

  hide(): void {
    this.open = false;
    this.root.classList.add('hidden');
  }

  private select(tab: PanelTab): void {
    this.tab = tab;
    for (const b of Array.from(this.root.querySelectorAll<HTMLElement>('.tab'))) b.classList.toggle('active', b.dataset.tab === tab);
    for (const b of Array.from(this.root.querySelectorAll<HTMLElement>('.tab-body'))) b.classList.toggle('hidden', b.dataset.body !== tab);
    this.render();
  }

  private setCourse(id: BodyId): void {
    const v = this.view?.();
    this.onSetCourse?.(v && v.target === id ? null : id);
    this.render();
  }

  render(): void {
    if (this.tab === 'nav') this.renderNav();
    else if (this.tab === 'journal') this.renderJournal?.($('journal-list'));
    else this.renderSurvey?.($('survey-list'));
  }

  private renderNav(): void {
    const el = $('nav-list');
    const v = this.view?.();
    if (!v) return;
    const intro = document.createElement('div');
    intro.className = 'empty';
    const last = navKeyLabel(Math.min(v.rows.length, 10) - 1);
    intro.textContent = `Select a destination (1–${last}). The marker leads to it; once local it marks the landing site.`;
    const rows = v.rows.map((r, i) => {
      const def = BODIES[r.id];
      const b = document.createElement('button');
      b.className = `navrow${v.target === r.id ? ' selected' : ''}`;
      b.setAttribute('aria-pressed', String(v.target === r.id));
      const name = document.createElement('span');
      name.className = 'name';
      const key = navKeyLabel(i);
      name.textContent = `${key === null ? '' : `${key}  `}${def.name}${r.id === v.here ? ' · here' : ''}`;
      const meta = document.createElement('span');
      meta.className = 'meta';
      meta.textContent = `${kindLabel(def)} · ${r.status}`;
      const d = document.createElement('span');
      d.className = 'd';
      d.textContent = v.target === r.id ? `● ${fmt(r.distance)}` : fmt(r.distance);
      b.append(name, meta, d);
      b.title = def.description;
      b.addEventListener('click', (e) => {
        e.preventDefault();
        this.setCourse(r.id);
      });
      return b;
    });
    el.replaceChildren(intro, ...rows);
  }
}
