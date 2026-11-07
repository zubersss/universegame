# U-113 · camp props as sprites (D-117, D-125, B-131) — 2026-11-07

Code: `Code/Runtime/Art/SheetProp.cs` (new) with `ModelSwap`, `PoiPlacer`, `BaseBuilder`, `CraftingStation` wiring; EditMode `PropSpriteTests` (the six sheets against the hand-off, the pure fit rules); PlayMode `U076SceneTests` keeps the 3D path's camp (it switches the cartoon path off for its run, D-132).

How it works: when a `props/common/<prop>` key resolves to a v3 sheet and to no model (B-131 removed the six glbs and their maps), the card's SpriteRenderer stays and `SheetProp` dresses it: frame 0 at the sheet's PPU and pivot (the ground line 10 px above the frame bottom; the wall tile has none), a `tile` sheet repeats its module across the footprint (the pad: 128×48 at 2 m; the wall: a 64×64 tile at 1 m in x and y per D-125, so BaseBuilder's 1 × 1 cell and stretch rule stand), the door's 88×176 scales uniformly into its 1 × 2 cell (Fit.Height), and the sheet's §11.8 Animator plays its clips: the door's `open` (6 frames) once forward on use and backward on close, the smelter's `working` (8, loop) while its station works, the lamp's `flicker` (4, loop) by night and in the dark. Every other key keeps the model path.

| Key | Frame | Clip | Interactable |
|---|---|---|---|
| props/common/landing_pad | 128×48, tile at 2 m | — | no |
| props/common/shelter_wall | 64×64, tile x + y at 1 m (D-125), ground line 0 | — | no |
| props/common/shelter_door | 88×176 | open 6 once | yes |
| props/common/smelter | 112×192 | working 8 loop | yes |
| props/common/storage_crate | 80×72 | — | yes |
| props/common/lamp | 64×160 | flicker 4 loop | no |

Found on the first PlayMode pass (06:36): the camp sidecars had no Addressables entry at `<key>/json` (the importer addressed only planets/* and the rig sets' jsons), so ModelSwap's probe never took the sheet path and the cards showed frame 0 unanimated; the importer now addresses props/* sidecars too and CheckSetup's AddressPlanetSidecars pass covers the ones already on disk (79 addressed 06:52); PropSpriteTests asserts the six addresses.

Capture: `camp_1x.png` (= `../u104/hud_1080p.png`), the on-foot frame by the camp at 1× (the U-104 capture, re-shot after B-131's export: the painted pad, wall, door, smelter, crate and lamp replace the grey stand-ins). Its evidence line and the frame are listed in the batch's status entry.
