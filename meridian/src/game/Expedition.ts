import { BODIES, BODY_IDS, SYSTEM_BODY_IDS, isBodyId, type BodyId } from '../world/bodies';
import { FIRST_LIGHT as SURVEY_SPECS, SURVEY_BODIES as FIRST_LIGHT_ORDER } from '../world/survey';
import { speciesById } from '../props/species';
import { ABILITIES } from '../abilities/catalog';
import { isAbilityId, type AbilityId } from '../abilities/save';

// Expedition progress: arrivals and the powers they unlock, discoveries,
// samples, relays and the final transmission, and the First Light route and
// scans. Pure data plus rules, so it can be saved, validated and unit-tested.
// Every operation is idempotent: repeating an interaction never duplicates
// rewards.

/** The bodies of the relay survey (samples, relays, transmission): the Quiet System, whatever system is in play. */
export const SURVEY_BODIES: readonly BodyId[] = SYSTEM_BODY_IDS.quiet;

/**
 * The power arriving at a body unlocks (charter K): its catalog power, or null
 * for none, an unknown id, or the base 'walk' every body allows.
 */
export function powerFor(body: BodyId): AbilityId | null {
  const p = isBodyId(body) ? BODIES[body].power : null;
  return isAbilityId(p) ? p : null;
}

/** First Light route waypoint id (WORLDS builds the same string in sites.ts): 0 is nearest the landing site, the last is the beacon. */
export const routeId = (body: BodyId, i: number): string => `${body}:route:${i}`;
/** First Light scan target id (WORLDS builds the same string in sites.ts). */
export const poiId = (body: BodyId, i: number): string => `${body}:poi:${i}`;

/** A route waypoint or scan target of a chapter. */
export interface ChapterMark {
  id: string;
  label: string;
}

/** One First Light chapter: arrive (unlocking the body's power), reach its route's waypoints, scan its targets. */
export interface Chapter {
  body: BodyId;
  power: AbilityId;
  route: readonly ChapterMark[];
  scans: readonly ChapterMark[];
}

/**
 * "First Light" (charter H): Earth (Skyborne Flight), then the Moon (Lunar
 * Step), then Mars (Redline), each with WORLDS' guided route and scan targets
 * (src/world/survey.ts), then free exploration. Only ids and labels live
 * here; positions come from WORLDS' mission sites.
 */
export const FIRST_LIGHT: readonly Chapter[] = FIRST_LIGHT_ORDER.flatMap((body) => {
  const power = powerFor(body);
  const spec = SURVEY_SPECS[body];
  if (!power || !spec) return [];
  return [{
    body,
    power,
    route: spec.route.map((r, i) => ({ id: routeId(body, i), label: r.label })),
    scans: spec.scans.map((t, i) => ({ id: poiId(body, i), label: t.label })),
  }];
});

const ROUTE_AT = new Map(FIRST_LIGHT.flatMap((c) => c.route.map((r, i) => [r.id, { chapter: c, i }] as const)));
const POI_IDS = new Set(FIRST_LIGHT.flatMap((c) => c.scans.map((t) => t.id)));
/** Every First Light waypoint (cap for the saved route list). */
export const ROUTE_POINTS = ROUTE_AT.size;

export const isRouteId = (id: string): boolean => ROUTE_AT.has(id);
export const isPoiId = (id: string): boolean => POI_IDS.has(id);

/** First Light runs while its bodies are in play (Sol); the Quiet System keeps the relay survey. */
export function firstLightInPlay(): boolean {
  return FIRST_LIGHT.length > 0 && FIRST_LIGHT.every((c) => BODY_IDS.includes(c.body));
}

/** What the objective panel asks for next. */
export type ObjectiveStep = 'travel' | 'land' | 'route' | 'scan' | 'free' | 'survey';

export interface Objective {
  title: string;
  detail: string;
  /** The body the step happens at (null: nowhere in particular). */
  body: BodyId | null;
  step: ObjectiveStep;
  /** The route waypoint or scan target the step points at, else null. */
  target: string | null;
}

/** A body's name inside a sentence ("the Moon"; other bodies by name). */
const inText = (body: BodyId): string => (body === 'moon' ? 'the Moon' : BODIES[body].name);

export interface ExpeditionState {
  /** Samples carried, by body of origin. */
  inventory: Record<BodyId, number>;
  /** Sample site IDs that have been collected (depleted). */
  collected: string[];
  /** Bodies whose survey relay is active. */
  relays: BodyId[];
  /** Species IDs with journal entries. */
  species: string[];
  /** Stable object IDs that have been scanned (props, samples, relays, First Light targets). */
  scanned: string[];
  transmitted: boolean;
  /** First Light route waypoints reached (`${body}:route:${i}`). */
  route: string[];
}

export function newExpedition(): ExpeditionState {
  return { inventory: { ilex: 0, vesper: 0, cairn: 0 }, collected: [], relays: [], species: [], scanned: [], transmitted: false, route: [] };
}

/** Body that a sample/relay ID belongs to (IDs are `${body}:...`). */
export function bodyOfId(id: string): BodyId | null {
  const b = id.slice(0, id.indexOf(':'));
  return SURVEY_BODIES.includes(b) ? b : null;
}

export class Expedition {
  state: ExpeditionState = newExpedition();
  /** Bodies arrived at (landed on), in arrival order (SaveData.discoveries). */
  discoveries: BodyId[] = [];
  /** Powers those arrivals unlocked, in unlock order (SaveData.unlocked). */
  unlocked: AbilityId[] = [];
  /** Set whenever progress changes (cleared by the save system). */
  dirty = false;

  reset(s: ExpeditionState = newExpedition(), discoveries: BodyId[] = [], unlocked: AbilityId[] = []): void {
    this.state = s;
    this.discoveries = discoveries;
    this.unlocked = unlocked;
    this.dirty = false;
  }

  /**
   * Record an arrival at a body: it joins the discoveries and its power (if
   * any) is unlocked, each once. Returns whether anything was new.
   */
  arrive(body: BodyId): boolean {
    if (!isBodyId(body)) return false;
    const power = powerFor(body);
    const newBody = !this.discoveries.includes(body);
    const newPower = power !== null && !this.unlocked.includes(power);
    if (newBody) this.discoveries.push(body);
    if (newPower) this.unlocked.push(power);
    if (newBody || newPower) this.dirty = true;
    return newBody || newPower;
  }

  /** The power active while exploring a body: its own once unlocked, else null (never another body's). */
  activePower(body: BodyId): AbilityId | null {
    const p = powerFor(body);
    return p && this.unlocked.includes(p) ? p : null;
  }

  /**
   * Reach a First Light waypoint. The earlier waypoints of the same route
   * count as reached too, so skipping ahead never soft-locks the route.
   * Returns whether anything was new.
   */
  reachRoute(id: string): boolean {
    const at = ROUTE_AT.get(id);
    if (!at) return false;
    let added = false;
    for (const r of at.chapter.route.slice(0, at.i + 1)) {
      if (this.state.route.includes(r.id)) continue;
      this.state.route.push(r.id);
      added = true;
    }
    if (added) this.dirty = true;
    return added;
  }

  routeDone(body: BodyId): boolean {
    const c = FIRST_LIGHT.find((ch) => ch.body === body);
    return !!c && c.route.every((r) => this.state.route.includes(r.id));
  }

  scansDone(body: BodyId): boolean {
    const c = FIRST_LIGHT.find((ch) => ch.body === body);
    return !!c && c.scans.every((t) => this.state.scanned.includes(t.id));
  }

  /**
   * The current First Light chapter: the first body of the progression whose
   * power is still locked or whose route or scans are unfinished; null once
   * all are done (free exploration). Progress made early on a later body
   * counts when its chapter comes.
   */
  chapter(): BodyId | null {
    const c = FIRST_LIGHT.find((ch) => !this.unlocked.includes(ch.power) || !this.routeDone(ch.body) || !this.scansDone(ch.body));
    return c ? c.body : null;
  }

  isCollected(sampleId: string): boolean {
    return this.state.collected.includes(sampleId);
  }

  /** Collect a sample once. Returns false if it was already collected. */
  collect(sampleId: string): boolean {
    const body = bodyOfId(sampleId);
    if (!body || this.isCollected(sampleId)) return false;
    this.state.collected.push(sampleId);
    this.state.inventory[body]++;
    this.dirty = true;
    return true;
  }

  relayActive(body: BodyId): boolean {
    return this.state.relays.includes(body);
  }

  /** Why a relay cannot be activated right now (null when it can). */
  relayBlocker(body: BodyId): string | null {
    if (this.relayActive(body)) return 'This relay is already transmitting.';
    if (this.state.inventory[body] < 1) return 'Collect a sample from this world first.';
    return null;
  }

  /** Activate a body's relay, consuming one local sample, once. */
  activateRelay(body: BodyId): boolean {
    if (this.relayBlocker(body)) return false;
    this.state.inventory[body]--;
    this.state.relays.push(body);
    this.dirty = true;
    return true;
  }

  get canTransmit(): boolean {
    return !this.state.transmitted && SURVEY_BODIES.every((b) => this.relayActive(b));
  }

  /** Transmit the three-relay survey once. */
  transmit(): boolean {
    if (!this.canTransmit) return false;
    this.state.transmitted = true;
    this.dirty = true;
    return true;
  }

  /**
   * Record a scan of a stable object ID. Returns whether the object and its
   * species were new (a new species adds a journal entry).
   */
  scan(objectId: string, speciesId: string | null): { newObject: boolean; newSpecies: boolean } {
    const newObject = !this.state.scanned.includes(objectId);
    if (newObject) this.state.scanned.push(objectId);
    let newSpecies = false;
    if (speciesId && speciesById(speciesId) && !this.state.species.includes(speciesId)) {
      this.state.species.push(speciesId);
      newSpecies = true;
    }
    if (newObject || newSpecies) this.dirty = true;
    return { newObject, newSpecies };
  }

  get samplesCarried(): number {
    const inv = this.state.inventory;
    return inv.ilex + inv.vesper + inv.cairn;
  }

  /** The next step for the objective panel: First Light while its bodies are in play, else the relay survey. */
  objective(currentBody: BodyId | null): Objective {
    return firstLightInPlay() ? this.firstLightObjective(currentBody) : this.surveyObjective(currentBody);
  }

  private firstLightObjective(here: BodyId | null): Objective {
    const c = FIRST_LIGHT.find((ch) => ch.body === this.chapter());
    if (!c) {
      return { title: 'First Light complete', detail: 'Earth, the Moon and Mars are charted. Explore freely.', body: null, step: 'free', target: null };
    }
    const name = inText(c.body);
    const power = ABILITIES[c.power];
    if (!this.unlocked.includes(c.power)) {
      return here === c.body
        ? { title: `Land on ${name}`, detail: `Touch down to unlock ${power.name}.`, body: c.body, step: 'land', target: null }
        : { title: `Land on ${name}`, detail: `Set course for ${name} (Tab) and land to unlock ${power.name}.`, body: c.body, step: 'travel', target: null };
    }
    if (here !== c.body) {
      const routeLeft = c.route.filter((r) => !this.state.route.includes(r.id)).length;
      const scansLeft = c.scans.filter((t) => !this.state.scanned.includes(t.id)).length;
      const left = [routeLeft ? `${routeLeft} of ${c.route.length} waypoints` : '', scansLeft ? `${scansLeft} of ${c.scans.length} scans` : ''];
      return { title: `Return to ${name}`, detail: `First Light continues there: ${left.filter(Boolean).join(' and ')} to go.`, body: c.body, step: 'travel', target: null };
    }
    const k = c.route.findIndex((r) => !this.state.route.includes(r.id));
    if (k >= 0) {
      const r = c.route[k];
      return { title: `Reach ${r.label}`, detail: `${power.name} route, waypoint ${k + 1} of ${c.route.length} · ${power.feedback.hint}.`, body: c.body, step: 'route', target: r.id };
    }
    // The chapter is unfinished and its route is done, so a scan target is left.
    const j = c.scans.findIndex((t) => !this.state.scanned.includes(t.id));
    const t = c.scans[j];
    return { title: `Scan ${t.label}`, detail: `Scan target ${j + 1} of ${c.scans.length} · aim at it and hold F.`, body: c.body, step: 'scan', target: t.id };
  }

  private surveyObjective(currentBody: BodyId | null): Objective {
    const s = this.state;
    if (s.transmitted) return { title: 'Survey transmitted', detail: 'The expedition is complete. The system is yours to explore.', body: null, step: 'free', target: null };
    if (this.canTransmit) return { title: 'Transmit the survey', detail: 'All three relays are live. Press T aboard the ship to transmit.', body: null, step: 'survey', target: null };
    const pending = SURVEY_BODIES.filter((b) => !this.relayActive(b));
    const here = currentBody && pending.includes(currentBody) ? currentBody : null;
    const body = here ?? pending[0];
    const name = body.charAt(0).toUpperCase() + body.slice(1);
    if (s.inventory[body] > 0) {
      return { title: `Activate the ${name} relay`, detail: 'Bring the sample to the relay mast and press E.', body, step: 'survey', target: null };
    }
    return {
      title: `Survey ${name}`,
      detail: here ? 'Collect a sample near the relay (E), then activate the relay.' : `Set course for ${name} (Tab) and land at the marked site.`,
      body,
      step: 'survey',
      target: null,
    };
  }
}
