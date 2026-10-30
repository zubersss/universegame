# Studio round (legacy branches) — LEAD reconciliation, M1 / L4

Reconciled 2026-10-29 against `main` 0cf5a22 (MERIDIAN baseline). Read-only: no studio branch was changed, merged or deleted; each one is preserved on the remote at the tip below. Labels: VERIFIED (checked against code here), REPORTED (only in the studio notes), CONTRADICTED (this code says otherwise).

## Branches

| Branch | Tip | Commits past 0cf5a22 | Delivered | State |
|---|---|---|---|---|
| `studio/integration` | 9eaf7ec | 57 | Orrin and Saro, Extended Survey, studio save schema 2, fauna, audio bus mix, data-driven terrain look, GAUGE test hooks, baseline photos | on hold (studio decisions D-005/D-006) |
| `studio/atlas` | 586dc69 | 61 (5 not on integration) | 41efe23 Orrin columns and Saro salt terrain | unmerged on purpose: browser walk failed (B-005) |
| `studio/biome` | aa94660 | 62 (6 not on integration) | 4897b87 flora/minerals/fauna for five worlds, f425345 footsteps and voices | fliers, burrowers, swarms never browser-checked |
| `studio/lumen` | 87706d1 | 65 (9 not on integration) | High photo set, 0b8dba8, e027ee7 | terrain pass seen only on Ilex ground at Balanced |
| `studio/echo` | 5c6e844 | 13 (all on integration) | Mixer, VoicePool, volume sliders, creature and discovery cues | soak 1 19.6 min flat (REPORTED) |
| `studio/gauge` | f2d91e6 | 11 (all on integration) | BUGS.md, quick journey, N-body test hooks, `TRAVEL_BODIES` | 3-body travel gate passed (REPORTED); 5-body gate never run |

## Claims

- VERIFIED: studio schema 2 keeps schema 1's shape plus `extendedTransmitted`/`discovered` and migrates schema-1 records including positions (`studio/integration` `src/save/SaveSystem.ts` header). The charter's schema 2 is different and forbids position migration.
- VERIFIED: commit 848579b fixes a GLSL `flat` local introduced by studio commit 796174a; `main`'s `terrainMaterial.ts` has no such local.
- VERIFIED: `GENERATOR_VERSION` (1) feeds every body seed (`main` `src/world/bodies.ts`), so bumping it changes the Quiet System.
- VERIFIED: audio voice cap 32 with a 0.5 s sweep, creature sub-cap 12, glue compressor and limiter (`Mixer.ts`, `VoicePool.ts` on integration; both import nothing).
- REPORTED: all studio pass counts (173/175/179 unit tests), quick-journey times, the travel gate, both soaks, every perf number (headless SwiftShader: draw counts real, frame times meaningless), "bit-identical to 0cf5a22" goldens.
- CONTRADICTED: none found.

## Bugs that apply to this code

| Bug | Applies to `main` | Note |
|---|---|---|
| B-001 `isBodyId` lists ids literally | yes (`src/world/bodies.ts`) | harmless with three bodies; must check the catalog once BodyDef is catalog-driven (WORLDS, W2) |
| B-002 LOD over budget with a detached photo camera | code is `main`'s (`TerrainManager.ts`) | within charter L budgets; only with a camera far from the focus entity |
| Vesper landing site on a collider seam | yes (`PROGRESS.md`, terrain collision seams) | mitigated by retries; relevant to `groundProbe` and "no falls" (WORLDS) |
| No shader pre-warm | yes (no `compile`/`compileAsync` in `src`) | expect a first-sight hitch; candidate for M5 polish (LEAD) |
| B-003, B-005, B-006, stale look fixture, `prevScanPhase` | no (studio-only code) | B-003 is a risk if the studio terrain look is ported |

## Conflicts with the charter

1. Save schema 2 number clash: do not port studio's schema 2 or its migration. A studio schema-2 record in a dev browser fails the charter's schema-2 validation and is preserved under `save-corrupt`.
2. Bodies: Orrin, Saro and the Extended Survey have no place in the charter (real solar system plus the optional Quiet System of Ilex, Vesper and Cairn).
3. Studio budgets (A4) are not charter L; B-002 "fails" only against studio limits.
4. Studio process files (Director/GAUGE roles, `BUGS.md`, studio sections of `PROGRESS.md`) are superseded by charter D and E; they stay on the branches.
5. `src/fauna/**` has no charter owner or planned body; deferred (possible with W15 if free).

## Worth porting later (each through its owner, with tests)

| Owner | What | Studio commits |
|---|---|---|
| LEAD | body-list test hooks, autopilot route tests, `quick.spec.ts` | 9ef2749 |
| LEAD | travel spec over a body list (`TRAVEL_BODIES`) for the 20-cycle gate | 9ef2749, 6d7ca2a, 73ef0d7 |
| LEAD | `Mixer.ts`, `VoicePool.ts` and their tests; PLAYER's `abilitySounds.ts` would sit on top | a42ea74, e5882d9 |
| LEAD | music and effects volume sliders (comfort) | c6e5607 |
| LEAD | compact nav rows and `Digit[1-9]` (still not enough for 10+ destinations) | f3766ea, b2d03ad |
| WORLDS | `isBodyId` against the catalog; `seamDistance`/`avoidSeams` for sites | b2d03ad |
| WORLDS | concavity byte; "original worlds unchanged" golden test | 9e5a95f, `worlds.test.ts` |
| WORLDS | data-driven terrain look (medium risk, see B-003); `photos.spec.ts` as `worlds-photos.spec.ts` | 796174a, bf3b95f, 848579b, 0b8dba8, da2b3bb, 26c34cf, e027ee7 |
| LEAD (design only) | per-species discovery times as a model for `discoveries[]` | 9e5a95f |
