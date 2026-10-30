import { BODIES, BODY_IDS, GENERATOR_VERSION, SYSTEM_BODY_IDS, SYSTEM_EXTENT, WORLD_SEED, isBodyId, type BodyId, type SystemId } from '../world/bodies';
import { cruiseMaxSpeed } from '../world/scale';
import { sanitizeSettings, type Settings } from '../game/settings';
import { BODY_HANDOFF } from '../game/config';
import { ROUTE_POINTS, SURVEY_BODIES, isPoiId, isRouteId, newExpedition, powerFor, type ExpeditionState } from '../game/Expedition';
import { validateAbilityFields, type AbilityId, type AbilityState } from '../abilities/save';
import type { KvStore } from './db';

// Save format (schema 2, charter section I): only the seed, versions, the
// system, poses/velocities, mode, settings and progress (arrivals, unlocks,
// ability state, survey and First Light). Terrain, meshes and physics are
// regenerated. A record from an older schema is kept read-only under
// LEGACY_KEY and never migrated (positions do not carry across scales).

/** The schema this build writes. LEAD's constant; bodies.ts SAVE_SCHEMA_VERSION is no longer read. */
export const SAVE_SCHEMA = 2;

export type V3 = [number, number, number];
export type V4 = [number, number, number, number];
export type SaveMode = 'PILOTING' | 'CRUISING' | 'LANDED' | 'ON_FOOT';

export interface SaveData {
  schema: typeof SAVE_SCHEMA;
  generator: number;
  seed: number;
  savedAt: string;
  playTime: number;
  /** The star system every body id in the record belongs to (the one in play). */
  system: SystemId;
  mode: SaveMode;
  /** Active body for LANDED/ON_FOOT (and flight near a body); null in open space. */
  bodyId: BodyId | null;
  ship: { sys: V3; quat: V4; vel: V3; gear: number; throttle: number };
  /** abilityState: PLAYER's on-foot ability state (a record written before P2 holds null, read as 'walk'). */
  player: { sys: V3; heading: V3; pitch: number; abilityState: AbilityState } | null;
  cruise: { speed: number; throttle: number } | null;
  lastSafeLanding: { bodyId: BodyId; posPlanet: V3; quat: V4 } | null;
  navTarget: BodyId | null;
  /** Bodies arrived at (landed on), in arrival order. */
  discoveries: BodyId[];
  /** Powers those arrivals unlocked: PLAYER's AbilityIds that are some catalog body's power (never 'walk'). */
  unlocked: AbilityId[];
  settings: Settings;
  expedition: ExpeditionState;
}

export const SAVE_KEY = 'save';
export const PREV_KEY = 'save-prev';
export const CORRUPT_KEY = 'save-corrupt';
export const LEGACY_KEY = 'save-legacy';

/** Largest plausible distance from the system origin (m). */
const MAX_COORD = SYSTEM_EXTENT;
/** Ship speed outside cruise (m/s). */
const MAX_FLIGHT_SPEED = 20000;
/** Cruise speed: the cap of the longest possible hop (m/s). */
const MAX_CRUISE_SPEED = cruiseMaxSpeed(2 * SYSTEM_EXTENT);
/** Every power an arrival can unlock (catalog powers except the base 'walk'). */
const POWERS: ReadonlySet<AbilityId> = new Set(Object.keys(BODIES).map((id) => powerFor(id)).filter((p): p is AbilityId => p !== null));

type Result = { ok: true; data: SaveData } | { ok: false; error: string };

const isObj = (x: unknown): x is Record<string, unknown> => typeof x === 'object' && x !== null && !Array.isArray(x);
const isNum = (x: unknown): x is number => typeof x === 'number' && Number.isFinite(x);
const isSystem = (x: unknown): x is SystemId => typeof x === 'string' && Object.prototype.hasOwnProperty.call(SYSTEM_BODY_IDS, x);
/** Saves name only the bodies in play (BODY_IDS), not every catalog body; saves across systems (L15) widen this. */
const isPlayed = (x: unknown): x is BodyId => typeof x === 'string' && (BODY_IDS as readonly string[]).includes(x);
/** The system in play (BODY_IDS is one system's bodies; read at call time). */
const playedSystem = (): SystemId => BODIES[BODY_IDS[0]].system;
/** A played body the ship can set down on or enter. */
const isLandable = (x: unknown): x is BodyId => isPlayed(x) && BODIES[x].explore !== 'none';

function vec(x: unknown, n: number, bound: number): number[] | null {
  if (!Array.isArray(x) || x.length !== n) return null;
  for (const v of x) if (!isNum(v) || Math.abs(v) > bound) return null;
  return x as number[];
}

const len = (v: readonly number[]): number => Math.hypot(v[0], v[1], v[2]);

/** Never deeper than half the radius: no surface pose lies near a body's core. */
const MIN_SURFACE_RADII = 0.5;

/** Within the body's release radius (BODY_HANDOFF.releaseRadii × R) of its center, and not near its core. */
function nearBody(p: readonly number[], id: BodyId): boolean {
  const d = BODIES[id];
  const r = Math.hypot(p[0] - d.center[0], p[1] - d.center[1], p[2] - d.center[2]);
  return r >= MIN_SURFACE_RADII * d.radius && r <= BODY_HANDOFF.releaseRadii * d.radius;
}

function unitQuat(x: unknown): V4 | null {
  const q = vec(x, 4, 1.01);
  if (!q) return null;
  const l = Math.hypot(q[0], q[1], q[2], q[3]);
  return Math.abs(l - 1) < 1e-3 ? (q as V4) : null;
}

function stringList(x: unknown, valid: (s: string) => boolean, max: number): string[] | null {
  if (!Array.isArray(x) || x.length > max) return null;
  const seen = new Set<string>();
  for (const s of x) {
    if (typeof s !== 'string' || s.length > 120 || !valid(s) || seen.has(s)) return null;
    seen.add(s);
  }
  return x as string[];
}

const SAMPLE_RE = /^(ilex|vesper|cairn):sample:[0-2]$/;
const OBJECT_RE = /^(ilex|vesper|cairn):[a-z0-9:/_-]+$/;
const SPECIES_RE = /^(ilex|vesper|cairn)-[a-z]+$/;

/**
 * The survey (inventory, samples, relays) is the Quiet System's, whatever
 * system is in play; First Light progress (waypoints, scan targets) is
 * history by id, like discoveries.
 */
function validateExpedition(x: unknown): ExpeditionState | string {
  if (!isObj(x)) return 'progress missing';
  const inv = x.inventory;
  if (!isObj(inv)) return 'inventory missing';
  const inventory = newExpedition().inventory;
  for (const b of SURVEY_BODIES) {
    const n = inv[b];
    if (!Number.isInteger(n) || (n as number) < 0 || (n as number) > 3) return `bad inventory count for ${b}`;
    inventory[b] = n as number;
  }
  const collected = stringList(x.collected, (s) => SAMPLE_RE.test(s), 9);
  if (!collected) return 'bad collected list';
  const relays = stringList(x.relays, (s) => SURVEY_BODIES.includes(s), 3);
  if (!relays) return 'bad relay list';
  const species = stringList(x.species, (s) => SPECIES_RE.test(s), 32);
  if (!species) return 'bad species list';
  const scanned = stringList(x.scanned, (s) => OBJECT_RE.test(s) || isPoiId(s), 5000);
  if (!scanned) return 'bad scan list';
  if (typeof x.transmitted !== 'boolean') return 'bad transmission flag';
  // Absent from schema-2 records written before First Light: no waypoint reached.
  const route = x.route === undefined ? [] : stringList(x.route, isRouteId, ROUTE_POINTS);
  if (!route) return 'bad route list';
  // Consistency: carried + spent samples per body never exceed what was collected there.
  for (const b of SURVEY_BODIES) {
    const got = collected.filter((s) => s.startsWith(`${b}:`)).length;
    const spent = relays.includes(b) ? 1 : 0;
    if (inventory[b] + spent > got) return `inconsistent samples for ${b}`;
  }
  if (x.transmitted && relays.length !== 3) return 'transmission without three relays';
  return { inventory, collected, relays: relays as BodyId[], species, scanned, transmitted: x.transmitted, route };
}

/** Validate an untrusted save object (types, bounds, versions, finite numbers). */
export function validateSave(raw: unknown): Result {
  if (!isObj(raw)) return { ok: false, error: 'Not a save object.' };
  if (legacySummary(raw)) return { ok: false, error: 'This save is from an earlier version of the game and cannot be continued in this version.' };
  if (raw.schema !== SAVE_SCHEMA) return { ok: false, error: `Unsupported save schema ${String(raw.schema)}.` };
  if (raw.generator !== GENERATOR_VERSION) return { ok: false, error: 'Save is from a different world generator version.' };
  if (raw.seed !== WORLD_SEED) return { ok: false, error: 'Save is for a different world seed.' };
  if (typeof raw.savedAt !== 'string' || raw.savedAt.length > 40) return { ok: false, error: 'Bad timestamp.' };
  if (!isNum(raw.playTime) || raw.playTime < 0 || raw.playTime > 1e8) return { ok: false, error: 'Bad play time.' };
  const system = raw.system;
  if (!isSystem(system)) return { ok: false, error: 'Bad system.' };
  if (system !== playedSystem()) return { ok: false, error: `Save is for another star system (${system}).` };
  const mode = raw.mode;
  if (mode !== 'PILOTING' && mode !== 'CRUISING' && mode !== 'LANDED' && mode !== 'ON_FOOT') return { ok: false, error: 'Bad mode.' };
  const bodyId = raw.bodyId === null ? null : isPlayed(raw.bodyId) ? raw.bodyId : undefined;
  if (bodyId === undefined) return { ok: false, error: 'Bad body.' };
  const surface = mode === 'LANDED' || mode === 'ON_FOOT';
  if (surface && !isLandable(bodyId)) return { ok: false, error: 'Surface mode without a body.' };
  const s = raw.ship;
  if (!isObj(s)) return { ok: false, error: 'Ship state missing.' };
  // Velocity: flight speeds, or a cruise up to the longest hop's cap while cruising.
  const maxSpeed = mode === 'CRUISING' ? MAX_CRUISE_SPEED : MAX_FLIGHT_SPEED;
  const sys = vec(s.sys, 3, MAX_COORD);
  const quat = unitQuat(s.quat);
  const vel = vec(s.vel, 3, maxSpeed);
  if (!sys || !quat || !vel || len(sys) > MAX_COORD || len(vel) > maxSpeed) return { ok: false, error: 'Bad ship pose.' };
  if (surface && !nearBody(sys, bodyId!)) return { ok: false, error: 'Ship too far from its body.' };
  if (!isNum(s.gear) || s.gear < 0 || s.gear > 1 || !isNum(s.throttle) || s.throttle < 0 || s.throttle > 1) return { ok: false, error: 'Bad ship controls.' };
  // Ability fields: PLAYER's strict validator (the on-foot state, power ids,
  // duplicates), then only powers some catalog body unlocks. A null state (a
  // record written before P2, or not on foot) reads as 'walk'.
  const p = raw.player;
  const ability = validateAbilityFields(mode === 'ON_FOOT' && isObj(p) ? p.abilityState : null, raw.unlocked);
  if (typeof ability === 'string') return { ok: false, error: `Bad ability save: ${ability}.` };
  if (!ability.unlocked.every((u) => POWERS.has(u))) return { ok: false, error: 'Bad unlocked powers.' };
  let player: SaveData['player'] = null;
  if (mode === 'ON_FOOT') {
    if (!isObj(p)) return { ok: false, error: 'Player state missing.' };
    const psys = vec(p.sys, 3, MAX_COORD);
    const heading = vec(p.heading, 3, 1.01);
    if (!psys || !heading || !isNum(p.pitch) || Math.abs(p.pitch) > 1.6) return { ok: false, error: 'Bad player pose.' };
    if (Math.abs(Math.hypot(heading[0], heading[1], heading[2]) - 1) > 1e-3) return { ok: false, error: 'Bad player heading.' };
    // The player must be on the ship's body (the ship was checked above). No
    // distance to the ship is imposed: powers carry the player anywhere on the
    // body, and First Light targets lie tens of kilometres from the landing site.
    if (!nearBody(psys, bodyId!)) return { ok: false, error: 'Player too far from the body.' };
    // The field is required; its value was validated above.
    if (!('abilityState' in p)) return { ok: false, error: 'Bad ability state.' };
    player = { sys: psys as V3, heading: heading as V3, pitch: p.pitch, abilityState: ability.abilityState };
  } else if (p !== null) return { ok: false, error: 'Unexpected player state.' };
  let cruise: SaveData['cruise'] = null;
  if (mode === 'CRUISING') {
    const c = raw.cruise;
    if (!isObj(c) || !isNum(c.speed) || c.speed < 0 || c.speed > MAX_CRUISE_SPEED || !isNum(c.throttle) || c.throttle < 0 || c.throttle > 1) {
      return { ok: false, error: 'Bad cruise state.' };
    }
    cruise = { speed: c.speed, throttle: c.throttle };
  } else if (raw.cruise !== null) return { ok: false, error: 'Unexpected cruise state.' };
  let lastSafeLanding: SaveData['lastSafeLanding'] = null;
  if (raw.lastSafeLanding !== null) {
    const l = raw.lastSafeLanding;
    if (!isObj(l) || !isLandable(l.bodyId)) return { ok: false, error: 'Bad last landing.' };
    // posPlanet is body-relative: within the body's release radius of its center.
    const pp = vec(l.posPlanet, 3, MAX_COORD);
    const lq = unitQuat(l.quat);
    const R = BODIES[l.bodyId].radius;
    if (!pp || !lq || len(pp) > BODY_HANDOFF.releaseRadii * R || len(pp) < MIN_SURFACE_RADII * R) return { ok: false, error: 'Bad last landing pose.' };
    lastSafeLanding = { bodyId: l.bodyId, posPlanet: pp as V3, quat: lq };
  }
  const navTarget = raw.navTarget === null ? null : isPlayed(raw.navTarget) ? raw.navTarget : undefined;
  if (navTarget === undefined) return { ok: false, error: 'Bad navigation target.' };
  // Discoveries are history without positions: any catalog body (a Sol save stays valid in Quiet play).
  const discoveries = stringList(raw.discoveries, isBodyId, Object.keys(BODIES).length);
  if (!discoveries) return { ok: false, error: 'Bad discoveries.' };
  const exp = validateExpedition(raw.expedition);
  if (typeof exp === 'string') return { ok: false, error: `Bad progress: ${exp}.` };
  return {
    ok: true,
    data: {
      schema: SAVE_SCHEMA,
      generator: GENERATOR_VERSION,
      seed: WORLD_SEED,
      savedAt: raw.savedAt,
      playTime: raw.playTime,
      system,
      mode,
      bodyId,
      ship: { sys: sys as V3, quat, vel: vel as V3, gear: s.gear, throttle: s.throttle },
      player,
      cruise,
      lastSafeLanding,
      navTarget,
      discoveries,
      unlocked: ability.unlocked,
      settings: sanitizeSettings(raw.settings),
      expedition: exp,
    },
  };
}

/** Read-only history shown for a save from an older schema. */
export interface LegacySave {
  schema: number;
  savedAt: string | null;
  playTime: number | null;
  body: string | null;
  /** Active survey relays (0–3) and whether the survey was transmitted. */
  relays: number | null;
  transmitted: boolean | null;
}

/** Summary of a record written by an older save schema, or null for anything else. */
export function legacySummary(raw: unknown): LegacySave | null {
  if (!isObj(raw) || !Number.isInteger(raw.schema)) return null;
  const schema = raw.schema as number;
  if (schema < 0 || schema >= SAVE_SCHEMA) return null;
  const e = isObj(raw.expedition) ? raw.expedition : {};
  return {
    schema,
    savedAt: typeof raw.savedAt === 'string' && raw.savedAt.length <= 40 ? raw.savedAt : null,
    playTime: isNum(raw.playTime) && raw.playTime >= 0 ? raw.playTime : null,
    body: typeof raw.body === 'string' && raw.body.length <= 40 ? raw.body : null,
    relays: Array.isArray(e.relays) && e.relays.length <= 3 ? e.relays.length : null,
    transmitted: typeof e.transmitted === 'boolean' ? e.transmitted : null,
  };
}

export type SlotState = { data: SaveData | null; error: string | null; present: boolean };

/**
 * IndexedDB persistence with a previous-good backup kept in the same
 * transaction. A corrupt latest record is never overwritten silently: it is
 * copied to its own key before the next write, and never rotated into the
 * backup slot.
 */
export class SaveStore {
  latest: SlotState = { data: null, error: null, present: false };
  previous: SlotState = { data: null, error: null, present: false };
  /** A save from an older schema, kept read-only (null when there is none). */
  legacy: LegacySave | null = null;
  /** Why persistence is not working, or why the last snapshot was not written (null when saves work). */
  failure: string | null = null;
  /** The last write was refused because its snapshot would not load (storage itself works). */
  refused = false;

  constructor(private readonly kv: KvStore | null) {
    if (!kv) this.failure = 'Browser storage is unavailable.';
  }

  get available(): boolean {
    return this.kv !== null;
  }

  private static slot(raw: unknown): SlotState {
    if (raw === undefined || legacySummary(raw)) return { data: null, error: null, present: false };
    const r = validateSave(raw);
    return r.ok ? { data: r.data, error: null, present: true } : { data: null, error: r.error, present: true };
  }

  async read(): Promise<void> {
    if (!this.kv) return;
    try {
      const raw = await this.kv.get(SAVE_KEY);
      // An older schema moves to its own key before anything can overwrite it.
      if (legacySummary(raw) && (await this.kv.get(LEGACY_KEY)) === undefined) await this.kv.put(LEGACY_KEY, raw);
      this.latest = SaveStore.slot(raw);
      this.previous = SaveStore.slot(await this.kv.get(PREV_KEY));
      this.legacy = legacySummary(await this.kv.get(LEGACY_KEY));
    } catch (e) {
      this.failure = `Could not read saves: ${(e as Error).message}`;
    }
  }

  /** Write a snapshot; resolves true only after the transaction completed. */
  async write(data: SaveData): Promise<boolean> {
    if (!this.kv) return false;
    // A snapshot the loader would refuse never replaces the latest save: it
    // would read back as corrupt and cost the progress since the last good one.
    const check = validateSave(data);
    this.refused = !check.ok;
    if (!check.ok) {
      this.failure = `The current state cannot be saved: ${check.error}`;
      return false;
    }
    try {
      if (this.latest.present && !this.latest.data) {
        // Preserve a corrupt latest record before replacing it.
        const old = await this.kv.get(SAVE_KEY);
        if ((await this.kv.get(CORRUPT_KEY)) === undefined && old !== undefined) await this.kv.put(CORRUPT_KEY, old);
      }
      await this.kv.rotateAndPut(SAVE_KEY, PREV_KEY, data, (old) => validateSave(old).ok);
      if (this.latest.data) this.previous = { ...this.latest };
      this.latest = { data, error: null, present: true };
      this.failure = null;
      return true;
    } catch (e) {
      const err = e as Error;
      this.failure = err.name === 'QuotaExceededError' ? 'Browser storage is full.' : `Saving failed: ${err.message}`;
      return false;
    }
  }
}

/** Serialize for a backup file. */
export function exportJson(data: SaveData): string {
  return JSON.stringify(data, null, 1);
}

/** Parse and validate a backup file's text. */
export function importJson(text: string): Result {
  if (text.length > 2_000_000) return { ok: false, error: 'File is too large to be a MERIDIAN backup.' };
  let raw: unknown;
  try {
    raw = JSON.parse(text);
  } catch {
    return { ok: false, error: 'File is not valid JSON.' };
  }
  return validateSave(raw);
}
