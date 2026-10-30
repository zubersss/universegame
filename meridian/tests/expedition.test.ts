import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { Expedition, FIRST_LIGHT, SURVEY_BODIES, firstLightInPlay, isPoiId, isRouteId, powerFor } from '../src/game/Expedition';
import { BODIES, BODY_IDS, SOL_M2_BODIES, SYSTEM_BODY_IDS, setPlaySystem } from '../src/world/bodies';
import { computeSites } from '../src/world/sites';
import { FIRST_LIGHT as SURVEY_SPECS } from '../src/world/survey';

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

  it('names the power each arrival unlocks (never the base walk)', () => {
    expect(powerFor('earth')).toBe('skyborne-flight');
    expect(powerFor('moon')).toBe('lunar-step');
    expect(powerFor('mars')).toBe('redline');
    expect(powerFor('sun')).toBeNull();
    expect(powerFor('ilex')).toBeNull();
    expect(powerFor('pluto')).toBeNull();
    expect(powerFor('constructor')).toBeNull();
  });

  it('records each arrival once, with its power, idempotently', () => {
    const e = new Expedition();
    expect(e.arrive('ilex')).toBe(true);
    expect(e.dirty).toBe(true);
    expect(e.unlocked).toEqual([]);
    e.dirty = false;
    expect(e.arrive('ilex')).toBe(false); // repeat: nothing new, nothing to save
    expect(e.dirty).toBe(false);
    expect(e.arrive('earth')).toBe(true);
    expect(e.arrive('moon')).toBe(true);
    expect(e.arrive('earth')).toBe(false);
    expect(e.arrive('pluto')).toBe(false);
    expect(e.discoveries).toEqual(['ilex', 'earth', 'moon']);
    expect(e.unlocked).toEqual(['skyborne-flight', 'lunar-step']);
    // A restored record missing an unlock gains it on the next arrival there.
    e.reset(undefined, ['earth'], []);
    expect(e.arrive('earth')).toBe(true);
    expect([e.discoveries, e.unlocked]).toEqual([['earth'], ['skyborne-flight']]);
    e.reset();
    expect([e.discoveries, e.unlocked, e.dirty]).toEqual([[], [], false]);
  });

  it('keeps the relay survey on the Quiet System bodies', () => {
    expect(SURVEY_BODIES).toEqual(['ilex', 'vesper', 'cairn']);
    expect(Object.keys(new Expedition().state.inventory)).toEqual([...SURVEY_BODIES]);
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
    expect(next.step).toBe('survey');
  });
});

/** Everything a First Light chapter asks for on one body. */
function complete(e: Expedition, body: string): void {
  const c = FIRST_LIGHT.find((ch) => ch.body === body)!;
  e.arrive(body);
  e.reachRoute(c.route[c.route.length - 1].id);
  for (const t of c.scans) e.scan(t.id, null);
}

describe('First Light (L9a)', () => {
  beforeEach(() => setPlaySystem(SOL_M2_BODIES));
  afterEach(() => setPlaySystem(SYSTEM_BODY_IDS.quiet));

  it('runs Earth, the Moon and Mars with their powers and WORLDS route and scan ids', () => {
    expect(FIRST_LIGHT.map((c) => [c.body, c.power])).toEqual([['earth', 'skyborne-flight'], ['moon', 'lunar-step'], ['mars', 'redline']]);
    for (const c of FIRST_LIGHT) {
      const spec = SURVEY_SPECS[c.body];
      expect(c.route).toEqual(spec.route.map((r, i) => ({ id: `${c.body}:route:${i}`, label: r.label })));
      expect(c.scans).toEqual(spec.scans.map((t, i) => ({ id: `${c.body}:poi:${i}`, label: t.label })));
      expect([c.route.length, c.scans.length]).toEqual([3, 3]);
      for (const r of c.route) expect([isRouteId(r.id), isPoiId(r.id)]).toEqual([true, false]);
      for (const t of c.scans) expect([isRouteId(t.id), isPoiId(t.id)]).toEqual([false, true]);
    }
    // The same strings WORLDS builds for the mission sites (Moon and Mars need no dataset here).
    for (const id of ['moon', 'mars']) {
      const sites = computeSites(BODIES[id]);
      const c = FIRST_LIGHT.find((ch) => ch.body === id)!;
      expect(sites.route.map((r) => r.id)).toEqual(c.route.map((r) => r.id));
      expect(sites.scans.map((t) => t.id)).toEqual(c.scans.map((t) => t.id));
    }
    expect(firstLightInPlay()).toBe(true);
  });

  it('gives a body its own power only once an arrival unlocked it', () => {
    const e = new Expedition();
    expect(e.activePower('moon')).toBeNull();
    e.arrive('earth');
    expect(e.activePower('moon')).toBeNull(); // Earth's unlock is not the Moon's
    expect(e.activePower('earth')).toBe('skyborne-flight');
    e.arrive('moon');
    expect(e.activePower('moon')).toBe('lunar-step');
    expect(e.activePower('mars')).toBeNull(); // never another body's power
    e.arrive('mars');
    expect(e.activePower('mars')).toBe('redline');
    for (const id of ['ilex', 'sun', 'venus', 'pluto']) expect(e.activePower(id), id).toBeNull();
  });

  it('leads from Earth to the Moon to Mars, then to free exploration', () => {
    const e = new Expedition();
    expect(e.chapter()).toBe('earth');
    expect(e.objective(null)).toMatchObject({ step: 'travel', body: 'earth', target: null, title: 'Land on Earth' });
    expect(e.objective(null).detail).toMatch(/Skyborne Flight/);
    expect(e.objective('earth')).toMatchObject({ step: 'land', body: 'earth' });
    e.arrive('earth');
    expect(e.objective('earth')).toMatchObject({ step: 'route', body: 'earth', target: 'earth:route:0', title: 'Reach Tasman coast at Hokitika' });
    expect(e.objective('earth').detail).toMatch(/waypoint 1 of 3 · Hold Space to fly/);
    expect(e.objective('moon')).toMatchObject({ step: 'travel', body: 'earth', title: 'Return to Earth' });
    expect(e.objective('moon').detail).toBe('First Light continues there: 3 of 3 waypoints and 3 of 3 scans to go.');
    expect(e.reachRoute('earth:route:0')).toBe(true);
    expect(e.objective('earth').target).toBe('earth:route:1');
    // Skipping ahead marks the earlier waypoints too: the route never soft-locks.
    expect(e.reachRoute('earth:route:2')).toBe(true);
    expect(e.state.route).toEqual(['earth:route:0', 'earth:route:1', 'earth:route:2']);
    expect(e.routeDone('earth')).toBe(true);
    expect(e.objective('earth')).toMatchObject({ step: 'scan', target: 'earth:poi:0', title: 'Scan Aoraki / Mount Cook' });
    e.scan('earth:poi:1', null);
    e.scan('earth:poi:0', null);
    expect(e.objective('earth')).toMatchObject({ step: 'scan', target: 'earth:poi:2' });
    expect(e.objective(null).detail).toBe('First Light continues there: 1 of 3 scans to go.');
    expect(e.chapter()).toBe('earth');
    e.scan('earth:poi:2', null);
    expect(e.scansDone('earth')).toBe(true);
    expect(e.chapter()).toBe('moon');
    expect(e.objective('earth')).toMatchObject({ step: 'travel', body: 'moon', title: 'Land on the Moon' });
    expect(e.objective('earth').detail).toMatch(/Lunar Step/);
    complete(e, 'moon');
    expect(e.chapter()).toBe('mars');
    expect(e.objective('moon')).toMatchObject({ step: 'travel', body: 'mars', title: 'Land on Mars' });
    e.arrive('mars');
    expect(e.objective('mars')).toMatchObject({ step: 'route', target: 'mars:route:0' });
    expect(e.objective('mars').detail).toMatch(/Redline route/);
    complete(e, 'mars');
    expect(e.chapter()).toBeNull();
    expect(e.objective('mars')).toMatchObject({ step: 'free', body: null, target: null, title: 'First Light complete' });
    expect(e.unlocked).toEqual(['skyborne-flight', 'lunar-step', 'redline']);
  });

  it('is idempotent: repeating an arrival, a waypoint or a scan changes nothing', () => {
    const e = new Expedition();
    complete(e, 'earth');
    e.reachRoute('moon:route:1');
    e.dirty = false;
    const before = JSON.stringify([e.state, e.discoveries, e.unlocked]);
    expect(e.arrive('earth')).toBe(false);
    expect(e.reachRoute('earth:route:2')).toBe(false);
    expect(e.reachRoute('earth:route:0')).toBe(false);
    expect(e.reachRoute('moon:route:0')).toBe(false);
    expect(e.scan('earth:poi:1', null)).toEqual({ newObject: false, newSpecies: false });
    complete(e, 'earth');
    expect(JSON.stringify([e.state, e.discoveries, e.unlocked])).toBe(before);
    expect(e.dirty).toBe(false);
    expect(e.chapter()).toBe('moon');
    // Ids outside the grammar or the progression are ignored.
    for (const id of ['earth:route:3', 'earth:route:-1', 'pluto:route:0', 'ilex:route:0', 'earth:poi:0', 'earth:route:', 'route:0']) {
      expect(e.reachRoute(id), id).toBe(false);
    }
    expect(e.dirty).toBe(false);
  });

  it('counts progress made out of order (arriving at Mars first unlocks Redline at once)', () => {
    const e = new Expedition();
    expect(e.arrive('mars')).toBe(true);
    expect(e.unlocked).toEqual(['redline']);
    expect(e.activePower('mars')).toBe('redline');
    expect(e.chapter()).toBe('earth');
    expect(e.objective('mars')).toMatchObject({ step: 'travel', body: 'earth' });
    complete(e, 'mars');
    expect(e.chapter()).toBe('earth');
    complete(e, 'moon');
    expect(e.chapter()).toBe('earth');
    complete(e, 'earth');
    // Mars and the Moon were finished early: they count now, straight to free exploration.
    expect(e.chapter()).toBeNull();
    expect(e.objective(null).step).toBe('free');
    expect(e.unlocked).toEqual(['redline', 'lunar-step', 'skyborne-flight']);
    // A chapter is not done by its route and scans alone: its power must be unlocked by an arrival.
    const f = new Expedition();
    f.reachRoute('earth:route:2');
    for (const t of FIRST_LIGHT[0].scans) f.scan(t.id, null);
    expect(f.chapter()).toBe('earth');
    expect(f.objective('earth').step).toBe('land');
    f.arrive('earth');
    expect(f.chapter()).toBe('moon');
  });
});

describe('First Light outside Sol play', () => {
  it('keeps the Quiet survey objective while Earth, the Moon and Mars are not in play', () => {
    expect(BODY_IDS).toEqual(SYSTEM_BODY_IDS.quiet);
    expect(firstLightInPlay()).toBe(false);
    const e = new Expedition();
    complete(e, 'earth');
    expect(e.objective('ilex')).toEqual({
      title: 'Survey Ilex', detail: 'Collect a sample near the relay (E), then activate the relay.', body: 'ilex', step: 'survey', target: null,
    });
    expect(e.objective(null)).toMatchObject({ title: 'Survey Ilex', body: 'ilex', step: 'survey' });
    expect(e.collect('earth:sample:0')).toBe(false);
    expect(e.state.inventory).toEqual({ ilex: 0, vesper: 0, cairn: 0 });
  });
});
