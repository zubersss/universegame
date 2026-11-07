# U-103 · drawn Pilgrim rig (B-122) and the painted Space scene — captures 2026-11-07 02:50–02:53

Shot by `tools/unity_capture.ps1 -Test CaptureU103Ship -Name u103_ship` (log unity_capture_20261107_025009.log) and `-Test CaptureSpaceArt -Name u103_space` (unity_capture_20261107_025151.log), both 1920×1080, graphics device on, cartoon stage on Earth.

| File | What it shows | Evidence line |
|---|---|---|
| `1_pad.png` | the upright Pilgrim rig on the pad, aboard, at rest | `ship art: rig (6 bones, playing fin_wobble, animator on), fx on rig True`; tilt 0.0°, alt 0.1 m, stand-in False |
| `2_tilted_climb.png` | full thrust, D held: −35° tilt, the puff loop at `tail_exhaust`, the attitude puffs at `attitude_l/r`, fins wobbling | tilt −35.0°, v (24.5, 5.1) m/s, T/W 1.22, alt 28.6 m |
| `3_escape_line.png` | upright again just under the Escape Line (the next metres launch) | v (25.2, 38.4) m/s, camera on the hull |
| `space_1_saturn.png` … `space_5_earth_luna.png` | the B-119 discs (Saturn with its rings, Jupiter, Neptune, the belt's 286 rocks, Earth + Luna) over the B-120 starfield scene | `belt rocks 286, rings ready True` |
| `space_6_pilgrim.png` | the top-down Pilgrim from the rig's `pilgrim_top` (nose right, fin_wobble) parked outside Earth's well, thrusting | `space pilgrim: rig fit 0.299, playing fin_wobble` |

Note for U-109's review: the flat strip above layer0's grainy top edge in `2_tilted_climb.png` is the first ClimbSky (a flat colour from the measured top row); it is being replaced by layer0's own top metre continued upward and shaded, and `u109/` will be re-shot.

Re-shot 2026-11-07 03:56–03:58 under U-117 (unity_capture_20261107_035637.log): space_1 … space_6 with the discs on a FullRect sprite mesh (no texel stairs on the limb at 10× in space_6_pilgrim) and the starfield's tile period growing with the zoom (no visible repeat across the far frame in space_1_saturn). The 1-px line across the sky in 2_tilted_climb.png predates the wrap-in-y import fix (u109/README.md); u109/2_climb_28m.png is the same altitude after it.
