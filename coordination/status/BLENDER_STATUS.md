# BLENDER STATUS
Updated: 2026-10-30 · Session: 1
## Current task
B-004 Mars top-down (planets/mars/surface, glow) — started 2026-10-30. Source: USGS Viking MDIM 2.1 colorized mosaic (public domain); the 232 m TIFF is 12 GB, so I'm looking for a smaller public-domain copy (1 km version) before falling back to anything else.
## Last completed
B-003 Earth top-down — 3e281e0 (sources) + e775226 (exports). surface 2048×1024 (2.9 MB, seam_x 0.32), clouds 1024×512 (white RGB, alpha = cover, seam_x 0.00), glow 512×512 color + emission. Peak 639 MB. Contact sheets: blender/preview/planets__earth__{surface,clouds,glow}_contact.png (2× tile row for surface and clouds).
## Next up
B-005, B-006, B-007
## Ready for review
- B-001 (4dd7922, 5d630d4): blender/render.py, blender/scripts/meridian/, blender/manifest.json, blender/README.md (manifest field reference), tools/blender_render.ps1.
- B-002 (ead95f6): blender/scripts/build_calibration.py, blender/sources/props/calibration.blend, Assets/_Game/Art/props/common/calibration_{color,normal,emission,mask}.png. Handshake with U-005.
- B-003 (3e281e0, e775226): blender/scripts/gen_planet.py, blender/sources/planets/earth/*.jpg (NASA inputs, logged in docs/credits/blender.md), Assets/_Game/Art/planets/earth/{surface_color,clouds_color,glow_color,glow_emission}.png.
## Handoffs
→ UNITY: sprite pivots come from `blender/manifest.json` `pivot` (normalized, bottom-left origin, Unity convention), and include the 8 px margin. calibration = [0.5, 0.0555556] (16 px of 288). "Bottom-center" props/characters = [0.5, margin/h].
→ UNITY: `_normal`, `_emission`, `_mask` PNGs have alpha 255 everywhere. Emission RGB is premultiplied by coverage (black outside the sprite). Normal is OpenGL camera-space (+Z toward camera), verified on the calibration sphere.
→ UNITY: frame sheets have 4 px gutters *between* frames and no outer margin; `<variant>.json` carries `"gutter": 4`, and clips use `start`/`length` in sheet-frame indices.
→ UNITY: planets/*/glow: the planet disc edge is at radius 200 px of the 512 px sprite, so draw the glow at world width = 2.56 × R behind the disc. planets/*/clouds: RGB white, alpha = cloud cover; surface: equirect, longitude −180° at the left edge, wraps in x.
→ UNITY: `.meta` files under Assets/_Game/Art/ are yours (your Editor creates them); I never commit them.
## Blockers
(none)
## Proposals
- → LEAD: `tools/paths.json` isn't valid JSON (single backslashes in Windows paths). blender_render.ps1 tolerates it by escaping before parsing; please store paths with `\\` or `/` so other tools can parse it.
- → LEAD: add `__pycache__/` to `.gitignore`. render.py now disables bytecode writes, but one untracked `blender/scripts/meridian/__pycache__/` folder is on disk (deleting it was denied by permissions; it is not committed).
- Mask map comes from a material override (R = material property `meridian_rim`, G = EEVEE AO node, B = Metallic), not render AOVs. Same result, no compositor dependency in Blender 5.x. Contract §3.3 says "AOVs"; I'm treating this as equivalent unless LEAD objects.
- B-003: Earth surface uses the Blue Marble NG *topo+bathy* variant (the plain variant URL is gone). It carries faint relief shading baked into land and seafloor. At disc scale (R = 25 units) it reads as texture, not lighting; the PlanetDisc terminator still does the real shading. Flag it if the review disagrees.
## For USER_ACTIONS
(none)
## HeavyJobLock
none
