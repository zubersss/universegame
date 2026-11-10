# Art v7: the piece format (B-260 a) — DRAFT for UNITY's answer

BLENDER, 2026-11-10. Written before either side builds to it (D-205, STYLE_V7 §3: the stage is many separate pieces
the game moves). Nothing here is exported yet; part (b) waits for LEAD's word after B-258 part 3. Every number below
comes from what `blender/scripts/v7_frame_pieces.py` already writes per piece (`blender/preview/b258/pieces/<id>.json`),
so the pilot's pieces can be exported to this without a second render. **UNITY: answer per numbered line ("ok" or what
your sway mesh and your lights need instead); questions for you are marked Q.**

## A. One stage piece (a plant, a frond, a vine, a grass clump, a trunk, a rock)

Files, contract §1 naming: `Assets/_Game/Art/<category>/<name>/<variant>_color.png`, `<variant>_normal.png`, `<variant>.json`.

1. **Key**: `stage_v7/<planet>_<region>/<piece>`, e.g. `stage_v7/earth_forest/fern_b`. The pilot's keys are
   `pilot_v7/camp/<piece>` (its own label and atlas, never the common atlas, never in a release build).
2. **Colour map**: 8-bit RGBA, straight alpha, sRGB. It carries the PAINTED light (the frame's one sun from the upper
   right, cool sky, warm bounce from the ground). This is a contract exception to §2 "no baked lighting" and is the
   point of v7; the game's lights ADD to it through the normal map. Colour is bled 8 px outward under alpha 0 and the
   picture has an 8 px transparent margin (§2), so a bending mesh never pulls in a dark fringe.
3. **Px per metre** (`"ppu"` in the json, per piece, not the global 128): rendered and painted at 384, shipped SHRUNK:
   near and play-plane pieces at **192** (x2 the 96 camera, x1.5 the 128 camera: only ever shrunk on screen, D-198);
   middle pieces at **128**; a far veil is a strip at **32-48**, enlarged by the game (soft is right there).
   Q1: can the importer set `pixelsPerUnit` per sprite from the json?
4. **Pivot** (`"pivot": [x, y]`, 0..1 from the bottom-left, Unity's convention): the ROOT: where the plant leaves the
   ground, or where a rock or trunk meets the ground line. Not the picture's middle.
5. **Size**: `"width_m"`, `"height_m"` (above the ground line), `"under_m"` (how far the piece reaches BELOW the ground
   line: a rock sits 0.0-0.3 m in the earth; the game draws the ground's lip in front of that part).
6. **Motion** (`"motion"`): `"stands"` (rock, trunk, stump, log: never bends), `"sways"` (rooted below, bends in wind and
   when the surveyor passes), `"hangs"` (fixed above, swings: a vine, a hanging frond; its pivot is the ATTACHMENT).
7. **Bend weight**: TWO NUMBERS AND A POWER, not a mask: `"bend": {"from_m": d0, "to_m": d1, "power": p}`. The weight
   of a point is `clamp((d - d0) / (d1 - d0), 0, 1) ^ p`, d = its distance from the pivot in metres: 0 at the root,
   1 at the farthest tip. Why radial and not by height: these plants grow OUT from one root (a fern's fronds arch
   sideways; by height its tips would hardly move). Why not a mask: a mask costs a texture read or an import step, and
   fronds that overlap in a flat picture cannot swing apart whatever the mask says. The rule for that case is LEAD's
   (13:3x, c): **a part that must move on its own is its own piece with its own pivot** (a large frond, a vine).
   Q2: is a weight per mesh vertex computed from these numbers at import what your sway mesh wants, or do you want
   them as shader constants?
8. **Spine** (optional, `"spine_px": [[x, y], ...]` from root to tip, px from the bottom-left): for long thin pieces
   (a vine, a tall grass stem, a hanging frond) so a chain or a bone strip can follow it. Absent on radial plants.
9. **Parts** (optional, `"parts": [{"root_px", "tip_px", "length_m"}]`): each leaf's or frond's own root and tip as the
   3D mesh has them (part 1's sway table). Information only: for a push-aside effect or a later finer mesh.
10. **Layer** (`"layer"`): `far` | `middle` | `near` | `play` | `foreground`. Depth and parallax belong to the LAYER,
    not the piece; proposed (the game's numbers are UNITY's and LEAD's): far 0.75 of the camera's travel, middle 0.40,
    near 0.08, play 0, foreground -0.35 (it passes faster than the play plane). Haze is the layer's too (a tint toward
    the region's haze colour: far 0.80, middle 0.35, near 0.08), not baked into the piece, so one piece serves two layers.
11. **Normal map**: `<variant>_normal.png`, contract §2 unchanged: camera space, OpenGL (+X right, +Y up, +Z toward the
    viewer), (n+1)/2, linear, (128,128,255) where transparent, dilated 8 px. It is the PAINTED surface's normal (the
    strokes' ridges are in it). Q3: with the light already painted in the colour, how strong do you want the game's
    lights (a multiplier you choose), and do you want an unlit `mask` channel to hold them back on a piece's lit side?
12. **Atlas**: one atlas per region AND layer (`stage_v7_earth_forest_near`, `..._middle`): pieces that draw together
    pack together; rotation off (the pivot and the bend are in the picture's axes); a far veil is its own unpacked
    texture, clamp, no mips. Normal maps pack to the same layout.
13. **Sort**: `"sort_y": true` for play-plane and near pieces (by the pivot's y, the usual 2D rule); layers sort by layer.

## B. The stage file (where the pieces stand)

`stage_v7/<planet>_<region>/<stage>.json`: the SAME file my composer (`build_v7_frame.py`) reads to make the preview
frame, so the frame LEAD judges and the stage the game builds are one layout:

```json
{ "stage": "camp", "ground_y_m": 0.0, "haze_rgb": [0.74, 0.82, 0.72],
  "light": { "pool_x_m": 8.5, "pool_radius_m": 5.0, "warm": [1.10, 1.04, 0.86], "shade": [0.80, 0.90, 1.02] },
  "instances": [ { "piece": "fern_b", "layer": "near", "x_m": 3.2, "y_m": 0.0, "scale": 1.0, "flip": false },
                 { "piece": "calathea_a", "layer": "foreground", "x_m": 0.6, "y_m": -0.4, "scale": 2.5, "flip": true } ] }
```
`x_m` from the stage's left edge, `y_m` above the ground line, `scale` on top of the piece's own size (the foreground
uses the near pieces at 2-3x), `flip` mirrors in x (the painted light then comes from the wrong side: the composer
allows it only in the foreground and far layers, which are in shade or haze).

## C. A figure's frame sheet (colour + normal)

As contract §5 / §11 and B-250's exported json (`frames`, `clips` with `fps` and `ground_speed`, sockets, the four
points), with: `<variant>_color.png` and `<variant>_normal.png` on the SAME layout; `"ppu"` per sheet (192 proposed: x2
the 96 camera); frames rendered at 384 and shrunk; the paint is in the materials, so a held pose is the same picture
frame after frame (no filter that crawls); the pivot at the feet on the ground line as today; pages by clip group as
B-250 (side, side_air, side_dig). The price of 12 against 24 drawings a second is B-263's table.

## D. What I need back from UNITY (one message)

Q1 per-sprite ppu from the json; Q2 vertex weights or shader constants; Q3 the lights' strength and a hold-back mask;
Q4 the largest single sprite your sway mesh takes without a cost you can measure (a 2.25 x 1.25 m plant at 192 is
432 x 240 px; a 6.5 m trunk is 330 x 1250); Q5 anything your wind, push-aside or chain code needs that is not here.
