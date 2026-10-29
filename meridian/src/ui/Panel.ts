import { BODIES, BODY_IDS, type BodyId } from '../world/bodies';

// Navigation / journal / survey panel (Tab). The simulation is paused while it
// is open; buttons are ordinary focusable DOM buttons.

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
    // Tab (open/close) is handled by the game input; digits pick a destination.
    document.addEventListener('keydown', (e) => {
      if (!this.open) return;
      if (this.tab === 'nav' && /^Digit[1-9]$/.test(e.code)) {
        const id = BODY_IDS[Number(e.code.slice(5)) - 1];
        if (id) this.setCourse(id);
      }
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
    intro.textContent = `Select a destination (1–${BODY_IDS.length}). The marker leads to it; once local it marks the landing site.`;
    const rows = v.rows.map((r, i) => {
      const def = BODIES[r.id];
      const b = document.createElement('button');
      b.className = `navrow${v.target === r.id ? ' selected' : ''}`;
      b.setAttribute('aria-pressed', String(v.target === r.id));
      const name = document.createElement('span');
      name.className = 'name';
      name.textContent = `${i + 1}  ${def.name}${r.id === v.here ? ' · here' : ''}`;
      const meta = document.createElement('span');
      meta.className = 'meta';
      meta.textContent = `${def.kind === 'moon' ? 'Moon' : 'Planet'} · ${r.status}`;
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
