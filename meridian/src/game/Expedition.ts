import { BODIES, SYSTEM_BODY_IDS, isBodyId, type BodyId } from '../world/bodies';
import { speciesById } from '../props/species';

// Expedition progress: arrivals and the powers they unlock, discoveries,
// samples, relays and the final transmission. Pure data plus rules, so it can
// be saved, validated and unit-tested. Every operation is idempotent:
// repeating an interaction never duplicates rewards.

/** The bodies of the relay survey (samples, relays, transmission): the Quiet System, whatever system is in play. */
export const SURVEY_BODIES: readonly BodyId[] = SYSTEM_BODY_IDS.quiet;

/**
 * The power arriving at a body unlocks (charter K): its catalog power, or null
 * for none, an unknown id, or the base 'walk' every body allows.
 */
export function powerFor(body: BodyId): string | null {
  const p = isBodyId(body) ? BODIES[body].power : null;
  return p === 'walk' ? null : p;
}

export interface ExpeditionState {
  /** Samples carried, by body of origin. */
  inventory: Record<BodyId, number>;
  /** Sample site IDs that have been collected (depleted). */
  collected: string[];
  /** Bodies whose survey relay is active. */
  relays: BodyId[];
  /** Species IDs with journal entries. */
  species: string[];
  /** Stable object IDs that have been scanned (props, samples, relays). */
  scanned: string[];
  transmitted: boolean;
}

export function newExpedition(): ExpeditionState {
  return { inventory: { ilex: 0, vesper: 0, cairn: 0 }, collected: [], relays: [], species: [], scanned: [], transmitted: false };
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
  unlocked: string[] = [];
  /** Set whenever progress changes (cleared by the save system). */
  dirty = false;

  reset(s: ExpeditionState = newExpedition(), discoveries: BodyId[] = [], unlocked: string[] = []): void {
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

  /** The next step of the survey, for the objective panel. */
  objective(currentBody: BodyId | null): { title: string; detail: string; body: BodyId | null } {
    const s = this.state;
    if (s.transmitted) return { title: 'Survey transmitted', detail: 'The expedition is complete. The system is yours to explore.', body: null };
    if (this.canTransmit) return { title: 'Transmit the survey', detail: 'All three relays are live. Press T aboard the ship to transmit.', body: null };
    const pending = SURVEY_BODIES.filter((b) => !this.relayActive(b));
    const here = currentBody && pending.includes(currentBody) ? currentBody : null;
    const body = here ?? pending[0];
    const name = body.charAt(0).toUpperCase() + body.slice(1);
    if (s.inventory[body] > 0) {
      return { title: `Activate the ${name} relay`, detail: 'Bring the sample to the relay mast and press E.', body };
    }
    return {
      title: `Survey ${name}`,
      detail: here ? 'Collect a sample near the relay (E), then activate the relay.' : `Set course for ${name} (Tab) and land at the marked site.`,
      body,
    };
  }
}
