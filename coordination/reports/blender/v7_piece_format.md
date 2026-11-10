# Art v7: the piece format (B-260 a) — agreed between BLENDER and UNITY, for LEAD to lift

BLENDER, 2026-11-10 (draft 14:4x; UNITY's answer of 14:5x folded in: coordination/reports/unity/v7_piece_format_answer.md).
Written before either side builds to it (D-205, STYLE_V7 §3: the stage is many separate pieces the game moves). Nothing
is exported yet: part (b) waits for LEAD's word after B-258 part 3. Every number comes from what
`blender/scripts/v7_frame_pieces.py` writes per piece (`blender/preview/b258/pieces/<id>.json`), so the pilot's pieces
can be exported to this without a second render. One line per field; "(U)" marks what UNITY asked for or settled.

## A. One stage piece (a plant, a frond, a vine, a grass clump, a trunk, a rock)

Files, contract §1 naming: `Assets/_Game/Art/<category>/<name>/<variant>_color.png`, `<variant>_normal.png`, `<variant>.json`.

1. **Key**: `stage_v7/<planet>_<region>/<piece>`, e.g. `stage_v7/earth_forest/fern_b`. THE PILOT: every file under
   `Assets/_Game/Art/pilot_v7/` and nowhere else, keys `pilot_v7/camp/<piece>`; the importer gives that prefix its own
   group and atlases and a release build leaves the group out (U).
2. **Colour map**: 8-bit RGBA, straight alpha, sRGB. It carries the PAINTED light (the frame's one sun from the upper
   right, a cool sky, the ground's warm bounce). A CONTRACT EXCEPTION to §2 "no baked lighting", and the point of v7; the
   game's lights ADD to it through the normal map. Colour bled 8 px outward under alpha 0; the picture CROPPED to its
   content plus an 8 px transparent margin (a grid mesh draws its whole rectangle; the margin is what lets it ship with
   mips) (U).
3. **Px per metre** (`"ppu"`, per piece, not the global 128; the importer already sets pixelsPerUnit from a sidecar
   json's "ppu", one value a PNG (U)): rendered and painted at 384, shipped SHRUNK: near and play-plane pieces **192**
   (x2 the 96 camera, x1.5 the 128 camera: only ever shrunk on screen, D-198); middle pieces **128**; a far veil is a
   strip at **32-48**, enlarged by the game (soft is right there).
4. **Pivot** (`"pivot": [x, y]`, 0..1 from the bottom-left): the ROOT: where the plant leaves the ground, or where a rock
   or trunk meets the ground line. Not the picture's middle. A hanging piece's pivot is its ATTACHMENT.
5. **Size**: `"width_m"`, `"height_m"` (above the ground line), `"under_m"` (how far it reaches BELOW the ground line: a
   rock sits 0.0-0.3 m in the earth; the ground's lip is drawn in front of that part).
6. **Motion** (`"motion"`): `"stands"` (rock, trunk, stump, log: never bends), `"sways"` (rooted below; bends in the wind
   and when the surveyor passes), `"hangs"` (fixed above; swings: a vine, a hanging frond).
7. **Bend**: three numbers, no mask: `"bend": {"from_m": d0, "to_m": d1, "power": p}`: a point's weight is
   `clamp((d - d0) / (d1 - d0), 0, 1) ^ p`, d = its distance from the pivot in metres (0 at the root, 1 at the farthest
   tip). Radial, not by height: these plants grow OUT from one root (a fern's fronds arch sideways). UNITY turns the
   numbers into a weight per vertex when the stage's mesh is built at load (one mesh per layer and atlas, a grid of
   about 0.2 m cells per piece, the wind in the vertex shader from global constants: one draw call a layer) (U).
   A part that must move on its own is ITS OWN PIECE with its own pivot (LEAD 13:3x, c).
8. **Give** (`"give_m"`, per swaying or hanging piece): how far the farthest tip travels in a full gust: a soft fern
   about 0.25, a stiff shrub about 0.06 (U). BLENDER sets it per kind: grass 0.18, fern 0.25, broad leaf 0.14, weed 0.10.
9. **Size limits** (U): no limit below one atlas page (2048 px a side); a `"sways"` piece no taller than about 1024 px
   (a taller thing = a `"stands"` trunk + separate swaying crowns); what costs on the Intel chip is SCREEN AREA COVERED
   per overlapping layer, not vertices. A frame is planned on at most about 80 instances in view (the measured ms per 100
   pieces comes from the built player in U-216's report).
10. **Spine** (optional, `"spine_px": [[x, y], ...]` root to tip, px from the bottom-left): for long thin pieces (a vine,
    a tall stem, a hanging frond). A `"hangs"` piece also carries `"half_width_px"` (one number, or one per spine point)
    and `"free_end"` true | false (false = fixed at both ends: the second attachment is the spine's last point) (U).
11. **Parts** (optional, `"parts": [{"root_px", "tip_px", "length_m"}]`): each leaf's or frond's own root and tip as the
    3D mesh has them. Information only (a push-aside effect, a later finer mesh).
12. **Normal map**: `<variant>_normal.png`, contract §2 unchanged (camera space, OpenGL: +X right, +Y up, +Z toward the
    viewer; (n+1)/2; linear; (128,128,255) where transparent; dilated 8 px). It is the PAINTED surface's normal (the
    strokes' ridges are in it). The global light stays 1.0 by day so the paint shows as painted; a light of the game's
    adds at most about +0.35 in its pool through the normal map; NO mask channel for the pilot (the shader holds an added
    light back by the colour's own brightness; if a lit pilot piece still burns out, the mask becomes the normal map's
    alpha). A flipped instance flips the normal's x in the shader (U).
13. **Atlas**: one atlas per region AND layer (`stage_v7_earth_forest_near`, `..._middle`); rotation off (the pivot and
    the bend are in the picture's axes); a far veil is its own unpacked texture, clamp. Normal maps on the same layout.
14. **Draw order** (U): inside a layer, the stage file's INSTANCE ORDER (no sort by y). The surveyor and the animals
    draw in front of the whole play layer and behind the foreground. So a piece the surveyor passes BEHIND is not a
    play-layer instance: see `play_front` below.

## B. The stage file (where the pieces stand)

`<key's folder>/<stage>.json`: the SAME file BLENDER's composer (`build_v7_frame.py`) reads to make the preview frame,
so the frame LEAD judges and the stage the game builds are one layout and one set of numbers:

```json
{ "stage": "camp", "ground_y_m": 0.0, "spawn_x_m": 8.2, "haze_rgb": [0.80, 0.86, 0.76],
  "layers": { "far":        { "parallax": 0.75, "haze": 0.80 },
              "middle":     { "parallax": 0.40, "haze": 0.36 },
              "near":       { "parallax": 0.0,  "haze": 0.05 },
              "play_front": { "parallax": 0.0,  "haze": 0.0  },
              "foreground": { "parallax": -0.35, "haze": 0.0, "tint": [0.30, 0.40, 0.42] } },
  "light": { "pool_x_m": 8.8, "pool_y_m": 0.9, "pool_rx_m": 5.2, "pool_ry_m": 3.4,
             "warm": [1.14, 1.07, 0.86], "shade": [0.70, 0.83, 0.97] },
  "instances": [ { "piece": "fern_b", "layer": "near", "x_m": 3.7, "y_m": 0.10, "scale": 1.0, "flip": false },
                 { "piece": "calathea_a", "layer": "foreground", "x_m": 0.5, "y_m": -2.05, "scale": 2.6, "flip": true } ] }
```
- `x_m` from the stage's left edge, `y_m` above the ground line, `scale` on top of the piece's own size (the foreground
  uses the near pieces at 2-3x), `flip` mirrors in x. `spawn_x_m`: where the camp's spawn point stands (U).
- `layers`: parallax (the share of the camera's travel the layer keeps: 0 = moves with the play plane; negative = passes
  faster) and haze (a tint toward `haze_rgb`) belong to the LAYER, so one piece serves several layers and the composer
  and the game read the same numbers (U). The numbers above are BLENDER's proposal; the game's are UNITY's and LEAD's.
- `play_front` (BLENDER's addition, CONFIRMED by UNITY 14:5x: one more draw call, well inside Earth's budget): low
  pieces at the play plane that stand IN FRONT of the surveyor's feet (a grass tuft on the ground's lip). They must not
  slide against the ground (parallax 0), so they cannot be `foreground` instances; they draw after the surveyor and the
  animals and before the foreground. LOW TUFTS ON THE LIP ONLY: nothing in it may cover the surveyor's hands or the
  reticle (U).
- Instance order inside a layer is the draw order (the composer writes back rows first).

## C. A figure's frame sheet (colour + normal)

As contract §5 / §11 and B-250's exported json (`frames`, `clips` with `fps` and `ground_speed`, sockets, the four
points), with: `<variant>_color.png` and `<variant>_normal.png` on the SAME layout; `"ppu"` per sheet (192 proposed: x2
the 96 camera); frames rendered at 384 and shrunk; the paint is in the materials, so a held pose is the same picture
frame after frame (no filter that crawls); the pivot at the feet on the ground line as today; pages by clip group as
B-250 (side, side_air, side_dig). The price of 12 against 24 drawings a second is B-263's table.

## D. For LEAD (contract draft)

Two exceptions to contract §2 to rule: the painted light in a v7 colour map (A.2) and `ppu` per piece (A.3). Nothing is
open between the roles: everything above is agreed as written (`play_front` included).
