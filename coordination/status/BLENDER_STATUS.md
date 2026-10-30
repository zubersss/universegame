# BLENDER STATUS
Updated: 2026-10-30 · Session: 1
## Current task
B-003 Earth top-down (planets/earth/surface, clouds, glow) — started 2026-10-30
## Last completed
B-002 calibration props/common/calibration — ead95f6. color/normal/emission/mask 160×288 (1 m cube + 1 m sphere, origin at cube base, 16 px margin). Verified numerically: albedo exact (cube 60,120,200; sphere 200,60,50), front face normal (128,128,255), relit sphere brightest upper-right, emission stripe (255,160,40), mask cube (0,255,255) / sphere (128,255,0), 8 px padding clean, dilation present, byte-identical on re-render. 12.7 s, peak 1086 MB. Contact sheet: blender/preview/props__common__calibration_contact.png (panels: color, color RGB without alpha (dilation), normal, relit upper-right, emission, mask).
## Next up
B-004, B-005, B-006
## Ready for review
- B-001 (4dd7922, 5d630d4): blender/render.py, blender/scripts/meridian/, blender/manifest.json, blender/README.md (manifest field reference), tools/blender_render.ps1.
- B-002 (ead95f6): blender/scripts/build_calibration.py, blender/sources/props/calibration.blend, Assets/_Game/Art/props/common/calibration_{color,normal,emission,mask}.png. Handshake with U-005.
## Handoffs
→ UNITY: sprite pivots come from `blender/manifest.json` `pivot` (normalized, bottom-left origin, Unity convention), and include the 8 px margin. calibration = [0.5, 0.0555556] (16 px of 288). "Bottom-center" props/characters = [0.5, margin/h].
→ UNITY: `_normal`, `_emission`, `_mask` PNGs have alpha 255 everywhere. Emission RGB is premultiplied by coverage (black outside the sprite). Normal is OpenGL camera-space (+Z toward camera), verified on the calibration sphere.
→ UNITY: frame sheets have 4 px gutters *between* frames and no outer margin; `<variant>.json` carries `"gutter": 4`, and clips use `start`/`length` in sheet-frame indices.
## Blockers
(none)
## Proposals
- → LEAD: `tools/paths.json` isn't valid JSON (single backslashes in Windows paths). blender_render.ps1 tolerates it by escaping before parsing; please store paths with `\\` or `/` so other tools can parse it.
- → LEAD: add `__pycache__/` to `.gitignore`. render.py now disables bytecode writes, but one untracked `blender/scripts/meridian/__pycache__/` folder is on disk (deleting it was denied by permissions; it is not committed).
- Mask map comes from a material override (R = material property `meridian_rim`, G = EEVEE AO node, B = Metallic), not render AOVs. Same result, no compositor dependency in Blender 5.x. Contract §3.3 says "AOVs"; I'm treating this as equivalent unless LEAD objects.
## For USER_ACTIONS
(none)
## HeavyJobLock
none
