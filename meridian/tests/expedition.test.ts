import { describe, expect, it } from 'vitest';
import { Expedition } from '../src/game/Expedition';
import { BODIES, BODY_IDS, CORE_BODY_IDS, EXTENDED_BODY_IDS } from '../src/world/bodies';
import { computeSites } from '../src/world/sites';

describe('expedition rules', () => {
  it('collects each sample once and never duplicates rewards', () => {
    const e = new Expedition();
    expect(e.collect('ilex:sample:0')).toBe(true);
    expect(e.collect('ilex:sample:0')).toBe(false);
    expect(e.state.inventory.ilex).toBe(1);
    expect(e.state.collected).toEqual(['ilex:sample:0']);
    expect(e.collect('nowhere:sample:0')).toBe(false);
  });

  it('activates a relay only with a local sample, consuming exactly one, once', () => {
    const e = new Expedition();
    expect(e.relayBlocker('ilex')).toMatch(/Collect a sample/);
    e.collect('vesper:sample:1');
    expect(e.activateRelay('ilex')).toBe(false); // a Vesper sample does not work at Ilex
    e.collect('ilex:sample:2');
    e.collect('ilex:sample:1');
    expect(e.activateRelay('ilex')).toBe(true);
    expect(e.state.inventory.ilex).toBe(1);
    expect(e.activateRelay('ilex')).toBe(false); // repeat: no second consumption
    expect(e.state.inventory.ilex).toBe(1);
    expect(e.state.relays).toEqual(['ilex']);
    expect(e.relayBlocker('ilex')).toMatch(/already/);
  });

  it('transmits once, only after all three relays', () => {
    const e = new Expedition();
    expect(e.transmit()).toBe(false);
    // The new worlds' relays play no part in the core survey.
    for (const b of EXTENDED_BODY_IDS) {
      e.collect(`${b}:sample:0`);
      expect(e.activateRelay(b)).toBe(true);
      expect(e.canTransmit).toBe(false);
    }
    for (const b of CORE_BODY_IDS) {
      e.collect(`${b}:sample:0`);
      expect(e.canTransmit).toBe(false);
      expect(e.activateRelay(b)).toBe(true);
    }
    expect(e.canTransmit).toBe(true);
    expect(e.transmit()).toBe(true);
    expect(e.transmit()).toBe(false);
    // Core survey done; with both extended relays already live the Extended Survey is ready.
    expect(e.objective(null).title).toBe('Transmit the Extended Survey');
  });

  it('transmits the Extended Survey once, only after the core survey and both extended relays', () => {
    const e = new Expedition();
    for (const b of EXTENDED_BODY_IDS) {
      e.collect(`${b}:sample:1`);
      e.activateRelay(b);
    }
    expect(e.canTransmitExtended).toBe(false); // core survey not sent yet
    expect(e.transmitExtended()).toBe(false);
    for (const b of CORE_BODY_IDS) {
      e.collect(`${b}:sample:1`);
      e.activateRelay(b);
    }
    expect(e.transmitExtended()).toBe(false);
    expect(e.transmit()).toBe(true);
    expect(e.relaysActive('core')).toBe(3);
    expect(e.relaysActive('extended')).toBe(2);
    e.dirty = false;
    expect(e.transmitExtended()).toBe(true);
    expect(e.dirty).toBe(true);
    e.dirty = false;
    expect(e.transmitExtended()).toBe(false); // idempotent
    expect(e.transmit()).toBe(false);
    expect(e.dirty).toBe(false);
    expect(e.state.extendedTransmitted).toBe(true);
    expect(e.objective('saro')).toEqual({ title: 'Extended Survey transmitted', detail: expect.any(String), body: null });
  });

  it('guides the player to the new worlds after the core survey', () => {
    const e = new Expedition();
    for (const b of CORE_BODY_IDS) {
      e.collect(`${b}:sample:0`);
      e.activateRelay(b);
    }
    expect(e.objective('cairn').title).toBe('Transmit the survey');
    e.transmit();
    const a = e.objective('cairn');
    expect(a.body).toBe('orrin');
    expect(a.title).toBe('Extended Survey · Survey Orrin');
    expect(a.detail).toMatch(/Set course for Orrin/);
    // Being on a pending world makes it the objective.
    expect(e.objective('saro').body).toBe('saro');
    e.collect('saro:sample:2');
    expect(e.objective('saro').title).toBe('Extended Survey · Activate the Saro relay');
    e.activateRelay('saro');
    expect(e.objective('saro').body).toBe('orrin');
    e.collect('orrin:sample:0');
    e.collect('ilex:sample:1');
    expect(e.samplesCarried).toBe(2);
  });

  it('records scans as stable journal entries', () => {
    const e = new Expedition();
    const a = e.scan('ilex:ilex-lantern:5/10/2/3:4', 'ilex-lantern');
    expect(a).toEqual({ newObject: true, newSpecies: true });
    const b = e.scan('ilex:ilex-lantern:5/10/2/3:4', 'ilex-lantern');
    expect(b).toEqual({ newObject: false, newSpecies: false });
    const c = e.scan('ilex:ilex-lantern:5/10/2/9:1', 'ilex-lantern');
    expect(c).toEqual({ newObject: true, newSpecies: false });
    expect(e.state.species).toEqual(['ilex-lantern']);
    expect(e.scan('ilex:relay', null)).toEqual({ newObject: true, newSpecies: false });
  });

  it('cannot soft-lock: every world offers spare samples and carried samples are never lost', () => {
    for (const b of BODY_IDS) {
      const sites = computeSites(BODIES[b]);
      expect(sites.samples.length).toBeGreaterThanOrEqual(2);
      expect(new Set(sites.samples.map((s) => s.id)).size).toBe(sites.samples.length);
    }
    const e = new Expedition();
    // Collect everything everywhere first, then activate in any order.
    for (const b of BODY_IDS) for (const s of computeSites(BODIES[b]).samples) e.collect(s.id);
    for (const b of [...BODY_IDS].reverse()) expect(e.activateRelay(b)).toBe(true);
    expect(e.state.inventory).toEqual({ ilex: 2, vesper: 2, cairn: 2, orrin: 2, saro: 2 });
    expect(e.transmit()).toBe(true);
    expect(e.transmitExtended()).toBe(true);
  });

  it('guides the next objective', () => {
    const e = new Expedition();
    expect(e.objective('ilex').title).toBe('Survey Ilex');
    e.collect('ilex:sample:0');
    expect(e.objective('ilex').title).toBe('Activate the Ilex relay');
    e.activateRelay('ilex');
    const next = e.objective('ilex');
    expect(next.body).toBe('vesper');
    expect(next.detail).toMatch(/Set course for Vesper/);
  });
});
