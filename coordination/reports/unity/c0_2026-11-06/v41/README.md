# C0 v4.1 re-shoot · U-108 · 2026-11-06 23:15

v4.1 (D-100/D-101/D-102: thinner ink, faceless snoozle, upright Pilgrim). `SceneCapture.CaptureV41Set` via `tools/unity_capture.ps1 -Name v41 -Test CaptureV41Set`; the film pass is on in every still but 8. Art in the scene: B-125 surveyor, B-126 snoozle rig set v3.1 (`replaces_part` head/leaves, `swap_cycle` on the beat), B-127 gull (52 frames, fly 40–51), B-114 plains layers, B-115 film overlays.

Run: plants 48 (full rate 38, cheap 10), rig set style v3, daylight override 0.45, 1920×1080.

| Shot | File | What it shows | Logged facts |
|---|---|---|---|
| 1 | 1_idle.png | the surveyor idle among the snoozles | clip idle, plants 48 (full rate 38, cheap 10), set v3 flora/earth/rigset, nearest snoozle head head_open, leaves leaves_up, mouth none, swaps [head leaves], beat 0.545 s |
| 2 | 2_walk.png | walking right, mid-stride | clip walk, vx 4.0 m/s, nearest snoozle head head_open, leaves leaves_up, mouth none, swaps [head leaves], beat 0.545 s |
| 3 | 3_jump.png | the jump, rising | clip jump, vy 5.3 m/s, nearest snoozle head head_open, leaves leaves_up, mouth none, swaps [head leaves], beat 0.545 s |
| 4 | 4_land.png | the frame after touchdown (squash) | clip land, impact 6.8 m/s, squash y 0.70, nearest snoozle head head_open, leaves leaves_up, mouth none, swaps [head leaves], beat 0.545 s |
| 5 | 5_plant_react.png | the nearest snoozle reacting to the surveyor (turned, react swap on the head, leaves up) | reacting True, facing 1, snoozle head head_open, leaves leaves_up, mouth none, swaps [head leaves], beat 0.545 s, react action turn_bounce swap head_open |
| 6 | 6_critter_gull.png | one gull framed on purpose, 8 m off (outside its 6 m flee range), airborne | gull at (72.22, 340.07), viewport (0.64, 0.36), 3.1 m over the ground, state Wander, pick 4, flies True, sprite gull_40, clip fly (40-51) |
| 7 | 7_iris_mid.png | the iris 0.175 s into its 0.35 s close, centred on the surveyor | radius 0.870 screen heights |
| 8 | 8_film_off.png | the same frame without the film pass | film effects off |
| 9 | 9_film_on.png | the same frame with the film pass (B-115 grain, vignette, dust, scratches) | film effects on |

Sheets in play: characters/surveyor/side 192×192×98, creatures/earth/gull 112×96×52, flora/earth/rigset 7 parts, 1 plant(s), characters/calibration_v3/side 160×160×20.
