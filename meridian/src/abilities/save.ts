// Ability fields of the schema-2 save (charter I: player.abilityState and
// the top-level unlocked list). Three-free so SaveSystem can import it in
// Node tests.

import { isAbilityId } from './catalog';
import { isAbilityState, type AbilityId, type AbilityState } from './types';

export { isAbilityId };
export type { AbilityId, AbilityState };

/** Ability fields of the schema-2 save. */
export interface AbilitySave {
  abilityState: AbilityState;
  unlocked: AbilityId[];
}

/** Most powers there are (cap for the unlocked list). */
export const MAX_UNLOCKED = 12;

/**
 * Strict validator for the schema-2 ability fields (player.abilityState,
 * null when not on foot, and the top-level unlocked list), for SaveSystem's
 * validateSave: returns the fields, or an error string for a malformed
 * record (which then never rotates over the previous good backup).
 */
export function validateAbilityFields(abilityState: unknown, unlocked: unknown): AbilitySave | string {
  if (abilityState !== null && abilityState !== undefined && !isAbilityState(abilityState)) return 'player.abilityState is not an ability state';
  if (!Array.isArray(unlocked)) return 'unlocked is not a list';
  if (unlocked.length > MAX_UNLOCKED) return 'unlocked is too long';
  for (const id of unlocked) if (!isAbilityId(id)) return `unlocked has an unknown power: ${String(id).slice(0, 40)}`;
  if (new Set(unlocked).size !== unlocked.length) return 'unlocked has duplicates';
  return { abilityState: (abilityState ?? 'walk') as AbilityState, unlocked: [...(unlocked as AbilityId[])] };
}

/**
 * Lenient reader for ability fields that were already validated (or come
 * from an older record): unknown power ids are dropped; a missing or invalid
 * state reads as walking. Which saved states resume is the controller's rule
 * (flight hovers where it was saved, superspeed resumes braking, others walk).
 */
export function readAbilitySave(raw: unknown): AbilitySave {
  const r = (raw ?? {}) as { abilityState?: unknown; unlocked?: unknown };
  const unlocked = Array.isArray(r.unlocked) ? [...new Set(r.unlocked.filter(isAbilityId))] : [];
  return { abilityState: isAbilityState(r.abilityState) ? r.abilityState : 'walk', unlocked };
}
