# UNITY STATUS
Updated: 2026-10-30 11:50 · Session: 1
## Current task
U-009 Player controller with real gravity — starting 11:50.
## Last completed
U-008 Dig and place — f15f617 — EditMode 57/57, PlayMode 4/4 (+1 skip = preview capture, runs only from the tool). Beam digs the surface tile (drops its item, tile gone from the tilemap), Builder places stone in air; 2 diffs per chunk; save → fresh session → load → dug tile still absent, placed tile still present. Diff file `terrain_<planet>.bin` (magic MTD1, version 1). Only touched chunks rebuild collision. Edits made while a chunk is generating or half-applied re-generate that chunk.
U-006 Lit art preview — 5a75d90 — LEAD's approach worked: PlayMode capture `ArtPreviewCapture` (graphics on, 3 frames, targetSortingLayers = all, normal maps Accurate). Calibration sphere lit upper-right, falls off lower-left. Also rendered ships/pilgrim/{side,top}, planets/earth/surface, planets/sun/surface, terrain/earth/grass, all OK. Evidence: coordination/reports/unity/previews_2026-10-30.md. The old editor ArtPreview.cs + ArtPreview.unity are removed (superseded).
U-007 Terrain v1 — 2007876 — EditMode 54/54, PlayMode 3/3 (twice). 25 chunks resident, never one beyond radius 2 while flying 200 m; chunk apply p99 0.88–0.91 ms, 1/400 frames over 2 ms; worst frame 3.1–3.6 ms; 0 B GC per 300 settled frames. Real B-007/B-008 sheets in use. Seam look at ortho 9: visual check pending.
## Next up
U-011, U-016, U-010
## Ready for review
U-006 (5a75d90), U-007 (2007876; seam visual check pending), U-008 (f15f617)
→ LEAD: lit previews for B-002…B-006 keys are in logs/ (list in previews_2026-10-30.md); emission maps don't show yet (P-08).
## Handoffs
→ LEAD: my batch runs make Unity write `Assets/_Game/Tests/LeadQA.meta` and `Tests/LeadQA/*.meta` (your folder); please commit them.
→ BLENDER: keys are always 3 segments. Single-variant assets use `base`: `fx/thruster/base_color.png`, `characters/surveyor/base_color.png` + `base.json`. Creatures: `creatures/earth/stag` → `Art/creatures/earth/stag_color.png` + `stag.json`.
→ BLENDER: character sheets at 256 px with 4 px gutters fit 2048 only up to 7 columns (8 × 256 + 7 × 4 = 2076).
## Blockers
(none)
## Proposals
P-06: U-007 asserts §11.1 "chunk apply ≤ 2 ms per frame" as ≥ 99% of streaming frames ≤ 2 ms plus "no hitch > 33 ms". Code plans bands against 1 ms; single OS stalls on the shared laptop (one 20 ms band seen while Blender ran) can't be engineered away. LEAD: confirm, or name the measurement you want.
P-07: Autotiling uses plain Tiles + a precomputed 47-blob index (BlobAutotile.cs, worker thread) instead of RuleTile assets: RuleTile neighbor evaluation on the main thread doesn't fit the 2 ms budget. Same 47-tile sheets; layout in coordination/reports/unity/terrain_blob_layout.md (BLENDER already matches it).
P-09: Rig reach 5 m (Bible silent). Builder places the selected material without an inventory check until inventory exists (M3); drops are pooled physics bodies, max 64 live.
P-08: Add a task for the `Sprite_LitEmissive` Shader Graph material (Bible §10.5): Sprite-Lit-Default ignores `_EmissionMap`, so windows, thrusters and the Sun don't glow yet. Suggested before U-010/U-011 visuals.
## For USER_ACTIONS
(none)
## HeavyJobLock
none
