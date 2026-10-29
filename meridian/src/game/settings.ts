import type { QualityPreset } from './config';

export interface Settings {
  preset: QualityPreset;
  adaptive: boolean;
  sensitivity: number;
  invertY: boolean;
  volume: number;
  reducedMotion: boolean;
}

export const DEFAULT_SETTINGS: Settings = {
  preset: 'balanced',
  adaptive: true,
  sensitivity: 1,
  invertY: false,
  volume: 0.8,
  reducedMotion: false,
};

const finite = (x: unknown, lo: number, hi: number, d: number): number =>
  typeof x === 'number' && Number.isFinite(x) ? Math.min(hi, Math.max(lo, x)) : d;

/** Validate untrusted settings data, falling back to defaults per field. */
export function sanitizeSettings(raw: unknown): Settings {
  const s = (raw && typeof raw === 'object' ? raw : {}) as Record<string, unknown>;
  const preset = s.preset === 'low' || s.preset === 'balanced' || s.preset === 'high' ? s.preset : DEFAULT_SETTINGS.preset;
  return {
    preset,
    adaptive: typeof s.adaptive === 'boolean' ? s.adaptive : DEFAULT_SETTINGS.adaptive,
    sensitivity: finite(s.sensitivity, 0.2, 3, DEFAULT_SETTINGS.sensitivity),
    invertY: typeof s.invertY === 'boolean' ? s.invertY : DEFAULT_SETTINGS.invertY,
    volume: finite(s.volume, 0, 1, DEFAULT_SETTINGS.volume),
    reducedMotion: typeof s.reducedMotion === 'boolean' ? s.reducedMotion : DEFAULT_SETTINGS.reducedMotion,
  };
}
