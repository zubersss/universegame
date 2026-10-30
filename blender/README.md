# blender/ — MERIDIAN art pipeline (owner: BLENDER)

`tools/blender_render.ps1 <key|category|all> [-Preview]` → `render.py` → `Assets/_Game/Art/`.
The contract (`coordination/ASSET_CONTRACT.md`) is authoritative; this file documents the manifest.

## manifest.json — one entry per asset key

| Field        | Meaning |
|--------------|---------|
| `key`        | `category/name/variant`; output `Assets/_Game/Art/<category>/<name>/<variant>_<map>.png` |
| `source`     | `.blend` path relative to `blender/` (`sources/<category>/<name>.blend`) |
| `build`      | optional script (relative to `blender/`) with `build(blend_path)` that (re)creates the source |
| `collection` | collection whose objects are rendered; everything else is hidden |
| `camera`     | `side` (looks +Y; right +X, up +Z) or `top` (looks −Z; right +X, up +Y); orthographic, PPU 128 |
| `size`       | `[w, h]` px of the file (or of one frame for sheets), including the 8 px padding |
| `ppu`        | pixels per metre, default 128. Only for variants whose contract cap is below real scale (e.g. `ships/*/top`) |
| `origin`     | world point treated as the asset origin (default `[0,0,0]`) |
| `pivot`      | normalized image position of `origin`, from the bottom-left (Unity convention). The camera is placed so the origin lands exactly there. "Bottom-center" sprites use `[0.5, 8/h]` so feet sit on the padding line |
| `maps`       | subset of `color, normal, emission, mask`; `color` required, `normal` required for lit categories |
| `samples`    | EEVEE render samples (capped at 64; preview 8) |
| `engine`     | `eevee` (default) or `cycles` (planet bakes only) |
| `tileable`   | `x`, `y` or `xy`: run the wrap-seam check and add a 2× tile to the contact sheet |
| `animations` | sheets: `{columns, fps, facing, hitbox?, clips:[{name, frame_start, length, loop}]}`; `frame_start` is the Blender frame |
| `generator`  | alternative to rendering: script with `generate(entry, ctx) -> {map: HxWx4 uint8}` (planet bakes, tile sets) |

## Pass conventions (what a source material must provide)
A Principled BSDF per material: Base Color → `color` (unlit, sRGB, Standard view), Normal input
(or the geometry normal) → camera-space `normal` (linear, (n+1)/2, +Z toward camera),
Emission Color × Strength → `emission` (premultiplied by coverage, black elsewhere),
custom property `meridian_rim` → `mask` R, AO → `mask` G, Metallic → `mask` B.
Frame sheets: 4 px gutters between frames, no outer margin; `<variant>.json` carries `gutter`.
