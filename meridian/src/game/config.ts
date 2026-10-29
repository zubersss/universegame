// All tunable gameplay/engine constants live here.

export const SIM_HZ = 60;
export const SIM_DT = 1 / SIM_HZ;
export const MAX_STEPS_PER_FRAME = 4;
/** Incoming frame gaps are clamped to this (seconds). */
export const MAX_FRAME_GAP = 0.25;

export const REBASE_DISTANCE = 2048;
export const REBASE_ROUND = 1024;

export const FLIGHT = {
  mass: 16000,
  tauAtmo: 1.0,
  tauSpace: 3.0,
  tauBrake: 0.35,
  k1: 0.002,
  k2: 0.00002,
  accelAtmo: 35,
  brakeAtmo: 70,
  accelSpace: 100,
  brakeSpace: 250,
  capLow: 120,
  capAtmo: 350,
  capAtmoBoost: 600,
  capSpace: 900,
  capSpaceBoost: 1800,
  lowClearance: 500,
  atmoBlendClearance: 1500,
  boostMinClearance: 1000,
  /** Commanded body-local angular rates (rad/s). */
  pitchRate: 1.0,
  yawRate: 0.75,
  rollRate: 1.3,
  angTau: 0.18,
  /** Vertical (Space/Ctrl) target speeds. */
  verticalSpeedLow: 18,
  verticalSpeedAtmo: 60,
  verticalSpeedSpace: 150,
  throttleRate: 0.55,
  /** Mouse virtual-stick recentering time constant (s). */
  stickTau: 0.22,
  stickGain: 0.0045,
  /** Gear deploys below this clearance (m). */
  gearClearance: 70,
} as const;

export const CRUISE = {
  maxSpeed: 15000,
  accel: 5000,
  turnRate: 0.15,
  envelopeMargin: 10000,
  exitSpeed: 900,
  safetyMargin: 1500,
} as const;

export const LANDING = {
  engageAltitude: 50,
  engageSpeed: 25,
  maxSlopeDeg: 12,
  maxTangential: 3,
  maxDescent: 2,
  stableTime: 0.3,
  descentFar: 5,
  descentNear: 1.4,
  contactTolerance: 0.12,
  holdAltitude: 7,
} as const;

export const WALK = {
  height: 1.8,
  radius: 0.35,
  skin: 0.02,
  step: 0.3,
  maxSlopeDeg: 45,
  walk: 4.5,
  sprint: 7.5,
  jump: 5,
  eye: 1.62,
  accel: 30,
  airAccel: 6,
  snap: 0.3,
  boardDistance: 7,
  interactDistance: 3.2,
} as const;

export const CAMERA = {
  chaseBack: 14,
  chaseUp: 5,
  /** Distance ahead of the ship the chase camera looks at (m). */
  lookAhead: 30,
  posK: 7,
  rotK: 9,
  fov: 70,
  boostFov: 78,
  near: 0.1,
} as const;

export const SCAN = {
  range: 40,
  holdTime: 1.2,
  coneDeg: 4,
} as const;

export const BODY_HANDOFF = {
  activateRadii: 3,
  releaseRadii: 4,
} as const;

export type QualityPreset = 'low' | 'balanced' | 'high';

export interface PresetSpec {
  maxWidth: number;
  maxHeight: number;
  splitPx: number;
  maxChunks: number;
  shadowSize: number;
  bloom: boolean;
  composer: boolean;
  skySamples: number;
  aerialSamples: number;
  propDensity: number;
  propRange: number;
  cloudQuality: number;
  triplanarDetail: boolean;
}

export const PRESETS: Record<QualityPreset, PresetSpec> = {
  low: {
    maxWidth: 1280, maxHeight: 720, splitPx: 6, maxChunks: 96, shadowSize: 1024,
    bloom: false, composer: false, skySamples: 8, aerialSamples: 3,
    propDensity: 0.55, propRange: 0.7, cloudQuality: 0, triplanarDetail: false,
  },
  balanced: {
    maxWidth: 1600, maxHeight: 900, splitPx: 4, maxChunks: 160, shadowSize: 2048,
    bloom: true, composer: true, skySamples: 12, aerialSamples: 4,
    propDensity: 1, propRange: 1, cloudQuality: 1, triplanarDetail: true,
  },
  high: {
    maxWidth: 1920, maxHeight: 1080, splitPx: 2.5, maxChunks: 240, shadowSize: 2048,
    bloom: true, composer: true, skySamples: 16, aerialSamples: 6,
    propDensity: 1.25, propRange: 1.3, cloudQuality: 2, triplanarDetail: true,
  },
};

export const BUDGETS = {
  /** Main-thread terrain integration (uploads + collider installs) per frame, ms. */
  uploadMsPerFrame: 2,
  maxQueuedJobs: 8,
  maxInFlightJobs: 3,
  chunkCacheBytes: 64 * 1024 * 1024,
  maxTerrainColliders: 48,
  maxPropColliders: 128,
  autosaveSeconds: 30,
} as const;
