import type { AbilityConfig, AbilityId, BodyPower, FlightParams } from './types';

// Every power as data: primitive, where it is active, controls, starting
// tunables (charter section K; changes are recorded in the commit that makes
// them) and feedback. Only data lives here; behaviour is in the primitives.

const FLIGHT: FlightParams = {
  accel: 25,
  cruise: 90,
  boost: 220,
  climb: 30,
  brake: 60,
  turn: 1.5,
  ceiling: 2000,
  takeoffHold: 0.6,
  landHeight: 1.5,
  landSpeed: 4,
};

const BLINK_CONTROLS = [
  { keys: 'Hold right mouse', action: 'preview the target' },
  { keys: 'Q or left click', action: 'step to it' },
];

const DRIFT_CONTROLS = [
  { keys: 'W A S D', action: 'thruster bursts' },
  { keys: 'X', action: 'dampers' },
];

export const ABILITIES: Readonly<Record<AbilityId, AbilityConfig>> = {
  'skyborne-flight': {
    id: 'skyborne-flight',
    name: 'Skyborne Flight',
    primitive: 'flight',
    bodyIds: ['earth'],
    milestone: 'M2',
    controls: [
      { keys: 'Hold Space', action: 'take off' },
      { keys: 'Space / Ctrl', action: 'climb / descend' },
      { keys: 'W / S', action: 'speed up / slow down' },
      { keys: 'Shift', action: 'boost' },
      { keys: 'X', action: 'brake to a hover' },
      { keys: 'Descend slowly', action: 'land' },
    ],
    params: FLIGHT,
    feedback: { hint: 'Hold Space to fly', color: '#7fd3ff', sound: 'flight', vfx: 'contrails' },
  },
  redline: {
    id: 'redline',
    name: 'Redline',
    primitive: 'speed',
    bodyIds: ['mars'],
    milestone: 'M2',
    controls: [
      { keys: 'Hold Q', action: 'run at superspeed (on the ground)' },
      { keys: 'Mouse', action: 'steer' },
      { keys: 'X or release Q', action: 'brake' },
    ],
    params: { accel: 40, top: 110, yawLow: 3, yawHigh: 0.8, maxSlopeDeg: 35, brake: 50, lookaheadTime: 2, lookaheadMargin: 50 },
    feedback: { hint: 'Hold Q to run', color: '#ff7a3d', sound: 'redline', vfx: 'speed lines' },
  },
  'lunar-step': {
    id: 'lunar-step',
    name: 'Lunar Step',
    primitive: 'blink',
    bodyIds: ['moon'],
    milestone: 'M2',
    controls: BLINK_CONTROLS,
    params: { range: 60, cooldown: 1.2, groundWithin: 2, airborneWithin: 3 },
    feedback: { hint: 'Right mouse to aim, Q to step', color: '#c8b6ff', sound: 'blink', vfx: 'blink flash' },
  },
  'sunline-dash': {
    id: 'sunline-dash',
    name: 'Sunline Dash',
    primitive: 'speed',
    bodyIds: ['mercury'],
    milestone: 'M3',
    controls: [{ keys: 'Q', action: 'dash 15 m (3 charges, recharge in shadow)' }],
    params: { accel: 240, top: 60, yawLow: 3, yawHigh: 1.5, maxSlopeDeg: 35, brake: 120, lookaheadTime: 0.5, lookaheadMargin: 20, burstDistance: 15, burstTime: 0.25, charges: 3, recharge: 1, overheat: 60 },
    feedback: { hint: 'Q to dash', color: '#ffd166', sound: 'dash', vfx: 'heat shimmer' },
  },
  'pressure-glide': {
    id: 'pressure-glide',
    name: 'Pressure Glide',
    primitive: 'flight',
    bodyIds: ['venus'],
    milestone: 'M3',
    controls: [
      { keys: 'Hold Space', action: 'take off' },
      { keys: 'W / S', action: 'speed up / slow down' },
      { keys: 'Ctrl', action: 'descend' },
    ],
    params: { ...FLIGHT, accel: 12, cruise: 45, boost: 70, climb: 8, brake: 40, turn: 1.2, ceiling: 600, glideRatio: 8, poweredClimbMax: 250, thermalClimb: 8 },
    feedback: { hint: 'Hold Space to glide', color: '#ffb36b', sound: 'glide', vfx: 'pressure wake' },
  },
  'anchor-blink': {
    id: 'anchor-blink',
    name: 'Anchor Blink',
    primitive: 'blink',
    bodyIds: ['europa'],
    milestone: 'M3',
    controls: BLINK_CONTROLS,
    params: { range: 40, cooldown: 1.2, groundWithin: 2, airborneWithin: 3, anchorRange: 140, friction: 0.1 },
    feedback: { hint: 'Right mouse to aim; anchors reach farther', color: '#9be7ff', sound: 'blink', vfx: 'ice flash' },
  },
  'wing-glide': {
    id: 'wing-glide',
    name: 'Wing Glide',
    primitive: 'flight',
    bodyIds: ['titan'],
    milestone: 'M3',
    controls: [
      { keys: 'Space', action: 'flap' },
      { keys: 'W / S', action: 'speed up / slow down' },
    ],
    params: { ...FLIGHT, accel: 10, cruise: 35, boost: 50, climb: 6, brake: 30, turn: 1.4, ceiling: 400, flapImpulse: 6 },
    feedback: { hint: 'Space to flap', color: '#ffcf8a', sound: 'wings', vfx: 'wing trails' },
  },
  'storm-lift': {
    id: 'storm-lift',
    name: 'Storm Lift',
    primitive: 'drift',
    bodyIds: ['jupiter'],
    milestone: 'M3',
    controls: [...DRIFT_CONTROLS, { keys: 'Updrafts', action: 'ride them upward' }],
    params: { burst: 12, bubbleRadius: 6000, updraft: 15 },
    feedback: { hint: 'Bursts to steer, X to damp', color: '#f2c38b', sound: 'storm', vfx: 'lightning glow' },
  },
  'ring-skate': {
    id: 'ring-skate',
    name: 'Ring Skate',
    primitive: 'drift',
    bodyIds: ['saturn'],
    milestone: 'M3',
    controls: DRIFT_CONTROLS,
    params: { burst: 20, bubbleRadius: 8000 },
    feedback: { hint: 'Bursts to skate, X to damp', color: '#e8dcb5', sound: 'skate', vfx: 'ice spray' },
  },
  'cold-drift': {
    id: 'cold-drift',
    name: 'Cold Drift',
    primitive: 'drift',
    bodyIds: ['uranus'],
    milestone: 'M3',
    controls: [{ keys: 'W A S D', action: 'long bursts' }],
    params: { burst: 10, drift: 8 },
    feedback: { hint: 'Long bursts to cross', color: '#a8f0ee', sound: 'drift', vfx: 'crystal haze' },
  },
  'gale-rider': {
    id: 'gale-rider',
    name: 'Gale Rider',
    primitive: 'drift',
    bodyIds: ['neptune'],
    milestone: 'M3',
    controls: [{ keys: 'W A S D', action: 'bursts across the jet bands' }],
    params: { burst: 14, bandSpeed: 60 },
    feedback: { hint: 'Burst across the bands', color: '#6f9bff', sound: 'gale', vfx: 'band streaks' },
  },
  'terminator-step': {
    id: 'terminator-step',
    name: 'Terminator Step',
    primitive: 'flight',
    bodyIds: ['proxima-b'],
    milestone: 'M4',
    controls: [
      { keys: 'Hold Space', action: 'take off' },
      { keys: 'Right mouse, Q', action: 'blink, also in flight' },
    ],
    params: FLIGHT,
    blinkInFlight: { range: 60, cooldown: 1.2, groundWithin: 2, airborneWithin: 3 },
    feedback: { hint: 'Fly the terminator; blink anywhere', color: '#ff9f7f', sound: 'flight', vfx: 'contrails' },
  },
};

export function isAbilityId(x: unknown): x is AbilityId {
  return typeof x === 'string' && Object.prototype.hasOwnProperty.call(ABILITIES, x);
}

/** The power a body offers, from its BodyDef.power when present (WORLDS, W2), else walking only. */
export function bodyPower(def: { id: string; power?: unknown }): BodyPower {
  const p = def.power;
  if (p === null) return null;
  if (p === 'walk' || isAbilityId(p)) return p;
  return 'walk';
}

/** The power config active on a body, or null (walking only, or no exploration). */
export function abilityFor(power: BodyPower): AbilityConfig | null {
  return power && power !== 'walk' ? ABILITIES[power] : null;
}
