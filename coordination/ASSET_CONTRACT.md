# MERIDIAN — Asset Contract v2.5

> **v2.5 (D-079, 2026-11-06).** Stage layers (§10: per-region layer files, caps, `stage.json`, stage sheets), clips at the sidecar's fps (60 for the surveyor and apexes), the feel clip set (§9 Rig row).

> **v2 (D-062, 2026-11-02).** Models replace sprites. §9 is the rule set for every 3D category
> (`terrain`, `backgrounds` (now skyline/ridge/deck meshes), `ships`, `characters`, `creatures`,
> `props`). §1–§8 still apply to the categories that stay 2D: `icons`, `ui`, `planets` (equirects),
> `fx` (billboard sheets), and to keys, folders, legal and hand-off rules.

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
Mid-size creatures (D-034): frames may be 320 px in 6 columns (sheet ≤ 2048) so the per-sheet ppu stays ≥ 100.
Large creatures (D-042): 400 px frames in 5 columns (≤ 2048) with shortened clip lengths recorded in the .json.
UI art (D-044): `ui/<group>/<name>`, color + alpha, unlit, no normal; sized per asset in the manifest.

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

## 9. 3D model assets (v2)

| Rule | Value |
|------|-------|
| File | `Assets/_Game/Art/<category>/<name>/<variant>.glb` (glTF binary, Y-up, metres), textures beside it as `<variant>_<map>.png`; sources `blender/sources/<category>/<name>.blend` |
| Orientation | Faces **+X in Unity** (screen right). glTFast mirrors X on import, so **export facing glTF −X** (D-065); up +Y; the play plane is z = 0 with the model centred on it (depth split front/back) |
| Origin | Characters, creatures (walkers), props: bottom-centre at the feet/base. Fliers, ships, fx: centre of mass. Terrain block textures: n/a |
| Textures | `color` (sRGB base colour), `normal` (tangent space, OpenGL +Y), `mask` (R metallic, G ambient occlusion, B rim/interactive glow, A smoothness), `emission` (sRGB). 1024² default; 2048² for the surveyor, ships and apex parts; terrain sets 512² per face |
| Triangles | small creature/prop ≤ 3 k · medium ≤ 8 k · large ≤ 20 k · apex ≤ 60 k across parts · surveyor ≤ 12 k · ship ≤ 15 k · POI prop ≤ 6 k. Count after export |
| Materials | One material per model where possible (two for emissive parts); no transparent materials except glass/fins (alpha clip preferred) |
| Rig and clips | Armature baked to keyframes at the sidecar's fps (30 default; **60 for the surveyor and apexes**, v2.5), root motion off, loop flags set; clip names exactly as §5's sheet clip names (`idle`, `walk`, `run`, `jump`, `fall`, `dig`, `hurt`, `death`, `attack`, flier set …). Feel clips (v2.5, Bible §4.2): surveyor `jump_anticipate`, `land_hard`, `dash`, `parry`, `parry_hit`, `hit_react`; every creature with an attack `hit_react`, `stagger`. Every action clip carries 2–4 frames of anticipation and one overshoot key. Extra clips named in the task |
| LOD | Optional `LOD1` mesh at ≤ 50 % triangles inside the same glb (`<variant>_LOD1`); required for apexes and ships |
| Terrain materials | Per tile material: `terrain/<planet>/<material>/top_<map>.png` and `side_<map>.png`, tileable, 2 m per repeat, 512²; plus `terrain/<planet>/backwall_<map>.png` |
| Stage layers (v2.5) | See §10: per region `rocks_near.glb`, `ridge_mid.glb`, `hills_far.glb`, `skyline_far.glb`, `setpiece_<a|b|c>.glb`, `stage.json`, `skydome_color.png`; per planet `clouds_color.png` and the foreground pieces under `props/<planet>_foreground/`. Giants: `deck_far/mid/near.glb` translucent cloud planes plus `wisp_*` foreground |
| Review evidence | A stamped turntable contact sheet (characters/creatures/ships: front +X, ¾, back; props and wall-type assets: camera side −Z, ¾, far side; D-068) rendered in Eevee with the planet's Sun and a neutral grey floor: `blender/preview/review_<key>.png`; plus the Unity lit preview from `tools/unity_art_preview.ps1` for Done |
| Import | `ArtImporter` v5 (UNITY): glb → materials from the four maps, clip names kept, address = key, placeholder retired. Never hand-edit a glb's import settings |

### 9.1 Rulings from the B-077 handshake (v2.1, D-063)
1. **Sidecar json.** Every model ships `<variant>.json` beside the glb: `clips` (name, frames, fps, loop), `sockets` (name → node), `triangles`, `lod1` (bool). glTF has no loop flag; the importer reads loops from here.
2. **Clip timing.** A clip of n frames at the sidecar's fps (30; 60 for the surveyor and apexes, v2.5) has its last key equal to its first and exports as n/fps s; the importer loops without repeating the last frame.
3. **No images inside the glb.** Materials carry factors only; `ArtImporter` builds the URP Lit material from the four PNGs beside the glb.
4. **Mask channels.** R metallic, G baked ambient occlusion, B rim/interactive glow, A smoothness (= 1 − roughness).
5. **Colour check tolerance** for v2 bakes: ±4/255 (Cycles colour bakes run ~1.5 % low).
6. **Memory gate.** Model bake + export jobs with 1024² maps use the 1.5 GB gate (measured 1.44–1.56 GB); 2048² maps need ≥ 2.0 GB free (measured 1.77–1.89 GB; D-066).
7. **Sockets** are empties named `socket_<name>` exported as glTF nodes, and listed in the json.
8. **LFS.** `*.glb` and `*.gltf` are LFS (`.gitattributes`). A glb committed before this rule is re-added once (`git rm --cached` + `git add`) by its owner so it becomes a pointer.
9. **Model map size (D-072).** Model maps are exempt from §2's 4 MB PNG cap; the 2048² cap and the §11.1 texture budget still apply.

## 10. Stage layers (v2.5, D-079)

Bible §10.10 defines the stack; this section fixes the files, caps and evidence. Every layer mesh
follows §9 (glb, Y-up, metres, the facing rule, four maps beside the glb, sidecar json). No layer
asset carries collision. Haze: bake the vertex colour toward the region's sky haze by depth
(20 % at z 20 → 45 % at z 60 → 70 % at z 150 and beyond, as B-102); UNITY's distance fog adds
the rest.

| Layer file (under `backgrounds/<planet>_<region>/` unless noted) | Depth z | Period / size | Triangles | Textures |
|---|---|---|---|---|
| `props/<planet>_foreground/<name>.glb` (6 per planet; ≥ 2 with translucent edges) | −3 … −1.5 m | pieces 1.5–4 m tall, origin base | ≤ 2 k each, no LOD1 | one 1024² atlas per planet (`props/<planet>_foreground/atlas_*`) |
| `rocks_near.glb` | 8 … 14 m | tileable every 128 m | ≤ 6 k | planet-shared `backgrounds/<planet>/rocks_atlas_*` 2048² |
| `ridge_mid.glb` | 20 … 60 m | 256 m | ≤ 8 k | 1024² own maps (unchanged) |
| `hills_far.glb` | 80 … 140 m | 512 m | ≤ 4 k | 1024² own maps |
| `skyline_far.glb` (composed peaks; three silhouettes per planet in rotation) | 150 … 400 m | 1024 m | ≤ 6 k | 1024² own maps |
| `setpiece_a.glb`, `setpiece_b.glb`, `setpiece_c.glb` | 30 … 140 m (per `stage.json`) | one landmark each, origin base | ≤ 10 k, LOD1 ≤ 4 k | 2048² own maps |
| `backgrounds/<planet>/clouds_color.png` | 500 m | 2048 × 512 RGBA strip, period 2048 m | — | ≤ 2 MB stored (BC7) |
| `skydome_color.png` | dome | 2048 × 1024 equirect | — | unchanged |
| Giants: `deck_far.glb`, `deck_mid.glb`, `deck_near.glb`, `props/<planet>_foreground/wisp_*.glb` | per B-097 | 256 m | ≤ 2 k per plane | 2048 × 1024 RGBA per plane |

Per-planet cap: the sum of every layer texture a planet can have resident (all its regions) is
≤ 700 MB stored (BC7/BC5 with mips); BLENDER reports the sum in its render report and
`ArtImporter` (UNITY, U-091) rejects the newest layer of a planet over the cap.

**`stage.json`** (one per region beside `ridge_mid.glb`; authored by BLENDER, read by UNITY):
```json
{ "region": "earth_forest",
  "setpieces": [ { "key": "setpiece_a", "at": 0.18, "z": 110, "scale": 1.0, "mirror": false },
                 { "key": "setpiece_b", "at": 0.55, "z": 60,  "scale": 1.2, "mirror": true  },
                 { "key": "setpiece_c", "at": 0.82, "z": 130, "scale": 0.9, "mirror": false } ],
  "foreground": { "pieces": ["tuft", "fern", "boulder", "log"], "spacing_m": 12 },
  "haze_rgb": [0.72, 0.78, 0.86] }
```
`at` is the fraction of the region's width from its western edge (UNITY applies it on the wrapped
world). A region has 2–4 set-pieces, no two within 120 m.

**Review evidence (stage sheet).** `blender/preview/stage_<planet>_<region>.png`: the whole stack
(layers 0–7, with the play-plane ground as a grey block row) rendered in Eevee from the side-rail
camera at 60 px/m, 1920 × 1080, under that planet's Sun and haze, stamped by `review.py`; plus
UNITY's `*_depth.png` smoke capture for Done. The sheet must read as one composed set: a dominant
landmark, a secondary one, open sky on at least a third of the width, no visible facet or tiling
seam at 1080p.
