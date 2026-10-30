import { SUN_HEAT } from './config';

// Star heat hazard (Sol only: the Quiet System has no star body). The zone
// follows the ship's distance from the star's center in star radii; a timer
// counts down only in the danger zone and resets outside it, and the recall is
// due when it runs out or at once inside the hard radius. Pure and Node-tested;
// Game steps it in the fixed step while flying and moves the ship out after
// the fixed steps (never inside one) when `recall` is set.

export type HeatZone = 'none' | 'caution' | 'danger' | 'recall';

/** The heat zone at `distance` (m) from the center of a star of radius `radius` (m). */
export function heatZone(distance: number, radius: number): HeatZone {
  const r = distance / radius;
  if (r < SUN_HEAT.hardRadii) return 'recall';
  if (r < SUN_HEAT.dangerRadii) return 'danger';
  if (r < SUN_HEAT.cautionRadii) return 'caution';
  return 'none';
}

export class HeatTimer {
  /** The zone of the last step. */
  zone: HeatZone = 'none';
  /** Seconds left in the danger zone before the recall. */
  remaining: number = SUN_HEAT.recallSeconds;
  /** Set once the recall is due; stays set until reset(). */
  recall = false;

  /** Advance by dt (s) in `zone`; returns whether the recall is due. */
  step(dt: number, zone: HeatZone): boolean {
    this.zone = zone;
    if (zone === 'danger') this.remaining = Math.max(0, this.remaining - dt);
    else if (zone !== 'recall') this.remaining = SUN_HEAT.recallSeconds;
    if (zone === 'recall' || this.remaining <= 0) this.recall = true;
    return this.recall;
  }

  /** Back to a cool ship (after the recall). */
  reset(): void {
    this.zone = 'none';
    this.remaining = SUN_HEAT.recallSeconds;
    this.recall = false;
  }
}

/** The HUD warning for a heat state near the star `starName`, or null outside the zones. */
export function heatWarning(t: HeatTimer, starName: string): { text: string; danger: boolean } | null {
  switch (t.zone) {
    case 'caution':
      return { text: `Solar heat rising: turn away from the ${starName}`, danger: false };
    case 'danger':
      return { text: `Heat shield failing: emergency recall in ${Math.ceil(t.remaining)} s`, danger: true };
    case 'recall':
      return { text: 'Heat shield limit: emergency recall', danger: true };
    default:
      return null;
  }
}
