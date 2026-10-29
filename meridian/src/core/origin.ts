import { Vector3 } from 'three';
import { REBASE_DISTANCE, REBASE_ROUND } from '../game/config';

/**
 * Floating origin: the system-coordinate (double precision) position of the
 * local physics/render origin. Rebasing never rotates axes or changes
 * velocities; it only translates every local-space consumer by one delta.
 */
export class FloatingOrigin {
  readonly origin = new Vector3();
  count = 0;
  private readonly delta = new Vector3();
  private readonly next = new Vector3();

  /** Origin for a system position, rounded to REBASE_ROUND increments. */
  static rounded(sys: Vector3, out = new Vector3()): Vector3 {
    return out.set(
      Math.round(sys.x / REBASE_ROUND) * REBASE_ROUND,
      Math.round(sys.y / REBASE_ROUND) * REBASE_ROUND,
      Math.round(sys.z / REBASE_ROUND) * REBASE_ROUND,
    );
  }

  needsRebase(local: Vector3): boolean {
    return local.lengthSq() > REBASE_DISTANCE * REBASE_DISTANCE;
  }

  toSystem(local: Vector3, out: Vector3): Vector3 {
    return out.copy(local).add(this.origin);
  }

  toLocal(sys: Vector3, out: Vector3): Vector3 {
    return out.copy(sys).sub(this.origin);
  }

  /**
   * Move the origin so `local` (a controlled entity) ends up near zero.
   * `apply` runs after the origin moved and receives the delta to add to
   * every local-space position.
   */
  rebaseAround(local: Vector3, apply: (delta: Vector3) => void): boolean {
    this.toSystem(local, this.next);
    FloatingOrigin.rounded(this.next, this.next);
    return this.rebaseTo(this.next, apply);
  }

  rebaseTo(newOrigin: Vector3, apply: (delta: Vector3) => void): boolean {
    this.delta.copy(this.origin).sub(newOrigin);
    if (this.delta.lengthSq() === 0) return false;
    this.origin.copy(newOrigin);
    this.count++;
    apply(this.delta);
    return true;
  }
}
