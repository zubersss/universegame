# MERIDIAN art pipeline v4.1 (cartoon) — how a sheet is drawn, measured and reviewed

For a fresh BLENDER session. Rules live in `docs/PROJECT_BIBLE.md` §9 (v4.1) and
`coordination/ASSET_CONTRACT.md` §11 (v3.1); this file is how the code meets them.

## 1. The chain in one line

`scripts/build_<asset>_v3.py` draws Grease Pencil strokes into `sources/<cat>/<asset>.blend` →
`render.py` (style `v3` entries in `manifest.json`) reads the evaluated strokes and rasterizes
them in **numpy** (`scripts/gp_raster.py`, no EEVEE/GPU) → packs a sheet + json, validates it
(`scripts/meridian/v3.py`) → writes `blender/preview/review_<name>.png` (`review.py`).

## 2. Drawing (builders + `scripts/gp_draw.py`)

- Units are metres in the XZ plane (x right, z up, camera looks along +Y). PPU 64: 1 m = 64 px.
- One GP drawing per frame number; `G.mark_clips(scene, [(clip, n), ...])` puts a timeline
  marker on each clip's first drawing. render.py reads clips by marker (a clip may name another
  marker with `"marker"`, e.g. top_idle → idle).
- Materials: `G.mat(gp, name, fill=hex|None, ink=True, ink_hex=INK, behind=False, fill_alpha=1)`.
  The sRGB hex is stored on the material, so colours never round-trip through linear.
  - `behind=True` (ink-behind): small parts (beaks, feet, thin feathers) draw their ink at 2r
    *under* the fill, so the visible line is the same width and the colour keeps its area.
  - `fill_alpha<1`: a flat translucent wash (the surveyor's helmet glass, D-096).
- Ink weights (v3.1, D-100): `G.OUTER` = 1.25/64 m radius (2.5 px nominal → 2.0–3.0 after the
  ±20 % jitter), `G.INNER` = 0.625/64 (1.25 px → 1.0–1.5). Never scale them; the review fails
  anything outside the ranges.
- Required interior detail (v3.1): `G.seam`, `G.stitches`, `G.rivets`, `G.hatch`, `G.specks`,
  `G.ribs` (all at INNER). Draw them right after the part they decorate (same drawing), so
  nearer parts still cover them in paint order.
- Shadows: `G.shadow_of(hex)` = mid tone (70/30 with the planet's brown), `G.deep_of(hex)` =
  deep tone (45/55). At most these two per colour (D-100).
- Shapes: `lumpy_ellipse`, `bowed_line`, `bezier`, `hose_outline` (rubber-hose limbs),
  `pie_eye` (characters and creatures only — **never on plants, objects, the ship or planets**, D-101).
- Posing parts through a transform: wrap the drawing, `G.Xf(d, f)`; every helper that calls
  `G.stroke` then draws `f(points)` (rig-set preview loops, upright Pilgrim tilt).
- Determinism: never use Python `hash()` on strings for seeds (randomized per process); use
  `zlib.crc32` or fixed integers.

## 3. Rasterizing (`scripts/gp_raster.py`)

`collect(scene, objects, frame)` returns strokes in paint order (objects by `order` property,
layers bottom→top, strokes in order) with world xz, per-point radius, fill/ink colours,
`behind`, `fill_alpha`. `render_frame(strokes, fw, fh, ppu, pivot, ss)` draws even-odd fills and
capsule ink at `ss`× supersampling (4 for exports, 2 for previews), box-filters to 1x, returns
straight-alpha RGBA and the measured widths per stroke.

## 4. Sheets, rig sets and checks (`render.py`, `scripts/meridian/v3.py`)

- `do_v3_sheet`: frames → `post.pack_sheet` (4 px gutters, `v3.columns_for`) → `<variant>_color.png`
  + `<variant>.json` (§11.2 fields + `gutter`, `squash_root`). Fails on: json invalid
  (`v3.validate_sheet`: fps 12, ppu, caps per clip — idle 8–12, walk/run/fly 12–16, jump/land
  8–10, else ≤ 16 — frames multiple of 4, sheet ≤ 2048), a frame touching the 2 px edge margin,
  or (pivot at the feet) ink more than 2 px **below the ground line** (geometric check; the
  bottom edge is otherwise unchecked).
- `do_v3_rigset`: each `part_<name>` GP object drawn around its origin (= pivot), shelf-packed,
  rects bottom-left in px, plants from the builder (`scene["rig_plants"]`) incl. `offset_m`,
  `order`, `slots` (`replaces_part` swaps the bone's own sprite) and `idle.swap_cycle`. The
  review shows the assembled loop when the entry names `"loop": "<preview entry>"`.
- `preview_only` entries never export; `ppu_scale` (design sheets of big assets, e.g. 0.5x for
  the 12 m Pilgrim) is allowed only on them.
- fakegp-drawn sets (gp_draw strokes, numpy raster, no `.blend`): `do_ground_strip_set` (B-130,
  `build_c2_ground_strip.export`), `do_icon_set` (B-128), `do_prop_sheet_set` (B-131: the `props/common/camp_set`
  row exports the six camp props; a single row with `prop_sheet` exports one). Prop sheets: colour + json only
  (D-117), one sheet ≤ 512² packed to the smallest fit, static props = 1 frame and `"animations": []` (like the
  ground strips), extra json fields `tile`, `module_m`, `interactable`, `ground_line_px`; every frame is checked
  against the 2 px edge margin (that check found a lamp pivot sign bug the accepted preview never measured).
- Type changes under one key (D-117): ArtImporter un-addresses a colour map beside a `.glb` (IsModelKey), so a v3
  export that replaces a v2 model removes `<variant>.glb` + `_normal/_mask/_emission` after writing the sheet:
  `do_prop_sheet_set` always, `do_v3_sheet` when the row has `"replaces_v2": true` (B-132 stag, wolf). The `.meta`
  files are UNITY's to delete (D-016); commit the deletions with explicit paths.
- numpy-painted sets (no GP): `do_disc_set` (`build_discs_v3.export`: planets/<planet>/disc +
  json at space_ppu 3, Luna, Saturn ring parts + sidecars + disc_rig.json), `do_space_starfield`
  (`gen_painted_bg.export_space`: backgrounds/space/starfield/layer0 2048x1024 tiling in x and y
  + layer1..3 nebula cards + SceneLayout json), `do_painted_bg` (planet layers: `gen_painted_bg.SCENES` has the
  B-114 plains, `build_backdrop_v3.SCENES` the B-133 forest and coast, all at `backgrounds/<planet>/<scene>/`,
  the shape `ParallaxLayers.ConfigureFor(planet, scene)` loads; the `earth_<biome>` names belong to the archived
  3D DepthBands), `do_hud` (`build_hud_v3.build`), `do_palette_strip`.

## 5. The review sheet (`review.py`, contract §11.7)

`v3_sheet_review`: the asset at 1x on its planet's painted layers, every clip as a numbered
strip, a design row at N× when `design_zoom` is set, a 2× detail crop (densest line work), the
palette with mid + deep swatches, the measured outer/interior widths and interior strokes per
frame, palette hits, json validity, the **ten-box §9.7 list** (x measured, s BLENDER self-check
from the entry's `self_check`, ! fail, blank = LEAD's to tick; the face box is automatic for
characters/creatures and needs a `face` self-check for everything else) and the "ours" line.
Exports are stamped (file time + hash); STALE.txt marks keys whose last render failed.

## 6. Running it (locks, gates, queue)

- `tools/blender_render.ps1 <key>[,<key>...] [-Preview]`. Previews are light; a style-v3 export
  or anything with a `size` > 512 is a heavy job: HeavyJobLock, 1.5 GB free gate, no Unity
  Editor (D-091), one wrapper call = one job (D-037), ≤ 20 min.
- Order of heavy jobs: the board's `## Heavy job queue` (D-109). While another role holds the
  lock or a want: no `blender.exe` at all (D-073); work the `## While waiting` list (numpy and
  scripts only, ≤ ~300 MB extra RAM). Check locks in one call and start Blender only in a later
  call after reading a clear result.
- numpy-only scripts run without Blender:
  `"C:/Program Files/Blender Foundation/Blender 5.2/5.2/python/bin/python.exe" -I <script> <out_dir>`
  (build_discs_v3.py, build_hud_v3.py, gen_painted_bg.py all have a preview `__main__`).
- Commit explicit file paths, never Art directories (UNITY owns every `.meta`, D-016).
- Long jobs (the 98-frame surveyor ≈ 11 min) exceed the 10-min foreground limit: run them in
  the background and keep working on light items; never leave an idle background waiter.

## 7. Lock-free previews of sheets (D-109: no blender.exe while UNITY holds the lock or a want)

- A builder imports gp_draw through the real Blender when `bpy.data` exists, else through `meridian.fakegp`
  (`fakegp.install()` makes `import bpy` succeed and patches `gp_draw.mat`). The same drawing functions then run
  in Blender's bundled python: `"C:/Program Files/Blender Foundation/Blender 5.2/5.2/python/bin/python.exe" -I`.
- Match the export exactly: one FakeDrawing per frame, `gp_raster.render_frame(strokes, fw, fh, 64, pivot, ss,
  seed=entry_seed * 1000 + frame_number)` with 1-based frame numbers (the timeline), ss 2 for previews, 4 for exports.
- `review.v3_sheet_review(entry, meta, frames, sheet_png, out, stats)` builds the export's own review from a
  preview sheet written outside `Assets/` (stamped "preview"); `review._read` reads PNGs with numpy when bpy is not
  live. Example: `build_creatures_earth_v3.preview(<dir>)` (render_frames → sheet_of → v3_sheet_review).
- Memory: a fakegp sheet preview is ~100-300 MB; a 2048x1024 painted layer with FFT washes can pass 300 MB, so
  run backdrop previews only when the gate is open or the lock is yours.

## 8. Creature kit (B-132, `scripts/build_creatures_earth_v3.py`)

- One `draw_<name>(d, M, pose, seed)` per quadruped on shared parts: `Body` (squash about the ground with
  volume kept, pitch `rock` about `rock_at`, `lean`, `bob`, `shift`), `turn` (head rotation about the neck joint),
  `scale_about` (heads drawn 1.15-1.3x for era proportions), `legs_pass` (far pair in the mid tone first, near pair
  second, both under the body; hose legs with `bend` + per-pose `fold`; hooves, paws, claws), `eyes` (pie eyes in
  3/4, dizzy spirals while stars circle; never X eyes), `stars`, `puff`.
- Clips: `bump_clip()` is shared; `gallop(t, A, lz)` interpolates six keyed poses (airborne extension, front
  landing, gathered with folded front legs, hind push, launch) with the far pair one key behind.
- Clip order idle 0, walk 1, react 2, bump 3 matches Gus and Creature.cs's indices; anything after (flee,
  follow) is found by name. Faces: closed mouths or a small round "o", never teeth (D-087).
