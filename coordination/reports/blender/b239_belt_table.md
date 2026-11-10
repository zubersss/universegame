# B-239 · The giants' belt table: one source for the far discs and the close view (BLENDER, 2026-11-09)

Card: lift the four giants' belt tables out of `build_discs_v3.paint` into ONE table both builders read; prove the far
discs BYTE-IDENTICAL after it; draft `planets/<giant>/close.json` per giant into blender/preview only. No new art, no
export. The design it serves: `b237_limb_band_design.md` (LEAD ruled its four points 22:0x).

## 1. What changed in the source

- **New: `blender/scripts/giants_v3.py`** (no imports, no drawing): `GIANTS` holds, per giant, the belts as (v_top, tone
  recipe), the edge wobble (wob, freq), the storms (Jupiter's Red Spot; Neptune's dark storm and its companion cloud),
  the edges that carry ink dashes, and Saturn's rings (tilt, inner, outer, the Cassini gap, three bands); `NIGHT` (the
  night crescent's circle) and `SHADE` (the one shadow tone: 0.3 of the way to brown); `tone()`, `storm_blobs()`, and
  `close_json()` for the close view's draft.
- **`blender/scripts/build_discs_v3.py`** reads it: the four `elif name == <giant>` branches of `paint()` are one
  `paint_giant()`; `BAND_EDGES`, the night crescent's test, `shade()` and `saturn_rings()` take their numbers from the
  table. The inner planets' branches are untouched.
- **The proof command:** `build_discs_v3.py --b239 <art> <out dir>` rebuilds the four far discs and Saturn's two ring
  parts, writes each into the out dir, compares each written file's sha1 with the exported file's (and the sheet json's
  text), then writes the four `close.json` drafts there. It writes nothing under the art folder and exits 1 on any
  difference.

## 2. A finding on the way: the shelved soft limb was still the builder's default

The first proof run (22:07, the painting code untouched) DIFFERED from every exported file: 36,081 pixels on Jupiter's
sheet (about 4,000 a frame: the limb's ring), 32,391 on Saturn's, 26,028 / 25,464 on Uranus's / Neptune's, about 9,550
on each ring part. Cause: `build_disc(name, limb=True)` and `saturn_rings(..., limb=True)` still defaulted to B-143's
soft alpha limb, which D-128's amendment shelved ("code kept, never run", c43c8da3, 11-07). The exported far discs have
no soft limb. So `export()` and the review, both on the default, would have re-drawn every far disc's limb at the next
re-export of the disc set, against the ruling.

Fixed in step A: both defaults are `limb=False`; only `b143()` (the shelved soft-limb run itself) asks for the limb. It
is a change of a default in my builder, made because the ruling and the exported files both say so; LEAD may want it
noted beside D-128.

## 3. The proof (hashes before / after)

Three runs of the same command, each in my lock (numpy, about 3 minutes, peak about 360 MB):

| Run | Code state | Result |
|-----|-----------|--------|
| 22:07:14-22:10:17 | paint untouched, the soft limb still the default | 6 of 6 files DIFFER (section 2) |
| 22:13:26-22:16:19 (BEFORE) | paint untouched (its numbers inline), no soft limb; commit a1935c8b | 6 of 6 BYTE-IDENTICAL, 4 of 4 json texts identical |
| 22:28:30-22:31:23 (AFTER) | paint, BAND_EDGES, the night crescent, shade() and saturn_rings() read `giants_v3.GIANTS` | 6 of 6 BYTE-IDENTICAL, 4 of 4 json texts identical |

BEFORE, sha1 of the rebuilt file = sha1 of the exported file:

| File | Size | sha1 (rebuilt = exported) |
|------|------|---------------------------|
| planets/jupiter/disc_color.png (1976 x 1976, 9 frames) | 1,753,456 bytes | 91b43c2526d50762cb4b7cfd0c04aa72deb60d24 |
| planets/saturn/disc_color.png (1796 x 1796, 9 frames) | 1,232,774 | 39629e39c22a59ff40c68119f6639a53ba6b2b2a |
| planets/uranus/disc_color.png (1836 x 1100, 12 frames) | 482,187 | e55e55a70725dc3fd3fca1e6757fa9617ea0233b |
| planets/neptune/disc_color.png (1796 x 1076, 12 frames) | 474,902 | 180e4a9f2ba4f2883109bc33536463e1053c6502 |
| planets/saturn/rings_back_color.png (1332 x 416) | 10,776 | 55aaaa8b729d17248415365153630b4edac1f165 |
| planets/saturn/rings_front_color.png (1332 x 416) | 11,348 | 102c349eb3f003c78515fd5437732ea7d879864f |

AFTER (22:28, from the shared table): the same six sha1 values, file for file, and the same sizes. The run's own line for
each reads "rebuilt sha1 X | exported sha1 X | BYTE-IDENTICAL"; its last line, "RESULT: all byte-identical"; exit 0. The
rebuilt files are in `blender/preview/b239/` (and the BEFORE run's in `blender/preview/b239_before/`).

So: before = after = exported, for the four giants' far discs, their sheet jsons and Saturn's two ring parts.

## 4. The close.json drafts

Written by the AFTER run into `blender/preview/b239/` (preview only, `"draft": true`, not exported): `jupiter_close.json`,
`saturn_close.json`, `uranus_close.json`, `neptune_close.json`. Each is filled from the table by `giants_v3.close_json()`,
so its numbers are the far disc's.

| Giant | radius_u | loop_frames | belts | storms | rings |
|-------|----------|-------------|-------|--------|-------|
| Jupiter | 106 | 9 | 8 | red_spot (1 blob: lon 0.25 turns, v -0.38, radius 0.13; drift 0.35 turns a loop) | - |
| Saturn | 96 | 9 | 5 | - | tilt 0.30, 1.24-2.27 radii, the gap 1.95-2.03, 3 bands |
| Uranus | 57 | 12 | 3 | - | - |
| Neptune | 56 | 12 | 4 | dark_storm (1 blob) and companion_cloud (17 small blobs in a chain), both drifting 0.4 turns a loop | - |

Fields (I read Jupiter's draft whole; the other three by their counts and tones): `belts` [{v_top, tone_hex, night_hex}]
from the north down (the first v_top is 1.1, above the pole; the last belt runs to the south pole); `edge_wobble` {amp,
freq, the formula}; `ink_dash_edges`; `night` {centre, radius, toward_hex, t}; `storms` [{name, tone_hex, night_hex,
drift_turns_per_loop, blobs}]; `rings` (Saturn); `swap` (DiscSprite's 6 / 5).

Two differences from the design note's sketch of this json, both because the far disc does it this way: the night side is
a mix toward brown (`toward_hex` + `t`, with `night_hex` given per belt), not a multiply colour; and a storm is a list of
blobs, because Neptune's cloud is a chain of seventeen.

## 5. B-240 (1): the inner set (22:45)

The same compare for everything else the change touched (through `shade()` and the night crescent's test):
`build_discs_v3.py --b239 Assets/_Game/Art blender/preview/b239_inner inner`, in my lock 22:45:12-22:45:56 (44 s, peak
212 MB), on the code as it is after B-239. "Before" is the exported file (drawn by the old code); "after" is the rebuilt
one. All ten files BYTE-IDENTICAL, all five sheet jsons' text identical; nothing to fix.

| File | Size | sha1 (exported = rebuilt) |
|------|------|---------------------------|
| planets/mercury/disc_color.png (1292 x 104, 12 frames) | 44,567 bytes | bf4bbdf23508a4907d205c68b3f3cd3f256359dc |
| planets/mercury/disc_near_color.png (512 x 512, k 5.86) | 243,028 | 3274562e798904fdb56be7b7ae72b94ab6eed3a5 |
| planets/venus/disc_color.png (2012 x 164, 12 frames) | 77,512 | 69fff11b9f992660545842e43608ec289a592c0c |
| planets/venus/disc_near_color.png (512 x 512, k 3.42) | 263,274 | be324d2713d9a10c23abdc44e2e86a1018b52f94 |
| planets/earth/disc_color.png (1932 x 348, 12 frames) | 169,435 | a3c986c81c67aa3460da027b9edbe037430a1611 |
| planets/earth/disc_near_color.png (512 x 512, k 3.28) | 253,037 | 56aa047be2c01c3da658c65da29155b61be97dbd |
| planets/mars/disc_color.png (1532 x 124, 12 frames) | 37,946 | 51cb132151f7d7cb8fdc0e331bf9791c86d7a7e7 |
| planets/mars/disc_near_color.png (512 x 512, k 4.82) | 226,806 | c18f7d8d49895f94864718ff998b1109c39996c8 |
| planets/earth/luna_color.png (812 x 64, 12 frames) | 4,776 | f6de1e64b3f0068b3aedefd5d1d4df20e13c0ce0 |
| planets/earth/luna_near_color.png (356 x 356, k 8.00) | 127,748 | 6acaa6fdb8c6467469d524688325105d16e2ec8a |

The near frames' jsons were not compared (their dict is built inline in `near_export`, which B-239 did not touch).
With section 3 that is every file the disc builder exports: 16 pngs and 9 sheet jsons, all reproduced byte for byte.

### Later re-runs of both proofs (each after a change to giants_v3.py or build_discs_v3.py)

| When | What had changed | Giants (6 pngs, 4 jsons) | Inner set (10 pngs, 5 jsons) |
|------|------------------|--------------------------|------------------------------|
| 23:06 / 23:09 | B-240: the far disc's ink marks lifted into `giants_v3.MARKS` (read by `interior_marks`) | all byte-identical | all byte-identical |
| 23:53 / 23:56 | B-241: `close_json` gained a storm's `streak` and its taper (the painting code untouched) | all byte-identical | all byte-identical |
| 11-10 01:14–01:18 / 01:28–01:29 | B-243, BEFORE its export: `giants_v3` gained `STRIP_SCALE` 7.5, `EDGE_VARIANT`, `strips_json` (close.json's `strips`); the inner run also with `night_hatches.groups` written as objects (UNITY's JsonUtility) | all byte-identical | all byte-identical |
| 11-10 01:30–01:33 / 01:33–01:34 | B-243, AFTER the export of `planets/common/close_view` (24 new files; no disc file written), same lock | all byte-identical | all byte-identical |

B-243's hashes (sha1; rebuilt = exported in every row, 11-10 01:33 / 01:34; the 9 sheet jsons' text identical):

| File | Bytes | sha1 |
|------|-------|------|
| planets/jupiter/disc | 1753456 | 91b43c2526d50762cb4b7cfd0c04aa72deb60d24 |
| planets/saturn/disc | 1232774 | 39629e39c22a59ff40c68119f6639a53ba6b2b2a |
| planets/uranus/disc | 482187 | e55e55a70725dc3fd3fca1e6757fa9617ea0233b |
| planets/neptune/disc | 474902 | 180e4a9f2ba4f2883109bc33536463e1053c6502 |
| planets/saturn/rings_back | 10776 | 55aaaa8b729d17248415365153630b4edac1f165 |
| planets/saturn/rings_front | 11348 | 102c349eb3f003c78515fd5437732ea7d879864f |
| planets/mercury/disc | 44567 | bf4bbdf23508a4907d205c68b3f3cd3f256359dc |
| planets/mercury/disc_near | 243028 | 3274562e798904fdb56be7b7ae72b94ab6eed3a5 |
| planets/venus/disc | 77512 | 69fff11b9f992660545842e43608ec289a592c0c |
| planets/venus/disc_near | 263274 | be324d2713d9a10c23abdc44e2e86a1018b52f94 |
| planets/earth/disc | 169435 | a3c986c81c67aa3460da027b9edbe037430a1611 |
| planets/earth/disc_near | 253037 | 56aa047be2c01c3da658c65da29155b61be97dbd |
| planets/mars/disc | 37946 | 51cb132151f7d7cb8fdc0e331bf9791c86d7a7e7 |
| planets/mars/disc_near | 226806 | c18f7d8d49895f94864718ff998b1109c39996c8 |
| planets/earth/luna | 4776 | f6de1e64b3f0068b3aedefd5d1d4df20e13c0ce0 |
| planets/earth/luna_near | 127748 | 6acaa6fdb8c6467469d524688325105d16e2ec8a |

The giants' BEFORE run (01:14) used the source as it stood before UNITY's field names went in (`strips.scale`, `cut_row`,
`rows_from`, the hatch groups as objects); those edits touch only what `close_json` writes, and the AFTER runs prove the
final source. B-243's export: `tools/blender_render.ps1 planets/common/close_view`, exit 0, 7.5 s, peak 356 MB, log line
2026-11-10T01:30:00; every strip's seam 0.00 (close_grain 0.95 in x, 1.04 in y), limb_band's palette 100 %.

## 6. Not done, not checked

- Added since B-239 (B-240): the drafts gain `rim` (the far limb is lumpy, not a circle: r(angle) = 1 + 0.012 sin(3 angle +
  ph3) + 0.008 sin(5 angle + ph5), the two phases per body), so the close view's limb can follow the far disc's own curve.
- No art was drawn and nothing was exported; `git status` shows no change under Assets/_Game/Art/planets.
- The drafts' hex tones were not compared against pixels of the exported discs by a separate check; they are computed
  from the same recipes the byte-identical painting uses.
- One slip of mine at 22:32: a shell line ended in a bare `python` call that hung and went to the background; I stopped
  it at once (no python or Blender process left, checked). No lock was on file when it started.
