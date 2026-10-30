import { describe, expect, it } from 'vitest';
import { Expedition } from '../src/game/Expedition';
import { BODIES, BODY_IDS } from '../src/world/bodies';
import { computeSites } from '../src/world/sites';

describe('expedition rules', () => {
  it('collects each sample once and never duplicates rewards', () => {
    const e = new Expedition();
    expect(e.collect('ilex:sample:0')).toBe(true);
    expect(e.collect('ilex:sample:0')).toBe(false);
    expect(e.state.inventory.ilex).toBe(1);
    expect(e.state.collected).toEqual(['ilex:sample:0']);
    expect(e.collect('nowhere:sample:0')).toBe(false);
    expect(e.collect('earth:sample:0')).toBe(false); // catalog body not in play yet
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
    for (const b of BODY_IDS) {
      e.collect(`${b}:sample:0`);
      expect(e.canTransmit).toBe(false);
      expect(e.activateRelay(b)).toBe(true);
    }
    expect(e.canTransmit).toBe(true);
    expect(e.transmit()).toBe(true);
    expect(e.transmit()).toBe(false);
    expect(e.objective(null).title).toBe('Survey transmitted');
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
    expect(e.state.inventory).toEqual({ ilex: 2, vesper: 2, cairn: 2 });
    expect(e.transmit()).toBe(true);
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
