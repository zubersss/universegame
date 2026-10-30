// Ability contracts (charter section I): AbilityState lives inside ON_FOOT;
// AbilityConfig describes one power as a primitive plus parameters. PLAYER
// owns both; HUD, saves and audio consume them. Four primitives only
// (charter K); variants are parameter sets plus small rule hooks.

/** The four movement primitives. */
export type Primitive = 'flight' | 'speed' | 'blink' | 'drift';
export const PRIMITIVES: readonly Primitive[] = ['flight', 'speed', 'blink', 'drift'];

/** On-foot ability state: walking, or one primitive active. */
export type AbilityState = 'walk' | Primitive;
export const ABILITY_STATES: readonly AbilityState[] = ['walk', ...PRIMITIVES];

/** Power ids, spelled as WORLDS' BodyDef.power values. */
export type AbilityId =
  | 'skyborne-flight'
  | 'redline'
  | 'lunar-step'
  | 'sunline-dash'
  | 'pressure-glide'
  | 'anchor-blink'
  | 'wing-glide'
  | 'storm-lift'
  | 'ring-skate'
  | 'cold-drift'
  | 'gale-rider'
  | 'terminator-step';

/** What BodyDef.power holds: a power, 'walk' (explorable, no power) or null (no exploration). */
export type BodyPower = AbilityId | 'walk' | null;

/** One control line for the HUD and the journal: keys and what they do. */
export interface ControlLine {
  keys: string;
  action: string;
}

/** Flight primitive (Skyborne Flight; Pressure Glide and Wing Glide variants). Units: m, m/s, m/s², rad/s, s. */
export interface FlightParams {
  accel: number;
  cruise: number;
  boost: number;
  climb: number;
  brake: number;
  turn: number;
  /** Ceiling above the ground (m). */
  ceiling: number;
  /** Hold Space this long on the ground to take off (s). */
  takeoffHold: number;
  /** Landing: below this height above the ground (m) at less than landSpeed (m/s). */
  landHeight: number;
  landSpeed: number;
  /** Variants: unpowered glide ratio, powered-climb limit above ground (m), climb in thermals (m/s), speed per flap (m/s). */
  glideRatio?: number;
  poweredClimbMax?: number;
  thermalClimb?: number;
  flapImpulse?: number;
}

/** Speed primitive (Redline; Sunline Dash burst variant). */
export interface SpeedParams {
  accel: number;
  top: number;
  /** Yaw rate at low and at top speed (rad/s). */
  yawLow: number;
  yawHigh: number;
  maxSlopeDeg: number;
  brake: number;
  /** Collision lookahead: speed × lookaheadTime + lookaheadMargin (m). */
  lookaheadTime: number;
  lookaheadMargin: number;
  /** Burst variant: distance (m) in burstTime (s), charges, recharge per charge (s), overheat limit (s). */
  burstDistance?: number;
  burstTime?: number;
  charges?: number;
  recharge?: number;
  overheat?: number;
}

/** Blink primitive (Lunar Step; Anchor Blink variant). */
export interface BlinkParams {
  range: number;
  cooldown: number;
  /** Target must have ground within this distance below it (m), or be airborne within airborneWithin of ground. */
  groundWithin: number;
  airborneWithin: number;
  /** Anchor variant: long range to anchor points (m); surface friction. */
  anchorRange?: number;
  friction?: number;
}

/** Drift primitive (zones: Storm Lift, Ring Skate, Cold Drift, Gale Rider). */
export interface DriftParams {
  burst: number;
  /** Zone bubble radius (m), updraft (m/s), band speed (m/s), base drift (m/s). */
  bubbleRadius?: number;
  updraft?: number;
  bandSpeed?: number;
  drift?: number;
}

/** Player-facing feedback for a power (HUD, audio cue name, VFX style). */
export interface AbilityFeedback {
  hint: string;
  /** CSS colour for the HUD accent and VFX tint. */
  color: string;
  sound: string;
  vfx: string;
}

interface ConfigBase {
  id: AbilityId;
  /** Player-facing name. */
  name: string;
  /** Bodies or zones where the power is active (charter K: never elsewhere). */
  bodyIds: string[];
  controls: ControlLine[];
  feedback: AbilityFeedback;
  /** Milestone that delivers it (charter M). */
  milestone: 'M2' | 'M3' | 'M4';
}

export type AbilityConfig =
  /** Flight; the capstone variant (Terminator Step) also allows blinks while flying. */
  | (ConfigBase & { primitive: 'flight'; params: FlightParams; blinkInFlight?: BlinkParams })
  | (ConfigBase & { primitive: 'speed'; params: SpeedParams })
  | (ConfigBase & { primitive: 'blink'; params: BlinkParams })
  | (ConfigBase & { primitive: 'drift'; params: DriftParams });

/** Facts the transition rules need, sampled on the fixed step. */
export interface TransitionContext {
  grounded: boolean;
  /** Horizontal speed (m/s). */
  speed: number;
  /** The primitive of the power available here (null = none here). */
  primitiveHere: Primitive | null;
  /** That power has been unlocked. */
  unlocked: boolean;
  /** Inside the destination's zone (drift). */
  inZone: boolean;
}

/** Highest speed at which superspeed may hand back to walking (m/s): the sprint speed. */
export const SPEED_EXIT_MAX = 7.5;

/**
 * Charter J transition rules. Powers start only from walking, only where
 * their primitive is the local power and only once unlocked. Flight ends
 * only on the ground (never mid-air); superspeed ends only after braking to
 * sprint speed; a blink resolves to walking on arrival; drift hands back
 * only on solid footing or on leaving the zone. Boarding deactivates powers
 * (it only happens on the ground). Returns null when allowed, else the reason.
 */
export function transitionBlocked(from: AbilityState, to: AbilityState, c: TransitionContext): string | null {
  if (from === to) return null;
  if (to !== 'walk') {
    if (from !== 'walk') return 'one power at a time';
    if (c.primitiveHere !== to) return 'not available here';
    if (!c.unlocked) return 'not unlocked yet';
    if (to === 'speed' && !c.grounded) return 'needs ground';
    if (to === 'flight' && !c.grounded) return 'take off from the ground';
    if (to === 'drift' && !c.inZone) return 'outside the zone';
    return null;
  }
  switch (from) {
    case 'flight':
      return c.grounded ? null : 'flight never ends mid-air';
    case 'speed':
      return c.speed <= SPEED_EXIT_MAX + 1e-6 ? null : 'brake first';
    case 'drift':
      return c.grounded || !c.inZone ? null : 'still drifting';
    case 'blink':
      return null;
    default:
      return null;
  }
}

export function isAbilityState(x: unknown): x is AbilityState {
  return typeof x === 'string' && (ABILITY_STATES as readonly string[]).includes(x);
}
