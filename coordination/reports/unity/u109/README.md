# U-109 · climb sky — captures 2026-11-07 05:31 (fourth pass)

`tools/unity_capture.ps1 -Test CaptureU109Climb -Name u109_climb` (unity_capture_20261107_053102.log), 1920×1080, the cartoon stage on Earth. Two camera-attached strips of 1 m rows in phase with layer0's top edge: the flat shade behind the painted layers (sorting BackOrder − 3: the painting's top-band colour at the edge, space black `span` metres above it) and the overlay in front of them (BackOrder + the layer count), which fades the painting's own grain into that colour over its top 1.5 m (ClimbSkyMath.OverlayAlpha). The B-120 starfield tile sits between the shade and the painting from half the climb.

| File | Camera | Evidence line |
|---|---|---|
| `1_ground.png` | y 343.1 (the pad) | edge 351.6 (rest 351.0), span 37.6 m, top measured #A4BCBD (the mean of layer0's top 64 rows), frame bottom #A4BCBD top #A4BCBD, stars not loaded |
| `2_climb_28m.png` | y 374.9 (ship 31.9 m: cycle 254's ~28 m frame) | edge 380.2: the painted edge 5.3 m above the camera, the painting fading into the shade over its top 1.5 m, the flat shade above, frame top #A1B8BA |
| `3_halfway.png` | y 528.9 (ship 190.0 m) | frame bottom #A3BBBC → top #556163, stars loaded, alpha 0.00 |
| `4_escape_line.png` | y 727.4 (under the line) | frame bottom #424B4D → top #020205, stars alpha 0.60, shown |

History of the join (all on this card): first pass 02:53, a flat strip over the grainy painting (a band read at the join); 04:21, layer0's top metre mirrored upward (a 1 m lattice three metres up); 04:46, the band faded over 2.5 m (a tonal step at the first metre: the band's mean is not the top row's); 05:02, per-row phases (cloud fragments and row steps); 05:21, the overlay: no sampled band above the edge at all, the painting fades into the sky colour from below (the strips still sampled the shared material's last sprite at v = 1: vertical streaks in the opaque metre); 05:31, both strips bind a white texel through a MaterialPropertyBlock (ClimbSkyPlayTests asserts it): the frame above is the result. Also fixed on the way (0b4af5a): the 1-px dark line across the sky (the side-scene layers imported with wrap Repeat in y; now Repeat in x / Clamp in y).

