// Test-only API. Only bundled in development and the `testhooks` build
// (dist-test/); the production build (dist/) never includes this module.
// Hooks inject *input* (keys, mouse motion) and read telemetry; they never
// set gameplay state such as "landed" or "mission complete" directly.

import type { Game } from '../game/Game';
import type { SaveStore } from '../save/SaveSystem';
import { Autopilot, type AutopilotGoal } from './autopilot';
import { dirToFace, faceDir } from '../world/cube';
import { tangentBasis } from '../world/sites';
import { Raycaster, Vector3 } from 'three';
import { GROUPS } from '../physics/Physics';
import { frameStats, gpuEstimate } from './perf';
import { BODIES, BODY_IDS, type BodyId } from '../world/bodies';

export interface MeridianTestApi {
  game: Game;
  snapshot(): Record<string, unknown>;
  hold(code: string, down: boolean): void;
  press(code: string): void;
  mouse(dx: number, dy: number): void;
  releaseAll(): void;
  autopilot(goal: AutopilotGoal | null): void;
  autopilotState(): { headingError: number; distance: number; phase: string; phaseTime: number; wp: number; route: number[][] };
  /** Candidate landing sites around the ship: flat ones and steep ones (directions). */
  surveySites(count: number, minDist: number, maxDist: number): { flat: [number, number, number][]; steep: [number, number, number][] };
  /** Distance between the rendered terrain mesh and the physics contact below the player (m). */
  groundDisagreement(): { mesh: number; physics: number; feetToMesh: number } | null;
  /** Direction from the body center to a point offset from the ship (meters along the ship's right/forward). */
  dirNearShip(right: number, forward: number): [number, number, number];
  terrainCoverageOk(): boolean;
  faceUnderShip(): number;
  faceEdgeTarget(beyondMeters: number): [number, number, number];
  /** Draw only every Nth frame so software-rendered tests run closer to real time. */
  setRenderEvery(n: number): void;
  /** Nearest strong grove/ridge to the landing site as [x, z] meters in the landing-site frame. */
  findFeature(kind: 'grove' | 'ridge'): [number, number] | null;
  /** Fixed screenshot camera in the landing-site frame (null to release). */
  photo(eye: [number, number, number] | null, target?: [number, number, number]): void;
  /** Persistence status (read-only). */
  saveState(): Record<string, unknown>;
  /** Mission objects of the shown body (relay and sample positions in local coordinates). */
  missionTargets(): { id: string; kind: string; dir: [number, number, number] }[];
  /** Every body in BODY_IDS (system order) with its landing-site direction, so specs never hard-code the list. */
  bodies(): { id: BodyId; name: string; kind: string; radius: number; airless: boolean; landing: [number, number, number] }[];
  /**
   * Geography/placement fingerprint around the shown body's landing site:
   * collision heights (physics raycasts), generator heights farther out, and
   * every static PropSystem instance within 250 m (ID + position, mm).
   * Only PropSystem's deterministic, static props are included; moving
   * things (creatures) must never live in PropSystem (see PROGRESS.md,
   * Studio: Interfaces), so they can never enter this fingerprint.
   * `expect` (optional) makes the call return null unless that body is shown.
   */
  fingerprint(expect?: BodyId): { body: string; contact: (string | null)[]; heights: string[]; props: string[]; pendingCells: number } | null;
  /** Resource counters for leak checks. */
  resources(): Record<string, number | null>;
  /** Frame-interval statistics, GPU allocation estimate and render/terrain counts. */
  perf(lastFrames?: number): Record<string, unknown>;
  /** Clear the frame-interval history. */
  resetFrames(): void;
  /** Scannable props near the controlled entity: stable ID, species and aim point (planet-relative). */
  nearbyScannables(radius: number): { id: string; species: string; atPlanet: [number, number, number]; distance: number; dir: [number, number, number] }[];
}

export interface TestHookExtras {
  saves: () => SaveStore;
}

export function installTestHooks(game: Game, extras?: TestHookExtras): void {
  const ap = new Autopilot(game);
  game.beforeStep = (dt) => ap.step(dt);
  const api: MeridianTestApi = {
    game,
    autopilot(goal) {
      ap.setGoal(goal);
    },
    autopilotState() {
      return {
        headingError: ap.headingError, distance: ap.distance, phase: ap.phase, phaseTime: ap.phaseTime,
        wp: ap.wp, route: ap.route.map((p) => [p.x, p.y, p.z]),
      };
    },
    surveySites(count, minDist, maxDist) {
      const def = game.body!.def;
      const gen = game.body!.gen;
      const c = game.ship.currPos.clone().sub(game.bodyCenterLocal).normalize();
      const [t1, t2] = tangentBasis([c.x, c.y, c.z]);
      const flat: [number, number, number][] = [];
      const steep: [number, number, number][] = [];
      const slopeAt = (d: number[]) => {
        const [a1, a2] = tangentBasis(d as [number, number, number]);
        const e = 6 / def.radius;
        const h = (x: number[]) => {
          const l = Math.hypot(x[0], x[1], x[2]);
          return gen.height(x[0] / l, x[1] / l, x[2] / l);
        };
        let rough = 0;
        let maxS = 0;
        const h0 = h(d);
        for (const [u, v] of [[1, 0], [-1, 0], [0, 1], [0, -1], [0.7, 0.7], [-0.7, 0.7], [0.7, -0.7], [-0.7, -0.7]]) {
          const q = [0, 1, 2].map((i) => d[i] + e * (u * a1[i] + v * a2[i]));
          const dh = h(q) - h0;
          maxS = Math.max(maxS, Math.abs(dh) / 6);
          rough = Math.max(rough, Math.abs(dh));
        }
        return { slopeDeg: (Math.atan(maxS) * 180) / Math.PI, rough };
      };
      for (let k = 0; k < 400 && (flat.length < count || steep.length < count); k++) {
        const ang = k * 2.39996;
        const dist = minDist + ((k * 0.618034) % 1) * (maxDist - minDist);
        const kk = dist / def.radius;
        const d = [0, 1, 2].map((i) => c.getComponent(i) + kk * (Math.cos(ang) * t1[i] + Math.sin(ang) * t2[i]));
        const l = Math.hypot(d[0], d[1], d[2]);
        const dir: [number, number, number] = [d[0] / l, d[1] / l, d[2] / l];
        const s = slopeAt(dir);
        if (s.slopeDeg < 5 && flat.length < count) flat.push(dir);
        else if (s.slopeDeg > 22 && steep.length < count) steep.push(dir);
      }
      return { flat, steep };
    },
    groundDisagreement() {
      const p = game.player;
      if (!p) return null;
      const up = p.up;
      const feet = p.feet(new Vector3());
      const o = feet.clone().addScaledVector(up, 2);
      const hit = game.physics.castRay(o.x, o.y, o.z, -up.x, -up.y, -up.z, 10, undefined, p.body);
      const rc = new Raycaster(o.clone(), up.clone().negate(), 0, 10);
      game.body!.terrain.root.updateMatrixWorld(true);
      const hits = rc.intersectObjects(game.body!.terrain.root.children, false);
      if (!hit || hits.length === 0) return null;
      return { mesh: hits[0].distance - 2, physics: hit.toi - 2, feetToMesh: hits[0].distance - 2 };
    },
    dirNearShip(right, forward) {
      const s = game.ship;
      const pt = s.localToWorld(new Vector3(right, 0, -forward), new Vector3()).sub(game.bodyCenterLocal).normalize();
      return [pt.x, pt.y, pt.z];
    },
    terrainCoverageOk() {
      // Every quadtree leaf has a mesh (no holes) and nothing else is rendered (no overlap).
      const tm = game.body!.terrain;
      let leaves = 0;
      let ok = true;
      const walk = (n: { isLeaf: boolean; mesh: unknown; children: unknown[] | null }) => {
        if (n.isLeaf) {
          leaves++;
          if (!n.mesh) ok = false;
        } else for (const c of n.children as (typeof n)[]) walk(c);
      };
      for (const r of tm.roots) walk(r as never);
      let meshes = 0;
      tm.forEachMeshNode(() => meshes++);
      return ok && leaves === meshes;
    },
    findFeature(kind) {
      const sites = game.body!.sites;
      const R = game.body!.def.radius;
      const n = new Vector3(...sites.landing.dir);
      const relay = new Vector3(...sites.relay.dir);
      const fz = relay.sub(n.clone().multiplyScalar(relay.dot(n))).normalize();
      const fx = new Vector3().crossVectors(fz, n).normalize();
      const info = { height: 0, biome: 0, variation: 0, special: 0, rockiness: 0 };
      let best: [number, number] | null = null;
      let bestD = Infinity;
      for (let z = -3000; z <= 3000; z += 100) {
        for (let x = -3000; x <= 3000; x += 100) {
          const d = n.clone().addScaledVector(fx, x / R).addScaledVector(fz, z / R).normalize();
          game.body!.gen.info(d.x, d.y, d.z, info);
          const ok = kind === 'grove' ? info.special > 0.75 && info.biome > 0.6 : info.rockiness > 0.7;
          const dist = Math.hypot(x, z);
          if (ok && dist < bestD && dist > 250) {
            bestD = dist;
            best = [x, z];
          }
        }
      }
      return best;
    },
    saveState() {
      const st = extras?.saves();
      if (!st) return { available: false };
      const slot = (x: typeof st.latest) => ({ present: x.present, valid: !!x.data, error: x.error, savedAt: x.data?.savedAt ?? null, mode: x.data?.mode ?? null, body: x.data?.body ?? null, relays: x.data?.expedition.relays ?? null });
      return { available: st.available, failure: st.failure, latest: slot(st.latest), previous: slot(st.previous) };
    },
    missionTargets() {
      const b = game.body;
      if (!b) return [];
      const out: { id: string; kind: string; dir: [number, number, number] }[] = [{ id: b.sites.relay.id, kind: 'relay', dir: b.sites.relay.dir }];
      for (const smp of b.sites.samples) out.push({ id: smp.id, kind: 'sample', dir: smp.dir });
      return out;
    },
    bodies() {
      return BODY_IDS.map((id) => {
        const d = BODIES[id];
        return { id, name: d.name, kind: d.kind, radius: d.radius, airless: d.atmosphere === null, landing: game.landingSiteOf(id) };
      });
    },
    fingerprint(expect) {
      const b = game.body;
      if (!b || !game.bodyShown) return null;
      if (expect !== undefined && b.def.id !== expect) return null;
      // Centered on the body's fixed landing site (not the ship, which lands a few meters off).
      const n = new Vector3(...b.sites.landing.dir);
      const ship = n.clone().multiplyScalar(b.def.radius + b.gen.height(n.x, n.y, n.z));
      const [t1, t2] = tangentBasis([n.x, n.y, n.z]);
      const R = b.def.radius;
      // Sample points are offset from the exact site so none lies on a chunk seam:
      // sites can sit exactly on a tile boundary, where a ray can pass between
      // adjacent colliders (their f32 transforms meet within ~0.1 mm).
      const at = (dx: number, dy: number) =>
        n.clone().add(new Vector3(...t1).multiplyScalar((dx + 0.731) / R)).add(new Vector3(...t2).multiplyScalar((dy + 0.419) / R)).normalize();
      // Collision-mesh heights at fixed points; null where no collider is resident.
      const contact: (string | null)[] = [];
      for (const [dx, dy] of [[0, 0], [12, 0], [-12, 0], [0, 12], [0, -12], [20, 20], [-20, -20], [30, -30]]) {
        const d = at(dx, dy);
        if (!b.collision.readyAt(d.clone().multiplyScalar(R))) {
          contact.push(null);
          continue;
        }
        const top = d.clone().multiplyScalar(R + b.def.maxHeight + 50).add(game.bodyCenterLocal);
        const hit = game.physics.castRay(top.x, top.y, top.z, -d.x, -d.y, -d.z, b.def.maxHeight + 400, GROUPS.queryTerrain);
        contact.push(hit ? (b.def.maxHeight + 50 - hit.toi).toFixed(3) : 'miss');
      }
      const heights: string[] = [];
      for (const [dx, dy] of [[400, 0], [0, 400], [-400, 0], [0, -400], [900, 900], [-900, 900]]) {
        const d = at(dx, dy);
        heights.push(b.gen.height(d.x, d.y, d.z).toFixed(4));
      }
      // Static props only: PropSystem holds nothing that moves (creatures live elsewhere).
      const props = b.props
        .nearby(ship, 250)
        .map((i) => `${i.id}@${i.p.x.toFixed(3)},${i.p.y.toFixed(3)},${i.p.z.toFixed(3)}`)
        .sort();
      return { body: b.def.id, contact, heights, props, pendingCells: b.props.stats.pending };
    },
    perf(lastFrames) {
      const t = game.telemetry() as Record<string, any>;
      return {
        frames: frameStats(game, lastFrames),
        gpu: gpuEstimate(game),
        draw: t.draw,
        terrain: t.terrain ? { rendered: t.terrain.rendered, leaves: t.terrain.leaves, colliders: t.terrain.colliders } : null,
        props: t.props ? { drawn: t.props.drawn, triangles: t.props.triangles, colliders: t.props.colliders } : null,
        physics: t.physics,
        heapMB: t.heapMB,
        quality: t.quality,
        timings: t.timings,
        chunks: { cacheMB: t.chunks.cacheMB, genMsAvg: t.chunks.genMsAvg, genMsMax: t.chunks.genMsMax },
        gl: (() => {
          const gl = game.render.renderer.getContext();
          const ext = gl.getExtension('WEBGL_debug_renderer_info');
          return ext ? String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)) : String(gl.getParameter(gl.RENDERER));
        })(),
      };
    },
    resetFrames() {
      game.frameIntervalCount = 0;
    },
    resources() {
      const t = game.telemetry() as Record<string, any>;
      return {
        geometries: t.draw.geometries, textures: t.draw.textures, bodies: t.physics.bodies, colliders: t.physics.colliders,
        cacheMB: t.chunks.cacheMB, cacheCount: t.chunks.cacheCount, heapMB: t.heapMB, terrainRendered: t.terrain ? t.terrain.rendered : 0,
        propCells: t.props ? t.props.cells : 0, propInstances: t.props ? t.props.instances : 0, generated: t.chunks.generated,
      };
    },
    nearbyScannables(radius) {
      const b = game.body;
      if (!b) return [];
      const from = game.controlledPos().clone().sub(game.bodyCenterLocal);
      return b.props
        .nearby(from, radius)
        .filter((i) => i.species.scannable)
        .map((i) => {
          const at = i.p.clone().addScaledVector(i.up, i.h * 0.5);
          const dir = i.p.clone().normalize();
          return { id: i.id, species: i.species.id, atPlanet: [at.x, at.y, at.z] as [number, number, number], distance: at.distanceTo(from), dir: [dir.x, dir.y, dir.z] as [number, number, number] };
        })
        .sort((a, b2) => a.distance - b2.distance);
    },
    photo(eye, target) {
      game.photoCamera = eye ? { eye, target: target ?? [0, 0, 0] } : null;
    },
    setRenderEvery(n) {
      game.renderEvery = Math.max(1, Math.floor(n));
    },
    faceEdgeTarget(beyond) {
      // Point `beyond` meters past the nearest edge of the landing site's cube face.
      const def = game.body!.def;
      const n = game.body!.sites.landing.dir;
      const f = dirToFace(n[0], n[1], n[2]);
      let best: number[] = [];
      let bd = Infinity;
      for (const [u, v] of [[1, f.v], [-1, f.v], [f.u, 1], [f.u, -1]]) {
        const d = [0, 0, 0];
        faceDir(f.face, u, v, d);
        const dist = Math.acos(Math.min(1, d[0] * n[0] + d[1] * n[1] + d[2] * n[2])) * def.radius;
        if (dist < bd) {
          bd = dist;
          best = d;
        }
      }
      const k = (bd + beyond) / bd;
      const t = [n[0] + (best[0] - n[0]) * k, n[1] + (best[1] - n[1]) * k, n[2] + (best[2] - n[2]) * k];
      const l = Math.hypot(t[0], t[1], t[2]);
      return [t[0] / l, t[1] / l, t[2] / l];
    },
    faceUnderShip() {
      const p = game.ship.currPos.clone().sub(game.bodyCenterLocal);
      return game.body!.terrain.leafForDir(p.x, p.y, p.z).face;
    },
    snapshot: () => game.telemetry(),
    hold(code, down) {
      if (down) game.input.injected.add(code);
      else game.input.injected.delete(code);
    },
    press(code) {
      game.input.press(code);
    },
    mouse(dx, dy) {
      game.injectMouse(dx, dy);
    },
    releaseAll() {
      game.input.injected.clear();
    },
  };
  (window as unknown as { __meridian: MeridianTestApi }).__meridian = api;
}
