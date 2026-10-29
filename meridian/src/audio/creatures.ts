// Synthesis recipes for fauna sound events, keyed by species id. Species
// without an entry use DEFAULT_CREATURE. Recipes are data: GameAudio plays
// them as pooled voices through a per-voice equal-power panner.

export type CreatureEvent = 'call' | 'alarm' | 'step';

/** One layer of a creature sound. */
export interface CreatureLayer {
  /** 'noise' = filtered noise burst; otherwise an oscillator of that type. */
  src: 'noise' | OscillatorType;
  /** Oscillator pitch or noise filter centre (Hz). */
  freq: number;
  /** Optional pitch/filter glide target over the layer (Hz). */
  glide?: number;
  /** Noise filter (default bandpass) and its Q. */
  filter?: BiquadFilterType;
  q?: number;
  peak: number;
  attack: number;
  decay: number;
  /** Start offset (s). */
  delay?: number;
  /** Repeat this many times, `every` seconds apart (rattles, knocks). */
  repeat?: number;
  every?: number;
}

export type CreatureVoice = Readonly<Record<CreatureEvent, readonly CreatureLayer[]>>;

export const DEFAULT_CREATURE: CreatureVoice = {
  call: [{ src: 'sine', freq: 330, glide: 290, peak: 0.03, attack: 0.15, decay: 0.9 }],
  alarm: [{ src: 'noise', freq: 1600, q: 3, peak: 0.05, attack: 0.004, decay: 0.05, repeat: 3, every: 0.07 }],
  step: [{ src: 'noise', freq: 260, filter: 'lowpass', q: 0.8, peak: 0.04, attack: 0.004, decay: 0.06 }],
};

const VOICES: Readonly<Record<string, CreatureVoice>> = {
  // Grove trine: tall tripedal grazer. A hollow chalky knock answered by a low
  // drone; a dry clacking rattle when it bolts; soft thuds in threes.
  'ilex-trine': {
    call: [
      { src: 'noise', freq: 310, q: 9, peak: 0.07, attack: 0.004, decay: 0.16, repeat: 2, every: 0.32 },
      { src: 'triangle', freq: 98, glide: 92, peak: 0.028, attack: 0.35, decay: 2.2, delay: 0.55 },
      { src: 'sine', freq: 147, glide: 139, peak: 0.01, attack: 0.5, decay: 1.8, delay: 0.7 },
    ],
    alarm: [{ src: 'noise', freq: 1900, q: 4, peak: 0.06, attack: 0.003, decay: 0.035, repeat: 6, every: 0.045 }],
    step: [
      { src: 'noise', freq: 220, filter: 'lowpass', q: 0.9, peak: 0.05, attack: 0.004, decay: 0.07 },
      { src: 'sine', freq: 62, peak: 0.03, attack: 0.004, decay: 0.08 },
    ],
  },
};

export function creatureVoice(speciesId: string): CreatureVoice {
  return VOICES[speciesId] ?? DEFAULT_CREATURE;
}

/** Creature sounds beyond this distance (m) are not played. */
export const CREATURE_RANGE = 120;
/** At most this many creature voices (layers and repeats count singly) sound at once (inside the global cap). */
export const CREATURE_VOICE_CAP = 12;
