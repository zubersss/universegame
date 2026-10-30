import { Vector3 } from 'three';
import type { Player, WalkInput } from '../player/Player';
import { FOOT_OFFSET } from '../player/Player';
import { WALK } from '../game/config';
import { Flight, type FlightSense } from './flight';
import { Speed, type SpeedSense } from './speed';
import { Blink, type BlinkSense, type BlinkTarget } from './blink';
import type { AbilityConfig, BlinkParams, FlightParams, Primitive, SpeedParams } from './types';

// Glue between the primitives, the walker and the controls (charter K).
// A power reads the controls and the walk input's mouse look, moves the
// walker through its character controller (collisions, readiness), and
// reports a HUD readout. Activation and hand-back go through the
// AbilityController's transition rules.

/** What a power reads from the game each fixed step. */
export interface PowerWorld {
  player: Player;
  /** Held keys and mouse buttons (Input codes). */
  held(code: string): boolean;
  /** Edge presses (consumed). */
  pressed(code: string): boolean;
  /** This step's walk input (mouse look). */
  walk: WalkInput;
  /** Active body's centre (local) and gravity at the walker (m/s^2). */
  center: Vector3;
  gravity: number;
  /** Terrain collision is loaded under a local point. */
  ready(local: Vector3): boolean;
}

export interface PowerReadout {
  /** Charge 0..1 (1 when not charge-based). */
  charge: number;
  /** Seconds until usable again. */
  cooldown: number;
  hint: string;
  /** Short status ('flying', 'braking', 'aim', ...). */
  status: string;
}

export interface Power {
  readonly primitive: Primitive;
  /** While walking: the controls ask to start now. */
  wants(dt: number, w: PowerWorld): boolean;
  start(w: PowerWorld): void;
  /** After a reload into this power's state (LEAD M2 plan C): flight hovers in place, speed resumes braking. Powers without it reload walking. */
  resume?(w: PowerWorld): void;
  /** One step while active: 'active', or 'done' (hand back to walking). */
  step(dt: number, w: PowerWorld): 'active' | 'done';
  /** Every step, active or not (cooldowns, previews). */
  tick(dt: number, w: PowerWorld | null): void;
  readout(): PowerReadout;
  /** Refusal to show (red feedback), cleared after a moment. */
  readonly refusal: string | null;
}

const _feet = new Vector3();
const _p = new Vector3();
const _dir = new Vector3();
const _n = new Vector3();

const held = (w: PowerWorld, ...codes: string[]) => codes.some((c) => w.held(c));

/** Height of the feet above the ground below (m), null beyond `reach` or where nothing is loaded. */
function heightAboveGround(player: Player, reach: number): number | null {
  const g = player.groundAt(player.feet(_feet), 0.5, reach);
  return g ? Math.max(0, -g.h) : null;
}

// ------------------------------------------------------------------ flight

export class FlightPower implements Power {
  readonly primitive = 'flight' as const;
  readonly flight: Flight;
  private hold = 0;
  refusal: string | null = null;
  private sense: FlightSense = { up: new Vector3(), heading: new Vector3(), height: null, grounded: false, ready: true };

  constructor(readonly p: FlightParams) {
    this.flight = new Flight(p);
  }

  wants(dt: number, w: PowerWorld): boolean {
    // Hold Space: the first press jumps (walking), holding on takes off.
    this.hold = held(w, 'Space') ? this.hold + dt : 0;
    return this.hold >= this.p.takeoffHold;
  }

  private fill(w: PowerWorld): FlightSense {
    const pl = w.player;
    const s = this.sense;
    s.up.copy(pl.up);
    s.heading.copy(pl.heading);
    s.height = heightAboveGround(pl, this.p.ceiling + 600);
    s.grounded = pl.grounded;
    // Collision loaded along the path ahead (charter J: speed x 2 s + braking + 50 m).
    const v = this.flight.vel.length();
    const ahead = v * 2 + (v * v) / (2 * this.p.brake) + 50;
    _dir.copy(this.flight.vel);
    if (_dir.lengthSq() > 1e-6) _dir.normalize();
    s.ready = w.ready(_p.copy(pl.pos).addScaledVector(_dir, Math.min(ahead, 1500)));
    return s;
  }

  start(w: PowerWorld): void {
    const pl = w.player;
    this.hold = 0;
    this.flight.start(_p.copy(pl.vel).addScaledVector(pl.up, pl.vVert), this.fill(w));
  }

  resume(w: PowerWorld): void {
    this.hold = 0;
    this.flight.resume(this.fill(w));
  }

  step(dt: number, w: PowerWorld): 'active' | 'done' {
    const pl = w.player;
    pl.look(w.walk.yaw, w.walk.pitch);
    const r = this.flight.step(
      dt,
      {
        climb: held(w, 'Space'),
        descend: held(w, 'ControlLeft', 'ControlRight'),
        faster: held(w, 'KeyW', 'ArrowUp'),
        slower: held(w, 'KeyS', 'ArrowDown'),
        boost: held(w, 'ShiftLeft', 'ShiftRight'),
        brake: held(w, 'KeyX'),
      },
      this.fill(w),
    );
    pl.moveFree(dt, this.flight.vel, w.center);
    // What actually happened: collisions take the blocked part of the velocity.
    this.flight.vel.copy(pl.vel).addScaledVector(pl.up, pl.vVert);
    return r === 'landed' ? 'done' : 'active';
  }

  tick(): void {}

  readout(): PowerReadout {
    const f = this.flight;
    return { charge: 1, cooldown: 0, hint: 'Space/Ctrl climb · W/S speed · Shift boost · X hover', status: `${Math.round(f.vel.length())} m/s` };
  }
}

// ------------------------------------------------------------------ speed

export class SpeedPower implements Power {
  readonly primitive = 'speed' as const;
  readonly speed: Speed;
  refusal: string | null = null;
  private readonly normal = new Vector3();
  private sense!: SpeedSense;

  constructor(readonly p: SpeedParams) {
    this.speed = new Speed(p);
  }

  wants(_dt: number, w: PowerWorld): boolean {
    return held(w, 'KeyQ') && w.player.grounded;
  }

  private fill(w: PowerWorld): SpeedSense {
    const pl = w.player;
    const under = pl.groundAt(pl.feet(_feet), 0.5, 1.0);
    if (under) this.normal.copy(under.normal);
    this.sense = {
      up: pl.up,
      heading: pl.heading,
      grounded: pl.grounded,
      normal: under ? this.normal : null,
      clear: (dir, dist) => pl.sweepCapsule(dir, dist, 0.4),
      groundAhead: (dir, d) => {
        const g = pl.groundAt(pl.feet(_feet).addScaledVector(dir, d), 40, 80);
        if (!g) return null;
        return { h: g.h, slopeDeg: (Math.acos(Math.max(-1, Math.min(1, g.normal.dot(pl.up)))) * 180) / Math.PI };
      },
      ready: (d) => w.ready(_p.copy(pl.pos).addScaledVector(this.speed.course, d)),
      gravity: w.gravity,
    };
    return this.sense;
  }

  start(w: PowerWorld): void {
    this.speed.start(w.player.vel, this.fill(w));
  }

  resume(w: PowerWorld): void {
    this.speed.resume(this.fill(w));
  }

  step(dt: number, w: PowerWorld): 'active' | 'done' {
    const pl = w.player;
    pl.look(w.walk.yaw, w.walk.pitch);
    const r = this.speed.step(dt, { run: held(w, 'KeyQ'), brake: held(w, 'KeyX') }, this.fill(w));
    pl.moveFree(dt, this.speed.vel, w.center, 0.6);
    // A collision that the probes did not foresee takes the speed it blocked
    // (full 3D speed: on a slope the horizontal part alone is lower).
    const actual = Math.hypot(pl.vel.length(), pl.vVert);
    if (actual < this.speed.speed - 1) this.speed.speed = actual;
    return r === 'done' ? 'done' : 'active';
  }

  tick(): void {}

  readout(): PowerReadout {
    const s = this.speed;
    return { charge: 1, cooldown: 0, hint: 'Hold Q to run · mouse steers · X brakes', status: s.braking ? 'braking' : `${Math.round(s.speed)} m/s` };
  }
}

// ------------------------------------------------------------------ blink

export class BlinkPower implements Power {
  readonly primitive = 'blink' as const;
  readonly blink: Blink;
  /** Current aim target (updated every step while aiming). */
  readonly target: BlinkTarget = { ok: false, feet: new Vector3(), distance: 0, reason: null };
  /** Right mouse held: show the preview marker. */
  aiming = false;
  /** The last blink's departure and arrival feet points (effects). */
  readonly lastJump = { from: new Vector3(), to: new Vector3(), count: 0 };
  refusal: string | null = null;
  private refusalTime = 0;
  private pending: BlinkTarget | null = null;
  private readonly eye = new Vector3();
  private readonly aim = new Vector3();

  constructor(readonly p: BlinkParams) {
    this.blink = new Blink(p);
  }

  private sense(w: PowerWorld): BlinkSense {
    const pl = w.player;
    pl.aim(this.eye, this.aim);
    const physicsRay = (o: Vector3, d: Vector3, max: number) => {
      const g = pl.rayHit(o, d, max);
      return g ? { dist: g.dist, normal: g.normal } : null;
    };
    return {
      up: pl.up,
      eye: this.eye,
      aim: this.aim,
      grounded: pl.grounded,
      ray: physicsRay,
      groundBelow: (pt, max) => {
        const g = pl.groundAt(pt, 0.05, max);
        return g ? Math.max(0, -(g.h - _n.copy(pt).sub(pl.feet(_feet)).dot(pl.up))) : null;
      },
      fits: (feet) => pl.fitsAt(feet),
      ready: (pt) => w.ready(pt),
    };
  }

  tick(dt: number, w: PowerWorld | null): void {
    this.blink.tick(dt);
    if (this.refusal !== null) {
      this.refusalTime -= dt;
      if (this.refusalTime <= 0) this.refusal = null;
    }
    this.aiming = !!w && held(w, 'MouseRight');
    if (w && this.aiming) this.blink.target(this.sense(w), this.target);
  }

  wants(_dt: number, w: PowerWorld): boolean {
    if (!(w.pressed('KeyQ') || (this.aiming && w.pressed('MouseLeft')))) return false;
    const t = this.blink.target(this.sense(w), this.target);
    if (!t.ok) {
      // Red feedback; nothing is consumed.
      this.refusal = t.reason;
      this.refusalTime = 1.2;
      return false;
    }
    this.pending = t;
    return true;
  }

  start(w: PowerWorld): void {
    const t = this.pending;
    this.pending = null;
    if (!t || !this.blink.commit(t)) return;
    const pl = w.player;
    pl.feet(this.lastJump.from);
    this.lastJump.to.copy(t.feet);
    this.lastJump.count++;
    // Arrive at rest (charter K: arrival velocity 0), standing where the target is.
    pl.place(_p.copy(t.feet).addScaledVector(pl.up, FOOT_OFFSET + WALK.skin), pl.up);
  }

  step(): 'active' | 'done' {
    // The step itself happened in start(): back to walking at once.
    return 'done';
  }

  readout(): PowerReadout {
    const ready = this.blink.cooldown === 0;
    return {
      charge: ready ? 1 : 1 - this.blink.cooldown / this.p.cooldown,
      cooldown: this.blink.cooldown,
      hint: 'Hold right mouse to aim · Q or click to step',
      status: this.refusal ?? (this.aiming ? (this.target.ok ? `${Math.round(this.target.distance)} m` : this.target.reason ?? 'no target') : ready ? 'ready' : 'recharging'),
    };
  }
}

/** The runtime for a power's primitive (its own primitive; `also` primitives are M4). */
export function createPower(cfg: AbilityConfig): Power | null {
  switch (cfg.primitive) {
    case 'flight':
      return new FlightPower(cfg.params);
    case 'speed':
      return new SpeedPower(cfg.params);
    case 'blink':
      return new BlinkPower(cfg.params);
    default:
      return null;
  }
}
