# U-109 · climb sky — captures 2026-11-07 04:19–04:21 (second pass)

`tools/unity_capture.ps1 -Test CaptureU109Climb -Name u109_climb` (unity_capture_20261107_041922.log), 1920×1080, the cartoon stage on Earth. The strip behind ParallaxLayers continues layer0's own top metre upward (its top 64 texel rows, mirrored row by row, tinted by BandTint = Shade / the top row's mean), rows in phase with the painted edge; the B-120 starfield tile over it from half the climb.

| File | Camera | Evidence line |
|---|---|---|
| `1_ground.png` | y 343.1 (the pad) | edge 351.6 (rest 351.0), span 37.6 m, top measured #A3BBBD, frame bottom #A3BBBD top #A3BBBD, stars not loaded |
| `2_climb_28m.png` | y 374.8 (ship 30.0 m: cycle 254's ~28 m frame) | edge 380.1: the painted edge 5.3 m above the camera, the strip above it, frame top #9FB8BA, Textured True |
| `3_halfway.png` | y 528.5 (ship 189.4 m) | frame bottom #A2BABC → top #546163, stars loaded, alpha 0.00 |
| `4_escape_line.png` | y 726.8 (under the line) | frame bottom #424B4E → top #020205, stars alpha 0.60, shown |

Fixed since the first pass (02:53): (a) the flat strip above the grainy edge → the textured band (Textured True in every frame); (b) the 1-px dark line across the sky in the climb frames (also in u103/2_tilted_climb.png): the side-scene layer textures imported with wrap Repeat in y, so each hills layer's top texel row bilinear-blended with its bottom row (ground colour) along the sprite's top edge (the line sat exactly on layer2's top at rest and on layer1's top at 10 m and 29 m). They now import Repeat in x / Clamp in y (ArtImporter + the nine metas re-imported; the starfield's tile_y layer keeps both), and a row scan of the three sky frames finds no full-width line.

Known in this pass, fixed in the next commit: above the edge the mirrored 1 m band repeats as a faint lattice (2_climb_28m, the top 3 m of the frame). The band now fades into the flat shade over 2.5 m (ClimbSky.FadeM), so the grain crosses the join and dissolves before it can repeat.
