import { BODIES, BODY_IDS, CORE_BODY_IDS, EXTENDED_BODY_IDS } from '../world/bodies';
import { speciesFor } from '../props/species';
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
  const total = BODY_IDS.reduce((n, b) => n + speciesFor(b).filter((sp) => sp.scannable).length, 0);
  out.push(el('div', 'empty', `${s.species.length} of ${total} species logged · ${s.scanned.length} objects scanned. Hold F on foot to scan.`));
  for (const b of BODY_IDS) {
    const def = BODIES[b];
    out.push(el('h3', '', `${def.name} — ${def.biomeNames.join(' · ')}`));
    if (!speciesFor(b).some((sp) => sp.scannable)) out.push(el('div', 'entry unknown', 'No specimens catalogued yet.'));
    for (const sp of speciesFor(b)) {
      if (!sp.scannable) continue;
      const known = s.species.includes(sp.id);
      const entry = el('div', known ? 'entry' : 'entry unknown');
      const head = el('div', 'eh');
      head.append(el('span', 'en', known ? sp.name : 'Unidentified specimen'), el('span', 'eb', known ? 'Logged' : ''));
      entry.append(head);
      if (known) entry.append(el('div', 'ed', sp.description));
      out.push(entry);
    }
  }
  root.replaceChildren(...out);
}

/** Relay and sample status per body, and the transmissions (core survey, then the Extended Survey). */
export function renderSurvey(root: HTMLElement, e: Expedition): void {
  const s = e.state;
  const out: HTMLElement[] = [];
  const core = CORE_BODY_IDS.length;
  const ext = EXTENDED_BODY_IDS.length;
  const status = s.transmitted
    ? 'Survey transmitted. The expedition is complete; explore freely.'
    : e.canTransmit
      ? 'All three relays are active. Transmit the survey from the ship (T).'
      : `${e.relaysActive('core')} of ${core} relays active. Each relay needs one sample from its own world.`;
  out.push(el('div', 'empty', status));
  const relay = (b: (typeof BODY_IDS)[number]) => {
    const def = BODIES[b];
    const got = s.collected.filter((id) => id.startsWith(`${b}:`)).length;
    const entry = el('div', 'entry');
    const head = el('div', 'eh');
    head.append(el('span', 'en', `${def.name} relay`), el('span', 'eb', e.relayActive(b) ? 'Active' : 'Pending'));
    entry.append(head);
    entry.append(el('div', 'ed', `${sampleName(b)}s collected: ${got} of 3 · carried: ${s.inventory[b]}`));
    out.push(entry);
  };
  for (const b of CORE_BODY_IDS) relay(b);
  out.push(el('h3', '', 'Extended Survey'));
  out.push(el('div', 'empty', s.extendedTransmitted
    ? 'Extended Survey transmitted.'
    : e.canTransmitExtended
      ? 'Both outer relays are active. Transmit the Extended Survey from the ship (T).'
      : `${e.relaysActive('extended')} of ${ext} relays active.${s.transmitted ? '' : ' Transmitted after the core survey.'}`));
  for (const b of EXTENDED_BODY_IDS) relay(b);
  root.replaceChildren(...out);
}
