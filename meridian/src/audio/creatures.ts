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
  // Chalk skein: paper gliders. A papery flutter with a faint whistle; a sharp flutter burst; no footfalls.
  'ilex-skein': {
    call: [
      { src: 'noise', freq: 3000, q: 2, peak: 0.02, attack: 0.004, decay: 0.03, repeat: 5, every: 0.035 },
      { src: 'sine', freq: 2200, glide: 2500, peak: 0.006, attack: 0.08, decay: 0.5, delay: 0.1 },
    ],
    alarm: [{ src: 'noise', freq: 3400, q: 2, peak: 0.035, attack: 0.003, decay: 0.025, repeat: 10, every: 0.025 }],
    step: [],
  },
  // Ochre sounder: burrower. A muffled thump from under the crust; a hiss of sand as it sinks.
  'ilex-sounder': {
    call: [
      { src: 'sine', freq: 50, peak: 0.05, attack: 0.01, decay: 0.3 },
      { src: 'noise', freq: 150, filter: 'lowpass', q: 0.7, peak: 0.03, attack: 0.01, decay: 0.25 },
    ],
    alarm: [{ src: 'noise', freq: 3500, filter: 'highpass', q: 0.7, peak: 0.03, attack: 0.05, decay: 0.7 }],
    step: [],
  },
  // Dune sledge: plated dragger. A low grinding bellow; a huff of sand; a long drag per pull.
  'vesper-sledge': {
    call: [
      { src: 'sawtooth', freq: 66, glide: 55, peak: 0.018, attack: 0.3, decay: 1.6 },
      { src: 'noise', freq: 180, filter: 'lowpass', q: 1, peak: 0.03, attack: 0.25, decay: 1.4 },
    ],
    alarm: [{ src: 'noise', freq: 2000, filter: 'highpass', q: 0.7, peak: 0.05, attack: 0.01, decay: 0.3 }],
    step: [{ src: 'noise', freq: 900, q: 1, peak: 0.04, attack: 0.03, decay: 0.28 }],
  },
  // Mesa kite: a thin descending whistle, doubled when startled.
  'vesper-kite': {
    call: [{ src: 'sine', freq: 1800, glide: 1100, peak: 0.02, attack: 0.05, decay: 1.2 }],
    alarm: [{ src: 'sine', freq: 2000, glide: 1500, peak: 0.025, attack: 0.02, decay: 0.3, repeat: 2, every: 0.35 }],
    step: [],
  },
  // Glass tick: clicks like cooling glass; a rising burst of them when the colony scatters.
  'vesper-tick': {
    call: [{ src: 'noise', freq: 4500, q: 12, peak: 0.012, attack: 0.002, decay: 0.012, repeat: 4, every: 0.11 }],
    alarm: [{ src: 'noise', freq: 4000, glide: 6000, q: 10, peak: 0.02, attack: 0.002, decay: 0.01, repeat: 8, every: 0.03 }],
    step: [{ src: 'noise', freq: 5000, q: 8, peak: 0.004, attack: 0.002, decay: 0.008 }],
  },
  // Fog wader: a long falling hoot; a double hoot before it leaves; wet, slow footfalls.
  'orrin-wader': {
    call: [{ src: 'sine', freq: 260, glide: 180, peak: 0.03, attack: 0.2, decay: 1.6 }],
    alarm: [{ src: 'sine', freq: 300, glide: 220, peak: 0.035, attack: 0.08, decay: 0.45, repeat: 2, every: 0.5 }],
    step: [
      { src: 'noise', freq: 400, filter: 'lowpass', q: 1.2, peak: 0.035, attack: 0.01, decay: 0.15 },
      { src: 'sine', freq: 70, peak: 0.015, attack: 0.01, decay: 0.1 },
    ],
  },
  // Column drifter: a very low breathing drone; no footfalls.
  'orrin-drifter': {
    call: [
      { src: 'noise', freq: 120, filter: 'lowpass', q: 0.8, peak: 0.025, attack: 1.2, decay: 2.5 },
      { src: 'sine', freq: 41, peak: 0.02, attack: 1.2, decay: 2.5 },
    ],
    alarm: [{ src: 'noise', freq: 140, filter: 'lowpass', q: 0.8, peak: 0.03, attack: 0.4, decay: 1 }],
    step: [],
  },
  // Moss creeper: a brief chitter when disturbed; a soft rustling patter while it moves.
  'orrin-creeper': {
    call: [{ src: 'noise', freq: 4200, q: 6, peak: 0.006, attack: 0.002, decay: 0.015, repeat: 3, every: 0.04 }],
    alarm: [{ src: 'noise', freq: 5000, q: 6, peak: 0.012, attack: 0.002, decay: 0.015, repeat: 5, every: 0.02 }],
    step: [{ src: 'noise', freq: 3000, filter: 'highpass', q: 0.7, peak: 0.008, attack: 0.002, decay: 0.03 }],
  },
  // Brine skater: a tiny ticking skitter; a rapid burst when the group scatters.
  'saro-skater': {
    call: [{ src: 'noise', freq: 6000, q: 8, peak: 0.006, attack: 0.002, decay: 0.012, repeat: 2, every: 0.06 }],
    alarm: [{ src: 'noise', freq: 6000, q: 8, peak: 0.015, attack: 0.002, decay: 0.012, repeat: 9, every: 0.02 }],
    step: [{ src: 'noise', freq: 6000, q: 8, peak: 0.005, attack: 0.002, decay: 0.015 }],
  },
  // Crust tilter: a faint metallic creak as the plate turns; a soft salt crunch underfoot.
  'saro-tilter': {
    call: [
      { src: 'triangle', freq: 520, glide: 480, peak: 0.01, attack: 0.15, decay: 0.8 },
      { src: 'noise', freq: 1500, q: 15, peak: 0.012, attack: 0.1, decay: 0.7 },
    ],
    alarm: [{ src: 'triangle', freq: 560, glide: 470, peak: 0.014, attack: 0.05, decay: 0.35 }],
    step: [{ src: 'noise', freq: 2400, filter: 'highpass', q: 0.7, peak: 0.025, attack: 0.004, decay: 0.06 }],
  },
  // Salt veil: a very high, faint shimmer (two close tones beating); no footfalls.
  'saro-veil': {
    call: [
      { src: 'sine', freq: 5200, peak: 0.004, attack: 0.5, decay: 1.5 },
      { src: 'sine', freq: 5230, peak: 0.004, attack: 0.5, decay: 1.5 },
    ],
    alarm: [{ src: 'sine', freq: 5400, glide: 5800, peak: 0.006, attack: 0.1, decay: 0.4 }],
    step: [],
  },
};

export function creatureVoice(speciesId: string): CreatureVoice {
  return VOICES[speciesId] ?? DEFAULT_CREATURE;
}

/** Creature sounds beyond this distance (m) are not played. */
export const CREATURE_RANGE = 120;
/** At most this many creature voices (layers and repeats count singly) sound at once (inside the global cap). */
export const CREATURE_VOICE_CAP = 12;
