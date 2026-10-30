// Test-only autopilot. It pilots exclusively through the player's control
// path (held keys, edge presses and mouse motion injected into Input / the
// virtual stick), never by writing positions or gameplay state. Bundled only
// in dev and the testhooks build.

import { Quaternion, Vector3 } from 'three';
import type { Game } from '../game/Game';
import { CRUISE, FLIGHT } from '../game/config';
import { planPath, safetyRadius } from '../ship/Cruise';
import { BODIES, BODY_IDS, type BodyId } from '../world/bodies';

type V3 = [number, number, number];

export interface FlyGoal {
  kind: 'fly';
  /** Target direction from the active body center (unit vector), or null to hold heading. */
  dir: V3 | null;
  /** Desired clearance above terrain (m). */
  clearance: number;
  /** Throttle setpoint 0..1. */
  throttle: number;
  boost?: boolean;
  /** Pitch setpoint in degrees above the local horizon (default: automatic). */
  pitchDeg?: number;
}

export interface LandGoal {
  kind: 'land';
  dir: V3;
  /** Cruise clearance on the way to the site. */
  approachClearance: number;
}

export interface WalkGoal {
  kind: 'walk';
  /** Surface direction to walk to, or 'ship' for the boarding ladder. */
  target: V3 | 'ship';
  arrive: number;
  sprint?: boolean;
  /** Jump once when this close (m) to the target. */
  jumpAt?: number;
}

export interface TravelGoal {
  kind: 'travel';
  /** Destination body: climb out, cruise via waypoints, descend, then land at its landing site. */
  to: BodyId;
  /** Hold the brake once this fraction of the first cruise leg is covered (exercises brake cancel). */
  brakeAt?: number;
}

export interface AimGoal {
  kind: 'aim';
  /** Point to look at, relative to the shown body's center (m). */
  atPlanet: V3;
}

export type AutopilotGoal = FlyGoal | LandGoal | WalkGoal | TravelGoal | AimGoal;

/** The game's route inflation, so the autopilot flies the route a cruise hop is capped for. */
const PLAN_INFLATE = CRUISE.routeInflate;

function bodyCenter(id: BodyId, out = new Vector3()): Vector3 {
  const c = BODIES[id].center;
  return out.set(c[0], c[1], c[2]);
}

const _qi = new Quaternion();
const _sys = new Vector3();

const _f = new Vector3();
const _t = new Vector3();
const _up = new Vector3();
const _r = new Vector3();
const _p = new Vector3();

export class Autopilot {
  goal: AutopilotGoal | null = null;
  /** Last computed heading error (rad) and distance to target (m). */
  headingError = 0;
  distance = 0;
  /** Sub-state for land/walk goals. */
  phase = 'idle';
  phaseTime = 0;
  jumped = false;
  private bestDist = Infinity;
  private sideSign = 1;
  /** Travel route (system coordinates) and progress. */
  route: Vector3[] = [];
  wp = 0;
  private legStart = new Vector3();
  private brakeDone = false;

  constructor(private readonly game: Game) {}

  setGoal(g: AutopilotGoal | null): void {
    this.release();
    this.goal = g;
    this.phase = 'start';
    this.phaseTime = 0;
    this.jumped = false;
    this.route = [];
    this.wp = 0;
    this.brakeDone = false;
  }

  private hold(code: string, on: boolean): void {
    if (on) this.game.input.injected.add(code);
    else this.game.input.injected.delete(code);
  }

  release(): void {
    for (const k of ['KeyW', 'KeyS', 'Space', 'ControlLeft', 'ShiftLeft', 'KeyA', 'KeyD', 'KeyX']) this.hold(k, false);
  }

  /** Drive the virtual stick toward yaw/pitch commands (-1..1) through injected mouse motion. */
  private setStick(dt: number, yawCmd: number, pitchCmd: number): void {
    const game = this.game;
    const decay = Math.exp(-dt / FLIGHT.stickTau);
    const gain = FLIGHT.stickGain * game.settings.sensitivity;
    const inv = game.settings.invertY ? -1 : 1;
    game.injectMouse((yawCmd / decay - game.stick.x) / gain, -(pitchCmd / decay - game.stick.y) / gain / inv);
  }

  /** Point the nose along a world direction; returns the remaining angle (rad). */
  private steerDir(dt: number, d: Vector3): number {
    _qi.copy(this.game.ship.currQuat).invert();
    const l = _t.copy(d).normalize().applyQuaternion(_qi);
    const yawErr = Math.atan2(l.x, -l.z);
    const pitchErr = Math.atan2(l.y, Math.hypot(l.x, l.z));
    this.setStick(dt, Math.max(-0.9, Math.min(0.9, yawErr * 1.8)), Math.max(-0.9, Math.min(0.9, pitchErr * 2.2)));
    return Math.acos(Math.max(-1, Math.min(1, -l.z)));
  }

  private shipSystem(out: Vector3): Vector3 {
    return out.copy(this.game.ship.currPos).add(this.game.origin);
  }

  /** Clearance (m) from the ship to the nearest safety envelope (negative inside). */
  private envelopeClearance(p: Vector3): number {
    let m = Infinity;
    for (const id of BODY_IDS) m = Math.min(m, p.distanceTo(bodyCenter(id, _r)) - safetyRadius(BODIES[id]));
    return m;
  }

  private planRoute(to: BodyId): void {
    const def = BODIES[to];
    const sites = this.game.landingSiteOf(to);
    const n = new Vector3(...sites);
    const c = bodyCenter(to);
    const S = safetyRadius(def);
    // A gate well above the landing site, then a radial leg that ends inside the
    // envelope so cruise performs its automatic approach exit on the way in.
    const gate = c.clone().addScaledVector(n, S + 60000);
    const final = c.clone().addScaledVector(n, S - 5000);
    this.route = [...planPath(this.shipSystem(new Vector3()), gate, PLAN_INFLATE), final];
    this.wp = 0;
  }

  private stepTravel(dt: number, g: TravelGoal): void {
    const game = this.game;
    const ship = game.ship;
    const sys = this.shipSystem(_sys);
    if (game.mode === 'LANDED') {
      if (this.phase === 'start' || this.phaseTime > 2) {
        game.input.press('Space');
        this.setPhase('takeoff');
      }
      return;
    }
    if (this.phase === 'start' || this.phase === 'takeoff') this.setPhase('climb');
    if (this.phase === 'climb') {
      // Climb until well clear of every envelope (the planner inflates them by 8 km).
      this.hold('KeyW', ship.flight.throttle < 0.98);
      this.hold('Space', true);
      const env = game.env.update(ship.currPos);
      this.hold('ShiftLeft', env.clearance > 1200);
      const up = _up.copy(env.up);
      ship.forward(_f);
      const pitch = Math.asin(Math.max(-1, Math.min(1, _f.dot(up))));
      this.setStick(dt, 0, Math.max(-0.7, Math.min(0.7, (1.2 - pitch) * 2)));
      if (this.envelopeClearance(sys) > PLAN_INFLATE + 2000) {
        this.release();
        this.planRoute(g.to);
        this.setPhase('align');
      }
      return;
    }
    const target = this.route[this.wp];
    if (!target) return;
    _p.copy(target).sub(sys);
    this.distance = _p.length();
    if (this.phase === 'align') {
      this.hold('Space', false);
      this.hold('ShiftLeft', false);
      // Keep moderate speed while turning.
      this.hold('KeyW', ship.flight.throttle < 0.25);
      this.hold('KeyS', ship.flight.throttle > 0.35);
      const err = this.steerDir(dt, _p);
      this.headingError = err;
      if (game.mode === 'CRUISING') {
        this.setPhase('cruise');
      } else if (err < 0.04 && ship.angvel.length() < 0.05 && this.phaseTime > 1) {
        this.release();
        this.legStart.copy(sys);
        game.input.press('KeyG');
        this.setPhase('engage');
      }
      return;
    }
    if (this.phase === 'engage') {
      this.steerDir(dt, _p);
      if (game.mode === 'CRUISING') this.setPhase('cruise');
      else if (this.phaseTime > 1) this.setPhase('align'); // refused: realign and retry
      return;
    }
    if (this.phase === 'cruise') {
      this.headingError = this.steerDir(dt, _p);
      if (game.mode !== 'CRUISING') {
        // Automatic approach exit (or a brake/toggle exit we requested).
        this.release();
        if (this.wp === this.route.length - 1) this.setPhase('descend');
        else this.setPhase('align');
        return;
      }
      this.hold('KeyW', game.cruiseThrottle < 1);
      const legLen = this.legStart.distanceTo(target);
      const covered = legLen - this.distance;
      if (g.brakeAt !== undefined && !this.brakeDone && covered > legLen * g.brakeAt) {
        this.brakeDone = true;
        this.setPhase('braking');
        return;
      }
      if (this.wp < this.route.length - 1) {
        const v = ship.speed;
        if (this.distance < (v * v) / (2 * CRUISE.accel) + v * 0.5 + 4000) {
          game.input.press('KeyG');
          this.setPhase('leaving');
        }
      }
      return;
    }
    if (this.phase === 'braking') {
      this.steerDir(dt, _p);
      this.hold('KeyX', game.mode === 'CRUISING');
      if (game.mode !== 'CRUISING') {
        this.release();
        this.setPhase('align');
      }
      return;
    }
    if (this.phase === 'leaving') {
      this.steerDir(dt, _p);
      if (game.mode !== 'CRUISING') {
        this.wp++;
        this.setPhase('align');
      }
      return;
    }
    if (this.phase === 'descend') {
      // Head for a point 1.5 km above the landing site, then hand over to the landing goal.
      if (!game.body || !game.bodyShown || game.body.def.id !== g.to) return;
      const dir = game.landingSiteOf(g.to);
      _t.set(...dir);
      const h = game.terrainHeightAt(_t);
      const aim = _r.copy(_t).multiplyScalar(game.ref.radius + h + 1500).add(game.bodyCenterLocal);
      _p.copy(aim).sub(ship.currPos);
      const env = game.env.update(ship.currPos);
      const horiz = _f.copy(_p).addScaledVector(env.up, -_p.dot(env.up)).length();
      this.distance = horiz;
      this.steerDir(dt, _p);
      this.hold('KeyW', ship.flight.throttle < 0.95);
      this.hold('KeyS', false);
      if (horiz < 3000 && env.clearance < 3500) {
        this.release();
        this.goal = { kind: 'land', dir, approachClearance: 70 };
        this.setPhase('approach');
      }
    }
  }

  private setPhase(p: string): void {
    if (this.phase !== p) {
      this.phase = p;
      this.phaseTime = 0;
    }
  }

  /** Called at the start of every fixed step. */
  step(dt: number): void {
    const g = this.goal;
    if (!g) return;
    this.phaseTime += dt;
    if (g.kind === 'walk') this.stepWalk(dt, g);
    else if (g.kind === 'aim') this.stepAim(dt, g);
    else if (g.kind === 'travel') this.stepTravel(dt, g);
    else if (this.game.mode === 'PILOTING') {
      if (g.kind === 'fly') this.stepFly(dt, g);
      else this.stepLand(dt, g);
    } else if (g.kind === 'land' && this.game.mode === 'LANDED') {
      this.release();
      this.setPhase('landed');
    }
  }

  /** Surface point (local) for a direction from the body center. */
  private surfacePoint(dir: V3, out: Vector3): Vector3 {
    const game = this.game;
    _t.set(dir[0], dir[1], dir[2]);
    const h = game.terrainHeightAt(_t);
    return out.copy(_t).multiplyScalar(game.ref.radius + h).add(game.bodyCenterLocal);
  }

  /** Steer the ship (virtual stick) toward a direction at a pitch setpoint. */
  private steerShip(dt: number, dir: V3 | null, pitchTarget: number): void {
    const game = this.game;
    const ship = game.ship;
    const env = game.env.update(ship.currPos);
    _up.copy(env.up);
    ship.forward(_f);
    const pitch = Math.asin(Math.max(-1, Math.min(1, _f.dot(_up))));
    let yawCmd = 0;
    if (dir) {
      _t.set(dir[0], dir[1], dir[2]);
      const shipDir = _r.copy(ship.currPos).sub(game.bodyCenterLocal).normalize();
      this.distance = Math.acos(Math.max(-1, Math.min(1, shipDir.dot(_t)))) * game.ref.radius;
      _t.addScaledVector(shipDir, -_t.dot(shipDir));
      const fh = _f.clone().addScaledVector(_up, -_f.dot(_up));
      if (_t.lengthSq() > 1e-12 && fh.lengthSq() > 1e-12) {
        _t.normalize();
        fh.normalize();
        const cross = fh.clone().cross(_t).dot(_up); // + = target to the left
        this.headingError = Math.atan2(cross, fh.dot(_t));
        yawCmd = Math.max(-0.9, Math.min(0.9, -this.headingError * 1.6));
      }
    }
    const pitchCmd = Math.max(-0.7, Math.min(0.7, (pitchTarget - pitch) * 2.0));
    const decay = Math.exp(-dt / FLIGHT.stickTau);
    const gain = FLIGHT.stickGain * game.settings.sensitivity;
    const inv = game.settings.invertY ? -1 : 1;
    game.injectMouse((yawCmd / decay - game.stick.x) / gain, -(pitchCmd / decay - game.stick.y) / gain / inv);
  }

  /** Clearance error using the lowest terrain ahead (terrain following). */
  private clearanceError(target: number): { err: number; minAhead: number; clearance: number } {
    const game = this.game;
    const ship = game.ship;
    const env = game.env.update(ship.currPos);
    ship.forward(_f);
    let minAhead = env.clearance;
    const speed = Math.max(ship.speed, 20);
    const fh0 = _r.copy(_f).addScaledVector(env.up, -_f.dot(env.up));
    if (fh0.lengthSq() > 1e-9) {
      fh0.normalize();
      for (let k = 1; k <= 8; k++) {
        const d = speed * 1.2 * k;
        const p = env.probe(ship.currPos.x + fh0.x * d, ship.currPos.y + fh0.y * d, ship.currPos.z + fh0.z * d);
        minAhead = Math.min(minAhead, p.clearance);
      }
    }
    const clr = env.clearance;
    return { err: target - Math.min(clr, minAhead + 0.5 * (clr - minAhead)), minAhead, clearance: clr };
  }

  private stepFly(dt: number, g: FlyGoal): void {
    const ship = this.game.ship;
    const thr = ship.flight.throttle;
    this.hold('KeyW', thr < g.throttle - 0.02);
    this.hold('KeyS', thr > g.throttle + 0.02);
    this.hold('ShiftLeft', !!g.boost);
    const { err, minAhead } = this.clearanceError(g.clearance);
    const band = Math.max(15, g.clearance * 0.05);
    this.hold('Space', err > band || minAhead < 40);
    this.hold('ControlLeft', err < -band && minAhead > 60);
    const autoPitch = Math.max(-0.3, Math.min(0.35, err / 600));
    this.steerShip(dt, g.dir, g.pitchDeg !== undefined ? (g.pitchDeg * Math.PI) / 180 : autoPitch);
  }

  private stepLand(dt: number, g: LandGoal): void {
    const game = this.game;
    const ship = game.ship;
    const env = game.env.update(ship.currPos);
    if (this.phase === 'start') this.setPhase('approach');
    if (this.phase === 'approach') {
      const { err, minAhead } = this.clearanceError(g.approachClearance);
      this.steerShip(dt, g.dir, Math.max(-0.25, Math.min(0.3, err / 300)));
      const want = Math.max(0.12, Math.min(1, (this.distance - 60) / 900));
      const thr = ship.flight.throttle;
      this.hold('KeyW', thr < want - 0.03);
      this.hold('KeyS', thr > want + 0.03);
      this.hold('Space', err > 10 || minAhead < 25);
      this.hold('ControlLeft', err < -10 && minAhead > 40);
      if (this.distance < 45) {
        this.release();
        this.setPhase('stop');
      }
      return;
    }
    if (this.phase === 'stop') {
      this.steerShip(dt, null, 0);
      this.hold('KeyX', ship.speed > 1.5);
      if (ship.speed <= 1.5) {
        this.hold('KeyX', false);
        this.setPhase('descend');
      }
      return;
    }
    if (this.phase === 'descend') {
      this.steerShip(dt, null, 0);
      this.hold('ControlLeft', env.clearance > 35);
      if (env.clearance <= 35) {
        this.hold('ControlLeft', false);
        game.input.press('KeyL');
        this.setPhase('assist');
      }
      return;
    }
    if (this.phase === 'assist') {
      // Hands off; the landing assist does the rest. Re-press if it dropped out.
      if (!game.assist.active && this.phaseTime > 1) {
        game.input.press('KeyL');
        this.phaseTime = 0;
      }
      if (game.assist.active && game.assist.phase === 'holding' && this.phaseTime > 6) this.setPhase('rejected');
    }
  }

  /** Turn the first-person view toward a point using mouse motion only. */
  private stepAim(dt: number, g: AimGoal): void {
    const game = this.game;
    const p = game.player;
    if (game.mode !== 'ON_FOOT' || !p) return;
    const eye = p.eye(1, new Vector3());
    const d = _t.set(g.atPlanet[0], g.atPlanet[1], g.atPlanet[2]).add(game.bodyCenterLocal).sub(eye);
    const up = p.up;
    const vert = d.dot(up);
    const h = _r.copy(d).addScaledVector(up, -vert);
    const hl = h.length();
    let yawErr = 0;
    if (hl > 1e-6) {
      h.divideScalar(hl);
      yawErr = Math.atan2(p.heading.clone().cross(h).dot(up), p.heading.dot(h));
    }
    const pitchErr = Math.atan2(vert, hl) - p.pitch;
    const k = 0.0022 * game.settings.sensitivity;
    const inv = game.settings.invertY ? -1 : 1;
    const turn = Math.max(-4 * dt, Math.min(4 * dt, yawErr));
    const tilt = Math.max(-3 * dt, Math.min(3 * dt, pitchErr));
    game.injectMouse(-turn / k, -tilt / (k * inv));
    this.headingError = Math.abs(yawErr) + Math.abs(pitchErr);
    this.distance = d.length();
    this.setPhase(this.headingError < 0.01 ? 'aimed' : 'aiming');
  }

  private stepWalk(dt: number, g: WalkGoal): void {
    const game = this.game;
    const p = game.player;
    if (game.mode !== 'ON_FOOT' || !p) return;
    if (g.target === 'ship') game.ship.localToWorld(new Vector3(-2.25, -2.6, -1.2), _p);
    else this.surfacePoint(g.target, _p);
    const feet = p.feet(new Vector3());
    _t.copy(_p).sub(feet);
    _t.addScaledVector(p.up, -_t.dot(p.up));
    this.distance = _t.length();
    if (this.distance < g.arrive) {
      this.bestDist = Infinity;
      this.hold('KeyW', false);
      this.hold('ShiftLeft', false);
      this.setPhase('arrived');
      return;
    }
    // Unstick: if pressing forward without progress, side-step for a moment.
    if (this.phase === 'walking' && this.phaseTime > 2 && this.bestDist - this.distance < 0.3) {
      this.setPhase('sidestep');
      this.sideSign = -this.sideSign;
    }
    if (this.phase === 'sidestep') {
      if (this.phaseTime > 1.6) {
        this.setPhase('walking');
        this.bestDist = this.distance;
      }
    } else if (this.phase !== 'walking') {
      this.setPhase('walking');
      this.bestDist = this.distance;
    }
    if (this.phase === 'walking' && this.distance < this.bestDist - 0.3) {
      this.bestDist = this.distance;
      this.phaseTime = 0;
    }
    _t.normalize();
    if (this.phase === 'sidestep') _t.cross(p.up).multiplyScalar(this.sideSign).normalize();
    const cross = p.heading.clone().cross(_t).dot(p.up);
    this.headingError = Math.atan2(cross, p.heading.dot(_t));
    // Mouse-look yaw: turn at most ~5 rad/s.
    const k = 0.0022 * game.settings.sensitivity;
    const turn = Math.max(-5 * dt, Math.min(5 * dt, this.headingError));
    game.injectMouse(-turn / k, 0);
    this.hold('KeyW', Math.abs(this.headingError) < 1.0);
    this.hold('ShiftLeft', !!g.sprint);
    if (g.jumpAt !== undefined && !this.jumped && this.distance < g.jumpAt && p.grounded) {
      this.jumped = true;
      game.input.press('Space');
    }
  }
}
