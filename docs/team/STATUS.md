# Lightspeed Overhaul — Team Status

Owner: LEAD (only LEAD edits this file). WORLDS and PLAYER update their rows through READY/BLOCKED packets.
Charter: `docs/team/CHARTER.md` (binding). Handoffs: `docs/team/handoffs/`. Relay-mode packets: `docs/team/packets/<ROLE>.md`.

## Effective configuration (fill at session start; report, never assume)

| Session | Claude Code version | OS / environment | Model (`/model`) | Effort (`/effort status`) | Ultracode | Permission mode | `/list-agents` sees | Worktree / branch |
|---|---|---|---|---|---|---|---|---|
| LEAD | | | | | off | | | main checkout / `lead/*` |
| WORLDS | | | | | off | | | `../universegame-worlds` / `worlds/*` |
| PLAYER | | | | | off | | | `../universegame-player` / `player/*` |

Reference device: CPU · GPU (`chrome://gpu`) · RAM 8 GB · resolution · Chrome version · Node version.

## Decided (settled questions; do not re-research)

| # | Decision | Reason / evidence | Date |
|---|---|---|---|
| 1 | Engine baseline = MERIDIAN in `meridian/`; Lightspeed artifact is a content source | Charter section C; MERIDIAN passes the engineering contracts with recorded tests | 2026-10-29 |
| 2 | Player-facing title "Lightspeed"; directory stays `meridian/` | Owner's name for the game; avoids path churn | 2026-10-29 |
| 3 | Scale: radius ÷ 40 (12–200 km), positions at `EPOCH` ÷ one factor, cruise = max(15 km/s, hop ÷ 45 s), interstellar jump | Charter section H | 2026-10-29 |
| 4 | Character built in code (SkinnedMesh + bones); CC0 glTF only if verified in M1 | Charter section K | 2026-10-29 |
| 5 | Coordination: three local sessions + cross-session messaging; ultracode off; no agent teams on the primary path | Charter section G | 2026-10-29 |

## Integration base

| Branch | Commit | Checks last run | Checkpoint tag |
|---|---|---|---|
| `overhaul/integration` | | | |

## Handoff reconciliation (M1, L4)

| Handoff | Verified here | Contradicted by this code | Still disputed | Unique work preserved as |
|---|---|---|---|---|
| | | | | |

## Task table

| ID | Owner | Player-visible outcome | Depends on | Base | Owned files | Contract / acceptance check | Result (commit · checks run · remaining issues · next handoff) |
|---|---|---|---|---|---|---|---|
| L1 | LEAD | Baseline runs on the reference device | — | main | — | `npm ci`, `typecheck`, `test`, `build`, `preview`; plays in Chrome | |
| L2 | LEAD | Charter, status, settings committed | L1 | | `docs/team/*`, `.claude/settings.json` | files present on `overhaul/integration` | |
| L3 | LEAD | Messaging round-trip | L2 | | — | packet to and from WORLDS and PLAYER | |
| L4 | LEAD | Handoffs reconciled | L2 | | `docs/team/handoffs/*` | table above filled; unique work preserved | |
| L5 | LEAD | Contract foundations | L4 | | `src/game/*`, `src/save/*`, `src/ui/Hud.ts` | tests for Mode hooks, HUD slot API, schema-2 plan | |
| W1 | WORLDS | Solar-system catalog with sources | — | | `src/data/sol.json` | fields tagged measured/estimated/fictional; source + epoch recorded | |
| W2 | WORLDS | `scale.ts` and catalog-driven `BodyDef` | W1, L5 | | `src/world/*` | Ilex, Vesper, Cairn still play | |
| W3 | WORLDS | Earth dataset converted and licensed | — | | `src/data/**`, `scripts/data/*`, `ASSET_LICENSES.md` | sampling test (Everest high, Challenger Deep low, land ≈ 29%) | |
| W4 | WORLDS | Data-backed Earth surface spike | W3 | | `src/world/surface.ts` | region renders; proxy ↔ surface continuity test | |
| P1 | PLAYER | Rigged character walks on Ilex in third person | — | | `src/avatar/**`, `src/player/*` | screenshots; no foot sliding; camera avoids terrain | |
| P2 | PLAYER | Ability skeleton and IFACE to LEAD | — | | `src/abilities/**` | types compile; hook points requested | |
| P3 | PLAYER | Avatar journey scaffold | P1 | | `e2e/journey/avatar-walk.spec.ts` | spec runs on `dist-test/` | |

## Blockers

| Since | Session | What | What unblocks | Owner action needed |
|---|---|---|---|---|
| | | | | |

## Milestone gate results

| Milestone | Date | Gate checks (charter section M) | Evidence | Tag / PR |
|---|---|---|---|---|
| M1 | | | | |
| M2 | | | | |
| M3 | | | | |
| M4 | | | | |
| M5 | | | | |
