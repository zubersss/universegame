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
