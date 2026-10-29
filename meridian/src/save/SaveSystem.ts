import { BODY_IDS, CORE_BODY_IDS, EXTENDED_BODY_IDS, GENERATOR_VERSION, SAVE_SCHEMA_VERSION, WORLD_SEED, isBodyId, type BodyId } from '../world/bodies';
import { sanitizeSettings, type Settings } from '../game/settings';
import { newExpedition, type ExpeditionState } from '../game/Expedition';
import type { KvStore } from './db';

// Save format (schema 2): only the seed, versions, poses/velocities, mode,
// settings and progress. Terrain, meshes and physics are regenerated.
// Schema 2 adds the Orrin and Saro bodies and the Extended Survey flag; schema
// 1 records (three bodies) are migrated on load, keeping all progress.

export type V3 = [number, number, number];
export type V4 = [number, number, number, number];
export type SaveMode = 'PILOTING' | 'CRUISING' | 'LANDED' | 'ON_FOOT';

export interface SaveData {
  schema: number;
  generator: number;
  seed: number;
  savedAt: string;
  playTime: number;
  mode: SaveMode;
  /** Active body for LANDED/ON_FOOT (and flight near a body); null in open space. */
  body: BodyId | null;
  ship: { sys: V3; quat: V4; vel: V3; gear: number; throttle: number };
  player: { sys: V3; heading: V3; pitch: number } | null;
  cruise: { speed: number; throttle: number } | null;
  lastSafeLanding: { body: BodyId; posPlanet: V3; quat: V4 } | null;
  navTarget: BodyId | null;
  settings: Settings;
  expedition: ExpeditionState;
}

export const SAVE_KEY = 'save';
export const PREV_KEY = 'save-prev';
export const CORRUPT_KEY = 'save-corrupt';

/** Largest plausible distance from the system origin (m). */
const MAX_COORD = 5e6;
const MAX_SPEED = 20000;

type Result = { ok: true; data: SaveData } | { ok: false; error: string };

const isObj = (x: unknown): x is Record<string, unknown> => typeof x === 'object' && x !== null && !Array.isArray(x);
const isNum = (x: unknown): x is number => typeof x === 'number' && Number.isFinite(x);

function vec(x: unknown, n: number, bound: number): number[] | null {
  if (!Array.isArray(x) || x.length !== n) return null;
  for (const v of x) if (!isNum(v) || Math.abs(v) > bound) return null;
  return x as number[];
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

/** Bodies that existed in schema 1 (a schema-1 record may reference only these). */
const SCHEMA1_BODIES: readonly BodyId[] = ['ilex', 'vesper', 'cairn'];

function idPatterns(bodies: readonly BodyId[]) {
  const alt = bodies.join('|');
  return {
    sample: new RegExp(`^(${alt}):sample:[0-2]$`),
    object: new RegExp(`^(${alt}):[a-z0-9:/_-]+$`),
    species: new RegExp(`^(${alt})-[a-z]+$`),
  };
}
/** Species list cap (flora, minerals and fauna across every body, with headroom). */
const MAX_SPECIES = 96;
const PATTERNS = { 1: idPatterns(SCHEMA1_BODIES), 2: idPatterns(BODY_IDS) };

function validateExpedition(x: unknown, schema: 1 | 2): ExpeditionState | string {
  if (!isObj(x)) return 'progress missing';
  const re = PATTERNS[schema];
  const bodies = schema === 1 ? SCHEMA1_BODIES : BODY_IDS;
  const inv = x.inventory;
  if (!isObj(inv)) return 'inventory missing';
  const inventory = newExpedition().inventory;
  for (const k of Object.keys(inv)) if (!(bodies as readonly string[]).includes(k)) return `unknown inventory body ${k.slice(0, 20)}`;
  for (const b of bodies) {
    const n = inv[b];
    if (!Number.isInteger(n) || (n as number) < 0 || (n as number) > 3) return `bad inventory count for ${b}`;
    inventory[b] = n as number;
  }
  const collected = stringList(x.collected, (s) => re.sample.test(s), 3 * bodies.length);
  if (!collected) return 'bad collected list';
  const relays = stringList(x.relays, (s) => (bodies as readonly string[]).includes(s), bodies.length);
  if (!relays) return 'bad relay list';
  const species = stringList(x.species, (s) => re.species.test(s), MAX_SPECIES);
  if (!species) return 'bad species list';
  // Discovery times: optional (absent in schema 1 and early schema-2 records), keyed by logged species.
  const discovered: Record<string, number> = {};
  if (x.discovered !== undefined) {
    if (!isObj(x.discovered)) return 'bad discovery times';
    const keys = Object.keys(x.discovered);
    if (keys.length > MAX_SPECIES) return 'bad discovery times';
    for (const k of keys) {
      const t = x.discovered[k];
      if (!species.includes(k) || !isNum(t) || t < 0 || t > 1e8) return 'bad discovery time';
      discovered[k] = t;
    }
  }
  const scanned = stringList(x.scanned, (s) => re.object.test(s), 8000);
  if (!scanned) return 'bad scan list';
  if (typeof x.transmitted !== 'boolean') return 'bad transmission flag';
  // Schema 1 had no Extended Survey; it migrates as not transmitted.
  const extended = schema === 1 ? false : x.extendedTransmitted;
  if (typeof extended !== 'boolean') return 'bad extended transmission flag';
  // Consistency: carried + spent samples per body never exceed what was collected there.
  for (const b of bodies) {
    const got = collected.filter((s) => s.startsWith(`${b}:`)).length;
    const spent = relays.includes(b) ? 1 : 0;
    if (inventory[b] + spent > got) return `inconsistent samples for ${b}`;
  }
  if (x.transmitted && !CORE_BODY_IDS.every((b) => relays.includes(b))) return 'transmission without three relays';
  if (extended && !(x.transmitted && EXTENDED_BODY_IDS.every((b) => relays.includes(b)))) return 'extended transmission without its relays';
  return { inventory, collected, relays: relays as BodyId[], species, discovered, scanned, transmitted: x.transmitted, extendedTransmitted: extended };
}

/**
 * Validate an untrusted save object (types, bounds, versions, finite numbers).
 * Schema-1 records are validated against the three-body rules and returned
 * migrated to the current schema.
 */
export function validateSave(raw: unknown): Result {
  if (!isObj(raw)) return { ok: false, error: 'Not a save object.' };
  if (raw.schema !== SAVE_SCHEMA_VERSION && raw.schema !== 1) return { ok: false, error: `Unsupported save schema ${String(raw.schema).slice(0, 20)}.` };
  const schema = raw.schema as 1 | 2;
  const bodyOk = schema === 1 ? (x: unknown): x is BodyId => isBodyId(x) && SCHEMA1_BODIES.includes(x) : isBodyId;
  if (raw.generator !== GENERATOR_VERSION) return { ok: false, error: 'Save is from a different world generator version.' };
  if (raw.seed !== WORLD_SEED) return { ok: false, error: 'Save is for a different world seed.' };
  if (typeof raw.savedAt !== 'string' || raw.savedAt.length > 40) return { ok: false, error: 'Bad timestamp.' };
  if (!isNum(raw.playTime) || raw.playTime < 0 || raw.playTime > 1e8) return { ok: false, error: 'Bad play time.' };
  const mode = raw.mode;
  if (mode !== 'PILOTING' && mode !== 'CRUISING' && mode !== 'LANDED' && mode !== 'ON_FOOT') return { ok: false, error: 'Bad mode.' };
  const body = raw.body === null ? null : bodyOk(raw.body) ? raw.body : undefined;
  if (body === undefined) return { ok: false, error: 'Bad body.' };
  if ((mode === 'LANDED' || mode === 'ON_FOOT') && !body) return { ok: false, error: 'Surface mode without a body.' };
  const s = raw.ship;
  if (!isObj(s)) return { ok: false, error: 'Ship state missing.' };
  const sys = vec(s.sys, 3, MAX_COORD);
  const quat = unitQuat(s.quat);
  const vel = vec(s.vel, 3, MAX_SPEED);
  if (!sys || !quat || !vel) return { ok: false, error: 'Bad ship pose.' };
  if (!isNum(s.gear) || s.gear < 0 || s.gear > 1 || !isNum(s.throttle) || s.throttle < 0 || s.throttle > 1) return { ok: false, error: 'Bad ship controls.' };
  let player: SaveData['player'] = null;
  if (mode === 'ON_FOOT') {
    const p = raw.player;
    if (!isObj(p)) return { ok: false, error: 'Player state missing.' };
    const psys = vec(p.sys, 3, MAX_COORD);
    const heading = vec(p.heading, 3, 1.01);
    if (!psys || !heading || !isNum(p.pitch) || Math.abs(p.pitch) > 1.6) return { ok: false, error: 'Bad player pose.' };
    if (Math.abs(Math.hypot(heading[0], heading[1], heading[2]) - 1) > 1e-3) return { ok: false, error: 'Bad player heading.' };
    // The player must be near the ship (they walked out of it).
    if (Math.hypot(psys[0] - sys[0], psys[1] - sys[1], psys[2] - sys[2]) > 20000) return { ok: false, error: 'Player too far from the ship.' };
    player = { sys: psys as V3, heading: heading as V3, pitch: p.pitch };
  } else if (raw.player !== null) return { ok: false, error: 'Unexpected player state.' };
  let cruise: SaveData['cruise'] = null;
  if (mode === 'CRUISING') {
    const c = raw.cruise;
    if (!isObj(c) || !isNum(c.speed) || c.speed < 0 || c.speed > MAX_SPEED || !isNum(c.throttle) || c.throttle < 0 || c.throttle > 1) {
      return { ok: false, error: 'Bad cruise state.' };
    }
    cruise = { speed: c.speed, throttle: c.throttle };
  } else if (raw.cruise !== null) return { ok: false, error: 'Unexpected cruise state.' };
  let lastSafeLanding: SaveData['lastSafeLanding'] = null;
  if (raw.lastSafeLanding !== null) {
    const l = raw.lastSafeLanding;
    if (!isObj(l) || !bodyOk(l.body)) return { ok: false, error: 'Bad last landing.' };
    const pp = vec(l.posPlanet, 3, 200000);
    const lq = unitQuat(l.quat);
    if (!pp || !lq) return { ok: false, error: 'Bad last landing pose.' };
    lastSafeLanding = { body: l.body, posPlanet: pp as V3, quat: lq };
  }
  const navTarget = raw.navTarget === null ? null : bodyOk(raw.navTarget) ? raw.navTarget : undefined;
  if (navTarget === undefined) return { ok: false, error: 'Bad navigation target.' };
  const exp = validateExpedition(raw.expedition, schema);
  if (typeof exp === 'string') return { ok: false, error: `Bad progress: ${exp}.` };
  return {
    ok: true,
    data: {
      schema: SAVE_SCHEMA_VERSION,
      generator: GENERATOR_VERSION,
      seed: WORLD_SEED,
      savedAt: raw.savedAt,
      playTime: raw.playTime,
      mode,
      body,
      ship: { sys: sys as V3, quat, vel: vel as V3, gear: s.gear, throttle: s.throttle },
      player,
      cruise,
      lastSafeLanding,
      navTarget,
      settings: sanitizeSettings(raw.settings),
      expedition: exp,
    },
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
  /** Why persistence is not working (null when saves work). */
  failure: string | null = null;

  constructor(private readonly kv: KvStore | null) {
    if (!kv) this.failure = 'Browser storage is unavailable.';
  }

  get available(): boolean {
    return this.kv !== null;
  }

  private static slot(raw: unknown): SlotState {
    if (raw === undefined) return { data: null, error: null, present: false };
    const r = validateSave(raw);
    return r.ok ? { data: r.data, error: null, present: true } : { data: null, error: r.error, present: true };
  }

  async read(): Promise<void> {
    if (!this.kv) return;
    try {
      this.latest = SaveStore.slot(await this.kv.get(SAVE_KEY));
      this.previous = SaveStore.slot(await this.kv.get(PREV_KEY));
    } catch (e) {
      this.failure = `Could not read saves: ${(e as Error).message}`;
    }
  }

  /** Write a snapshot; resolves true only after the transaction completed. */
  async write(data: SaveData): Promise<boolean> {
    if (!this.kv) return false;
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
