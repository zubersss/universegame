import { BODIES, BODY_IDS, type BodyId } from '../world/bodies';
import { speciesFor } from '../props/species';
import { sampleName } from '../world/MissionObjects';
import { FIRST_LIGHT, SURVEY_BODIES, routeId, scanId } from '../world/survey';
import type { Expedition, ExpeditionState } from '../game/Expedition';

// Journal and survey tabs of the Tab panel (plain DOM, rebuilt on open).

function el(tag: string, cls: string, text?: string): HTMLElement {
  const e = document.createElement(tag);
  e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

/** Bodies with journal pages: the Quiet System worlds, or the First Light survey bodies in play. */
export function journalBodies(): BodyId[] {
  return BODY_IDS.filter((b) => BODIES[b].system === 'quiet' || SURVEY_BODIES.includes(b));
}

/** Reached First Light waypoints (expedition `route` progress; absent before it exists). */
function reachedRoute(s: ExpeditionState): readonly string[] {
  const r = (s as Partial<{ route: unknown }>).route;
  return Array.isArray(r) ? r.filter((x): x is string => typeof x === 'string') : [];
}

function entry(name: string, badge: string, note: string | null, known: boolean): HTMLElement {
  const e = el('div', known ? 'entry' : 'entry unknown');
  const head = el('div', 'eh');
  head.append(el('span', 'en', name), el('span', 'eb', badge));
  e.append(head);
  if (note) e.append(el('div', 'ed', note));
  return e;
}

/** First Light entries of a survey body: the route waypoints and the landmarks to scan. */
function firstLightEntries(b: BodyId, s: ExpeditionState): HTMLElement[] {
  const spec = FIRST_LIGHT[b];
  if (!spec) return [];
  const reached = reachedRoute(s);
  const out: HTMLElement[] = [];
  spec.route.forEach((r, i) => {
    const done = reached.includes(routeId(b, i));
    out.push(entry(`Route ${i + 1} of 3 · ${r.label}`, done ? 'Reached' : 'Ahead', null, done));
  });
  spec.scans.forEach((t, i) => {
    const known = s.scanned.includes(scanId(b, i));
    out.push(entry(known ? t.label : 'Unscanned landmark', known ? 'Scanned' : '', known ? t.note : null, known));
  });
  return out;
}

/** Species entries per body: discovered ones with their notes, the rest as unknown. */
export function renderJournal(root: HTMLElement, s: ExpeditionState): void {
  const out: HTMLElement[] = [];
  const bodies = journalBodies();
  const total = bodies.reduce((n, b) => n + speciesFor(b).filter((sp) => sp.scannable).length, 0);
  const landmarks = bodies.flatMap((b) => (FIRST_LIGHT[b]?.scans ?? []).map((_, i) => scanId(b, i)));
  const lines = [`${s.species.length} of ${total} species logged`];
  if (landmarks.length > 0) lines.push(`${landmarks.filter((id) => s.scanned.includes(id)).length} of ${landmarks.length} landmarks`);
  lines.push(`${s.scanned.length} objects scanned`);
  out.push(el('div', 'empty', `${lines.join(' · ')}. Hold F on foot to scan.`));
  for (const b of bodies) {
    const def = BODIES[b];
    out.push(el('h3', '', `${def.name} — ${def.biomeNames.join(' · ')}`));
    out.push(...firstLightEntries(b, s));
    for (const sp of speciesFor(b)) {
      if (!sp.scannable) continue;
      const known = s.species.includes(sp.id);
      out.push(entry(known ? sp.name : 'Unidentified specimen', known ? 'Logged' : '', known ? sp.description : null, known));
    }
  }
  root.replaceChildren(...out);
}

/** Relay and sample status per body and the transmission, or First Light progress in Sol. */
export function renderSurvey(root: HTMLElement, e: Expedition): void {
  const s = e.state;
  const out: HTMLElement[] = [];
  const bodies = journalBodies();
  if (bodies.some((b) => FIRST_LIGHT[b])) {
    // First Light: route and landmark progress per survey body.
    const reached = reachedRoute(s);
    out.push(el('div', 'empty', 'First Light survey: follow each route to its beacon and scan the landmarks along the way.'));
    for (const b of bodies) {
      const spec = FIRST_LIGHT[b];
      if (!spec) continue;
      const r = spec.route.filter((_, i) => reached.includes(routeId(b, i))).length;
      const sc = spec.scans.filter((_, i) => s.scanned.includes(scanId(b, i))).length;
      out.push(entry(`${BODIES[b].name} route`, r === 3 ? 'Complete' : `${r} of 3`, `Waypoints reached: ${r} of 3 · landmarks scanned: ${sc} of 3`, true));
    }
    root.replaceChildren(...out);
    return;
  }
  const status = s.transmitted
    ? 'Survey transmitted. The expedition is complete; explore freely.'
    : e.canTransmit
      ? 'All three relays are active. Transmit the survey from the ship (T).'
      : `${s.relays.length} of 3 relays active. Each relay needs one sample from its own world.`;
  out.push(el('div', 'empty', status));
  for (const b of bodies) {
    const got = s.collected.filter((id) => id.startsWith(`${b}:`)).length;
    out.push(entry(`${BODIES[b].name} relay`, e.relayActive(b) ? 'Active' : 'Pending', `${sampleName(b)}s collected: ${got} of 3 · carried: ${s.inventory[b]}`, true));
  }
  root.replaceChildren(...out);
}
