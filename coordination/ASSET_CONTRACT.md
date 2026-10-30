# MERIDIAN — Asset Contract v1.3

Owner: LEAD (edits and version bumps, logged in `DECISIONS.md`). BLENDER produces to it;
UNITY's `ArtImporter` enforces it. If an asset can't meet a rule, BLENDER proposes a
change in its status file; it never ships an exception silently.

## 1. Keys, folders, files

- **Asset key**: `category/name/variant`, lowercase, `a–z 0–9 _`, e.g. `ships/pilgrim/top`,
  `terrain/mars/regolith`, `creatures/earth/stag`. The key is the Addressable address and the
  `ArtKeys` constant; it never changes once a task referencing it is Done.
- **Files**: `Assets/_Game/Art/<category>/<name>/<variant>_<map>.png` with maps
  `color` (required), `normal` (required for lit categories), `emission`, `mask` (optional),
  plus `<variant>.json` for frame sheets. Example: `Assets/_Game/Art/ships/pilgrim/top_color.png`,
  `top_normal.png`, `top_emission.png`.
- **Placeholders**: UNITY keeps the same relative path under `Assets/_Game/Placeholders/`.
  When the real `_color.png` imports, `ArtImporter` moves the address to it. No manual step.
- **Sources**: `blender/sources/<category>/<name>.blend`; render scripts in `blender/scripts/`;
  the asset list in `blender/manifest.json`. Previews in `blender/preview/` (gitignored).

## 2. Global rules

| Rule            | Value                                                                                     |
|-----------------|-------------------------------------------------------------------------------------------|
| PPU             | 128 for every sprite (1 m = 128 px). Size art by real dimensions: a 12 m ship side profile is 1536 px long |
| Format          | PNG, 8-bit, RGBA straight (non-premultiplied) alpha, no color profile embedded             |
| Color map       | Unlit albedo, sRGB. No baked lighting, shadows, or ambient occlusion in the color; AO may go in `mask` G |
| Normal map      | Camera-space from an orthographic render, OpenGL convention (+X right, +Y up, +Z toward camera), encoded (n+1)/2, linear (not sRGB). Transparent regions filled with (128,128,255); edge normals dilated 8 px so bilinear filtering never bleeds the fill |
| Emission map    | sRGB RGB, black where nothing glows; alpha ignored                                         |
| Mask map        | Linear. R = rim/highlight strength (0–1), G = ambient occlusion, B = metallic, A unused    |
| Padding         | ≥ 8 px transparent margin on every side; frame sheets: 4 px gutters                       |
| Edges           | Anti-aliased, no halos; color dilated 8 px under transparent pixels                        |
| Max file        | 4 MB per PNG, 2048 × 2048 max (planet surfaces 2048 × 1024)                                |
| Tileables       | Terrain tiles and background layers tile seamlessly (tested by the render script with a 2× tiled preview) |
| Legal           | Only original work or CC0 inputs (HDRIs, photo textures); every CC0 input logged in `docs/credits/blender.md` with source and license |

## 3. Blender render requirements (`blender/render.py`)

One command renders any asset or everything: `tools/blender_render.ps1 <key|category|all> [-Preview]`
wraps `blender --background --python blender/render.py -- --asset <key>` (or `--category`,
`--all`, `--preview`). The script must:
1. Read `blender/manifest.json` (per asset: key, source `.blend`, collection or object, camera
   preset, output size, maps, frame-sheet animation list, pivot).
2. Use an orthographic camera; film transparent; view transform **Standard** (not AgX or
   Filmic) so albedo survives untouched; sRGB output for color and emission; linear for
   normal and mask.
3. Produce the color pass as unlit albedo (material override that routes base color to an
   emission shader, or Workbench flat shading), the normal pass from the Normal render pass
   converted to the convention in §2, emission from an emission-only override, mask from
   AOVs or an equivalent material override (R rim, G AO, B metallic; D-017).
4. Post-process (edge dilation, fill, gutters, sheet packing, size check) in Python; write
   the `.json` manifest for frame sheets; write a contact sheet to `blender/preview/`.
5. `-Preview` renders at 25% size with low samples to `blender/preview/` only.
6. Be deterministic and idempotent; exit non-zero with a one-line reason on any failure; log
   one line per asset to `logs/blender_<date>.log`.
7. Respect memory: Eevee for sprites, tile size 256, ≤ 64 samples; Cycles only for planet
   bakes at ≤ 128 samples with denoising; each batch is one process that exits.

## 4. Categories

| Category (`category/…`)  | Variant(s)                        | Maps                     | Size                                        | Pivot (sprite)      | Mesh       | Mips | Atlas          |
|--------------------------|-----------------------------------|--------------------------|---------------------------------------------|---------------------|------------|------|----------------|
| `planets/<planet>/`      | `surface` (equirect), `clouds`, `glow` | color (+emission for glow) | 2048×1024 · 1024×512 · 512×512            | center              | Full rect  | yes  | none (shader textures) |
| `terrain/<planet>/<material>` | one 47-blob tile set per material (slot order = `BlobAutotile.cs`; slots 47–62 = 16 variants of tile 46, picked by position hash; slot 63 empty; D-020), tiles 128 px, packed 8 columns | color, normal (+mask optional) | 1024×1024 (holds 64 tiles)            | center              | Full rect  | yes  | `planet_<planet>` |
| `backgrounds/<planet>/`  | `layer0` (far), `layer1`, `layer2` (near); `backgrounds/space/layer0..2` | color only | 2048×1024, tileable in x            | center              | Full rect  | yes  | none           |
| `ships/<name>/`          | `top`, `side`, optional `damaged` | color, normal, emission  | top ≤ 512×512 (large ships 768); side ≤ 1536×512 | center of mass (manifest) | Tight | yes | `common`      |
| `characters/<name>/`     | frame sheet (see §5)              | color, normal, emission  | 256 px frames, sheet ≤ 2048×2048            | bottom-center       | Tight      | yes  | `common`       |
| `creatures/<planet>/<name>` | frame sheet                    | color, normal (+emission) | frames 128 / 256 / 512 by size class; sheet ≤ 2048×2048 | bottom-center (fliers center) | Tight | yes | `planet_<planet>` |
| `props/<planet or common>/<name>` | `base`, optional `lit`   | color, normal (+emission, mask) | ≤ 512×512                           | bottom-center       | Tight      | yes  | `planet_<planet>` or `common` |
| `fx/<name>`              | frame sheet or single             | color (+emission)        | frames ≤ 256, sheet ≤ 1024×1024             | center              | Full rect  | no   | `common`       |
| `icons/<item>`           | `base`                            | color only, sRGB         | 128×128                                     | center              | Full rect  | no   | `icons`        |
| `ui/<name>`              | `base`                            | color                    | as needed ≤ 1024                            | center              | Full rect  | no   | `ui`           |

Size classes for creatures: small ≤ 1.5 m → 128 px frames; medium ≤ 4 m → 256; large → 512
(apexes may use multi-part sprites: `body`, `head`, `limb_n` variants, each ≤ 512).

## 5. Frame sheets (characters, creatures, fx)
Per-sheet scale (D-031): a sheet `.json` may set `"ppu"` (pixels per meter) when the creature does not fit its size class at PPU 128; ArtImporter imports at that PPU.

Pre-rendered frames in a grid, row-major, 4 px gutters, with `<variant>.json`:

```json
{
  "key": "creatures/earth/stag",
  "frame_width": 256, "frame_height": 256, "columns": 8, "frames": 30,
  "fps": 12, "pivot": [0.5, 0.0], "facing": "right",
  "animations": [
    {"name": "idle",   "start": 0,  "length": 8, "loop": true},
    {"name": "walk",   "start": 8,  "length": 8, "loop": true},
    {"name": "attack", "start": 16, "length": 6, "loop": false},
    {"name": "hurt",   "start": 22, "length": 2, "loop": false},
    {"name": "death",  "start": 24, "length": 6, "loop": false}
  ],
  "hitbox": {"x": 0.3, "y": 0.0, "w": 0.4, "h": 0.8}
}
```
Standard sets: creatures idle/walk/attack/hurt/death (≤ 30 frames); fliers add `fly`;
characters idle/walk/run/jump/fall/land/dig/aim/hurt/death (≤ 48 frames). Left-facing is a
runtime flip; never render it. `ArtImporter` slices sheets from the `.json`, so a sheet
without its `.json` fails import with a clear console message.

## 6. Import automation (`Assets/_Game/Code/Editor/ArtImporter.cs`, owned by UNITY)

For every `Assets/_Game/Art/**/*_color.png`: set texture type Sprite, PPU 128, filter
Bilinear, compression BC7 high quality, sRGB on, mips per §4, mesh type per §4, pivot per §4
(or the manifest), secondary textures `_NormalMap`, `_EmissionMap`, `_MaskTex` when the
sibling files exist; for `_normal.png` set type Normal map, BC5, sRGB off; for `_mask.png`
sRGB off; slice frame sheets from the `.json`; mark Addressable with address = key in the
group from §4; add to the atlas from §4; remove the address from the matching file in
`Placeholders/`; reject (log an error, skip) any file over the §2 limits or with a name that
doesn't match §1. Every rule has an EditMode test.

## 7. Verification before handoff

BLENDER: `tools/blender_render.ps1 <key>` succeeds; the contact sheet in `blender/preview/`
shows color, normal, and emission; sizes within §4; tileables pass the 2× tile check; files
committed via LFS with `[blender] <task-id>`. UNITY (or LEAD): `tools/unity_art_preview.ps1
<key>` produces a lit preview in `logs/`; no importer errors. LEAD compares both against the
style guide (Bible §9) in the review.

## 8. Changing the contract

Propose in your status file (what, why, which assets). LEAD decides within one review cycle,
bumps the version here, logs it in `DECISIONS.md`, and lists any re-exports as tasks.
Existing Done assets are not re-exported unless a task says so.
