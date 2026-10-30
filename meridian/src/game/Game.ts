import { Color, Mesh, Quaternion, Vector2, Vector3, type MeshStandardMaterial, type Texture } from 'three';
import { FixedStepper } from '../core/loop';
import { FloatingOrigin } from '../core/origin';
import { Input } from '../core/input';
import { clamp, quatFromForwardUp } from '../core/mathx';
import { RenderSystem } from '../render/RenderSystem';
import { Space } from '../render/Space';
import { atmoUniforms, createSkyMesh, patchAerial, setAtmosphereBody, updateSkyMesh } from '../render/Atmosphere';
import { Lighting } from '../render/Lighting';
import { CameraRig } from '../render/CameraRig';
import { makeTerrainDetailTexture } from '../render/terrainTextures';
import { Clouds } from '../render/Clouds';
import { Motes } from '../render/Motes';
import { BodyProxies } from '../render/BodyProxies';
import { AdaptiveQuality } from '../render/Adaptive';
import { GameAudio } from '../audio/GameAudio';
import { GROUPS, Physics, RAPIER } from '../physics/Physics';
import { Ship } from '../ship/Ship';
import { Exhaust } from '../ship/Exhaust';
import { BOARDING_POINT, GEAR_PAD_BOTTOM_Y } from '../ship/ShipModel';
import { NO_CONTROLS, type FlightOutput, type FlightOverride, type ShipControls } from '../ship/FlightModel';
import { LandingAssist, emptyProbe, probeFootprint, type FootprintProbe } from '../ship/LandingAssist';
import { CruiseController, cruiseHop, freeDistance, insideEnvelope, type CruiseExitReason, type CruiseLegStats } from '../ship/Cruise';
import { Player, FOOT_OFFSET, playerShape, type WalkInput } from '../player/Player';
import { FlightEnvProvider } from '../world/FlightEnvProvider';
import { ActiveBody } from '../world/ActiveBody';
import { computeSites } from '../world/sites';
import { MissionObjects, sampleName } from '../world/MissionObjects';
import { Expedition, SURVEY_BODIES } from './Expedition';
import { canActivate, proxyBodies, startBodyOf, startSite, surfaceReady } from './playSystem';
import { OnFootHost, type OnFootExitReason } from './onFoot';
import { rayCapsule } from './scan';
import type { Species } from '../props/species';
import type { PropInstance } from '../props/PropSystem';
import { SAVE_SCHEMA, type SaveData } from '../save/SaveSystem';
import type { AbilitySave } from '../abilities/save';
import { bodyGravity, dominantBody } from '../world/environment';
import { ChunkStore, WorkerBackend } from '../terrain/ChunkStore';
import { bodyDataReady } from '../world/surface';
import { createTerrainMaterials, makeTerrainUniforms, setTerrainPalette, type TerrainUniforms } from '../terrain/terrainMaterial';
import { Hud, type Prompt } from '../ui/Hud';
import { Markers, type MarkerSpec } from '../ui/Markers';
import { BODY_HANDOFF, CRUISE, FLIGHT, LANDING, MAX_FRAME_GAP, MAX_STEPS_PER_FRAME, SCAN, SIM_DT, SURFACE_READY, WALK, BUDGETS, PRESETS, type QualityPreset } from './config';
import { GENERATOR_VERSION, WORLD_SEED } from '../world/bodies';
import type { Settings } from './settings';
import { BODIES, BODY_IDS, PLAY_SYSTEM, sunDirFor, type BodyDef, type BodyId } from '../world/bodies';

export type AppState = 'title' | 'loading' | 'playing' | 'paused' | 'panel';
export type Mode = 'PILOTING' | 'CRUISING' | 'LANDED' | 'ON_FOOT';

const _v1 = new Vector3();
const _v2 = new Vector3();
const _v3 = new Vector3();
const _v4 = new Vector3();
const _q = new Quaternion();

/** Candidate exit spots in ship-local coordinates (ground height found by raycast). */
const EXIT_SPOTS: readonly Vector3[] = [
  new Vector3(-4.1, 0, -1.2), new Vector3(-4.1, 0, 1.9), new Vector3(4.1, 0, -1.2), new Vector3(4.1, 0, 1.9),
  new Vector3(0, 0, -10.2), new Vector3(0, 0, 10.8), new Vector3(-7, 0, 6.5), new Vector3(7, 0, 6.5),
];

/** What the scanner is aimed at. */
export interface ScanTarget {
  id: string;
  species: Species | null;
  label: string;
  /** Distance along the view ray (m). */
  distance: number;
}

export interface LandedPose {
  bodyId: BodyId;
  /** Ship origin relative to the body center (double precision). */
  posPlanet: Vector3;
  quat: Quaternion;
}

/** A body handoff step (diagnostics and tests): detailed terrain built, swapped in for the proxy, or freed. */
export interface HandoffEvent {
  /** Simulation time (s). */
  t: number;
  event: 'activate' | 'show' | 'release';
  body: BodyId;
}

/**
 * A finished cruise leg (diagnostics and tests): hop, cap, entry and peak as
 * CruiseController.legStats gives them (cap = cruiseMaxSpeed(hop); peak <= cap
 * for a leg engaged from flight).
 */
export interface CruiseLeg extends CruiseLegStats {
  /** Simulation times (s) of the engage (or the restore) and of the hand-back to normal flight. */
  start: number;
  end: number;
  /** Nav target at the hand-back, or null (a retarget mid-leg changes it; hop and cap stay the leg's longest). */
  target: BodyId | null;
  exit: CruiseExitReason;
}

/** Entries kept in each diagnostics log (the oldest drops first). */
const LOG_LIMIT = 32;

function pushBounded<T>(log: T[], entry: T): void {
  log.push(entry);
  if (log.length > LOG_LIMIT) log.shift();
}

function distTo(p: Vector3, c: readonly number[]): number {
  return Math.sqrt((p.x - c[0]) ** 2 + (p.y - c[1]) ** 2 + (p.z - c[2]) ** 2);
}

/** Owns the frame loop, the floating origin, the active body and the gameplay mode. */
export class Game {
  readonly input = new Input();
  readonly physics = new Physics();
  readonly stepper = new FixedStepper(SIM_DT, MAX_STEPS_PER_FRAME, MAX_FRAME_GAP);
  readonly space = new Space();
  readonly lighting: Lighting;
  readonly cameraRig: CameraRig;
  readonly hud = new Hud();
  readonly markers = new Markers();
  readonly sky: Mesh;
  readonly ship: Ship;
  readonly exhaust = new Exhaust();
  readonly clouds = new Clouds();
  readonly motes: Motes;
  readonly audio = new GameAudio();
  readonly proxies: BodyProxies;
  private footAcc = 0;
  readonly store: ChunkStore;
  readonly terrainUniforms: TerrainUniforms;
  readonly terrainMaterials: MeshStandardMaterial[];
  readonly assist = new LandingAssist();
  readonly probe: FootprintProbe = emptyProbe();
  player: Player | null = null;
  /** The one body with detailed terrain, collision and props (null in open space). */
  body: ActiveBody | null = null;
  /** The active body's local terrain is shown and its distant proxy hidden. */
  bodyShown = false;
  /** Where a new expedition starts: the play system's start body (fixed for the game's lifetime). */
  readonly startBody: BodyDef = startBodyOf(PLAY_SYSTEM);
  /** Reference body for up/altitude/lighting: the active body, else the dominant one. */
  ref: BodyDef = this.startBody;
  state: AppState = 'title';
  /** Change only through setMode() so the ON_FOOT hooks see every transition. */
  mode: Mode = 'LANDED';
  /** Ability hook points around ON_FOOT (installed by the ability system). */
  readonly onFoot = new OnFootHost();
  settings: Settings;
  /** Floating origin: system-coordinate position of the local origin (double precision). */
  readonly floating = new FloatingOrigin();
  readonly origin = this.floating.origin;
  readonly bodyCenterLocal = new Vector3();
  lastSafeLanding: LandedPose | null = null;
  rebaseCount = 0;
  simTime = 0;
  stepCount = 0;
  frameCount = 0;
  pausedAt = 0;
  /** Shared clock for cloud advection (local and proxy shells agree). */
  cloudTime = 0;
  private lastTime = -1;
  private rafId = 0;
  /** Mouse virtual stick (x = yaw, y = pitch), -1..1. */
  readonly stick = new Vector2();
  private pendingMouse = new Vector2();
  private orbitMouse = new Vector2();
  private readonly flightOut: FlightOutput = { force: new Vector3(), angvel: new Vector3() };
  private readonly override: FlightOverride = { vTarget: new Vector3(), tau: 1, aMax: 1, angTargetLocal: new Vector3() };
  readonly env: FlightEnvProvider;
  readonly groundAlbedo = new Color(0xa8763e);
  private takeoffTimer = 0;
  /** Interplanetary cruise (sole owner of the ship transform while cruising). */
  readonly cruise = new CruiseController();
  /** Cruise speed setting 0..1 (W/S while cruising). */
  cruiseThrottle = 1;
  private pendingCruiseExit: CruiseExitReason | null = null;
  private cruiseStart = 0;
  /** Recent finished cruise legs, oldest first (bounded). */
  readonly cruiseLog: CruiseLeg[] = [];
  /** Recent body handoff steps, oldest first (bounded). */
  readonly handoffLog: HandoffEvent[] = [];
  /** Navigation destination (Tab panel). */
  navTarget: BodyId | null = null;
  /** Sustained-frame-time quality steps (resolution, then props, then distant LOD). */
  readonly adaptive: AdaptiveQuality;
  /** Survey progress (samples, relays, journal, transmission). */
  readonly expedition = new Expedition();
  /** Relay and sample deposits of the shown body. */
  mission: MissionObjects | null = null;
  scanTarget: ScanTarget | null = null;
  private scanState = { id: '', progress: 0, done: false };
  /** Persistence hook: called after important interactions and periodically when dirty. */
  onAutosave: ((reason: string) => void) | null = null;
  private autosaveTimer = 0;
  private lastSavedPos = new Vector3(1e12, 0, 0);
  private arrivedAt: BodyId | null = null;
  /** Recovery waiting for collision around the destination. */
  private pendingRecovery: (() => boolean) | null = null;
  onStateChange: ((s: AppState) => void) | null = null;
  onLoadingProgress: ((text: string) => void) | null = null;
  /** Gameplay notices (mode changes, rejections) for the HUD. */
  onNotice: ((title: string, text: string, teal?: boolean) => void) | null = null;
  /** Draw every Nth frame (test-only throttle for software rendering; always 1 in play). */
  renderEvery = 1;
  /**
   * Test-only fixed camera for reproducible screenshots: eye/target given as
   * offsets in the landing-site frame (x = east-ish, y = up, z = toward relay).
   */
  photoCamera: { eye: [number, number, number]; target: [number, number, number] } | null = null;
  /** Test-only hook run at the start of each fixed step (autopilot); null in production. */
  beforeStep: ((dt: number) => void) | null = null;
  lastFrameDt = 0;
  /** Ring buffer of recent frame intervals (ms) for profiling. */
  readonly frameIntervals = new Float32Array(4096);
  frameIntervalCount = 0;
  /** Smoothed per-frame CPU timings (ms) for diagnostics. */
  readonly timings = { sim: 0, terrain: 0, render: 0, frame: 0 };
  private tTerrain = 0;
  /** Seconds spent in the loading state (diagnostics). */
  loadingTime = 0;
  /** Counters for diagnostics/tests. */
  readonly counters = {
    landings: 0, takeoffs: 0, exits: 0, boardings: 0, jumps: 0, rejectedLandings: 0, recoveries: 0,
    activations: 0, releases: 0, releasesNotCoarse: 0,
    cruiseEngages: 0, cruiseRefused: 0, cruiseExitApproach: 0, cruiseExitBrake: 0, cruiseExitToggle: 0, cruiseExitSafety: 0,
    scans: 0, collects: 0, collectRepeats: 0, relayActivations: 0, relayRepeats: 0, transmissions: 0, autosaves: 0, restores: 0,
  };
  private lastRejectReason: string | null = null;

  constructor(readonly render: RenderSystem, settings: Settings) {
    this.settings = settings;
    this.adaptive = new AdaptiveQuality(render.preset === 'low' ? 33.3 : 16.7);
    this.input.attach(render.canvas);
    render.bgScene.add(this.space.group);
    this.sky = createSkyMesh(render.spec.skySamples);
    render.skyScene.add(this.sky);
    this.lighting = new Lighting(render.renderer, render.scene, render.spec.shadowSize);
    this.lighting.onEnvChange = (t) => this.applyEnvMap(t);
    this.cameraRig = new CameraRig(render.camera);
    this.cameraRig.terrainClearance = (p) => this.cameraTerrainDeficit(p);
    this.motes = new Motes(render.preset === 'low' ? 160 : 420);
    render.scene.add(this.clouds.group, this.motes.points);

    this.store = new ChunkStore(new WorkerBackend(), this.startBody.id);
    this.proxies = new BodyProxies(render.bgScene, new WorkerBackend('proxy'), render.spec.aerialSamples, render.spec.skySamples, render.spec.cloudQuality, proxyBodies());
    // Level-0 roots are shared: proxies and the local coarse planet use the same chunks.
    this.proxies.onRoot = (d) => this.store.seed(d);
    this.store.onData = (d) => {
      if (d.level === 0) this.proxies.addRoot(d);
    };
    this.terrainUniforms = makeTerrainUniforms(makeTerrainDetailTexture(256));
    this.terrainMaterials = createTerrainMaterials(this.terrainUniforms, render.spec.aerialSamples, render.preset === 'low');
    this.env = new FlightEnvProvider(this.startBody, this.bodyCenterLocal, this.origin, (d) => this.terrainHeightAt(d));

    // Start landed on the start body's deterministic landing clearing (startPose).
    const def = this.startBody;
    this.activateBody(def);
    this.showBody();
    const start = this.startPose();
    const shipSys = new Vector3(...def.center).add(start.posPlanet);
    FloatingOrigin.rounded(shipSys, this.origin);
    this.updateBodyCenterLocal();
    this.ship = new Ship(this.physics, shipSys.clone().sub(this.origin), start.quat);
    this.ship.gear = 1;
    this.ship.gearTarget = 1;
    this.parkShip();
    render.scene.add(this.ship.root, this.exhaust.points);
    for (const m of this.ship.visual.materials) patchAerial(m, render.spec.aerialSamples);
    this.cameraRig.orbitYaw = 2.5;
    this.cameraRig.orbitPitch = 0.12;
    this.physics.refreshQueries();

    window.addEventListener('resize', this.onResize);
    document.addEventListener('visibilitychange', this.onVisibility);
  }

  // ------------------------------------------------------------- lifecycle

  start(): void {
    this.rafId = requestAnimationFrame(this.frame);
  }

  setState(s: AppState): void {
    if (this.state === s) return;
    this.state = s;
    if (s === 'paused' || s === 'panel') this.pausedAt = performance.now();
    if (s === 'loading') this.loadingTime = 0;
    this.input.active = s === 'playing';
    if (s !== 'playing') {
      this.input.clearAll();
      this.input.releaseLock();
    }
    this.stick.set(0, 0);
    this.pendingMouse.set(0, 0);
    this.stepper.reset();
    if (s === 'playing') this.audio.resume();
    else this.audio.suspend();
    this.onStateChange?.(s);
  }

  /** Begin play once terrain and collision under the controlled entity are ready. */
  beginPlay(): void {
    this.setState('loading');
  }

  private onResize = (): void => {
    this.render.resize();
  };

  private onVisibility = (): void => {
    this.lastTime = -1;
    this.stepper.reset();
    if (document.hidden && this.state === 'playing') this.setState('paused');
  };

  private frame = (now: number): void => {
    this.rafId = requestAnimationFrame(this.frame);
    if (document.hidden) {
      this.lastTime = -1;
      return;
    }
    const rawMs = this.lastTime < 0 ? 0 : now - this.lastTime;
    const dt = Math.min(rawMs / 1000, MAX_FRAME_GAP);
    this.lastTime = now;
    this.lastFrameDt = dt;
    this.frameCount++;
    // Profiling records the real interval; only the simulation step is clamped.
    if (rawMs > 0) this.frameIntervals[this.frameIntervalCount++ % this.frameIntervals.length] = rawMs;
    let alpha = 1;
    const t0 = performance.now();
    if (this.state === 'playing') {
      const [mx, my] = this.input.takeMouse();
      this.pendingMouse.x += mx;
      this.pendingMouse.y += my;
      alpha = this.stepper.advance(dt, (h) => this.fixedUpdate(h)).alpha;
      this.updateHandoff();
      if (this.settings.adaptive && this.adaptive.frame(dt)) this.applyAdaptive();
      this.autosaveTimer += dt;
      if (this.autosaveTimer >= BUDGETS.autosaveSeconds && this.saveDirty()) this.autosave('periodic');
    } else if (this.state === 'loading') {
      this.loadingTime += dt;
      this.updateCollisionDemand();
      if (this.terrainReadyForPlay()) {
        if (this.pendingRecovery && !this.pendingRecovery()) {
          // destination not yet safe; keep waiting
        } else {
          this.pendingRecovery = null;
          this.focusOverride = null;
          this.setState('playing');
        }
      } else this.onLoadingProgress?.(this.loadingText());
    } else {
      this.input.takeMouse();
    }
    const t1 = performance.now();
    this.renderUpdate(dt, alpha);
    const t2 = performance.now();
    const k = 0.1;
    const tm = this.timings;
    tm.sim += (t1 - t0 - tm.sim) * k;
    tm.frame += (t2 - t0 - tm.frame) * k;
    tm.terrain += (this.tTerrain - tm.terrain) * k;
  };

  private terrainReadyForPlay(): boolean {
    const b = this.body;
    if (!b || !this.bodyShown) return true; // open space: no terrain to wait for
    if (!b.terrain.coarseReady) return false;
    if (this.mode === 'PILOTING' || this.mode === 'CRUISING') {
      const env = this.env.update(this.ship.currPos);
      if (env.clearance > 400) return true;
    }
    return b.collision.focusReady;
  }

  private loadingText(): string {
    const b = this.body;
    if (!b) return 'Preparing…';
    if (!b.terrain.coarseReady) return `Generating ${b.def.name}…`;
    return `Preparing terrain collision (${b.collision.count}/${Math.max(1, b.collision.focusKeys.length)})…`;
  }

  // ------------------------------------------------------------ simulation

  /** Local position of the entity the player currently controls. */
  controlledPos(): Vector3 {
    return this.mode === 'ON_FOOT' && this.player ? this.player.pos : this.ship.currPos;
  }

  private readControls(dt: number): ShipControls {
    const inp = this.input;
    const sens = this.settings.sensitivity;
    const inv = this.settings.invertY ? -1 : 1;
    this.stick.x += this.pendingMouse.x * FLIGHT.stickGain * sens;
    this.stick.y += -this.pendingMouse.y * FLIGHT.stickGain * sens * inv;
    this.pendingMouse.set(0, 0);
    if (this.stick.lengthSq() > 1) this.stick.normalize();
    this.stick.multiplyScalar(Math.exp(-dt / FLIGHT.stickTau));
    const key = (c: string) => (inp.isDown(c) ? 1 : 0);
    return {
      pitch: clamp(this.stick.y + (key('ArrowUp') - key('ArrowDown')) * inv, -1, 1),
      yaw: clamp(this.stick.x + key('ArrowRight') - key('ArrowLeft') + key('KeyD') - key('KeyA'), -1, 1),
      roll: key('KeyE') - key('KeyQ'),
      throttleAxis: key('KeyW') - key('KeyS'),
      vertical: key('Space') - Math.max(key('ControlLeft'), key('ControlRight')),
      boost: inp.isDown('ShiftLeft') || inp.isDown('ShiftRight'),
      brake: inp.isDown('KeyX'),
    };
  }

  private readWalk(): WalkInput {
    const inp = this.input;
    const k = 0.0022 * this.settings.sensitivity;
    const inv = this.settings.invertY ? -1 : 1;
    const key = (c: string) => (inp.isDown(c) ? 1 : 0);
    const w: WalkInput = {
      forward: key('KeyW') - key('KeyS') + key('ArrowUp') - key('ArrowDown'),
      right: key('KeyD') - key('KeyA') + key('ArrowRight') - key('ArrowLeft'),
      sprint: inp.isDown('ShiftLeft') || inp.isDown('ShiftRight'),
      jump: inp.consume('Space'),
      yaw: this.pendingMouse.x * k,
      pitch: -this.pendingMouse.y * k * inv,
    };
    this.pendingMouse.set(0, 0);
    return w;
  }

  /**
   * Terrain height above the reference body's datum for a unit direction. Until
   * that body's generator is active the body's maximum height is used, which
   * understates clearance (conservative).
   */
  terrainHeightAt(dir: Vector3): number {
    const b = this.body;
    if (b && b.def === this.ref) return b.heightAt(dir);
    return this.ref.maxHeight;
  }

  /** Collision residency demand around the controlled entity and along the ship's stopping path. */
  private updateCollisionDemand(): void {
    const b = this.body;
    if (!b) return;
    const onFoot = this.mode === 'ON_FOOT' && this.player && !this.focusOverride;
    const pos = this.focusOverride ?? (onFoot ? this.player!.pos : this.ship.currPos);
    const vel = onFoot ? this.player!.vel : this.ship.vel;
    const env = this.env.update(pos);
    _v1.copy(pos).sub(this.bodyCenterLocal);
    const decel = FLIGHT.brakeAtmo * 0.8;
    b.terrain.extraDemand = this.mode === 'CRUISING' ? [] : b.collision.computeWanted(_v1, vel, onFoot ? 0 : env.clearance, decel);
  }

  /**
   * The single place the gameplay mode changes. Entering ON_FOOT hands the
   * hooks the body's power only once an arrival unlocked it (charter K), and
   * the saved ability fields when the character is being restored.
   */
  private setMode(next: Mode, reason: OnFootExitReason = 'relocate', restored: AbilitySave | null = null): void {
    const prev = this.mode;
    if (prev === next) return;
    this.mode = next;
    const id = this.body?.def.id;
    const ctx = next === 'ON_FOOT' && id ? { body: id, power: this.expedition.activePower(id), restored } : null;
    this.onFoot.transition(prev, next, ctx, reason);
    if (prev === 'ON_FOOT') this.hud.setAbility(null);
  }

  private fixedUpdate(dt: number): void {
    this.simTime += dt;
    this.stepCount++;
    this.beforeStep?.(dt);
    if (this.stepCount % 6 === 0) this.updateCollisionDemand();
    const ship = this.ship;
    ship.beginStep();
    switch (this.mode) {
      case 'PILOTING':
        this.stepPiloting(dt);
        break;
      case 'CRUISING':
        this.stepCruising(dt);
        break;
      case 'LANDED':
        this.stepLanded();
        break;
      case 'ON_FOOT':
        this.stepOnFoot(dt);
        break;
    }
    ship.updateGearColliders();
    this.physics.step();
    ship.syncFromBody();
    if (this.mode === 'CRUISING') {
      // The cruise controller owns the transform; report its velocity.
      this.cruise.velocity(ship.vel);
      ship.angvel.set(0, 0, 0);
      if (this.pendingCruiseExit) this.finishCruise(this.pendingCruiseExit);
    }
    if (this.mode === 'PILOTING') this.checkTouchdown(dt);
    this.maybeRebase(this.controlledPos());
  }

  /**
   * Speed limit from terrain readiness: collision coverage, or no terrain shown
   * yet near a body that gets terrain (never near the Sun or a giant).
   */
  private readinessSpeedLimit(): number {
    if (this.body && this.bodyShown) return this.body.collision.speedLimit;
    _v4.copy(this.ship.currPos).add(this.origin);
    const dom = dominantBody(_v4);
    return dom.radii < 2.5 && surfaceReady(BODIES[dom.id]) ? 200 : Infinity;
  }

  private stepPiloting(dt: number): void {
    const ship = this.ship;
    const inp = this.input;
    if (inp.consume('KeyT')) this.transmit();
    if (inp.consume('KeyG')) {
      this.tryEngageCruise();
      if (this.mode !== 'PILOTING') {
        this.stepCruising(dt);
        return;
      }
    }
    const controls = this.state === 'playing' ? this.readControls(dt) : NO_CONTROLS;
    const env = this.env.update(ship.currPos);
    env.terrainSpeedLimit = this.readinessSpeedLimit();
    // Takeoff assistance: lift clear of the ground for a moment.
    if (this.takeoffTimer > 0) {
      this.takeoffTimer -= dt;
      if (controls.vertical >= 0) controls.vertical = 1;
    }
    // Landing assist toggle and probe.
    const lowEnough = env.clearance < LANDING.engageAltitude + 10;
    if (inp.consume('KeyL')) {
      if (this.assist.active) this.assist.disengage();
      else if (lowEnough && ship.speed < LANDING.engageSpeed && this.bodyShown) {
        this.assist.engage();
        this.onNotice?.('Landing assist', 'Braking and aligning to the surface.', true);
      } else {
        this.onNotice?.('Landing assist unavailable', `Descend below ${LANDING.engageAltitude} m and slow below ${LANDING.engageSpeed} m/s.`);
      }
    }
    if (this.assist.active && (controls.throttleAxis !== 0 || controls.vertical > 0 || controls.brake)) this.assist.disengage();
    const probing = this.assist.active || (ship.gearTarget > 0.5 && env.clearance < 60);
    if (probing) probeFootprint(this.physics, ship, env.up, this.probe);
    let override: FlightOverride | undefined;
    if (this.assist.active) {
      ship.gearTarget = 1;
      this.assist.compute(ship, env.up, this.probe, controls.yaw, this.override);
      override = this.override;
      if (this.assist.phase === 'holding' && this.assist.reason && this.assist.reason !== this.lastRejectReason) {
        this.counters.rejectedLandings++;
        this.onNotice?.('Landing rejected', this.assist.reason);
      }
      this.lastRejectReason = this.assist.phase === 'holding' ? this.assist.reason : null;
    } else {
      this.lastRejectReason = null;
      if (env.clearance < FLIGHT.gearClearance && ship.speed < 70) ship.gearTarget = 1;
      else if (env.clearance > FLIGHT.gearClearance + 25 || ship.speed > 95) ship.gearTarget = 0;
    }
    ship.flight.step(dt, { pos: ship.currPos, vel: ship.vel, quat: ship.currQuat, angvel: ship.angvel }, controls, env, this.flightOut, override);
    ship.applyControl(this.flightOut.force, this.flightOut.angvel);
  }

  // ---------------------------------------------------------------- cruise

  /** Whether cruise could engage at the ship's current position (for prompts). */
  cruiseAvailable(): boolean {
    _v4.copy(this.ship.currPos).add(this.origin);
    return insideEnvelope(_v4) === null;
  }

  private tryEngageCruise(): void {
    const ship = this.ship;
    _v4.copy(ship.currPos).add(this.origin);
    const chk = CruiseController.canEngage(_v4, ship.currQuat, ship.speed);
    if (!chk.ok) {
      this.counters.cruiseRefused++;
      this.onNotice?.('Cruise unavailable', chk.reason ?? '');
      return;
    }
    if (this.assist.active) this.assist.disengage();
    // The cap follows the route to the nav target (charter H); the Quiet System keeps 15 km/s.
    this.cruise.begin(_v4, ship.currQuat, ship.vel, cruiseHop(_v4, this.navTarget));
    this.cruiseStart = this.simTime;
    this.cruiseThrottle = 1;
    this.pendingCruiseExit = null;
    ship.gearTarget = 0;
    const b = ship.body;
    b.resetForces(false);
    b.setLinvel({ x: 0, y: 0, z: 0 }, false);
    b.setAngvel({ x: 0, y: 0, z: 0 }, false);
    b.setBodyType(RAPIER.RigidBodyType.KinematicPositionBased, true);
    this.setMode('CRUISING');
    this.counters.cruiseEngages++;
    this.onNotice?.('Cruise engaged', 'W/S set cruise speed · G or X returns to normal flight.', true);
  }

  private stepCruising(dt: number): void {
    const ship = this.ship;
    if (this.input.consume('KeyT')) this.transmit();
    const controls = this.state === 'playing' ? this.readControls(dt) : NO_CONTROLS;
    this.cruiseThrottle = clamp(this.cruiseThrottle + controls.throttleAxis * 0.5 * dt, 0, 1);
    const r = this.cruise.step(dt, {
      pitch: controls.pitch,
      yaw: controls.yaw,
      roll: controls.roll,
      throttle: this.cruiseThrottle,
      brake: controls.brake,
      toggleOff: this.input.consume('KeyG'),
    });
    // Rapier only carries the kinematic body to the pose cruise computed (one owner).
    const p = _v1.copy(this.cruise.pos).sub(this.origin);
    const q = this.cruise.quat;
    ship.body.setNextKinematicTranslation({ x: p.x, y: p.y, z: p.z });
    ship.body.setNextKinematicRotation({ x: q.x, y: q.y, z: q.z, w: q.w });
    if (r.exit) this.pendingCruiseExit = r.exit;
  }

  /** Hand the ship back to normal (dynamic) flight with the cruise velocity. */
  private finishCruise(reason: CruiseExitReason): void {
    this.pendingCruiseExit = null;
    const ship = this.ship;
    const b = ship.body;
    const v = this.cruise.velocity(_v2);
    b.setBodyType(RAPIER.RigidBodyType.Dynamic, true);
    b.setLinvel({ x: v.x, y: v.y, z: v.z }, true);
    b.setAngvel({ x: 0, y: 0, z: 0 }, true);
    ship.syncFromBody();
    ship.flight.reset();
    ship.flight.throttle = clamp(this.cruise.speed / FLIGHT.capSpace, 0, 1);
    this.setMode('PILOTING');
    pushBounded(this.cruiseLog, { start: this.cruiseStart, end: this.simTime, target: this.navTarget, ...this.cruise.legStats(), exit: reason });
    if (reason === 'approach') this.counters.cruiseExitApproach++;
    else if (reason === 'brake') this.counters.cruiseExitBrake++;
    else if (reason === 'toggle') this.counters.cruiseExitToggle++;
    else this.counters.cruiseExitSafety++;
    const near = this.cruise.aheadBody ? BODIES[this.cruise.aheadBody].name : null;
    const text =
      reason === 'approach' && near ? `Approaching ${near}: normal flight resumed.`
      : reason === 'safety' ? 'Safety stop at a planetary envelope.'
      : 'Normal flight resumed.';
    this.onNotice?.('Cruise ended', text, reason !== 'safety');
  }

  // --------------------------------------------------------------- landing

  /** After the physics step: declare LANDED only after stable supported contact. */
  private checkTouchdown(dt: number): void {
    const ship = this.ship;
    if (ship.gear < 0.95 || this.takeoffTimer > 0 || !this.bodyShown) {
      this.assist.stable = 0;
      return;
    }
    const env = this.env.update(ship.currPos);
    if (env.clearance > 8) {
      this.assist.stable = 0;
      return;
    }
    probeFootprint(this.physics, ship, env.up, this.probe);
    if (this.assist.touchdown(dt, ship, env.up, this.probe)) this.land();
  }

  private land(): void {
    this.audio.thump(1);
    this.parkShip();
    this.setMode('LANDED');
    this.assist.disengage();
    this.ship.flight.reset();
    this.counters.landings++;
    const def = this.body!.def;
    this.lastSafeLanding = {
      bodyId: def.id,
      posPlanet: this.ship.currPos.clone().sub(this.bodyCenterLocal),
      quat: this.ship.currQuat.clone(),
    };
    this.noteArrival(def);
    this.onNotice?.('Landed', `${def.name} — E to exit, Space to take off.`, true);
    this.input.clearAll(); // no held flight keys carry into the next takeoff
    this.autosave('landed');
  }

  /**
   * Record an arrival at a body (discovery plus its power, once). Called where
   * the ship comes to rest on a body (landing, placement, restore), never from
   * setMode, so mode changes stay free of progress side effects.
   */
  private noteArrival(def: BodyDef): void {
    this.expedition.arrive(def.id);
  }

  /** Park the ship at its current pose (no position snap). */
  private parkShip(): void {
    const b = this.ship.body;
    b.setLinvel({ x: 0, y: 0, z: 0 }, false);
    b.setAngvel({ x: 0, y: 0, z: 0 }, false);
    b.resetForces(false);
    b.setBodyType(RAPIER.RigidBodyType.KinematicPositionBased, true);
    this.ship.syncFromBody(true);
  }

  private takeOff(): void {
    const b = this.ship.body;
    b.setBodyType(RAPIER.RigidBodyType.Dynamic, true);
    b.setLinvel({ x: 0, y: 0, z: 0 }, true);
    this.setMode('PILOTING');
    this.takeoffTimer = 1.4;
    this.ship.flight.reset();
    this.counters.takeoffs++;
    this.input.clearPresses();
  }

  private stepLanded(): void {
    const inp = this.input;
    if (this.state !== 'playing') return;
    this.orbitMouse.add(this.pendingMouse);
    this.pendingMouse.set(0, 0);
    if (inp.consume('Space')) this.takeOff();
    else if (inp.consume('KeyE')) this.exitShip();
    else if (inp.consume('KeyT')) this.transmit();
  }

  /** Transmit the three-relay survey from the ship (the Quiet System's survey only). */
  private transmit(): void {
    if (PLAY_SYSTEM !== 'quiet') return;
    const e = this.expedition;
    if (e.state.transmitted) {
      this.onNotice?.('Survey transmitted', 'The survey has already been sent. Explore freely.', true);
      return;
    }
    if (!e.transmit()) {
      this.onNotice?.('Transmission unavailable', `All three relays must be active (${e.state.relays.length}/3).`);
      return;
    }
    this.counters.transmissions++;
    this.audio.complete();
    this.onNotice?.('Survey transmitted', 'Ilex, Vesper and Cairn are charted. The system remains open for exploration.', true);
    this.autosave('transmit');
  }

  /** Find a safe spot beside the ship (ground found by raycast, capsule clearance checked). */
  findExitSpot(out: Vector3): boolean {
    const ship = this.ship;
    const shape = playerShape();
    for (const spot of EXIT_SPOTS) {
      ship.localToWorld(spot, _v1);
      const up = _v2.copy(_v1).sub(this.bodyCenterLocal).normalize();
      const o = _v3.copy(_v1).addScaledVector(up, 4);
      const hit = this.physics.castRay(o.x, o.y, o.z, -up.x, -up.y, -up.z, 14, GROUPS.queryWalk);
      if (!hit) continue;
      if (hit.collider.parent()?.handle === ship.body.handle) continue; // under the hull
      if (hit.nx * up.x + hit.ny * up.y + hit.nz * up.z < Math.cos((40 * Math.PI) / 180)) continue;
      const center = o.addScaledVector(up, -hit.toi + FOOT_OFFSET + WALK.skin + 0.04);
      const rot = new Quaternion().setFromUnitVectors(new Vector3(0, 1, 0), up);
      const blocked = this.physics.world.intersectionWithShape(
        { x: center.x, y: center.y, z: center.z },
        { x: rot.x, y: rot.y, z: rot.z, w: rot.w },
        shape,
        undefined,
        GROUPS.queryWalk,
      );
      if (blocked) continue;
      out.copy(center);
      return true;
    }
    return false;
  }

  exitShip(): void {
    const spot = new Vector3();
    if (!this.findExitSpot(spot)) {
      this.onNotice?.('Cannot exit', 'No safe ground beside the ship here.');
      return;
    }
    const up = spot.clone().sub(this.bodyCenterLocal).normalize();
    const heading = this.ship.forward(new Vector3());
    if (this.player) this.player.dispose();
    this.player = new Player(this.physics, spot, up, heading);
    this.setMode('ON_FOOT');
    this.counters.exits++;
    this.physics.refreshQueries();
    this.input.clearAll();
    this.updateCollisionDemand();
  }

  private boardingPoint(out: Vector3): Vector3 {
    return this.ship.localToWorld(BOARDING_POINT, out);
  }

  /** Distance from the player's feet to the ship's boarding ladder (m). */
  boardingDistance(): number {
    if (!this.player) return Infinity;
    this.boardingPoint(_v1);
    return this.player.feet(_v2).distanceTo(_v1);
  }

  /**
   * Quit to the title. The character leaves ON_FOOT first, so the hooks exit and
   * clear their effects instead of freezing behind the title (Continue restores
   * from the save).
   */
  quitToTitle(): void {
    if (this.mode === 'ON_FOOT') {
      this.setMode('LANDED', 'relocate');
      this.player?.dispose();
      this.player = null;
      this.updateCollisionDemand();
    }
    this.setState('title');
  }

  private boardShip(): void {
    if (!this.player) return;
    this.setMode('LANDED', 'board');
    this.player.dispose();
    this.player = null;
    this.counters.boardings++;
    this.autosave('boarded');
    this.cameraRig.reset();
    this.physics.refreshQueries();
    this.input.clearAll(); // walking keys must not leak into the ship
    this.updateCollisionDemand();
  }

  private stepOnFoot(dt: number): void {
    const p = this.player;
    const body = this.body;
    if (!p || !body) return;
    const inp = this.input;
    const w = this.state === 'playing' ? this.readWalk() : { forward: 0, right: 0, sprint: false, jump: false, yaw: 0, pitch: 0 };
    if (this.onFoot.step(dt, w)) {
      // An active ability moved the character this step; the walk controller stays idle.
      this.updateScan(dt);
      if (inp.consume('KeyE')) this.interact();
      return;
    }
    // Never walk into missing collision data.
    _v1.copy(p.pos).sub(this.bodyCenterLocal);
    if (!body.collision.readyAt(_v1)) {
      w.forward = 0;
      w.right = 0;
      w.jump = false;
    }
    if (w.jump && p.grounded) this.counters.jumps++;
    _v2.copy(p.pos).add(this.origin);
    const c = body.def.center;
    const g = bodyGravity(body.def, _v2.x - c[0], _v2.y - c[1], _v2.z - c[2], _v3).length();
    const before = p.stepDistance;
    p.step(dt, w, this.bodyCenterLocal, g);
    this.footAcc += p.stepDistance - before;
    const stride = w.sprint ? 1.15 : 0.8;
    if (this.footAcc > stride) {
      this.footAcc = 0;
      this.audio.footstep(body.def.id, w.sprint);
    }
    if (p.justLanded) this.audio.thump(0.35);
    this.updateScan(dt);
    if (inp.consume('KeyE')) this.interact();
  }

  /** Nearest thing E would act on: an uncollected sample, the relay, or the ship's ladder. */
  interactionTarget(): { kind: 'sample' | 'relay' | 'ship'; id: string; distance: number } | null {
    const p = this.player;
    if (!p) return null;
    const feet = p.feet(_v1);
    let best: { kind: 'sample' | 'relay' | 'ship'; id: string; distance: number } | null = null;
    if (this.mission) {
      for (const t of this.mission.targets) {
        _v2.copy(t.pos).add(this.bodyCenterLocal);
        if (t.kind === 'sample') {
          if (this.expedition.isCollected(t.id)) continue;
          const d = feet.distanceTo(_v2);
          if (d < WALK.interactDistance && (!best || d < best.distance)) best = { kind: 'sample', id: t.id, distance: d };
        } else {
          // Relay: measured to the mast axis at the player's height.
          _v3.copy(_v2).addScaledVector(t.up, -3.2);
          const along = _v4.copy(feet).sub(_v3).dot(t.up);
          const d = _v4.copy(feet).sub(_v3).addScaledVector(t.up, -along).length();
          if (d < WALK.interactDistance + 1.2 && Math.abs(along) < 4 && (!best || d < best.distance)) best = { kind: 'relay', id: t.id, distance: d };
        }
      }
    }
    const bd = this.boardingDistance();
    if (bd < WALK.boardDistance && (!best || bd < best.distance)) best = { kind: 'ship', id: 'ship', distance: bd };
    return best;
  }

  private interact(): void {
    const t = this.interactionTarget();
    if (!t) return;
    const e = this.expedition;
    const body = this.body!.def;
    if (t.kind === 'ship') {
      // Never board in mid-air (charter J: flight never ends mid-air).
      if (this.player?.grounded) this.boardShip();
      return;
    }
    if (t.kind === 'sample') {
      if (e.collect(t.id)) {
        this.counters.collects++;
        this.audio.collect();
        this.mission?.sync((id) => e.isCollected(id), e.relayActive(body.id));
        this.onNotice?.(`${sampleName(body.id)} collected`, e.relayActive(body.id) ? 'Stowed in the sample case.' : `Take it to the ${body.name} relay.`, true);
        this.autosave('collect');
      } else this.counters.collectRepeats++;
      return;
    }
    const blocker = e.relayBlocker(body.id);
    if (blocker) {
      if (e.relayActive(body.id)) this.counters.relayRepeats++;
      this.onNotice?.(`${body.name} relay`, blocker);
      return;
    }
    e.activateRelay(body.id);
    this.counters.relayActivations++;
    this.audio.relay();
    this.mission?.sync((id) => e.isCollected(id), true);
    const next = e.objective(body.id);
    if (next.body && next.body !== body.id) this.setNavTarget(next.body);
    this.onNotice?.(
      `${body.name} relay active`,
      e.canTransmit ? 'All relays are live: transmit the survey from the ship (T).' : next.body ? `Course set for ${BODIES[next.body].name}.` : next.detail,
      true,
    );
    this.autosave('relay');
  }

  /** Scanner: aim at a natural object (or mission object) within range and hold F. */
  private findScanTarget(): ScanTarget | null {
    const p = this.player;
    const b = this.body;
    if (!p || !b) return null;
    // The crosshair ray: from the character camera when it is on, else the eye (PLAYER's Player.aim).
    const eye = _v1;
    const dir = _v2;
    p.aim(eye, dir);
    let best: ScanTarget | null = null;
    const a = new Vector3();
    const c = new Vector3();
    const consider = (id: string, species: Species | null, label: string, base: Vector3, top: Vector3, radius: number) => {
      const hit = rayCapsule(eye, dir, SCAN.range, base, top);
      if (!hit || hit.dist > radius || hit.t > SCAN.range) return;
      if (best && hit.t >= best.distance) return;
      best = { id, species, label, distance: hit.t };
    };
    _v3.copy(eye).sub(this.bodyCenterLocal);
    const near: PropInstance[] = b.props.nearby(_v3, SCAN.range + 15);
    for (const inst of near) {
      const sp = inst.species;
      if (!sp.scannable) continue;
      a.copy(inst.p).add(this.bodyCenterLocal);
      c.copy(a).addScaledVector(inst.up, inst.h);
      const r = Math.max(0.45, inst.h * sp.scanRadius);
      const known = this.expedition.state.species.includes(sp.id);
      consider(inst.id, sp, known ? sp.name : 'Unidentified specimen', a, c, r);
    }
    if (this.mission) {
      for (const t of this.mission.targets) {
        if (t.kind === 'sample' && this.expedition.isCollected(t.id)) continue;
        a.copy(t.pos).add(this.bodyCenterLocal).addScaledVector(t.up, -t.radius * 0.5);
        c.copy(t.pos).add(this.bodyCenterLocal).addScaledVector(t.up, t.kind === 'relay' ? 3.8 : t.radius * 0.5);
        consider(t.id, null, t.kind === 'relay' ? `${b.def.name} survey relay` : sampleName(b.def.id), a, c, t.kind === 'relay' ? 0.6 : t.radius);
      }
    }
    const found = best as ScanTarget | null;
    if (!found) return null;
    // Line of sight: terrain must not lie between the eye and the target.
    const hit = this.physics.castRay(eye.x, eye.y, eye.z, dir.x, dir.y, dir.z, found.distance, GROUPS.queryTerrain);
    if (hit && hit.toi < found.distance - 0.3) return null;
    return found;
  }

  private updateScan(dt: number): void {
    const target = this.findScanTarget();
    this.scanTarget = target;
    const st = this.scanState;
    const holding = this.state === 'playing' && this.input.isDown('KeyF');
    if (!holding || !target) {
      st.progress = 0;
      if (!holding) st.done = false;
      return;
    }
    if (st.id !== target.id) {
      st.id = target.id;
      st.progress = 0;
      st.done = false;
    }
    if (st.done) return;
    st.progress += dt;
    this.audio.scanTick(Math.min(1, st.progress / SCAN.holdTime));
    if (st.progress < SCAN.holdTime) return;
    st.done = true;
    this.counters.scans++;
    const sp = target.species;
    const r = this.expedition.scan(target.id, sp ? sp.id : null);
    this.audio.scanDone();
    if (sp && r.newSpecies) {
      this.onNotice?.(`Journal: ${sp.name}`, sp.description, true);
    } else if (sp) {
      this.onNotice?.(sp.name, r.newObject ? 'Another specimen logged.' : 'Already logged.', true);
    } else {
      this.onNotice?.(target.label, r.newObject ? 'Logged in the survey record.' : 'Already logged.', true);
    }
    if (r.newObject) this.autosave('scan');
  }

  /** Manual recovery: back to the ship (on foot) or to the last safe landing (ship). */
  recover(): void {
    this.counters.recoveries++;
    if (this.mode === 'ON_FOOT' && this.player) {
      // Wait for collision around the ship, then place the player beside it.
      this.pendingRecovery = () => {
        const spot = new Vector3();
        if (!this.findExitSpot(spot)) return false;
        this.player!.place(spot, spot.clone().sub(this.bodyCenterLocal).normalize());
        return true;
      };
      this.player.place(this.player.pos, this.player.up); // stop motion while waiting
      this.focusOverride = this.ship.currPos;
      this.setState('loading');
      return;
    }
    const pose = this.lastSafeLanding;
    if (!pose) {
      this.onNotice?.('Recovery unavailable', 'No safe landing has been recorded yet.');
      return;
    }
    this.placeShipLanded(pose.bodyId, pose.posPlanet, pose.quat);
    this.setState('loading');
  }

  /**
   * Put the ship, parked, at a planet-relative pose on any body (recovery and
   * save restore). Re-centers the origin, swaps the active body if needed and
   * leaves collision to be prepared by the loading state.
   */
  placeShipLanded(bodyId: BodyId, posPlanet: Vector3, quat: Quaternion): void {
    const def = BODIES[bodyId];
    if (this.mode === 'CRUISING') {
      this.pendingCruiseExit = null;
      this.ship.body.setBodyType(RAPIER.RigidBodyType.Dynamic, true);
    }
    if (this.player) {
      this.player.dispose();
      this.player = null;
    }
    const sys = new Vector3(def.center[0], def.center[1], def.center[2]).add(posPlanet);
    this.floating.rebaseTo(FloatingOrigin.rounded(sys), (d) => this.applyRebase(d));
    if (this.body && this.body.def.id !== bodyId) this.releaseBody();
    if (!this.body) this.activateBody(def);
    if (!this.bodyShown) this.showBody();
    this.ship.setPose(sys.sub(this.origin), quat);
    this.ship.gear = 1;
    this.ship.gearTarget = 1;
    this.parkShip();
    this.setMode('LANDED');
    this.noteArrival(def);
    this.assist.disengage();
    this.cameraRig.reset();
    this.lighting.snap();
    this.physics.refreshQueries();
    this.updateCollisionDemand();
  }

  /** While recovering on foot, collision is prepared around this point instead. */
  private focusOverride: Vector3 | null = null;

  /** Rebase when the controlled entity strays more than 2,048 m from the origin. */
  private maybeRebase(controlled: Vector3): void {
    if (!this.floating.needsRebase(controlled)) return;
    this.floating.rebaseAround(controlled, (d) => this.applyRebase(d));
  }

  /** Shift every local-space consumer by d (= oldOrigin - newOrigin); refresh queries. */
  private applyRebase(d: Vector3): void {
    this.physics.shiftAll(d.x, d.y, d.z);
    this.ship.onRebase(d);
    this.player?.onRebase(d);
    this.exhaust.onRebase(d);
    this.cameraRig.onRebase(d);
    this.updateBodyCenterLocal();
    this.physics.refreshQueries();
    this.rebaseCount++;
  }

  // -------------------------------------------------------------- handoff

  /** Create a body's detailed terrain/collision/props (not shown until the swap). */
  private activateBody(def: BodyDef): void {
    this.body = new ActiveBody(def, this.store, this.terrainMaterials, this.physics, this.render.spec.aerialSamples);
    // Keep the body coarse (its proxy's exact mesh) until the swap.
    this.body.terrain.holdCoarse = true;
    this.store.releaseOtherBodies();
    this.bodyShown = false;
    this.counters.activations++;
    this.logHandoff('activate', def.id);
    this.setRef(def);
  }

  private logHandoff(event: HandoffEvent['event'], body: BodyId): void {
    pushBounded(this.handoffLog, { t: this.simTime, event, body });
  }

  /** Swap the distant proxy for the local terrain (identical at level 0), then refine. */
  private showBody(): void {
    const b = this.body!;
    const def = b.def;
    this.render.scene.add(b.terrain.root, b.props.group);
    setAtmosphereBody(def);
    this.clouds.setBody(def, this.render.spec.cloudQuality);
    setTerrainPalette(this.terrainUniforms, def);
    b.terrain.holdCoarse = false;
    this.bodyShown = true;
    this.logHandoff('show', def.id);
    // Relay and sample deposits belong to the Quiet System survey only.
    if (SURVEY_BODIES.includes(def.id)) {
      const m = new MissionObjects(def, b.sites, b.gen, this.physics, this.render.spec.aerialSamples);
      m.sync((id) => this.expedition.isCollected(id), this.expedition.relayActive(def.id));
      this.render.scene.add(m.group);
      m.update(0, this.bodyCenterLocal);
      m.installCollider(this.bodyCenterLocal);
      this.mission = m;
    }
    if (this.navTarget === def.id && this.state === 'playing') {
      this.onNotice?.(`Approaching ${def.name}`, 'The landing site is marked.', true);
    }
  }

  /** Return the active body to its proxy and free its terrain, collision and props. */
  private releaseBody(): void {
    const b = this.body!;
    if (this.bodyShown && !b.terrain.atRoots) this.counters.releasesNotCoarse++;
    this.render.scene.remove(b.terrain.root, b.props.group);
    if (this.mission) {
      this.render.scene.remove(this.mission.group);
      this.mission.dispose();
      this.mission = null;
    }
    b.dispose();
    this.body = null;
    this.bodyShown = false;
    this.logHandoff('release', b.def.id);
    setAtmosphereBody(null);
    this.clouds.setBody(null, 0);
    this.physics.refreshQueries();
    this.counters.releases++;
  }

  /**
   * Activate within 3.3 radii (the coarse roots are already resident), show
   * at 3 radii, coarsen beyond 3.5 radii while departing and release beyond
   * 4 radii (hysteresis prevents thrashing). Only a body canActivate allows
   * (surface-ready; while cruising, the nav target) with its surface data loaded.
   */
  private updateHandoff(): void {
    const sys = _v4.copy(this.controlledPos()).add(this.origin);
    const b = this.body;
    if (b) {
      const R = b.def.radius;
      const d = distTo(sys, b.def.center);
      const flying = this.mode === 'PILOTING' || this.mode === 'CRUISING';
      if (this.bodyShown) {
        b.terrain.holdCoarse = flying && d > 3.5 * R;
        if (flying && ((d > BODY_HANDOFF.releaseRadii * R && b.terrain.atRoots) || d > (BODY_HANDOFF.releaseRadii + 0.5) * R)) this.releaseBody();
      } else if (d < BODY_HANDOFF.activateRadii * R && b.terrain.coarseReady) {
        this.showBody();
      } else if (d > BODY_HANDOFF.releaseRadii * R) {
        this.releaseBody();
      }
    }
    if (!this.body) {
      const cruising = this.mode === 'CRUISING';
      for (const id of BODY_IDS) {
        const def = BODIES[id];
        if (!canActivate(def, cruising, this.navTarget) || !bodyDataReady(def)) continue;
        if (distTo(sys, def.center) < (BODY_HANDOFF.activateRadii + 0.3) * def.radius) {
          this.activateBody(def);
          break;
        }
      }
    }
    if (!this.body) {
      const dom = BODIES[dominantBody(sys).id];
      if (dom !== this.ref) this.setRef(dom);
    }
    // Arrival indication at the navigation target's landing site.
    const t = this.navTarget;
    if (t && this.bodyShown && this.body && this.body.def.id === t && this.arrivedAt !== t) {
      const site = _v3.set(...this.body.sites.landing.dir).multiplyScalar(this.body.def.radius).add(this.bodyCenterLocal);
      if (this.controlledPos().distanceTo(site) < 600) {
        this.arrivedAt = t;
        this.onNotice?.(`${this.body.def.name} landing site`, 'Arrived. Land with L near the ground.', true);
      }
    }
  }

  private setRef(def: BodyDef): void {
    this.ref = def;
    this.env.body = def;
    this.groundAlbedo.setHex(def.palette.b1).convertSRGBToLinear();
    this.updateBodyCenterLocal();
  }

  private updateBodyCenterLocal(): void {
    const c = this.ref.center;
    this.bodyCenterLocal.set(c[0] - this.origin.x, c[1] - this.origin.y, c[2] - this.origin.z);
    atmoUniforms.uPlanetCenter.value.copy(this.bodyCenterLocal);
    if (this.body) this.body.terrain.root.position.copy(this.bodyCenterLocal);
  }

  /**
   * The opening pose: parked on the start body's landing clearing (startSite),
   * facing the Quiet survey relay or the first First Light route waypoint.
   */
  startPose(): { posPlanet: Vector3; quat: Quaternion } {
    const def = this.startBody;
    const site = startSite(def);
    const gen = this.body && this.body.def === def ? this.body.gen : null;
    const n = site.dir;
    const h = gen ? gen.height(n.x, n.y, n.z) : site.height;
    const posPlanet = n.clone().multiplyScalar(def.radius + h - GEAR_PAD_BOTTOM_Y);
    return { posPlanet, quat: quatFromForwardUp(site.forward, n) };
  }

  /**
   * Reset progress and return to the opening pose (title → New Expedition).
   * The opening pose is the first safe landing, so Recover always has a target.
   */
  newExpedition(): void {
    this.expedition.reset();
    this.expedition.dirty = true;
    this.navTarget = null;
    this.arrivedAt = null;
    this.simTime = 0;
    const start = this.startPose();
    this.lastSafeLanding = { bodyId: this.startBody.id, posPlanet: start.posPlanet.clone(), quat: start.quat.clone() };
    this.placeShipLanded(this.startBody.id, start.posPlanet, start.quat);
    this.mission?.sync((id) => this.expedition.isCollected(id), false);
    this.cameraRig.orbitYaw = 2.5;
    this.cameraRig.orbitPitch = 0.12;
  }

  /** Switch graphics preset at runtime (shader sample counts and AA mode apply on reload). */
  applyPreset(preset: QualityPreset): void {
    const r = this.render;
    if (preset !== r.preset) r.applyPreset(preset);
    const spec = PRESETS[preset];
    this.lighting.setShadowSize(spec.shadowSize);
    this.clouds.setBody(this.bodyShown && this.body ? this.body.def : null, spec.cloudQuality);
    this.proxies.setCloudQuality(spec.cloudQuality);
    this.adaptive.reset(preset === 'low' ? 33.3 : 16.7);
    this.applyAdaptive();
  }

  /** Apply the adaptive level (resolution now; prop density and LOD are read each frame). */
  applyAdaptive(): void {
    const scale = this.settings.adaptive ? this.adaptive.current.resolutionScale : 1;
    if (this.render.resolutionScale !== scale) {
      this.render.resolutionScale = scale;
      this.render.resize();
    }
  }

  /** Landing-site direction (unit vector from the body center) of any body. */
  landingSiteOf(id: BodyId): [number, number, number] {
    const d = computeSites(BODIES[id]).landing.dir;
    return [d[0], d[1], d[2]];
  }

  setNavTarget(id: BodyId | null): void {
    this.navTarget = id;
    this.arrivedAt = null;
    // Mid-cruise the cap follows the new destination's hop.
    if (this.mode === 'CRUISING') this.cruise.retarget(cruiseHop(this.cruise.pos, id));
  }

  private cameraTerrainDeficit(p: Vector3): number | null {
    if (!this.bodyShown) return null;
    _v2.copy(p).sub(this.bodyCenterLocal);
    const r = _v2.length();
    const ground = this.ref.radius + this.terrainHeightAt(_v2.divideScalar(r));
    const need = ground + 1.6 - r;
    return need > 0 ? need : null;
  }

  private applyEnvMap(t: Texture): void {
    for (const m of this.ship.visual.materials) {
      const sm = m as MeshStandardMaterial;
      if (sm.isMeshStandardMaterial) {
        sm.envMap = t;
        sm.needsUpdate = true;
      }
    }
  }

  // ------------------------------------------------------------- rendering

  private renderUpdate(dt: number, alpha: number): void {
    const r = this.render;
    const ship = this.ship;
    const landed = this.mode === 'LANDED' || this.mode === 'ON_FOOT';
    this.cloudTime += dt;
    ship.updateVisual(alpha, dt, landed);
    const shipPos = ship.root.position;
    const shipQuat = ship.root.quaternion;
    const radialUp = _v1.copy(shipPos).sub(this.bodyCenterLocal).normalize();
    const playing = this.state === 'playing' || this.state === 'paused' || this.state === 'loading' || this.state === 'panel';

    // True when the ON_FOOT hooks placed the camera (they also own its field of view).
    let hookCamera = false;
    if (playing && this.mode === 'ON_FOOT' && this.player) {
      const p = this.player;
      hookCamera = this.onFoot.frame(dt, alpha);
      if (!hookCamera) this.cameraRig.firstPerson(p.eye(alpha, _v3), p.up, p.heading, p.pitch);
    } else if (playing && (this.mode === 'PILOTING' || this.mode === 'CRUISING')) {
      this.cameraRig.chase(dt, shipPos, shipQuat, ship.speed, radialUp, this.mode === 'CRUISING');
    } else {
      const fwd = _v2.set(0, 0, -1).applyQuaternion(shipQuat);
      this.cameraRig.orbit(dt, shipPos, radialUp, fwd, this.orbitMouse.x, this.orbitMouse.y, this.state === 'title');
      this.orbitMouse.set(0, 0);
    }
    if (!hookCamera) this.cameraRig.updateFov(dt, ship.flight.boostActive && this.mode === 'PILOTING', this.settings.reducedMotion);
    ship.root.visible = true;
    if (this.photoCamera) this.applyPhotoCamera();

    this.exhaust.setPixelScale(r.size.y, r.camera.fov);
    const thrust = this.mode === 'CRUISING' ? 1 : landed ? 0 : Math.min(1, ship.flight.forwardThrust / 35);
    this.exhaust.update(this.state === 'playing' ? dt : 0, shipPos, shipQuat, ship.vel, thrust, ship.flight.boostActive || this.mode === 'CRUISING');

    // Camera far plane suited to the reference body (log depth handles the range).
    const camDist = r.camera.position.distanceTo(this.bodyCenterLocal);
    const R = this.ref.radius;
    const horizon = Math.sqrt(Math.max(camDist * camDist - R * R, 0)) + Math.sqrt((R + 2000) ** 2 - R * R);
    const far = clamp(horizon * 1.2 + 2000, 5000, 2.5e6);
    if (Math.abs(r.camera.far - far) > far * 0.05) {
      r.camera.far = far;
      r.camera.updateProjectionMatrix();
    }
    r.camera.updateMatrixWorld();

    // Terrain LOD/morph/culling/colliders for the active body.
    const tt = performance.now();
    if (this.body) {
      const b = this.body;
      const lvl = this.settings.adaptive ? this.adaptive.current : null;
      b.terrain.splitPx = r.spec.splitPx * (lvl ? lvl.splitScale : 1);
      b.terrain.maxChunks = r.spec.maxChunks;
      const focus = this.focusOverride ?? this.controlledPos();
      b.props.setQuality(r.spec.propDensity * (lvl ? lvl.propScale : 1), r.spec.propRange);
      const nearGround = this.mode === 'LANDED' || this.mode === 'ON_FOOT' || (this.mode === 'PILOTING' && this.env.update(ship.currPos).clearance < 150);
      b.update(dt, r.camera, this.bodyCenterLocal, focus, r.size.y, nearGround);
    }
    this.mission?.update(dt, this.bodyCenterLocal);
    this.tTerrain = performance.now() - tt;

    const focusPos = this.mode === 'ON_FOOT' && this.player ? this.player.pos : shipPos;
    // The environment map is GPU work outside the frame's render: only rebuild it on drawn frames.
    const drawn = this.renderEvery <= 1 || this.frameCount % this.renderEvery === 0;
    this.lighting.update(dt, focusPos, this.ref, this.bodyCenterLocal, this.groundAlbedo, this.body !== null, drawn);

    r.bgCamera.quaternion.copy(r.camera.quaternion);
    r.bgCamera.fov = r.camera.fov;
    r.bgCamera.updateProjectionMatrix();
    r.bgCamera.updateMatrixWorld();
    _q.copy(r.bgCamera.quaternion);
    const sc = this.lighting.skyColor;
    const skyLum = 0.2126 * sc.r + 0.7152 * sc.g + 0.0722 * sc.b;
    const starFade = 1 - Math.min(1, Math.max(0, (skyLum - 0.004) / 0.03));
    this.space.update(_q, r.renderer.getPixelRatio(), starFade);
    this.updateProxies();
    updateSkyMesh(this.sky, r.camera);
    this.clouds.update(this.cloudTime, this.bodyCenterLocal, this.lighting.skyColor);
    this.updateAmbience(dt);

    if (this.state === 'playing' || this.state === 'paused' || this.state === 'panel') this.updateHud();
    const tr = performance.now();
    if (this.renderEvery <= 1 || this.frameCount % this.renderEvery === 0) r.render();
    this.timings.render += (performance.now() - tr - this.timings.render) * 0.1;
  }

  /**
   * Distant bodies: camera-relative, scaled by BG_SCALE. They share the local
   * scene's lighting while the camera is in space so the handoff at three radii
   * is seamless; from inside an atmosphere they keep the space ambient.
   */
  private updateProxies(): void {
    const L = this.proxies.light;
    const lt = this.lighting;
    L.sunColor.setRGB(1.0, 0.96, 0.9).multiplyScalar(lt.sun.intensity);
    _v2.copy(this.render.camera.position).sub(this.bodyCenterLocal);
    const alt = _v2.length() - this.ref.radius;
    const inAir = !!this.ref.atmosphere && alt < this.ref.atmosphereHeight * 2;
    if (inAir) {
      L.hemiSky.setRGB(0.064, 0.0704, 0.096).multiplyScalar(lt.hemi.intensity);
      L.hemiGround.copy(L.hemiSky);
      L.cloudAmbient.setRGB(0.02, 0.022, 0.03);
    } else {
      L.hemiSky.copy(lt.hemi.color).multiplyScalar(lt.hemi.intensity);
      L.hemiGround.copy(lt.hemi.groundColor).multiplyScalar(lt.hemi.intensity);
      L.cloudAmbient.copy(lt.skyColor);
    }
    L.hemiUp.copy(lt.hemi.position).normalize();
    _v3.copy(this.render.camera.position).add(this.origin);
    this.proxies.update(_v3, this.bodyShown && this.body ? this.body.def.id : null, this.cloudTime);
  }

  private readonly moteColor = new Color();

  /** Motes and the sound mix follow the listener's surroundings. */
  private updateAmbience(dt: number): void {
    const r = this.render;
    const def = this.ref;
    const cam = r.camera.position;
    const camAlt = cam.distanceTo(this.bodyCenterLocal) - def.radius - this.terrainHeightAt(_v2.copy(cam).sub(this.bodyCenterLocal).normalize());
    const listenerDensity = this.env.update(this.controlledPos()).density;
    let motes = 0;
    if (def.atmosphere && this.bodyShown) {
      motes = (1 - Math.min(1, Math.max(0, (camAlt - 40) / 160))) * 0.55;
      if (def.id === 'ilex') this.moteColor.setRGB(0.9, 0.95, 0.72);
      else this.moteColor.setRGB(1.0, 0.78, 0.55);
    }
    _v3.copy(cam).add(this.origin);
    this.motes.update(dt, cam, _v3, this.moteColor, motes, r.size.y, r.camera.fov);
    if (this.state === 'playing') {
      const onFoot = this.mode === 'ON_FOOT' && !!this.player;
      const cruising = this.mode === 'CRUISING';
      this.audio.update(dt, {
        thrust: cruising ? 0.6 : this.mode === 'PILOTING' ? Math.min(1, this.ship.flight.forwardThrust / 35 + this.ship.flight.thrustAccel.length() / 120) : 0,
        boost: cruising || (this.ship.flight.boostActive && this.mode === 'PILOTING'),
        airspeed: this.ship.speed,
        density: listenerDensity,
        shipDistance: onFoot ? this.player!.pos.distanceTo(this.ship.currPos) : 0,
        shipActive: this.mode === 'PILOTING' || cruising,
        onFoot,
        body: def.id,
      });
    }
  }

  private applyPhotoCamera(): void {
    const b = this.body;
    if (!b) return;
    const pc = this.photoCamera!;
    const sites = b.sites;
    const n = new Vector3(...sites.landing.dir);
    const relay = new Vector3(...sites.relay.dir);
    const fz = relay.sub(n.clone().multiplyScalar(relay.dot(n))).normalize();
    const fx = new Vector3().crossVectors(fz, n).normalize();
    const R = b.def.radius;
    // Offsets are tangent-plane meters; heights are above the local terrain.
    const at = (o: [number, number, number]) => {
      const d = n.clone().addScaledVector(fx, o[0] / R).addScaledVector(fz, o[2] / R).normalize();
      return d.multiplyScalar(R + this.terrainHeightAt(d) + o[1]).add(this.bodyCenterLocal);
    };
    const cam = this.render.camera;
    cam.position.copy(at(pc.eye));
    cam.up.copy(n);
    cam.lookAt(at(pc.target));
    cam.updateMatrixWorld();
  }

  /** Navigation marker: the target body, or its landing site once that body is local. */
  private navMarker(markers: MarkerSpec[]): void {
    const t = this.navTarget;
    if (!t) return;
    const def = BODIES[t];
    const from = this.controlledPos();
    if (this.bodyShown && this.body && this.body.def.id === t) {
      const s = this.body.sites.landing;
      const n = _v2.set(...s.dir);
      const pos = n.clone().multiplyScalar(def.radius + this.terrainHeightAt(n) + 3).add(this.bodyCenterLocal);
      const distance = from.distanceTo(pos);
      // Down at the site already: the destination marker has done its job.
      if ((this.mode === 'LANDED' || this.mode === 'ON_FOOT') && distance < 300) return;
      markers.push({ id: 'nav', label: `${def.name} landing site`, pos, kind: 'nav', distance });
    } else {
      const pos = new Vector3(def.center[0] - this.origin.x, def.center[1] - this.origin.y, def.center[2] - this.origin.z);
      markers.push({ id: 'nav', label: def.name, pos, kind: 'nav', distance: Math.max(0, from.distanceTo(pos) - def.radius) });
    }
  }

  private updateHud(): void {
    const ship = this.ship;
    const def = this.ref;
    const hud = this.hud;
    const prompts: Prompt[] = [];
    const markers: MarkerSpec[] = [];
    const modeName = { PILOTING: 'Flight', CRUISING: 'Cruise', LANDED: 'Landed', ON_FOOT: 'On foot' }[this.mode];
    hud.setLocation(this.bodyShown ? def.name.toUpperCase() : `OPEN SPACE · ${def.name.toUpperCase()}`, modeName);
    hud.showFlight(this.mode !== 'ON_FOOT');
    const exp = this.expedition;
    if (this.mode === 'ON_FOOT' && this.player) {
      const p = this.player;
      hud.walk(this.boardingDistance(), bodyGravity(def, p.pos.x + this.origin.x - def.center[0], p.pos.y + this.origin.y - def.center[1], p.pos.z + this.origin.z - def.center[2], _v1).length());
      const bd = this.boardingDistance();
      const it = this.interactionTarget();
      if (it?.kind === 'sample') prompts.push({ key: 'E', text: `Collect ${sampleName(def.id).toLowerCase()}` });
      else if (it?.kind === 'relay') {
        const blocker = exp.relayBlocker(def.id);
        prompts.push(blocker ? { text: blocker, dim: true } : { key: 'E', text: 'Activate relay' });
      } else if (it?.kind === 'ship') prompts.push({ key: 'E', text: 'Board ship' });
      const st = this.scanTarget;
      if (st) {
        const scanning = this.input.isDown('KeyF') && this.scanState.id === st.id;
        const known = st.species ? exp.state.species.includes(st.species.id) : exp.state.scanned.includes(st.id);
        if (!scanning) prompts.push({ key: 'F', text: `Hold to scan · ${st.label}${known ? ' (logged)' : ''}` });
        hud.scan(scanning ? Math.min(1, this.scanState.progress / SCAN.holdTime) : null, st.label);
      } else hud.scan(null, '');
      hud.crosshairTarget(st !== null);
      // Beside the ship the boarding prompt is enough; the marker is for finding it.
      if (bd > WALK.boardDistance + 5) markers.push({ id: 'ship', label: 'Ship', pos: this.boardingPoint(_v2).clone(), kind: 'ship', distance: bd });
      hud.warning(null);
    } else {
      hud.scan(null, '');
      hud.crosshairTarget(false);
      const env = this.env.update(ship.currPos);
      const inSpace = !this.bodyShown || env.altitude > def.atmosphereHeight + 12000;
      const cruising = this.mode === 'CRUISING';
      hud.flight({
        speed: ship.speed,
        throttle: cruising ? this.cruiseThrottle : ship.flight.throttle,
        speedFraction: cruising ? ship.speed / this.cruise.maxSpeed : ship.flight.speedCap > 0 ? ship.speed / Math.max(ship.flight.speedCap, 1) : 0,
        altitude: inSpace ? env.altitude : this.mode === 'LANDED' ? 0 : env.clearance,
        altitudeApprox: inSpace,
        verticalSpeed: this.mode === 'LANDED' ? 0 : ship.vel.dot(env.up),
        boost: ship.flight.boostActive && !cruising,
        assist: this.assist.active,
        cruise: cruising,
        gear: ship.gearTarget > 0.5,
      });
      hud.stick(this.stick.x, this.stick.y);
      if (exp.canTransmit) prompts.push({ key: 'T', text: 'Transmit survey' });
      if (this.mode === 'LANDED') {
        prompts.push({ key: 'E', text: 'Exit ship' }, { key: 'Space', text: 'Take off' });
        hud.warning(null);
      } else if (cruising) {
        const c = this.cruise;
        prompts.push({ key: 'G', text: 'Leave cruise' }, { key: 'X', text: 'Brake' }, { key: 'W/S', text: 'Cruise speed' });
        hud.warning(c.exiting ? 'Leaving cruise…' : c.limited ? `Slowing: ${c.aheadBody ? `${BODIES[c.aheadBody].name} ahead` : 'edge of the charted system'}` : null);
      } else {
        if (this.assist.active) {
          const phase = this.assist.phase === 'descending' ? 'Descending' : this.assist.phase === 'braking' ? 'Braking' : 'Holding';
          prompts.push({ key: 'L', text: `Landing assist: ${phase}` });
          hud.warning(this.assist.phase === 'holding' ? this.assist.reason : null);
        } else {
          if (env.clearance < LANDING.engageAltitude + 10 && ship.speed < LANDING.engageSpeed) prompts.push({ key: 'L', text: 'Landing assist' });
          if (this.cruiseAvailable()) prompts.push({ key: 'G', text: 'Cruise' });
          const limit = this.readinessSpeedLimit();
          const limited = limit < ship.flight.speedCap && limit < 200;
          hud.warning(limited ? 'Preparing terrain ahead — speed limited' : null);
        }
      }
    }
    this.missionMarkers(markers);
    this.navMarker(markers);
    hud.prompts(prompts);
    this.markers.update(this.render.camera, markers, window.innerWidth, window.innerHeight);
    if (PLAY_SYSTEM === 'quiet') {
      const here = this.bodyShown && this.body ? this.body.def.id : null;
      const obj = exp.objective(here);
      let detail = obj.detail;
      if (!exp.state.transmitted && obj.body && obj.body !== here) {
        detail = this.navTarget === obj.body
          ? 'Follow the marker · G cruises between worlds once clear of the atmosphere.'
          : `Open navigation (Tab) and set course for ${BODIES[obj.body].name}.`;
      }
      hud.setObjective(obj.title, detail);
    } else {
      // The relay survey is the Quiet System's; Sol is free travel until its First Light objectives.
      hud.setObjective(
        'Explore the Solar System',
        this.navTarget
          ? 'Follow the marker · G cruises between worlds once clear of the atmosphere.'
          : `Open navigation (Tab) and set a course. Landing sites: ${SURFACE_READY.map((id) => BODIES[id].name).join(', ')}.`,
      );
    }
    const inv = exp.state.inventory;
    hud.inventory(SURVEY_BODIES.filter((b) => inv[b] > 0).map((b) => ({ name: sampleName(b), count: inv[b] })));
  }

  /** Relay and sample markers on the shown body while they are still needed. */
  private missionMarkers(markers: MarkerSpec[]): void {
    const b = this.body;
    if (!b || !this.bodyShown || !this.mission) return;
    const exp = this.expedition;
    const id = b.def.id;
    const from = this.controlledPos();
    const relayDone = exp.relayActive(id);
    const samples: MarkerSpec[] = [];
    for (const t of this.mission.targets) {
      const pos = t.pos.clone().add(this.bodyCenterLocal);
      const d = from.distanceTo(pos);
      if (t.kind === 'relay') {
        if (!relayDone || d < 300) markers.push({ id: t.id, label: relayDone ? 'Relay (active)' : `${b.def.name} relay`, pos, kind: 'relay', distance: d });
      } else if (!relayDone && exp.state.inventory[id] === 0 && !exp.isCollected(t.id) && d < 400) {
        samples.push({ id: t.id, label: sampleName(id), pos, kind: 'sample', distance: d });
      }
    }
    // Only the nearest deposit is labeled; the others are small glyphs.
    samples.sort((a, c) => (a.distance ?? 0) - (c.distance ?? 0));
    samples.forEach((m, i) => markers.push(i === 0 ? m : { ...m, minor: true }));
  }

  // ------------------------------------------------------------- saving

  /** Progress changed or the player moved meaningfully since the last save. */
  saveDirty(): boolean {
    if (this.expedition.dirty) return true;
    _v4.copy(this.controlledPos()).add(this.origin);
    return _v4.distanceTo(this.lastSavedPos) > 25 || this.mode !== this.lastSavedMode;
  }

  /** Request a save (the persistence layer writes it and reports the result). */
  autosave(reason: string): void {
    this.autosaveTimer = 0;
    this.counters.autosaves++;
    this.onAutosave?.(reason);
  }

  /** Called by the persistence layer once a snapshot has been durably written. */
  markSaved(data: SaveData): void {
    this.expedition.dirty = false;
    const p = data.player ? data.player.sys : data.ship.sys;
    this.lastSavedPos.set(p[0], p[1], p[2]);
    this.lastSavedMode = data.mode;
  }

  private lastSavedMode: Mode = 'LANDED';

  /** Serializable snapshot: poses, mode and progress only (terrain is regenerated). */
  snapshot(): SaveData {
    const ship = this.ship;
    const cruising = this.mode === 'CRUISING';
    const sys = cruising ? this.cruise.pos.clone() : ship.currPos.clone().add(this.origin);
    const q = cruising ? this.cruise.quat : ship.currQuat;
    const parked = this.mode === 'LANDED' || this.mode === 'ON_FOOT';
    const v = parked ? new Vector3() : cruising ? this.cruise.velocity(new Vector3()) : ship.vel;
    const p = this.player;
    let player: SaveData['player'] = null;
    if (this.mode === 'ON_FOOT' && p) {
      const f = p.feet(new Vector3()).add(this.origin);
      // The ability state is the hooks' (PLAYER); walking when none are installed.
      const abilityState = this.onFoot.saveState()?.abilityState ?? 'walk';
      player = { sys: [f.x, f.y, f.z], heading: [p.heading.x, p.heading.y, p.heading.z], pitch: p.pitch, abilityState };
    }
    const l = this.lastSafeLanding;
    const e = this.expedition;
    return {
      schema: SAVE_SCHEMA,
      generator: GENERATOR_VERSION,
      seed: WORLD_SEED,
      savedAt: new Date().toISOString(),
      playTime: this.simTime,
      system: this.ref.system,
      mode: this.mode,
      bodyId: this.body && this.bodyShown ? this.body.def.id : null,
      ship: {
        sys: [sys.x, sys.y, sys.z],
        quat: [q.x, q.y, q.z, q.w],
        vel: [v.x, v.y, v.z],
        gear: ship.gearTarget > 0.5 ? 1 : 0,
        throttle: clamp(ship.flight.throttle, 0, 1),
      },
      player,
      cruise: cruising ? { speed: this.cruise.speed, throttle: this.cruiseThrottle } : null,
      lastSafeLanding: l ? { bodyId: l.bodyId, posPlanet: [l.posPlanet.x, l.posPlanet.y, l.posPlanet.z], quat: [l.quat.x, l.quat.y, l.quat.z, l.quat.w] } : null,
      navTarget: this.navTarget,
      discoveries: [...e.discoveries],
      unlocked: [...e.unlocked],
      settings: { ...this.settings },
      expedition: JSON.parse(JSON.stringify(e.state)),
    };
  }

  /**
   * Restore a validated snapshot. The game enters the loading state (no
   * movement) until terrain and collision around the saved position are ready;
   * then the saved mode is revalidated before play resumes.
   */
  restore(data: SaveData): void {
    this.counters.restores++;
    this.expedition.reset(JSON.parse(JSON.stringify(data.expedition)), [...data.discoveries], [...data.unlocked]);
    this.navTarget = data.navTarget;
    this.arrivedAt = null;
    this.simTime = data.playTime;
    const l = data.lastSafeLanding;
    this.lastSafeLanding = l ? { bodyId: l.bodyId, posPlanet: new Vector3(...l.posPlanet), quat: new Quaternion(...l.quat).normalize() } : null;
    const ship = this.ship;
    if (this.mode === 'CRUISING') this.pendingCruiseExit = null;
    if (this.player) {
      this.player.dispose();
      this.player = null;
    }
    this.assist.disengage();
    const sys = new Vector3(...data.ship.sys);
    const quat = new Quaternion(...data.ship.quat).normalize();
    this.floating.rebaseTo(FloatingOrigin.rounded(sys), (d) => this.applyRebase(d));
    // The saved body, or any body the handoff could activate whose range contains the ship.
    let bodyId = data.bodyId && surfaceReady(BODIES[data.bodyId]) ? data.bodyId : null;
    if (!bodyId) {
      for (const id of BODY_IDS) {
        const def = BODIES[id];
        if (!canActivate(def, data.mode === 'CRUISING', data.navTarget)) continue;
        if (distTo(sys, def.center) < BODY_HANDOFF.activateRadii * def.radius) bodyId = id;
      }
    }
    if (this.body && this.body.def.id !== bodyId) this.releaseBody();
    if (bodyId && !this.body) this.activateBody(BODIES[bodyId]);
    if (this.body && !this.bodyShown) this.showBody();
    if (!this.body) this.setRef(BODIES[dominantBody(sys).id]);
    this.mission?.sync((id) => this.expedition.isCollected(id), this.expedition.relayActive(this.body!.def.id));
    const local = sys.clone().sub(this.origin);
    const vel = new Vector3(...data.ship.vel);
    this.focusOverride = null;
    this.pendingRecovery = null;
    if (data.mode === 'LANDED' || data.mode === 'ON_FOOT') {
      ship.setPose(local, quat);
      ship.gear = 1;
      ship.gearTarget = 1;
      this.parkShip();
      this.setMode('LANDED', 'restore');
      if (data.mode === 'ON_FOOT' && data.player) {
        const pl = data.player;
        const feet = new Vector3(...pl.sys).sub(this.origin);
        this.focusOverride = feet.clone();
        // The hooks get the saved ability state and the unlocks as of placement (after this restore's arrival).
        this.pendingRecovery = () =>
          this.placeRestoredPlayer(feet, new Vector3(...pl.heading), pl.pitch, { abilityState: pl.abilityState, unlocked: [...this.expedition.unlocked] });
      }
    } else {
      ship.body.setBodyType(RAPIER.RigidBodyType.Dynamic, true);
      ship.setPose(local, quat, vel);
      ship.gear = data.ship.gear;
      ship.gearTarget = data.ship.gear;
      ship.flight.reset();
      ship.flight.throttle = data.ship.throttle;
      this.setMode('PILOTING', 'restore');
      if (data.mode === 'CRUISING' && data.cruise) {
        // Cruise resumes only if its clearance is still safe at the saved speed,
        // braking at the acceleration the saved hop gives (begin sets it).
        const fwd = new Vector3(0, 0, -1).applyQuaternion(quat);
        this.cruise.begin(sys, quat, fwd.clone().multiplyScalar(data.cruise.speed), cruiseHop(sys, data.navTarget));
        const need = (data.cruise.speed * data.cruise.speed) / (2 * this.cruise.accel) + CRUISE.safetyMargin;
        if (!insideEnvelope(sys) && freeDistance(sys, fwd).distance > need) {
          this.cruise.speed = data.cruise.speed;
          this.cruiseStart = this.simTime;
          this.cruiseThrottle = data.cruise.throttle;
          ship.body.setBodyType(RAPIER.RigidBodyType.KinematicPositionBased, true);
          ship.setPose(local, quat);
          this.setMode('CRUISING');
        } else {
          const v = vel.length();
          if (v > CRUISE.exitSpeed) ship.setPose(local, quat, vel.multiplyScalar(CRUISE.exitSpeed / v));
          this.onNotice?.('Cruise not resumed', 'Saved cruise was no longer clear; normal flight restored.');
        }
      }
    }
    ship.syncFromBody(true);
    this.cameraRig.reset();
    this.lighting.snap();
    this.stick.set(0, 0);
    this.physics.refreshQueries();
    this.markSaved(data);
    // A surface save is an arrival there (a no-op for records this build wrote;
    // after markSaved so an imported record missing it is saved again).
    if (data.mode === 'LANDED' || data.mode === 'ON_FOOT') this.noteArrival(this.body!.def);
    this.updateCollisionDemand();
    this.setState('loading');
  }

  /** Place a restored on-foot player once collision is ready; falls back to beside the ship. */
  private placeRestoredPlayer(feet: Vector3, heading: Vector3, pitch: number, restored: AbilitySave): boolean {
    const b = this.body;
    if (!b) return true;
    _v1.copy(feet).sub(this.bodyCenterLocal);
    if (!b.collision.readyAt(_v1)) return false;
    const up = feet.clone().sub(this.bodyCenterLocal).normalize();
    // Ground under the saved feet, then a capsule clearance check.
    const o = feet.clone().addScaledVector(up, 3);
    const hit = this.physics.castRay(o.x, o.y, o.z, -up.x, -up.y, -up.z, 8, GROUPS.queryWalk);
    let center: Vector3 | null = null;
    if (hit) {
      center = o.addScaledVector(up, -hit.toi + FOOT_OFFSET + WALK.skin + 0.04);
      const rot = new Quaternion().setFromUnitVectors(new Vector3(0, 1, 0), up);
      const blocked = this.physics.world.intersectionWithShape(
        { x: center.x, y: center.y, z: center.z }, { x: rot.x, y: rot.y, z: rot.z, w: rot.w }, playerShape(), undefined, GROUPS.queryWalk,
      );
      if (blocked) center = null;
    }
    if (!center) {
      const spot = new Vector3();
      if (!this.findExitSpot(spot)) return false;
      center = spot;
      this.onNotice?.('Position adjusted', 'The saved spot was not clear; you are beside the ship.');
    }
    const h = heading.addScaledVector(up, -heading.dot(up)).normalize();
    this.player = new Player(this.physics, center, up, h);
    this.player.pitch = pitch;
    this.setMode('ON_FOOT', 'relocate', restored);
    this.physics.refreshQueries();
    return true;
  }

  /** Add mouse motion as if it came from the pointer (test hooks). */
  injectMouse(dx: number, dy: number): void {
    this.pendingMouse.x += dx;
    this.pendingMouse.y += dy;
  }

  /** Read-only state snapshot for diagnostics and automated tests. */
  telemetry(): Record<string, unknown> {
    const ship = this.ship;
    const sys = ship.currPos.clone().add(this.origin);
    const env = this.env.update(ship.currPos);
    const st = this.render.stats;
    const b = this.body;
    const store = this.store;
    const p = this.player;
    let playerInfo: Record<string, unknown> | null = null;
    if (p) {
      const feet = p.feet(new Vector3());
      const dir = feet.clone().sub(this.bodyCenterLocal);
      const r = dir.length();
      dir.divideScalar(r);
      playerInfo = {
        system: feet.clone().add(this.origin).toArray(),
        grounded: p.grounded,
        speed: p.speed,
        vVert: p.vVert,
        heightAboveSurface: r - (this.ref.radius + this.terrainHeightAt(dir)),
        boardingDistance: this.boardingDistance(),
        heading: p.heading.toArray(),
        up: p.up.toArray(),
      };
    }
    const mem = (performance as unknown as { memory?: { usedJSHeapSize: number } }).memory;
    const c = this.cruise;
    const lt = this.lighting;
    return {
      state: this.state,
      mode: this.mode,
      system: this.ref.system,
      body: b ? b.def.id : null,
      bodyShown: this.bodyShown,
      ref: this.ref.id,
      navTarget: this.navTarget,
      discoveries: [...this.expedition.discoveries],
      unlocked: [...this.expedition.unlocked],
      objective: this.expedition.objective(this.bodyShown && b ? b.def.id : null),
      simTime: this.simTime,
      frame: this.frameCount,
      frameDt: this.lastFrameDt,
      shipSystem: [sys.x, sys.y, sys.z],
      shipLocal: [ship.currPos.x, ship.currPos.y, ship.currPos.z],
      origin: [this.origin.x, this.origin.y, this.origin.z],
      speed: ship.speed,
      vel: [ship.vel.x, ship.vel.y, ship.vel.z],
      angvel: [ship.angvel.x, ship.angvel.y, ship.angvel.z],
      quat: [ship.currQuat.x, ship.currQuat.y, ship.currQuat.z, ship.currQuat.w],
      altitude: env.altitude,
      clearance: env.clearance,
      verticalSpeed: ship.vel.dot(env.up),
      throttle: ship.flight.throttle,
      speedCap: ship.flight.speedCap,
      terrainSpeedLimit: this.readinessSpeedLimit(),
      boost: ship.flight.boostActive,
      gear: ship.gear,
      cruise: {
        speed: c.speed, throttle: this.cruiseThrottle, ahead: Number.isFinite(c.ahead) ? c.ahead : -1, aheadBody: c.aheadBody,
        limited: c.limited, exiting: c.exiting, safetyStops: c.safetyStops, refusedTurns: c.refusedTurns,
        available: this.mode === 'PILOTING' && this.cruiseAvailable(),
        hop: c.hop, maxSpeed: c.maxSpeed, accel: c.accel, peak: c.peak,
      },
      cruiseLog: this.cruiseLog.map((l) => ({ ...l })),
      handoffLog: this.handoffLog.map((e) => ({ ...e })),
      // The light now (slewed), its target, and the reference body's catalog sun direction.
      light: {
        dir: lt.sunDir.toArray(), target: lt.star.dir.toArray(), bodySunDir: sunDirFor(this.ref),
        flux: lt.star.flux, scale: lt.fluxScale, angularRadius: lt.star.angularRadius,
        distance: Number.isFinite(lt.star.distance) ? lt.star.distance : -1,
      },
      assist: { active: this.assist.active, phase: this.assist.phase, reason: this.assist.reason, stable: this.assist.stable },
      probe: { hits: this.probe.hits, gaps: [...this.probe.gaps], slope: this.probe.slopeDeg, reason: this.probe.reason },
      player: playerInfo,
      counters: { ...this.counters },
      rebaseCount: this.rebaseCount,
      droppedSteps: this.stepper.droppedSteps,
      loadingTime: this.loadingTime,
      timings: { ...this.timings },
      draw: { calls: st.calls, triangles: st.triangles, geometries: st.geometries, textures: st.textures, w: st.width, h: st.height },
      physics: { bodies: this.physics.bodyCount, colliders: this.physics.colliderCount, refreshes: this.physics.refreshCount },
      terrain: b
        ? { ...b.terrain.stats, coarseReady: b.terrain.coarseReady, atRoots: b.terrain.atRoots, colliders: b.collision.count, focusReady: b.collision.focusReady }
        : null,
      props: b ? { ...b.props.stats, triangles: b.props.triangleEstimate } : null,
      proxies: { ready: this.proxies.readyCount },
      quality: { preset: this.render.preset, adaptive: this.settings.adaptive, level: this.adaptive.level, medianMs: this.adaptive.lastMedianMs, resolutionScale: this.render.resolutionScale },
      expedition: JSON.parse(JSON.stringify(this.expedition.state)),
      scan: { target: this.scanTarget ? this.scanTarget.id : null, label: this.scanTarget?.label ?? null, progress: this.scanState.progress, done: this.scanState.done },
      interaction: this.interactionTarget(),
      mission: this.mission ? { relayCollider: this.mission.hasCollider, targets: this.mission.targets.map((t) => ({ id: t.id, kind: t.kind, local: t.pos.clone().add(this.bodyCenterLocal).toArray() })) } : null,
      heapMB: mem ? mem.usedJSHeapSize / 1048576 : null,
      chunks: {
        generated: store.generated, seeded: store.seeded, discarded: store.discarded, errors: store.errors, queued: store.queued, inFlight: store.inFlightCount,
        cacheMB: store.cacheBytes / 1048576, cacheCount: store.cacheCount, genMsAvg: store.generated ? store.genMsTotal / store.generated : 0, genMsMax: store.genMsMax,
      },
    };
  }

  dispose(): void {
    cancelAnimationFrame(this.rafId);
    window.removeEventListener('resize', this.onResize);
    document.removeEventListener('visibilitychange', this.onVisibility);
    this.store.dispose();
    this.proxies.dispose();
  }
}
