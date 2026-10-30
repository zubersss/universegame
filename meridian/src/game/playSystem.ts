import { Vector3 } from 'three';
import { BODIES, BODY_IDS, SOL_M2_BODIES, SYSTEM_BODY_IDS, type BodyDef, type BodyId, type SystemId } from '../world/bodies';
import { computeSites, tangentBasis, type MissionSites } from '../world/sites';
import { START_BODY, SURFACE_READY } from './config';

// The star system in play and the rules that follow from it: the ?system=
// choice made at boot (before saves are read and the Game is built, since both
// read BODY_IDS), where a new expedition starts, and which bodies may take the
// surface handoff. No renderer or physics state, so boot, Game, saves and Node
// tests share one definition. The Quiet System keeps its M1 behaviour.

/** Systems a player can choose with ?system= (the Quiet System is the default until L10). */
export type PlayChoice = 'quiet' | 'sol';

/** The system a ?system= value asks for: 'sol', else (absent or anything else) the Quiet System. */
export function systemFromQuery(value: string | null): PlayChoice {
  return value === 'sol' ? 'sol' : 'quiet';
}

/** The bodies played in a system (for setPlaySystem): the Quiet System, or Sol's M2 set in travel order. */
export function playBodies(system: PlayChoice): readonly BodyId[] {
  return system === 'sol' ? SOL_M2_BODIES : SYSTEM_BODY_IDS.quiet;
}

/** The body a new expedition starts on in a system. */
export function startBodyOf(system: SystemId): BodyDef {
  const id = START_BODY[system];
  if (!id) throw new Error(`No start body for system ${system}`);
  return BODIES[id];
}

/** A surface the ship can land on in this build: every Quiet System body, and Sol's SURFACE_READY. */
export function surfaceReady(def: BodyDef): boolean {
  if (def.explore !== 'surface') return false;
  return def.system === 'quiet' || SURFACE_READY.includes(def.id);
}

/**
 * Whether the handoff may activate a body (detailed terrain, collision, props):
 * only a surface-ready body, so the Sun and the giants stay proxies; while
 * cruising, only the nav target, so a cruise past another world builds no
 * terrain. The Quiet System keeps its handoff: any of its bodies, in any mode.
 */
export function canActivate(def: BodyDef, cruising: boolean, navTarget: BodyId | null): boolean {
  if (!surfaceReady(def)) return false;
  return def.system === 'quiet' || !cruising || def.id === navTarget;
}

/**
 * Bodies drawn as distant terrain globes (BodyProxies): every body in play
 * except a star, which has no terrain to generate (its sites throw); the
 * background's sun billboard stands for it.
 */
export function proxyBodies(ids: readonly BodyId[] = BODY_IDS): BodyId[] {
  return ids.filter((id) => BODIES[id].kind !== 'star');
}

/**
 * The tangent frame at a body's landing site (its sites must be computable: a
 * data body needs ensureBodyData first): up is the site normal, forward points
 * toward the Quiet survey relay, or on a First Light body toward its first
 * route waypoint, and right = forward x up. startSite and the photo test
 * camera share it, so neither collapses where the relay sits on the site.
 */
export function siteFrame(def: BodyDef, sites: MissionSites = computeSites(def)): { up: Vector3; forward: Vector3; right: Vector3 } {
  const up = new Vector3(...sites.landing.dir);
  const toward = new Vector3(...(def.system !== 'quiet' && sites.route.length ? sites.route[0].dir : sites.relay.dir));
  const forward = toward.sub(up.clone().multiplyScalar(toward.dot(up)));
  // Outside the Quiet survey the relay sits on the landing site: any tangent will do.
  if (forward.lengthSq() < 1e-12) forward.set(...tangentBasis(sites.landing.dir)[0]);
  forward.normalize();
  return { up, forward, right: new Vector3().crossVectors(forward, up).normalize() };
}

/** The opening site on a body: the landing clearing, facing siteFrame's forward tangent. */
export function startSite(def: BodyDef): { dir: Vector3; height: number; forward: Vector3 } {
  const sites = computeSites(def);
  const { up, forward } = siteFrame(def, sites);
  return { dir: up, height: sites.landing.height, forward };
}
