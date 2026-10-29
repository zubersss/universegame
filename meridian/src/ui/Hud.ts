// DOM HUD. Text nodes are only touched when their value changes.

const $ = (id: string): HTMLElement => {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing HUD element #${id}`);
  return el;
};

export interface FlightHudData {
  speed: number;
  throttle: number; // 0..1
  speedFraction: number; // speed / cap for the marker
  altitude: number;
  altitudeApprox: boolean; // true in space: planetary altitude
  verticalSpeed: number;
  boost: boolean;
  assist: boolean;
  cruise: boolean;
  gear: boolean;
}

export interface Prompt {
  key?: string;
  text: string;
  dim?: boolean;
}

export class Hud {
  private readonly cache = new Map<HTMLElement, string>();
  private readonly els = {
    body: $('hud-body'),
    mode: $('hud-mode'),
    objective: $('objective-text'),
    objectiveSub: $('objective-sub'),
    speed: $('i-speed'),
    throttle: $('i-throttle'),
    throttleBar: $('i-throttle-bar'),
    speedBar: $('i-speed-bar'),
    alt: $('i-alt'),
    altLabel: $('i-alt-label'),
    altUnit: $('i-alt-unit'),
    vs: $('i-vs'),
    tBoost: $('t-boost'),
    tAssist: $('t-assist'),
    tCruise: $('t-cruise'),
    tGear: $('t-gear'),
    flight: $('flight-panel'),
    walk: $('walk-panel'),
    wShip: $('w-ship'),
    wGrav: $('w-grav'),
    prompts: $('prompts'),
    warning: $('warning'),
    crosshair: $('crosshair'),
    stick: $('stick-reticle'),
    notices: $('notices'),
    save: $('save-indicator'),
    scanRing: $('scan-ring'),
    scanProgress: $('scan-progress'),
    scanLabel: $('scan-label'),
    inventory: $('inventory-mini'),
  };
  private promptKey = '';
  private saveTimer = 0;

  private set(el: HTMLElement, text: string): void {
    if (this.cache.get(el) !== text) {
      this.cache.set(el, text);
      el.textContent = text;
    }
  }

  private setStyle(el: HTMLElement, prop: 'width' | 'left' | 'transform' | 'strokeDashoffset', value: string): void {
    const key = `${prop}`;
    const ck = this.cache.get(el);
    const v = `${key}:${value}`;
    if (ck !== v) {
      this.cache.set(el, v);
      (el.style as unknown as Record<string, string>)[prop] = value;
    }
  }

  /** Instrument-panel copies of the location (shown instead of the top label on small screens). */
  private readonly panelLoc = Array.from(document.querySelectorAll<HTMLElement>('.panel-loc'));

  setLocation(body: string, mode: string): void {
    this.set(this.els.body, body);
    this.set(this.els.mode, mode);
    for (const el of this.panelLoc) this.set(el, `${body} · ${mode}`);
  }

  setObjective(text: string, sub: string): void {
    this.set(this.els.objective, text);
    this.set(this.els.objectiveSub, sub);
  }

  showFlight(show: boolean): void {
    this.els.flight.classList.toggle('hidden', !show);
    this.els.walk.classList.toggle('hidden', show);
    this.els.stick.classList.toggle('hidden', !show);
    this.els.crosshair.classList.toggle('walk', !show);
  }

  flight(d: FlightHudData): void {
    this.set(this.els.speed, d.speed >= 10000 ? `${(d.speed / 1000).toFixed(1)}k` : d.speed.toFixed(0));
    this.set(this.els.throttle, `${Math.round(d.throttle * 100)}%`);
    this.setStyle(this.els.throttleBar, 'width', `${(d.throttle * 100).toFixed(1)}%`);
    this.setStyle(this.els.speedBar, 'left', `${(Math.min(1, Math.max(0, d.speedFraction)) * 100).toFixed(1)}%`);
    if (d.altitudeApprox) {
      this.set(this.els.altLabel, 'ALT~');
      this.set(this.els.alt, (d.altitude / 1000).toFixed(d.altitude < 100000 ? 1 : 0));
      this.set(this.els.altUnit, 'km');
    } else {
      this.set(this.els.altLabel, 'AGL');
      this.set(this.els.alt, d.altitude >= 10000 ? (d.altitude / 1000).toFixed(1) : d.altitude.toFixed(0));
      this.set(this.els.altUnit, d.altitude >= 10000 ? 'km' : 'm');
    }
    this.set(this.els.vs, (d.verticalSpeed >= 0 ? '+' : '') + d.verticalSpeed.toFixed(Math.abs(d.verticalSpeed) < 10 ? 1 : 0));
    this.els.tBoost.classList.toggle('on', d.boost);
    this.els.tAssist.classList.toggle('on', d.assist);
    this.els.tAssist.classList.toggle('teal', d.assist);
    this.els.tCruise.classList.toggle('on', d.cruise);
    this.els.tGear.classList.toggle('on', d.gear);
    this.els.tGear.classList.toggle('teal', d.gear);
  }

  walk(shipDistance: number, gravity: number): void {
    this.set(this.els.wShip, shipDistance >= 1000 ? `${(shipDistance / 1000).toFixed(2)}k` : shipDistance.toFixed(0));
    this.set(this.els.wGrav, gravity.toFixed(1));
  }

  stick(x: number, y: number): void {
    // x,y in -1..1, drawn up to 70 px from center.
    this.setStyle(this.els.stick, 'transform', `translate(${(x * 70).toFixed(1)}px, ${(-y * 70).toFixed(1)}px) rotate(45deg)`);
  }

  prompts(list: Prompt[]): void {
    const key = list.map((p) => `${p.key ?? ''}|${p.text}|${p.dim ? 1 : 0}`).join('\n');
    if (key === this.promptKey) return;
    this.promptKey = key;
    const el = this.els.prompts;
    el.replaceChildren(
      ...list.map((p) => {
        const d = document.createElement('div');
        d.className = p.dim ? 'prompt dim' : 'prompt';
        if (p.key) {
          const k = document.createElement('kbd');
          k.textContent = p.key;
          d.appendChild(k);
        }
        d.appendChild(document.createTextNode(p.text));
        return d;
      }),
    );
  }

  warning(text: string | null, danger = false): void {
    const el = this.els.warning;
    if (!text) {
      el.classList.add('hidden');
      return;
    }
    el.classList.remove('hidden');
    el.classList.toggle('danger', danger);
    this.set(el, text);
  }

  crosshairTarget(on: boolean): void {
    this.els.crosshair.classList.toggle('target', on);
  }

  scan(progress: number | null, label: string): void {
    if (progress === null) {
      this.els.scanRing.classList.add('hidden');
      return;
    }
    this.els.scanRing.classList.remove('hidden');
    this.setStyle(this.els.scanProgress, 'strokeDashoffset', (276.5 * (1 - progress)).toFixed(1));
    this.set(this.els.scanLabel, label);
  }

  notice(title: string, text: string, teal = false, seconds = 6): void {
    const n = document.createElement('div');
    n.className = teal ? 'notice teal' : 'notice';
    const h = document.createElement('div');
    h.className = 'h';
    h.textContent = title;
    n.appendChild(h);
    n.appendChild(document.createTextNode(text));
    this.els.notices.appendChild(n);
    while (this.els.notices.children.length > 4) this.els.notices.firstChild?.remove();
    window.setTimeout(() => n.classList.add('fade'), seconds * 1000);
    window.setTimeout(() => n.remove(), seconds * 1000 + 700);
  }

  saveStatus(text: string, error = false): void {
    const el = this.els.save;
    el.classList.remove('hidden');
    el.style.color = error ? 'var(--danger)' : '';
    this.set(el, text);
    window.clearTimeout(this.saveTimer);
    if (!error) this.saveTimer = window.setTimeout(() => el.classList.add('hidden'), 2500);
  }

  inventory(items: { name: string; count: number }[]): void {
    const el = this.els.inventory;
    if (items.length === 0) {
      el.classList.add('hidden');
      return;
    }
    el.classList.remove('hidden');
    const key = items.map((i) => `${i.name}:${i.count}`).join(',');
    if (this.cache.get(el) === key) return;
    this.cache.set(el, key);
    const title = document.createElement('div');
    title.className = 'title';
    title.textContent = 'Samples';
    el.replaceChildren(
      title,
      ...items.map((i) => {
        const d = document.createElement('div');
        d.className = 'item';
        const n = document.createElement('span');
        n.textContent = i.name;
        const c = document.createElement('b');
        c.textContent = String(i.count);
        d.append(n, c);
        return d;
      }),
    );
  }
}
