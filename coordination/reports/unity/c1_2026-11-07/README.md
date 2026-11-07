# C1 · UNITY evidence (2026-11-07; U-106 capture list, filled as each item lands)

Owner: UNITY. One line per item; LEAD writes C1_REPORT.md from this folder, `perf_2026-11-07.md` and `tests_2026-11-07.md`.

| # | Item | Card | Evidence | State |
|---|------|------|----------|-------|
| 1 | Drawn Pilgrim on the pad, tilted in the climb, under the Escape Line (B-122 rig: fin_wobble, leg_flex, hatch_open; puffs on tail_exhaust / attitude_l / attitude_r) | U-103 | `../u103/1_pad.png`, `2_tilted_climb.png`, `3_escape_line.png` (CaptureU103Ship) | pending the check |
| 2 | Space on the painted art: eight discs + Luna, Saturn's rings, the belt, the starfield scene, the top-down Pilgrim (pilgrim_top, fin_wobble) parked outside Earth's well | U-103 | `../space_2026-11-07/` or `logs/capture_u103_space_*.png` (CaptureSpaceArt, shots 1–6) | pending the check |
| 3 | Cartoon HUD at 1080p: gauges + needles at 12 Hz, the Escape Line tile + sign lettered in Patrick Hand, the ship rows (altitude, vertical speed, tilt, T/W), no fuel string anywhere | U-104 | `hud_1080p.png` (capture named in the U-104 hand-off) | swap code in progress |
| 4 | Climb sky: pad, half-way, under the Escape Line (gradient from layer0's top row to space black, starfield over the last third) | U-109 | `../u109/1_ground.png`, `2_halfway.png`, `3_escape_line.png` (CaptureU109Climb) | pending the check |
| 5 | 20 s flight strip under scripted input: pad → Escape Line → space → entry → touchdown (40 stills at 2 Hz, 6 × 7 contact sheet) | U-106 | `flight_strip/contact_sheet.png` + `still_NN.png` (CaptureC1FlightStrip) | to write (tests first) |
| 6 | Profile: Space, Earth, Mars rows green against D-089; the 11-leg dev-build probe with the Earth (warm) leg, Return rows on private commit, the Creep per visit row (info), the resident ≥ 1024² sheet count per planet, the worst iris-in frame per transition, the boot load breakdown | U-106 | `../perf_2026-11-07.md` (tools/unity_profile.ps1 -Build) | after items 1–5 |
| 7 | M1LoopTests, two runs green on the v3 art with the fuel-free flight | U-106 | `../tests_2026-11-07.md` | with item 6 |

Rules for the shots (D-110 (4)): review captures force-load every mip for the frame; the smoke shots keep the real streaming budget.
