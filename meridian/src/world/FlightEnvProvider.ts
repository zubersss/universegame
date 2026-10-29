import { Vector3 } from 'three';
import type { BodyDef } from './bodies';
import { airDensity, gravityAtSystem } from './environment';
import type { FlightEnv } from '../ship/FlightModel';

/**
 * Computes the flight environment (gravity, radial up, altitude, clearance,
 * density) at a local position. One instance is reused every step.
 */
export class FlightEnvProvider implements FlightEnv {
  body: BodyDef;
  readonly gravity = new Vector3();
  readonly up = new Vector3();
  altitude = 0;
  clearance = 0;
  density = 0;
  nearBody = true;
  terrainSpeedLimit = Infinity;
  private readonly tmp = new Vector3();
  private readonly sys = new Vector3();

  constructor(
    body: BodyDef,
    /** Active body center in local coordinates (kept current by the owner). */
    readonly centerLocal: Vector3,
    /** Local origin in system coordinates (kept current by the owner). */
    readonly origin: Vector3,
    /** Terrain height above the datum radius for a unit direction from the body center. */
    public heightAt: (dir: Vector3) => number,
  ) {
    this.body = body;
  }

  update(pos: Vector3): this {
    const def = this.body;
    this.up.copy(pos).sub(this.centerLocal);
    const r = this.up.length();
    this.up.divideScalar(r);
    this.altitude = r - def.radius;
    this.clearance = this.altitude - this.heightAt(this.up);
    this.density = airDensity(def, this.altitude);
    this.nearBody = r < def.radius * 3;
    this.sys.copy(pos).add(this.origin);
    gravityAtSystem(this.sys, this.gravity);
    return this;
  }

  probe = (x: number, y: number, z: number): { clearance: number; density: number } => {
    const def = this.body;
    this.tmp.set(x, y, z).sub(this.centerLocal);
    const rr = this.tmp.length();
    const alt = rr - def.radius;
    this.tmp.divideScalar(rr);
    return { clearance: alt - this.heightAt(this.tmp), density: airDensity(def, alt) };
  };
}
