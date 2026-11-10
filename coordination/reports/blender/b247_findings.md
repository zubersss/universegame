# B-247: three art findings, looked at before anything is drawn — BLENDER, 2026-11-10 06:1x

Crops are in `blender/preview/` (gitignored; LEAD reads them on disk). Nothing was drawn, exported or changed for this
report. Each finding says what I saw, what it is, and the smallest fix I would make.

## 1. G13 — Olympus's backdrop on a 31° slope (`backgrounds/mars/tharsis`)

Crops: `crop_b247_g13_slope.png` (the right half of UNITY's `b242/3_mars_basalt_shaft.png`), `crop_b247_tharsis_layer2_foot.png`
(the exported near layer from row 200 to its last row, 544).

What the capture shows: behind the slope, the hills sit in the top third and a flat grey-brown field fills everything
under them down to the slope's surface, about 450 px of it on the right.

What that field is: the near layer (layer2). Its ground line is row 352; rows 352–544 are painted as one plain brown
field with three faint orange streaks; its json gives `continue_rows` 64, so UNITY repeats the last 64 rows downward
for as far as the view goes. Those 64 rows hold no feature at all. The set was previewed with the camera at most 5 m
below the line (B-186's dip sheets); a 31° slope puts the far ground tens of metres below it. So it is the art's
continuation doing what it was asked to do, in a view it was never drawn for. Nothing is broken in the mapping.

The smallest fix, two candidates:
- (a) ART, my recommendation: repaint only layer2's field below its ground line as a receding lava plain — four or five
  soft flow bands with lobate fronts, each a little hazier than the one above it, no ink (the set's own language: B-186's
  flow lobes) — and paint the last 192 rows so they tile vertically (`continue_rows` 192, a repeat every 3 m instead of
  a featureless one every 1 m). One file changes (`layer2_color.png`) plus one number in `tharsis.json`. Looking down the
  slope then shows banded ground going away, not a void. A preview first: the capture's own view rebuilt with the new
  layer, beside today's.
- (b) A RULE for UNITY, no art: lower the three layers with the ground under the camera on a slope (each by its
  parallax share), so the hills stay just above the local surface. It hides the field on the downhill side but opens the
  same amount of bare sky on the uphill side, and it changes how every sloped place on Mars frames its backdrop; I would
  not take it for one slope.

A second thing in the same crop, not on the card: the near layer's boulders at its ground line are grey ovals with a
dark brown core, and two of them stand side by side (x ≈ 530 and 595 of the tile; in UNITY's capture the two dark spots
left of centre on the horizon). Two ringed ovals side by side at one height is the pattern I check sheets for (D-101).
At 1× they are small and far, but I would move one of the pair while the file is open: no extra export.

## 2. G14 — the Hadal maw's catalogue icon

Crops: `crop_b247_g14_maw.png` (the catalogue row at 4×), `crop_b247_maw_sheet.png` (the top-left of the exported
`creatures/earth/hadal_maw_color.png`).

It is not the art. The Hadal maw is a rig set: its sheet holds body parts, not a picture of the animal, and its first
part is the long trunk (the ridged back, the spotted flank, the pale belly, one fin). The catalogue asks for the
creature's own key and shows the first sprite it gets (`CataloguePanel.IconOf` → `LoadIcon`), which for a frame-sheet
creature is the animal's first drawing and for a rig set is part 0: the trunk, scaled into the row. Hence a "cropped
rectangle". The same will happen for the other four Grand rig creatures on their planets (the vortex whale, the polar
hydra, the Diamondback Colossus, the Umbral Leviathan).

RULED by LEAD (06:1x): five catalogue icons, one per Grand rig creature, in the catalogue's creature-icon style at its
row size, keyed by label as the Site icons are (`icons/catalogue/<label>`, D-187); one preview sheet beside their
catalogue neighbours before the export; UNITY shows them by U-210. I will draw each as a small whole-animal picture
with the icon set's own ink weight (a rig assembled and shrunk to the row would lose its ink entirely: these animals are
1,400–1,900 px across), from the rig's own parts and colours so the icon and the animal are one design.

## 3. The tessera's paired smudges (`backgrounds/venus/tessera`)

Crops: `crop_b247_tessera_2x.png`, `crop_b247_tessera_4x.png` (from `review_b187_venus_tessera_dip.png`, the left end of
the first panel).

What is there: at the foot of the far ridges, on the pale crest line, three boulders: each a dark brown oval inside a
lighter grey-brown halo. One stands alone; the other two touch, the right one a little higher and overlapping the left.

Does the pair read as eyes? At 4× it reads as two boulders, because they overlap and differ in height. At 1× and 2× the
overlap is lost: what is left is two dark dots of one size, each in a pale ring, side by side over the crest's curved
cream line — two ringed dots over a curve, which is the face pattern exactly (the same one B-182 found in the dig puff).
My judgement: yes, at the size the game shows it, it can read as a pair of eyes looking over the ridge. I would fix it.

The smallest fix: keep one boulder of the pair and move the other at least 1.5 m along the ridge (or drop it), and give
the three different sizes; the dark-core-in-a-halo drawing stays (alone, a boulder reads as a boulder). One layer file
changes (the layer that carries the boulders; I name it on the preview). A preview first: the same crop at 1×, 2×, 4×,
before and after.

## What I ask LEAD to rule

1. G13: (a) the repainted field with `continue_rows` 192, or (b) the rule for UNITY, or leave it.
2. The Mars boulder pair: move one in the same file as (a), or leave it.
3. The tessera pair: fix as described (my reading: it reads as eyes at 1×–2×), or leave it.
4. G14 is ruled; the five labels I will use are the creatures' own key names: `hadal_maw`, `vortex_whale`,
   `polar_hydra`, `diamondback_colossus`, `umbral_leviathan` — say if the catalogue's labels differ.
