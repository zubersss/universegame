# Lightspeed Overhaul — Team Status

Owner: LEAD (only LEAD edits this file). WORLDS and PLAYER update their rows through READY/BLOCKED packets.
Charter: `docs/team/CHARTER.md` (binding). Handoffs: `docs/team/handoffs/`. Relay-mode packets: `docs/team/packets/<ROLE>.md`.

## Effective configuration (fill at session start; report, never assume)

| Session | Claude Code version | OS / environment | Model (`/model`) | Effort (`/effort status`) | Ultracode | Permission mode | `/list-agents` sees | Worktree / branch |
|---|---|---|---|---|---|---|---|---|
| LEAD | 2.1.312 | claude.ai cloud container: Linux 6.18 x86_64, 4 vCPU Xeon 2.1 GHz, 15 GB RAM, no GPU, Node 22.22.0 | `claude-opus-5-5` (served `claude-opus-5-5`) | session effort `ultracode` | on | auto | no other sessions (this session: `universegame-e4`; inbound messaging available) | cloud checkout / `overhaul/integration`, `lead/*` |
| WORLDS | 2.1.312 | claude.ai cloud container (Linux 6.18, no GPU) | `claude-opus-5-5` (served `claude-opus-5-5`) | `max` (session record, read by LEAD) | on (session record) | auto | LEAD, PLAYER by `send_message` (session `session_01R5Bri4MB7rpCVatQcDYx2k`) | cloud checkout / `worlds/m1` |
| PLAYER | 2.1.312 | claude.ai cloud container (Linux 6.18, no GPU) | `claude-opus-5-5` (served `claude-opus-5-5`) | `high` (session record, read by LEAD) | on (session record) | auto | LEAD, WORLDS by `send_message` (session `session_01R5Bri2t2x9zuUq1hBHotXu`) | cloud checkout / `player/m1` |

Reference device: CPU · GPU (`chrome://gpu`) · RAM 8 GB · resolution · Chrome version · Node version — not measured yet (owner's laptop). The LEAD session runs in a cloud container without a GPU (headless Chromium 1243 on SwiftShader), so its browser checks prove behaviour, not frame rate.

## Decided (settled questions; do not re-research)

| # | Decision | Reason / evidence | Date |
|---|---|---|---|
| 1 | Engine baseline = MERIDIAN in `meridian/`; Lightspeed artifact is a content source | Charter section C; MERIDIAN passes the engineering contracts with recorded tests | 2026-10-29 |
| 2 | Player-facing title "Lightspeed"; directory stays `meridian/` | Owner's name for the game; avoids path churn | 2026-10-29 |
| 3 | Scale: radius ÷ 40 (12–200 km), positions at `EPOCH` ÷ one factor (moons: Decided #10), cruise = max(15 km/s, hop ÷ 45 s), interstellar jump | Charter section H | 2026-10-29 |
| 4 | Character built in code (SkinnedMesh + bones); CC0 glTF only if verified in M1 | Charter section K | 2026-10-29 |
| 5 | Coordination: three cloud sessions + cross-session messaging (`send_message`; `docs/team/packets/` as fallback); no agent teams on the primary path | Charter sections E, G | 2026-10-29 |
| 6 | The `studio/*` branches are a content source, not a base: nothing merges wholesale; ports go through the file owner with tests | Handoff reconciliation (`docs/team/handoffs/studio-round.md`) | 2026-10-29 |
| 7 | Studio save schema 2 and its position migration are not ported; the charter's schema 2 stands, older records are kept read-only under `save-legacy` | Charter section I; L5 | 2026-10-29 |
| 8 | Project settings live at the repo root (`.claude/settings.json`), where sessions start; `crossSessionInbound` is set per user | Owner approval (L2); a repo file may only tighten that setting | 2026-10-29 |
| 9 | Ultracode may stay on in every session (effort `xhigh` or `ultracode`); the ultracode-off rule and the keyword-only workflow limit are removed; workflow agents edit only their session's owned files (charter version 2, B.3, G) | Owner instruction | 2026-10-29 |
| 10 | A moon sits in its real direction from its parent at parent gameplay radius × √(real parent–moon distance at EPOCH ÷ real parent radius), at least 4.5 × the sum of the two gameplay radii (Europa and Titan otherwise sit inside their giants' 4R envelopes); planets and the Sun keep the single factor (charter version 2, H) | WORLDS DECISION: the single factor puts the Moon 7.7 km from Earth's center | 2026-10-29 |
| 11 | LEAD works autonomously: it merges milestone pull requests into `main` after a passing gate, takes over tasks whose owner session is not running, runs a missing consumer's checks itself, and gates M1–M4 on its own environment; reference-device numbers are recorded when the owner runs them (charter version 2, B, E, F, L, M, N, O) | Owner instruction | 2026-10-29 |

## Integration base

| Branch | Commit | Checks last run | Checkpoint tag |
|---|---|---|---|
| `overhaul/integration` | 30ccf78 (= `main`) | 2026-10-29: `npm ci`, typecheck, `npm test` 63/63, build, build:test, prod smoke 2/2; journeys running | — (`overhaul-m1` at the M1 gate) |

## Handoff reconciliation (M1, L4)

| Handoff | Verified here | Contradicted by this code | Still disputed | Unique work preserved as |
|---|---|---|---|---|
| Old-bot exports (`EXPORT-for-old-bots.md`) | none received yet | — | — | — |
| `studio/integration` notes (`PROGRESS.md`, `BUGS.md`) | studio schema 2 migrates positions; B-001, Vesper seam and missing shader pre-warm apply to `main`; 848579b fixes studio-only code | none found | every pass count, soak, travel gate and perf number (not re-run) | branch @ 9eaf7ec, untouched; summary `docs/team/handoffs/studio-round.md` |
| `studio/atlas`, `studio/biome`, `studio/lumen` | their extra commits are studio-only (Orrin/Saro terrain, five-world fauna, photo sets) | none found | B-003, B-005, B-006 causes | branches @ 586dc69, aa94660, 87706d1, untouched |
| `studio/echo`, `studio/gauge` | fully contained in `studio/integration`; audio caps and test hooks read in code | none found | soaks, 3-body travel gate | branches @ 5c6e844, f2d91e6, untouched |

## Task table

| ID | Owner | Player-visible outcome | Depends on | Base | Owned files | Contract / acceptance check | Result (commit · checks run · remaining issues · next handoff) |
|---|---|---|---|---|---|---|---|
| L1 | LEAD | Baseline runs in LEAD's environment (reference device when available) | — | main | — | `npm ci`, `typecheck`, `test`, `build`, `preview`; plays in Chromium | Cloud container, `main` 30ccf78: `npm ci`, typecheck, 63/63 tests, build (main chunk 5,144.6 kB, 1,892 kB gzip), build:test, prod smoke 2/2 (boots, takes off, nav, pause, resize; no errors or hotlinks). Journeys: expedition, flight, landing (10 cycles) passed; planet, saves, travel not run (run stopped by the owner). Reference-device run recorded when the owner runs it; not blocking. |
| L2 | LEAD | Charter, status, settings committed | L1 | | `docs/team/*`, `.claude/settings.json` | files present on `overhaul/integration` | Charter and status in 30ccf78. Owner approved repo-root `.claude/settings.json` (allow npm/npx/git/node); `crossSessionInbound` stays a per-user setting because a repo file may only tighten it. |
| L3 | LEAD | Messaging round-trip | L2 | | — | packet to and from WORLDS and PLAYER | Done: LEAD → WORLDS and PLAYER delivered; READY packets back from both; PLAYER → WORLDS delivered. Cloud sessions talk by `send_message`; `docs/team/packets/` stays the fallback. |
| L4 | LEAD | Handoffs reconciled | L2 | | `docs/team/handoffs/*` | table above filled; unique work preserved | Studio branches reconciled read-only, nothing deleted; DECISION packet sent; old-bot exports are reconciled when the owner supplies them; their absence does not block L4 or the M1 gate. |
| L5 | LEAD | Contract foundations | L4 | | `src/game/*`, `src/save/*`, `src/ui/Hud.ts` | tests for Mode hooks, HUD slot API, schema-2 plan | `lead/L5-contracts` 566d144: `setMode` + ON_FOOT hooks, `hud.setAbility`/`hud.setWarning`, `save-legacy` policy; typecheck, 72/72 tests. Browser checks before merge. IFACE packets to WORLDS (BodyDef fields) and PLAYER (hooks). |
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
| 2026-10-29 | WORLDS | Network policy denies `ssd.jpl.nasa.gov`, `www.ncei.noaa.gov` and `nssdc.gsfc.nasa.gov` (W1 Horizons vectors, W3 ETOPO, NASA fact-sheet radii and masses); W2 continues on labeled interim values | owner adds the three hosts under Allowed domains | yes |
| 2026-10-29 | LEAD | No reference-device numbers (needed for M5 performance evidence; does not block M1–M4) | owner runs the baseline and `PW_GPU=1` profile on the laptop | optional; recorded when run; blocks no gate |

## Milestone gate results

| Milestone | Date | Gate checks (charter section M) | Evidence | Tag / PR |
|---|---|---|---|---|
| M1 | | | | |
| M2 | | | | |
| M3 | | | | |
| M4 | | | | |
| M5 | | | | |
