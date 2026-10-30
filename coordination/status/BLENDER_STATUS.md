# BLENDER STATUS
Updated: 2026-10-30 · Session: 1
## Current task
B-007 Earth terrain sets — started 2026-10-30. Generator + manifest committed (da7783f); previews pass (seam ≈ 1.0 on tile 46 for all six). Full-size export waiting on heavy_unity.lock (unity_test PlayMode, 11:13); renders as soon as it clears.
## Last completed
B-006 Pilgrim — 4bbe06b. side 1536×512 and top 448×176, color/normal/emission each. 11.4 m industrial VTOL shuttle: lofted hull, belly lift pods (glowing vents + emitter plates), rear main engine (glowing throat + lip ring), fixed skids, dorsal fin + strobe, cockpit visor, portholes, nav lights (red port +Y, green starboard −Y). Worn paint, belly grime, chipped-metal scratches, hazard band and panel seams are procedural; seams also bump into the normal map. 11.7 s + 3.3 s, peak 1580 MB. Contact sheets: blender/preview/ships__pilgrim__{side,top}_contact.png.
Before that: B-005 Sun + space — f7a1534 · B-004 Mars — 3fd3c9d · B-003 Earth — 3e281e0, e775226 (details in coordination/reports/blender/renders_2026-10-30.md).
## Next up
B-009, B-010, B-012
## Ready for review
- B-002…B-005: in Review per board (waiting on the U-005 lit preview); no BLENDER action pending.
- B-006 (4bbe06b): blender/scripts/build_pilgrim.py, blender/sources/ships/pilgrim.blend, Assets/_Game/Art/ships/pilgrim/{side,top}_{color,normal,emission}.png. render.py gained a per-asset `ppu` override (documented in blender/README.md).
## Handoffs
→ UNITY: terrain/earth/* sheets follow your BlobAutotile.cs exactly (index = rank of the reduced mask, 0 = isolated, 46 = fully surrounded, N = tile above, 8 columns from top-left, no gutters, no .json; slots 47–63 transparent / normal (128,128,255)). Tiles join seamlessly in every combination (demo: blender/preview/terrain__earth__*_demo.png, assembled with the same rule). grass and soil share a seed, so their interiors match. water: alpha 0.8 (0.95 on the foam line), meant to draw on top of whatever is behind it.
→ UNITY: ships/pilgrim: pivot = centre of mass = image centre ([0.5, 0.5]) in both views. side is true scale (PPU 128, nose → +X); skid bottoms touch the ground 1.8 m (230 px) below the pivot. top is NOT PPU 128: the 448 px cap forces 36 px/m (ship 11.4 m = 410 px), nose → +X (angle 0 = transform.right); scale it in the top-down view as you need. Emission is idle glow; thrust flames come from fx/thruster.
→ UNITY: planets/sun/surface is self-lit: draw it with emission = the emission map and no terminator/sun-direction shading. sun/glow disc edge is at r = 160 px of 512 → glow world width = 3.2 × R. backgrounds/space/layer0 is opaque; layer1/2 are transparent (straight alpha) and tile in x and y.
→ UNITY: sprite pivots come from `blender/manifest.json` `pivot` (normalized, bottom-left origin, Unity convention), and include the 8 px margin. calibration = [0.5, 0.0555556] (16 px of 288). "Bottom-center" props/characters = [0.5, margin/h].
→ UNITY: `_normal`, `_emission`, `_mask` PNGs have alpha 255 everywhere. Emission RGB is premultiplied by coverage (black outside the sprite). Normal is OpenGL camera-space (+Z toward camera), verified on the calibration sphere.
→ UNITY: frame sheets have 4 px gutters *between* frames and no outer margin; `<variant>.json` carries `"gutter": 4`, and clips use `start`/`length` in sheet-frame indices.
→ UNITY: planets/*/glow: the planet disc edge is at radius 200 px of the 512 px sprite, so draw the glow at world width = 2.56 × R behind the disc. planets/*/clouds: RGB white, alpha = cloud cover; surface: equirect, longitude −180° at the left edge, wraps in x.
## Blockers
(none)
## Proposals
- → LEAD: `tools/paths.json` isn't valid JSON (single backslashes in Windows paths). blender_render.ps1 tolerates it by escaping before parsing; please store paths with `\\` or `/` so other tools can parse it.
- → LEAD: add `__pycache__/` to `.gitignore`. render.py disables bytecode writes, but one untracked `blender/scripts/meridian/__pycache__/` folder is on disk (deleting it was denied by permissions; it is not committed).
- → LEAD: B-006 board says top ≤ 448×448 "see UNITY handoff", but I found no such handoff in UNITY_STATUS or DECISIONS. I followed 448 as the cap (the contract allows 512) and rendered the top view at 36 px/m. If UNITY wanted true scale or a different px/m, it's one manifest field (`ppu`) and a re-render.
- → LEAD: Pilgrim has fixed landing skids, not animated legs (Bible §4.3 says legs deploy below 10 m). A `ships/pilgrim/side_legs` variant (legs extended) could be added later if UNITY wants the swap; not done, to stay inside B-006 scope.
- → LEAD/UNITY: terrain sheets have 17 empty slots (47–63). With one tile per mask, a 128 px texture repeats visibly on large flat areas (most on stone). Proposal: slots 47–62 hold 16 extra random variants of tile 46 (fully surrounded), and BlobAutotile/TerrainTileSet pick among them by a position hash. Needs a contract note + a UNITY change; I'd generate them in one re-export. Not done until LEAD decides.
- `git pull` is denied by permissions for this session; fine while all roles share one working tree.
(Settled by D-017: mask via material override; Earth topo+bathy variant.)
## For USER_ACTIONS
(none)
## HeavyJobLock
none
