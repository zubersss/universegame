// PLAYER-owned extension point (charter D): boot calls installPlayer(game) once,
// right after the Game exists. PLAYER installs its ON_FOOT hooks here with
// game.onFoot.install(...) (contract: src/game/onFoot.ts).

import type { Game } from '../game/Game';

export function installPlayer(_game: Game): void {
  // Nothing yet: walking uses Game's built-in controller until PLAYER installs hooks.
}
