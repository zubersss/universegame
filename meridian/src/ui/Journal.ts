import { BODIES, BODY_IDS } from '../world/bodies';
import { catalogFor, CATALOG } from '../fauna/catalog';
import { sampleName } from '../world/MissionObjects';
import type { Expedition, ExpeditionState } from '../game/Expedition';

// Journal and survey tabs of the Tab panel (plain DOM, rebuilt on open).

function el(tag: string, cls: string, text?: string): HTMLElement {
  const e = document.createElement(tag);
  e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

/** Species entries per body: discovered ones with their notes, the rest as unknown. */
export function renderJournal(root: HTMLElement, s: ExpeditionState): void {
  const out: HTMLElement[] = [];
  const total = CATALOG.length;
  out.push(el('div', 'empty', `${s.species.length} of ${total} species logged · ${s.scanned.length} objects scanned. Hold F on foot to scan.`));
  for (const b of BODY_IDS) {
    const def = BODIES[b];
    out.push(el('h3', '', `${def.name} — ${def.biomeNames.join(' · ')}`));
    for (const sp of catalogFor(b)) {
      const known = s.species.includes(sp.id);
      const entry = el('div', known ? 'entry' : 'entry unknown');
      const head = el('div', 'eh');
      const kind = sp.kind === 'fauna' ? 'Fauna' : sp.kind === 'mineral' ? 'Mineral' : 'Flora';
      head.append(el('span', 'en', known ? sp.name : sp.kind === 'fauna' ? 'Unidentified creature' : 'Unidentified specimen'), el('span', 'eb', known ? `${kind} · logged` : kind));
      entry.append(head);
      if (known) entry.append(el('div', 'ed', sp.description));
      out.push(entry);
    }
  }
  root.replaceChildren(...out);
}

/** Relay and sample status per body, and the transmission. */
export function renderSurvey(root: HTMLElement, e: Expedition): void {
  const s = e.state;
  const out: HTMLElement[] = [];
  const status = s.transmitted
    ? 'Survey transmitted. The expedition is complete; explore freely.'
    : e.canTransmit
      ? 'All three relays are active. Transmit the survey from the ship (T).'
      : `${s.relays.length} of 3 relays active. Each relay needs one sample from its own world.`;
  out.push(el('div', 'empty', status));
  for (const b of BODY_IDS) {
    const def = BODIES[b];
    const got = s.collected.filter((id) => id.startsWith(`${b}:`)).length;
    const entry = el('div', 'entry');
    const head = el('div', 'eh');
    head.append(el('span', 'en', `${def.name} relay`), el('span', 'eb', e.relayActive(b) ? 'Active' : 'Pending'));
    entry.append(head);
    entry.append(el('div', 'ed', `${sampleName(b)}s collected: ${got} of 3 · carried: ${s.inventory[b]}`));
    out.push(entry);
  }
  root.replaceChildren(...out);
}
