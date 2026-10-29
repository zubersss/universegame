// Per-world ambience data. Proposed to move into `BodyDef.ambience` (owned by
// ATLAS); until then it lives here, keyed by body, with a neutral default so
// bodies without an entry still sound reasonable.

import { BODIES, type BodyId } from '../world/bodies';

export type GroundKind = 'soil' | 'sand' | 'rock' | 'ice' | 'salt' | 'moss';

export interface AmbienceProfile {
  /** Wind loudness scale (0 = still air); multiplied by air density. */
  wind: number;
  /** Wind band centre in still air (Hz); rises with flow. */
  windTone: number;
  /** Tonal centre of the sparse ambient tones (Hz). */
  tonic: number;
  /** Scale of the ambient tones (semitones above the tonic). */
  scale: readonly number[];
  /** Timbre of the ambient tones. */
  timbre: OscillatorType;
  /** Mean seconds between ambient tones. */
  toneGap: number;
  /** Default ground under foot. */
  ground: GroundKind;
}

const PENTA = [0, 2, 4, 7, 9, 12, 14] as const;

export const DEFAULT_AMBIENCE: AmbienceProfile = {
  wind: 1, windTone: 300, tonic: 220, scale: PENTA, timbre: 'triangle', toneGap: 16, ground: 'soil',
};

const PROFILES: Partial<Record<BodyId, AmbienceProfile>> = {
  ilex: DEFAULT_AMBIENCE,
  vesper: { wind: 1, windTone: 300, tonic: 196, scale: PENTA, timbre: 'triangle', toneGap: 16, ground: 'sand' },
  cairn: { wind: 0, windTone: 300, tonic: 261.6, scale: PENTA, timbre: 'sine', toneGap: 16, ground: 'rock' },
};

export function ambienceFor(id: BodyId): AmbienceProfile {
  return PROFILES[id] ?? DEFAULT_AMBIENCE;
}

/** Airless bodies switch the on-foot mix to suit sounds. */
export function isAirless(id: BodyId): boolean {
  return BODIES[id].atmosphere === null;
}

/** Footstep timbre per ground: filter, cutoff (Hz), decay (s), level. */
export interface StepTimbre {
  filter: BiquadFilterType;
  cutoff: number;
  decay: number;
  level: number;
}

export const STEPS: Readonly<Record<GroundKind, StepTimbre>> = {
  soil: { filter: 'lowpass', cutoff: 900, decay: 0.07, level: 1 },
  sand: { filter: 'highpass', cutoff: 1800, decay: 0.11, level: 1 },
  rock: { filter: 'lowpass', cutoff: 500, decay: 0.07, level: 1 },
  ice: { filter: 'bandpass', cutoff: 2600, decay: 0.05, level: 0.8 },
  salt: { filter: 'highpass', cutoff: 2400, decay: 0.08, level: 0.9 },
  moss: { filter: 'lowpass', cutoff: 420, decay: 0.09, level: 0.8 },
};
