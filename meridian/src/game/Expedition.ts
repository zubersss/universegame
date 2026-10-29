import { BODIES, BODY_IDS, CORE_BODY_IDS, EXTENDED_BODY_IDS, isBodyId, type BodyId } from '../world/bodies';
import { speciesById } from '../props/species';

// Expedition progress: discoveries, samples, relays and the final transmission.
// Pure data plus rules, so it can be saved, validated and unit-tested. Every
// operation is idempotent: repeating an interaction never duplicates rewards.

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
  /** The core survey (Ilex, Vesper, Cairn relays) has been transmitted. */
  transmitted: boolean;
  /** The Extended Survey (the new worlds' relays) has been transmitted, after the core survey. */
  extendedTransmitted: boolean;
}

export function emptyInventory(): Record<BodyId, number> {
  const inv = {} as Record<BodyId, number>;
  for (const b of BODY_IDS) inv[b] = 0;
  return inv;
}

export function newExpedition(): ExpeditionState {
  return { inventory: emptyInventory(), collected: [], relays: [], species: [], scanned: [], transmitted: false, extendedTransmitted: false };
}

/** Body that a sample/relay ID belongs to (IDs are `${body}:...`). */
export function bodyOfId(id: string): BodyId | null {
  const b = id.slice(0, id.indexOf(':'));
  return isBodyId(b) ? b : null;
}

export class Expedition {
  state: ExpeditionState = newExpedition();
  /** Set whenever progress changes (cleared by the save system). */
  dirty = false;

  reset(s: ExpeditionState = newExpedition()): void {
    this.state = s;
    this.dirty = false;
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
    return !this.state.transmitted && CORE_BODY_IDS.every((b) => this.relayActive(b));
  }

  /** Transmit the three-relay (core) survey once. */
  transmit(): boolean {
    if (!this.canTransmit) return false;
    this.state.transmitted = true;
    this.dirty = true;
    return true;
  }

  /** The Extended Survey can be sent once, after the core survey, with every extended relay active. */
  get canTransmitExtended(): boolean {
    const s = this.state;
    return s.transmitted && !s.extendedTransmitted && EXTENDED_BODY_IDS.every((b) => this.relayActive(b));
  }

  /** Transmit the Extended Survey once. */
  transmitExtended(): boolean {
    if (!this.canTransmitExtended) return false;
    this.state.extendedTransmitted = true;
    this.dirty = true;
    return true;
  }

  /** Active relays of one survey. */
  relaysActive(survey: 'core' | 'extended'): number {
    return (survey === 'core' ? CORE_BODY_IDS : EXTENDED_BODY_IDS).filter((b) => this.relayActive(b)).length;
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
    let n = 0;
    for (const b of BODY_IDS) n += inv[b];
    return n;
  }

  /** The next step of the survey, for the objective panel. */
  objective(currentBody: BodyId | null): { title: string; detail: string; body: BodyId | null } {
    const s = this.state;
    if (s.extendedTransmitted) return { title: 'Extended Survey transmitted', detail: 'Every world is charted. The system is yours to explore.', body: null };
    if (this.canTransmitExtended) return { title: 'Transmit the Extended Survey', detail: 'Both outer relays are live. Press T aboard the ship to transmit.', body: null };
    if (this.canTransmit) return { title: 'Transmit the survey', detail: 'All three relays are live. Press T aboard the ship to transmit.', body: null };
    // The core survey first; after its transmission the Extended Survey guides the player on.
    const ids = s.transmitted ? EXTENDED_BODY_IDS : CORE_BODY_IDS;
    const pending = ids.filter((b) => !this.relayActive(b));
    const here = currentBody && pending.includes(currentBody) ? currentBody : null;
    const body = here ?? pending[0];
    const name = BODIES[body].name;
    const prefix = s.transmitted ? 'Extended Survey · ' : '';
    if (s.inventory[body] > 0) {
      return { title: `${prefix}Activate the ${name} relay`, detail: 'Bring the sample to the relay mast and press E.', body };
    }
    return {
      title: `${prefix}Survey ${name}`,
      detail: here ? 'Collect a sample near the relay (E), then activate the relay.' : `Set course for ${name} (Tab) and land at the marked site.`,
      body,
    };
  }
}
