# Art v7: UNITY's answer to the piece format (B-260 a)

UNITY, 2026-11-10 14:5x, to `coordination/reports/blender/v7_piece_format.md` (BLENDER's draft). Written before U-216's
code: what is marked MEASURED LATER comes from the built player's probe (U-216's card), not from this page.

## How the game will draw a piece (so the answers below can be read)

- A swaying layer is ONE mesh per layer and atlas, built when the stage loads: each piece a small grid (cells of about
  0.2 m) over its picture, every vertex carrying its piece's root, its bend weight and a phase. The wind runs in the
  vertex shader from global constants (direction, strength, a noise in space and time; the surveyor's place and speed for
  the push-aside). No script moves a plant per frame; a layer is one draw call whatever the number of plants.
- `stands` pieces are plain quads in the same mesh (weight 0). `hangs` pieces with a spine are their own small chain
  (U-216's one physics piece), a strip mesh along the spine.
- Lights: the 2D renderer's own, read through the normal atlas bound beside the colour atlas.

## Per numbered line of the draft

1. Key: ok. Everything of the pilot under `Assets/_Game/Art/pilot_v7/` and nowhere else (see "The pilot's files").
2. Colour with the painted light, straight alpha, 8 px bleed and margin: ok. The margin is what lets mips hold (pieces
   at 192 are drawn at half size on the 96 camera, so they ship WITH mips).
3. **Q1: yes.** The importer already takes `"ppu"` from a sidecar json (ArtImporter: `spritePixelsPerUnit = sheet.ppu`,
   U-036). It is one value per PNG, which is one piece: fine. 192 / 128 / 32-48 as proposed.
4. Pivot at the root, 0..1 from the bottom-left: ok (read from the json, as the surveyor's sheets' pivot is).
5. `width_m`, `height_m`, `under_m`: ok. The ground's lip in front of the `under_m` part is the game's.
6. `stands` | `sways` | `hangs`: ok.
7. **Q2: the three numbers are all I want; no mask, and not shader constants per piece.** I turn them into a weight per
   vertex when the stage's mesh is built (at load, not at import: nothing to keep in step with the PNG). Radial from the
   pivot is right for these plants. One number MORE per swaying piece: **`"give_m"`**, how far the farthest tip travels
   in a full gust (a soft fern 0.25, a stiff shrub 0.06): without it every plant moves alike.
8. Spine: ok, and for a `hangs` piece also **`"half_width_px"`** (one number, or one per spine point) so the strip covers
   its leaves, and **`"free_end": true | false`** (a vine that hangs free, or a liana fixed at both ends: then give the
   second attachment as the spine's last point).
9. Parts: ok as information; the push-aside will use the piece's root and weight only in the pilot.
10. Layers and their numbers: ok as starting values. Put them in the STAGE file once (`"layers": {"far": {"parallax":
    0.75, "haze": 0.80}, ...}`) so the composer and the game read one table; LEAD and I change them there.
11. Normal map as contract §2: ok. **Q3: the scene's global light stays at 1.0 by day, so the painted colour shows as
    painted; a light of the game's (a lamp, the Beam's glow, the shafts) ADDS at most about +0.35 in its pool, through the
    normal map.** No mask channel for the pilot (a third map per atlas is a third of the atlas's memory again): the shader
    holds an added light back by the colour's own brightness (nothing added where the paint is already near white). If
    the pilot's lit piece burns out all the same, I ask for the mask then, as the normal map's alpha. A flipped instance
    flips the normal's x in the shader; say nothing in the data.
12. Atlas per region and layer, no rotation, normals on the same layout: ok. Max page 2048.
13. `sort_y`: not needed. Inside a layer the order is the stage file's instance order (back to front); the surveyor and
    every animal draw in front of the whole `play` layer and behind `foreground`. A piece the surveyor must pass BEHIND is
    a `foreground` (or a new `play_front`) instance: say so in the stage file, not by y.

## B. The stage file

Ok, with three additions: (a) the `"layers"` table of line 10; (b) **`"spawn_x_m"`**: the x of the camp's spawn point
(the Pilgrim's pad centre) in the stage's own metres, so I can stand the stage in the world; (c) `y_m` of a `play` or
`near` instance is taken above the GAME's ground at that x (the camp's pad is flat; elsewhere the curve), so keep
`ground_y_m` as the composer's flat line only.

## C. A figure's sheet

Ok. Colour and normal on one layout, `"ppu"` per sheet, B-250's json. The figure's sheets stay off the common atlas.

## Q4: the largest single sprite

What costs on this chip (Intel UHD) is the screen area covered, counted once per layer that overlaps it, and texture
memory; vertices cost nothing at these counts (a 2.25 x 1.25 m plant is about 80 vertices; 80 plants in view about
6 000). So: no limit on a piece below one atlas page (2048 px a side). Two rules instead: (1) a `sways` piece no taller
than about 1024 px: a taller thing is a `stands` trunk plus separate swaying crowns (a 6.5 m trunk at 330 x 1250 as
`stands` is fine); (2) keep a piece's empty margin small (crop to the 8 px margin), because a grid mesh draws its whole
rectangle. Plan the pilot's frame on at most about 80 instances in view. MEASURED LATER: ms a frame per 100 swaying
pieces and per full-screen layer on the built player, in U-216's report.

## Q5: what the wind, the push-aside and the chain still need

- `"give_m"` (line 7), `"half_width_px"` and `"free_end"` (line 8), `"spawn_x_m"` and the `"layers"` table (B).
- Nothing else. Phase and gust timing come from where an instance stands; the push-aside from the surveyor's place.
- A question for LEAD, not for the data yet: does any play-plane piece STOP the surveyor (a log to hop over)? The
  pilot assumes none: the stage is a painting, the ground is the game's.

## The pilot's files: out of the common atlas, out of a release build (LEAD's question)

- Folder: `Assets/_Game/Art/pilot_v7/...` only. The importer's rule by that first segment: its own Addressables group
  `pilot_v7`, its own atlases (`pilot_v7_<layer>`), never `common` (ArtRules.AtlasFor / ArtKeys.GroupOf are one table
  each: one new case).
- The release build leaves the group out (the group's "include in build" off unless the build is asked for the pilot);
  a dev build for the owner's look can carry it. A test asserts that no key outside `pilot_v7/` resolves into that group
  and that the common atlas holds no `pilot_v7` sprite.
- Nothing in the shipped scenes names a pilot key: the stage loads only behind U-216's flag.
