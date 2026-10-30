// PLAYER-owned test hooks (charter D), exposed as window.__meridian.player in
// test builds only. Like the rest of the test API they inject input and read
// state; they never set gameplay state directly.

import type { Game } from '../game/Game';

export function playerTestHooks(_game: Game): Record<string, unknown> {
  return {};
}
