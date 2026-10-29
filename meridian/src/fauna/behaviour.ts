// Creature behaviour: a small state machine in the creature's home tangent
// plane (x, z in meters from its home point; curvature is negligible over a
// home range of tens of meters). Pure and allocation-free, so it can be unit
// tested and stepped at any rate. Runtime randomness comes from a per-creature
// PRNG; spawn points (not behaviour) are what must stay deterministic.

export type FaunaMode = 'idle' | 'wander' | 'alert' | 'flee';

/** Things a creature emits for sound (ECHO) and effects (LUMEN). */
export type FaunaEvent = 'call' | 'alarm' | 'step';

export interface BehaviourParams {
  /** Walking and fleeing ground speed (m/s). */
  walkSpeed: number;
  fleeSpeed: number;
  /** Turn rate (rad/s). */
  turnRate: number;
  /** Wander targets lie within this radius of home (m). */
  homeRadius: number;
  /** A walking player inside this distance makes it stop and watch (m). */
  alertRadius: number;
  /** A player inside this distance makes it flee (m). */
  fleeRadius: number;
  /** A loud ship (thrusting near the ground) inside this distance makes it flee (m). */
  shipFleeRadius: number;
  /** Idle pause range (s). */
  idleMin: number;
  idleMax: number;
  /** Calls per second while idle (Poisson rate). */
  callRate: number;
  /**
   * Curious species walk toward an observer while alert and stop this far
   * from it (m); 0 = stand still. They never stray beyond 2.5× the home radius.
   */
  curiousDistance?: number;
}

export interface CreatureState {
  mode: FaunaMode;
  x: number;
  z: number;
  /** Heading in the home frame: 0 = +z, increasing toward +x. */
  yaw: number;
  /** Current ground speed (m/s). */
  speed: number;
  /** Seconds left in the current idle/alert pause, or of calm needed after fleeing. */
  timer: number;
  /** Wander target. */
  tx: number;
  tz: number;
}

/** Threat positions in the creature's home frame. */
export interface Threats {
  player: boolean;
  px: number;
  pz: number;
  /** Ship thrusting near the ground (engine noise, downwash). */
  ship: boolean;
  sx: number;
  sz: number;
}

export function newCreatureState(x: number, z: number, yaw: number, timer: number): CreatureState {
  return { mode: 'idle', x, z, yaw, speed: 0, timer, tx: x, tz: z };
}

const TAU = Math.PI * 2;

function wrapAngle(a: number): number {
  a = (a + Math.PI) % TAU;
  if (a < 0) a += TAU;
  return a - Math.PI;
}

function turnToward(s: CreatureState, dx: number, dz: number, rate: number, dt: number): void {
  const want = Math.atan2(dx, dz);
  const d = wrapAngle(want - s.yaw);
  const m = rate * dt;
  s.yaw = wrapAngle(s.yaw + (d > m ? m : d < -m ? -m : d));
}

function approach(v: number, target: number, rate: number, dt: number): number {
  const m = rate * dt;
  return v < target ? Math.min(target, v + m) : Math.max(target, v - m);
}

/**
 * Advance one creature by dt. Returns the event emitted this step (or null).
 * Transitions: idle → wander (pause over) → idle (arrived); any → alert
 * (player close) → flee (player closer, or a loud ship near); flee → wander
 * back home once every threat is beyond 1.6× its radius for a calm period.
 */
export function stepBehaviour(s: CreatureState, p: BehaviourParams, t: Threats, dt: number, rnd: () => number): FaunaEvent | null {
  const pdx = s.x - t.px;
  const pdz = s.z - t.pz;
  const pd = t.player ? Math.sqrt(pdx * pdx + pdz * pdz) : Infinity;
  const sdx = s.x - t.sx;
  const sdz = s.z - t.sz;
  const sd = t.ship ? Math.sqrt(sdx * sdx + sdz * sdz) : Infinity;
  let ev: FaunaEvent | null = null;

  const scaredByPlayer = pd < p.fleeRadius;
  const scaredByShip = sd < p.shipFleeRadius;
  if ((scaredByPlayer || scaredByShip) && s.mode !== 'flee') {
    s.mode = 'flee';
    s.timer = 2.5;
    ev = 'alarm';
  } else if (s.mode !== 'flee' && s.mode !== 'alert' && pd < p.alertRadius) {
    s.mode = 'alert';
    s.timer = 1.5 + rnd() * 2;
  }

  switch (s.mode) {
    case 'flee': {
      // Away from the nearer threat.
      const fromShip = sd < pd;
      const ax = fromShip ? sdx : pdx;
      const az = fromShip ? sdz : pdz;
      turnToward(s, ax, az, p.turnRate * 1.6, dt);
      s.speed = approach(s.speed, p.fleeSpeed, p.fleeSpeed * 1.5, dt);
      const calm = pd > p.fleeRadius * 1.6 && sd > p.shipFleeRadius * 1.6;
      if (calm) {
        s.timer -= dt;
        if (s.timer <= 0) {
          s.mode = 'wander';
          pickTarget(s, p, rnd);
        }
      } else s.timer = 2.5;
      break;
    }
    case 'alert': {
      // Face the observer; curious species close in to a fixed distance first.
      const cd = p.curiousDistance ?? 0;
      const leashed = s.x * s.x + s.z * s.z > (p.homeRadius * 2.5) ** 2;
      const closing = t.player && cd > 0 && pd > cd + 0.5 && !leashed;
      s.speed = approach(s.speed, closing ? p.walkSpeed * 0.6 : 0, p.walkSpeed * 2, dt);
      if (t.player) turnToward(s, -pdx, -pdz, p.turnRate * 0.6, dt);
      if (pd > p.alertRadius * 1.3) {
        s.timer -= dt;
        if (s.timer <= 0) {
          s.mode = 'idle';
          s.timer = p.idleMin;
        }
      }
      break;
    }
    case 'wander': {
      const dx = s.tx - s.x;
      const dz = s.tz - s.z;
      const d = Math.sqrt(dx * dx + dz * dz);
      if (d < 0.6) {
        s.mode = 'idle';
        s.timer = p.idleMin + (p.idleMax - p.idleMin) * rnd();
        break;
      }
      turnToward(s, dx, dz, p.turnRate, dt);
      // Slow down for sharp turns and on arrival.
      const facing = Math.cos(wrapAngle(Math.atan2(dx, dz) - s.yaw));
      const want = p.walkSpeed * Math.max(0.15, facing) * Math.min(1, d / 2);
      s.speed = approach(s.speed, want, p.walkSpeed, dt);
      break;
    }
    default: {
      // idle
      s.speed = approach(s.speed, 0, p.walkSpeed * 2, dt);
      s.timer -= dt;
      if (rnd() < p.callRate * dt) ev = ev ?? 'call';
      if (s.timer <= 0) {
        s.mode = 'wander';
        pickTarget(s, p, rnd);
      }
    }
  }

  s.x += Math.sin(s.yaw) * s.speed * dt;
  s.z += Math.cos(s.yaw) * s.speed * dt;
  return ev;
}

/** Random wander target inside the home radius (uniform over the disc). */
function pickTarget(s: CreatureState, p: BehaviourParams, rnd: () => number): void {
  const r = p.homeRadius * Math.sqrt(rnd());
  const a = rnd() * TAU;
  s.tx = Math.sin(a) * r;
  s.tz = Math.cos(a) * r;
}
