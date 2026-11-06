# C0 · U-094 evidence (2026-11-06 16:08)

`earth_c0_placeholder.png`: Earth at the camp on the v4 2D path (`CartoonStage.Enabled`, Earth only), shot by
`SceneCapture.CaptureC0Earth` (tools/unity_capture.ps1 -Name c0 -Test CaptureC0Earth).

- Camera: orthographic, 16.875 m tall (orthographicSize 8.438 = 1080 px / 64 px per m), §5.1 stage rules kept.
- Background: 3 parallax layers from `SceneLayout.Default()` (no `backgrounds/earth/plains/plains.json` yet, B-114):
  flat tinted placeholder strips at parallax 0.1 / 0.3 / 0.6, bottoms at y_m 4 / 2 / 0 above the camp's ground line
  when the camera rests (frame/2 − 3 m over the floor). The painted layers replace them by key with no code change.
- Surveyor: B-111 step 2's `characters/surveyor/side` (real art, imported by v13; clips idle 10, walk 12, jump 8,
  land 8, look_camera 12 at 12 fps as Animator clips, controller `characters/surveyor/side/animator`). Clips the sheet
  lacks (run, fall, bump, conk_out, dash) play their stand-ins (walk, jump, idle).
- Still 3D in C0, by design: terrain blocks and back wall, the camp props, the Pilgrim (its old rig tool sprite in the hand).
- Checks: check 7 (16:05–16:08) compile 0 errors / 0 warnings, EditMode 268/268, PlayMode 26/26 on the U-093 + U-094
  filter (BumpTests, ConkOutTests, FeelPlayTests, SquashPlayTests, WardenPlayTests, RigModuleTests, InnerCreatureTests,
  MenuHudTests, CreatureTests, CartoonSmokeTests); `coordination/reports/unity/tests_2026-11-06.md`.

## U-095 · film pass (16:32 capture, 16:37 / 16:43 profiles)

`earth_c0_film_off.png` / `earth_c0_film_on.png`: the same frame with the Film effects setting off and on (one blit,
MERIDIAN/FilmPass: grain, dust and scratches from fx/film/{grain,dust,scratches} tiled 1:1 at 512 px, vignette,
±2 % flicker at 12 Hz, warm grade). `earth_c0_placeholder.png` is now the film-off frame.

- GPU cost (dev build, 1920×1080, FrameTimingManager, 120 frames each, Earth camp): film on 11.24 ms / off 11.62 ms
  (16:43), on 11.35 / off 11.58 (16:37): the pass is below the run-to-run noise (±0.4 ms), well inside the 0.6 ms line.
  `perf_2026-11-06.md`, row "Film pass GPU · Earth (dev build)".
- Toggle: `FilmPlayTests.TheToggleRemovesThePass` (real graphics device, 16:30): nothing is recorded while the setting
  is off, every render records while it is on. Overlays: `FilmTests` (512², repeat, no mips, sprite). HDR is off on
  MERIDIAN_URP; the cartoon camera renders no bloom post.
- The 16:43 gate run was red on one unrelated row (entry transition 1.77 s, breakdown slower everywhere with the Editor
  at 232 MB free during the measurement); see UNITY_STATUS for the note to LEAD.

## U-096 · iris wipe (16:55 capture, 16:52–16:55 check)

`iris_strip.png`: six frames of the iris-out closing on the surveyor at t = 0, 0.07, 0.14, 0.21, 0.28, 0.35 s (radii
1.021, 0.980, 0.858, 0.653, 0.368, 0.000 screen heights; accelerating close, the open is the same curve backwards).
One full-screen quad on the transition canvas with MERIDIAN/IrisWipe (a circle cutout, no texture, 4 px soft edge).

- Launch: input lock 0.3 s + iris-out on the ship + scene switch + iris-in on the ship in space: `TransitionTests`
  measured 1.00 s (limit 1.5). Entry: the camera pushes in while the iris closes on the ship (0.35 s), the planet loads
  while the screen is black, the iris opens on the ship flying in: 1.07 s (limit 1.5). The v3 white fades are retired.
- ConkOut (U-093) closes the iris on the fallen surveyor and opens it at the wake.
- Check (16:52–16:55, real graphics device): compile 0/0, EditMode 275/275 (IrisTests 3: cover radius to every
  corner, 0.35 s close to 0 / mirrored open, shader present; FilmTests 4), PlayMode 7/8, 0 failed, 1 skipped (the
  Editor GPU-cost test ignores itself: the number is the probe's); filter TransitionTests|WardenPlayTests|ConkOutTests|
  FilmPlayTests|CartoonSmokeTests.
