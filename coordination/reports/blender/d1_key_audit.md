# B-215 · The D1 key audit (BLENDER, 2026-11-08 21:35, HEAD 84a0c2e3+)

Every art key the D1 code and tables request, checked on disk under `Assets/_Game/Art/` (the `_color.png` and the `.json`), with the json fields the importer reads (`ArtImporter.SheetManifest`: frame grid, gutter, clips, parts, slice, pivot, style) checked against the png. Then every key present in a D1 folder that nothing requests.
Read-only: `blender/scripts/audit_d1_keys.py` (re-run it before the D1 build: `python -I blender/scripts/audit_d1_keys.py . <out.json> <table.md>`). No Blender, no exports.

**Sources:** `Settings/Resources/D1/D1Tables.json` (the dig tables' items per planet and tier, the planets) and `SkillTree.json` (66 nodes, their items); in `Code/`: `ArtKeys.cs`, `SkillTreePanel.cs`, `SpaceMap.cs`, `SideHud.cs`, `SideFx.cs`, `RigModule.cs`, `RigToolView.cs`, `PlayerRigInput.cs`, `ItemRegistry.cs` / `ItemIcons.cs`, `SmoothGround.cs`, `SurfaceLineView.cs`, `GroundStrip.cs`, `ResourceFinds.cs`, `CartoonStage.cs`, `MenuController.cs`, `TerrainBlockPalette.cs`. Composed keys are expanded from their sources: node ids, the tables' items, the map's bodies, the D1 planets (Earth, Mars, Mercury, Venus), tiers 2–5, decor slots 1–4.

## Summary

- **Requested: 321 keys. Missing: 0.** No required key is missing. By area:
  - Skill Tree: 85 (66 node icons + 19 kit pieces)
  - item icons: 22
  - map: 21
  - HUD and panels: 9
  - D1 ground: 47, plus 88 decor probes
  - other ground paths (strips, tile sheets, backwall): 30
  - FX: 5; tools: 4; surveyor sheets: 5; finds props: 5
- **29 optional probes come back empty by design.** `SmoothGround.ProbeDecor` (SmoothGround.cs:153) probes four slots per decor set. The art supplies fewer, so the extra slots stay empty and the scatter uses what exists:
  - region fills: Earth `fill_decor_sand_1..3`, Mars `fill_decor_basalt_1..3` (B-192: 3 each);
  - tiers (B-203): Earth t2–t4 3 each and t5 2; Mars t2–t3 3 each and t4–t5 2; Mercury and Venus 2 per tier.
  - Not a gap unless LEAD wants four per set.
- **json: every v3 key passes.** For each sheet, the frame grid matches the png, clips stay in range, parts sit inside the png, slices leave a centre and pivots are in 0..1.
  - The 10 flags are all **legacy v2** assets (no `style`, made before v3). Two of them, the Survey and Builder tools, have no json at all.
  - **8 of the 10 are still played in the D1 loop** (Findings 1–3). The other 2 are `characters/surveyor/mk1..3`, which only the 3D path loads (tests only, ArtKeys.cs:23–25).
  - The 22 terrain tile sheets without json are routed by path (ArtRules.cs:43), so they need no json. That path isn't D1's: D1's ground is SmoothGround.
- **Present but requested by nothing: 133 keys in the D1 folders.** 58 are D1 art awaiting wiring, 75 are older ground art.
  - Most is newly delivered D1 art waiting for UNITY's wiring (Finding 4).
  - One older group sits unwired on the ground: the lips, the surface decor, the per-variant dig puffs and three Earth strips (Finding 5).

## Findings

1. **v2 art in the dig loop's FX.** These are B-012 renders (10-30), the pre-cartoon style, played on every Beam hit and landing in D1:
   - `fx/dig_sparks/base` (SideFx.cs:24, :46)
   - `fx/dust/base` (SideFx.cs:25, :78)
   - The v3 replacements exist only per planet and band, as `terrain/<planet>/dig_puff` (requested, SideFx.cs:72, for the brush) and its variants (unrequested, Finding 5).
   - **Gap:** no v3 sparks or landing dust. Options:
     - a BLENDER card for v3 ink `fx/dig_sparks` + `fx/dust` in B-212's style;
     - or UNITY plays the dig_puff set in their place.
2. **The Beam's ray is the v2 one.**
   - `RigToolView.cs:66` loads `fx/beam_ray/base` (B-037, 256×32 frames, pre-v3).
   - B-205's v3 rays `fx/beam_ray/mk1..mk5` (teal→gold by Mk, D-087's mining Beam) are present and requested by nothing.
   - **Gap (UNITY):** load `fx/beam_ray/mk<BeamMk>`.
   - In the same way, `props/rig/beam` / `grapple` resolve to B-205's Mk1 copies. The `beam_mk1..5`, `grapple_mk1..3` and `jetpack_mk2 / mk3` keys (json `back_socket` / `back_socket_b`) are unrequested, so every Mk shows as Mk1.
3. **The Survey and Builder tools are v2, and both are D1.**
   - D1_TABLES: the Builder spends the dirt store on mounds, ramps and ladders from the start (§1, §3); the Survey branch's scan (§5).
   - Still v2 (B-037, 10-31):
     - `props/rig/survey` and `props/rig/builder` (RigModule.cs:21–22): colour / normal / emission pngs and **no json**, so the importer has no pivot for them. Their muzzles are code constants (RigModule.cs:33–34) measured on the v2 drawings.
     - `fx/survey_scan/base` (PlayerRigInput.cs:54, :99)
     - `fx/builder_ghost/base` (RigToolView.cs:67)
   - **Gap (BLENDER, if LEAD wants it before D1):**
     - a v3 Survey tool and a v3 Builder tool in B-205's contract (128×64 @ 128 ppu, pivot = the hand, json sockets);
     - a v3 scan ring and builder ghost;
     - no grip and nothing gun-like (D-087).
4. **Delivered D1 art waiting for UNITY's wiring** (none of it requested yet):
   - `ui/hud/` D1 set (B-211: U-174 / U-178)
   - `ui/hints/*` (B-213: U-185)
   - `ui/rank/*` (B-206: U-178)
   - `fx/rare/*` (B-212: U-174)
   - `fx/ui/*` (B-214: U-174 / U-175 / U-178)
   - `props/dig/*` (B-210: the ladder the Builder places, the grapple line and hook, the winch post, the recall beacon)
   - the tool Mks and rays (Finding 2)
   - `ui/panels/grain` (B-208: U-181)
   - `ui/skilltree/panel` (B-204's kit; SkillTreePanel.cs:173 backs the tree with `ui/panels/scroll` instead: wire it or retire it)
   - The surveyor's `side_b` sheet is requested (ArtKeys.cs:21), so its `climb_ladder` / `reel_up` clips arrive with it.
5. **Older ground art nobody requests.** The smooth ground (SmoothGround.cs) asks for `ground_band*`, `ground_fill*`, `dig_rim`, `ground_fill_t*`, `fill_decor*` and `surface_line`. It never asks for these keys, which are on disk for all four D1 planets:
   - `ground_lip` + `ground_lip_<variant>`: B-175 / B-180 / B-198, the brink lips; 13 keys.
   - `ground_decor_1..6` + `ground_decor_<variant>_1..3`: B-175 / B-178, the surface scatter; 51 keys.
   - `dig_puff_<variant>`: B-190 / B-191; 8 keys. SideFx.cs:72 asks only for the planet's base `dig_puff`.
   - Earth `ground_strip_sand / _soil / _stone`: GroundStrip.cs:19 asks only for `ground_strip`.
   - So in the D1 build the dig planets show no brink lips and no surface decor, and every band digs with the base puff.
   - **Gap (UNITY):** wire them, or LEAD retires them.

## Every requested key

| Area | Key | Requested by | Present | json (importer fields vs the png) |
|---|---|---|---|---|
| characters | `characters/surveyor/mk1` | Runtime/Art/ArtKeys.cs:25 | yes | legacy v2 (no `style`): see Findings |
| characters | `characters/surveyor/mk2` | Runtime/Art/ArtKeys.cs:25 | yes | legacy v2 (no `style`): see Findings |
| characters | `characters/surveyor/mk3` | Runtime/Art/ArtKeys.cs:25 | yes | legacy v2 (no `style`): see Findings |
| characters | `characters/surveyor/side` | Runtime/View2D/CartoonStage.cs:24 | yes | OK |
| characters | `characters/surveyor/side_b` | Runtime/Art/ArtKeys.cs:21 | yes | OK |
| decor | `terrain/earth/fill_decor_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_3` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_4` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_sand_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_sand_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_sand_3` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_sand_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/earth/fill_decor_t2_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_t2_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_t2_3` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_t2_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/earth/fill_decor_t3_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_t3_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_t3_3` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_t3_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/earth/fill_decor_t4_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_t4_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_t4_3` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_t4_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/earth/fill_decor_t5_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_t5_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/earth/fill_decor_t5_3` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/earth/fill_decor_t5_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/mars/fill_decor_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mars/fill_decor_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mars/fill_decor_3` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mars/fill_decor_4` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mars/fill_decor_basalt_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mars/fill_decor_basalt_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mars/fill_decor_basalt_3` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mars/fill_decor_basalt_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/mars/fill_decor_t2_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mars/fill_decor_t2_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mars/fill_decor_t2_3` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mars/fill_decor_t2_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/mars/fill_decor_t3_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mars/fill_decor_t3_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mars/fill_decor_t3_3` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mars/fill_decor_t3_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/mars/fill_decor_t4_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mars/fill_decor_t4_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mars/fill_decor_t4_3` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/mars/fill_decor_t4_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/mars/fill_decor_t5_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mars/fill_decor_t5_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mars/fill_decor_t5_3` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/mars/fill_decor_t5_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/mercury/fill_decor_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mercury/fill_decor_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mercury/fill_decor_3` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mercury/fill_decor_4` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mercury/fill_decor_t2_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mercury/fill_decor_t2_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mercury/fill_decor_t2_3` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/mercury/fill_decor_t2_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/mercury/fill_decor_t3_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mercury/fill_decor_t3_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mercury/fill_decor_t3_3` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/mercury/fill_decor_t3_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/mercury/fill_decor_t4_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mercury/fill_decor_t4_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mercury/fill_decor_t4_3` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/mercury/fill_decor_t4_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/mercury/fill_decor_t5_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mercury/fill_decor_t5_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/mercury/fill_decor_t5_3` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/mercury/fill_decor_t5_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/venus/fill_decor_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/venus/fill_decor_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/venus/fill_decor_3` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/venus/fill_decor_4` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/venus/fill_decor_t2_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/venus/fill_decor_t2_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/venus/fill_decor_t2_3` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/venus/fill_decor_t2_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/venus/fill_decor_t3_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/venus/fill_decor_t3_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/venus/fill_decor_t3_3` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/venus/fill_decor_t3_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/venus/fill_decor_t4_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/venus/fill_decor_t4_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/venus/fill_decor_t4_3` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/venus/fill_decor_t4_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/venus/fill_decor_t5_1` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/venus/fill_decor_t5_2` | Runtime/View2D/SmoothGround.cs:153 | yes | OK |
| decor | `terrain/venus/fill_decor_t5_3` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| decor | `terrain/venus/fill_decor_t5_4` | Runtime/View2D/SmoothGround.cs:153 | probe, empty by design |  |
| finds | `props/earth/data_cache` | Runtime/Mining/ResourceFinds.cs:58 | yes | OK |
| finds | `props/earth/vault_door` | Runtime/Mining/ResourceFinds.cs:65 | yes | OK |
| finds | `props/mars/lander_beacon` | Runtime/Mining/ResourceFinds.cs:59 | yes | OK |
| finds | `props/mercury/sunshade_probe` | Runtime/Mining/ResourceFinds.cs:60 | yes | OK |
| finds | `props/venus/pressure_capsule` | Runtime/Mining/ResourceFinds.cs:61 | yes | OK |
| fx | `fx/beam_ray/base` | Runtime/Player/RigToolView.cs:66 | yes | legacy v2 (no `style`): see Findings |
| fx | `fx/builder_ghost/base` | Runtime/Player/RigToolView.cs:67 | yes | legacy v2 (no `style`): see Findings |
| fx | `fx/dig_sparks/base` | Runtime/FX/SideFx.cs:24 | yes | legacy v2 (no `style`): see Findings |
| fx | `fx/dust/base` | Runtime/FX/SideFx.cs:25 | yes | legacy v2 (no `style`): see Findings |
| fx | `fx/survey_scan/base` | Runtime/Player/PlayerRigInput.cs:54 | yes | legacy v2 (no `style`): see Findings |
| hud | `ui/hud/escape_line` | Runtime/Ship/EscapeLineBand.cs:51 | yes | OK |
| hud | `ui/hud/escape_sign` | Runtime/Ship/EscapeLineBand.cs:68 | yes | OK |
| hud | `ui/hud/film_switch` | Runtime/UI/Settings/SettingsPanel.cs:80 | yes | OK |
| hud | `ui/hud/gauges` | Runtime/UI/SideHud.cs:389 | yes | OK |
| hud | `ui/panels/inventory` | Runtime/UI/CraftingPanel.cs:26 | yes | OK |
| hud | `ui/panels/pause` | Runtime/UI/MenuController.cs:265 | yes | OK |
| hud | `ui/panels/scroll` | Runtime/UI/CataloguePanel.cs:108 | yes | OK |
| hud | `ui/panels/settings` | Runtime/UI/Settings/SettingsPanel.cs:76 | yes | OK |
| hud | `ui/panels/sign` | Runtime/Art/ArtKeys.cs:51 | yes | OK |
| items | `icons/aluminium/base` | D1Tables.json / SkillTree.json item 'aluminium' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/carbon/base` | D1Tables.json / SkillTree.json item 'carbon' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/clay/base` | D1Tables.json / SkillTree.json item 'clay' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/copper/base` | D1Tables.json / SkillTree.json item 'copper' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/deep_core_sample/base` | D1Tables.json / SkillTree.json item 'deep_core_sample' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/deep_diamond/base` | D1Tables.json / SkillTree.json item 'deep_diamond' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/graphite/base` | D1Tables.json / SkillTree.json item 'graphite' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/helium3_condensate/base` | D1Tables.json / SkillTree.json item 'helium3_condensate' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/hematite/base` | D1Tables.json / SkillTree.json item 'hematite' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/iron/base` | D1Tables.json / SkillTree.json item 'iron' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/metallic_hydrogen/base` | D1Tables.json / SkillTree.json item 'metallic_hydrogen' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/nickel/base` | D1Tables.json / SkillTree.json item 'nickel' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/perchlorate/base` | D1Tables.json / SkillTree.json item 'perchlorate' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/phosphorus_pigment/base` | D1Tables.json / SkillTree.json item 'phosphorus_pigment' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/polar_ice/base` | D1Tables.json / SkillTree.json item 'polar_ice' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/silica/base` | D1Tables.json / SkillTree.json item 'silica' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/solarite/base` | D1Tables.json / SkillTree.json item 'solarite' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/sulfide/base` | D1Tables.json / SkillTree.json item 'sulfide' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/sulfur/base` | D1Tables.json / SkillTree.json item 'sulfur' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/superionic_ice/base` | D1Tables.json / SkillTree.json item 'superionic_ice' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/vitriol_glass/base` | D1Tables.json / SkillTree.json item 'vitriol_glass' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| items | `icons/water_ice/base` | D1Tables.json / SkillTree.json item 'water_ice' → ItemIcons (Runtime/Items/ItemRegistry.cs:66) | yes | OK |
| map | `ui/map/landed` | Runtime/Space/SpaceMap.cs:314 | yes | OK |
| map | `ui/map/minimap_chart` | Runtime/Space/SpaceMap.cs:304 | yes | OK |
| map | `ui/map/minimap_frame` | Runtime/Space/SpaceMap.cs:318 | yes | OK |
| map | `ui/map/name_tag` | Runtime/Space/SpaceMap.cs:275 | yes | OK |
| map | `ui/map/orbit_dot` | Runtime/Space/SpaceMap.cs:305 | yes | OK |
| map | `ui/map/planet_earth` | Runtime/Space/SpaceMap.cs:160 | yes | OK |
| map | `ui/map/planet_jupiter` | Runtime/Space/SpaceMap.cs:160 | yes | OK |
| map | `ui/map/planet_luna` | Runtime/Space/SpaceMap.cs:160 | yes | OK |
| map | `ui/map/planet_mars` | Runtime/Space/SpaceMap.cs:160 | yes | OK |
| map | `ui/map/planet_mercury` | Runtime/Space/SpaceMap.cs:160 | yes | OK |
| map | `ui/map/planet_neptune` | Runtime/Space/SpaceMap.cs:160 | yes | OK |
| map | `ui/map/planet_saturn` | Runtime/Space/SpaceMap.cs:160 | yes | OK |
| map | `ui/map/planet_uranus` | Runtime/Space/SpaceMap.cs:160 | yes | OK |
| map | `ui/map/planet_venus` | Runtime/Space/SpaceMap.cs:160 | yes | OK |
| map | `ui/map/rim_arrow` | Runtime/Space/SpaceMap.cs:322 | yes | OK |
| map | `ui/map/ship` | Runtime/Space/SpaceMap.cs:317 | yes | OK |
| map | `ui/map/station` | Runtime/Space/SpaceMap.cs:475 | yes | OK |
| map | `ui/map/sun` | Runtime/Space/SpaceMap.cs:160 | yes | OK |
| map | `ui/map/system_panel` | Runtime/Space/SpaceMap.cs:336 | yes | OK |
| map | `ui/map/title_cartouche` | Runtime/Space/SpaceMap.cs:337 | yes | OK |
| map | `ui/map/well_dash` | Runtime/Space/SpaceMap.cs:306 | yes | OK |
| terrain | `terrain/earth/dig_puff` | Runtime/FX/SideFx.cs:72 | yes | OK |
| terrain | `terrain/earth/dig_rim` | Runtime/View2D/SmoothGround.cs:396 | yes | OK |
| terrain | `terrain/earth/ground_band` | Runtime/View2D/SmoothGround.cs:391 | yes | OK |
| terrain | `terrain/earth/ground_band_sand` | Runtime/View2D/SmoothGround.cs:391 | yes | OK |
| terrain | `terrain/earth/ground_band_snow` | Runtime/View2D/SmoothGround.cs:391 | yes | OK |
| terrain | `terrain/earth/ground_band_stone` | Runtime/View2D/SmoothGround.cs:391 | yes | OK |
| terrain | `terrain/earth/ground_fill` | Runtime/View2D/SmoothGround.cs:393 | yes | OK |
| terrain | `terrain/earth/ground_fill_sand` | Runtime/View2D/SmoothGround.cs:395 | yes | OK |
| terrain | `terrain/earth/ground_fill_t2` | Runtime/View2D/SmoothGround.cs:401 | yes | OK |
| terrain | `terrain/earth/ground_fill_t3` | Runtime/View2D/SmoothGround.cs:401 | yes | OK |
| terrain | `terrain/earth/ground_fill_t4` | Runtime/View2D/SmoothGround.cs:401 | yes | OK |
| terrain | `terrain/earth/ground_fill_t5` | Runtime/View2D/SmoothGround.cs:401 | yes | OK |
| terrain | `terrain/earth/surface_line` | Runtime/View2D/SurfaceLineView.cs:40 | yes | OK |
| terrain | `terrain/mars/dig_puff` | Runtime/FX/SideFx.cs:72 | yes | OK |
| terrain | `terrain/mars/dig_rim` | Runtime/View2D/SmoothGround.cs:396 | yes | OK |
| terrain | `terrain/mars/ground_band` | Runtime/View2D/SmoothGround.cs:391 | yes | OK |
| terrain | `terrain/mars/ground_band_basalt` | Runtime/View2D/SmoothGround.cs:391 | yes | OK |
| terrain | `terrain/mars/ground_band_frost` | Runtime/View2D/SmoothGround.cs:391 | yes | OK |
| terrain | `terrain/mars/ground_band_talus` | Runtime/View2D/SmoothGround.cs:391 | yes | OK |
| terrain | `terrain/mars/ground_fill` | Runtime/View2D/SmoothGround.cs:393 | yes | OK |
| terrain | `terrain/mars/ground_fill_basalt` | Runtime/View2D/SmoothGround.cs:395 | yes | OK |
| terrain | `terrain/mars/ground_fill_t2` | Runtime/View2D/SmoothGround.cs:401 | yes | OK |
| terrain | `terrain/mars/ground_fill_t3` | Runtime/View2D/SmoothGround.cs:401 | yes | OK |
| terrain | `terrain/mars/ground_fill_t4` | Runtime/View2D/SmoothGround.cs:401 | yes | OK |
| terrain | `terrain/mars/ground_fill_t5` | Runtime/View2D/SmoothGround.cs:401 | yes | OK |
| terrain | `terrain/mars/surface_line` | Runtime/View2D/SurfaceLineView.cs:40 | yes | OK |
| terrain | `terrain/mercury/dig_puff` | Runtime/FX/SideFx.cs:72 | yes | OK |
| terrain | `terrain/mercury/dig_rim` | Runtime/View2D/SmoothGround.cs:396 | yes | OK |
| terrain | `terrain/mercury/ground_band` | Runtime/View2D/SmoothGround.cs:391 | yes | OK |
| terrain | `terrain/mercury/ground_band_ice` | Runtime/View2D/SmoothGround.cs:391 | yes | OK |
| terrain | `terrain/mercury/ground_fill` | Runtime/View2D/SmoothGround.cs:393 | yes | OK |
| terrain | `terrain/mercury/ground_fill_t2` | Runtime/View2D/SmoothGround.cs:401 | yes | OK |
| terrain | `terrain/mercury/ground_fill_t3` | Runtime/View2D/SmoothGround.cs:401 | yes | OK |
| terrain | `terrain/mercury/ground_fill_t4` | Runtime/View2D/SmoothGround.cs:401 | yes | OK |
| terrain | `terrain/mercury/ground_fill_t5` | Runtime/View2D/SmoothGround.cs:401 | yes | OK |
| terrain | `terrain/mercury/surface_line` | Runtime/View2D/SurfaceLineView.cs:40 | yes | OK |
| terrain | `terrain/venus/dig_puff` | Runtime/FX/SideFx.cs:72 | yes | OK |
| terrain | `terrain/venus/dig_rim` | Runtime/View2D/SmoothGround.cs:396 | yes | OK |
| terrain | `terrain/venus/ground_band` | Runtime/View2D/SmoothGround.cs:391 | yes | OK |
| terrain | `terrain/venus/ground_band_tessera` | Runtime/View2D/SmoothGround.cs:391 | yes | OK |
| terrain | `terrain/venus/ground_band_vent` | Runtime/View2D/SmoothGround.cs:391 | yes | OK |
| terrain | `terrain/venus/ground_fill` | Runtime/View2D/SmoothGround.cs:393 | yes | OK |
| terrain | `terrain/venus/ground_fill_t2` | Runtime/View2D/SmoothGround.cs:401 | yes | OK |
| terrain | `terrain/venus/ground_fill_t3` | Runtime/View2D/SmoothGround.cs:401 | yes | OK |
| terrain | `terrain/venus/ground_fill_t4` | Runtime/View2D/SmoothGround.cs:401 | yes | OK |
| terrain | `terrain/venus/ground_fill_t5` | Runtime/View2D/SmoothGround.cs:401 | yes | OK |
| terrain | `terrain/venus/surface_line` | Runtime/View2D/SurfaceLineView.cs:40 | yes | OK |
| terrain (strip / tile path) | `terrain/earth/backwall` | Runtime/Terrain/TerrainBlockPalette.cs:97 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/earth/grass` | Runtime/Art/ArtKeys.cs:61 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/earth/ground_strip` | Runtime/View2D/GroundStrip.cs:19 | yes | OK |
| terrain (strip / tile path) | `terrain/earth/sand` | Runtime/Art/ArtKeys.cs:63 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/earth/snow` | Runtime/Art/ArtKeys.cs:64 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/earth/soil` | Runtime/Art/ArtKeys.cs:60 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/earth/stone` | Runtime/Art/ArtKeys.cs:62 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/earth/water` | Runtime/Art/ArtKeys.cs:65 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/mars/backwall` | Runtime/Terrain/TerrainBlockPalette.cs:97 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/mars/basalt` | Runtime/Art/ArtKeys.cs:67 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/mars/ground_strip` | Runtime/View2D/GroundStrip.cs:24 | yes | OK |
| terrain (strip / tile path) | `terrain/mars/ground_strip_basalt` | Runtime/View2D/GroundStrip.cs:24 | yes | OK |
| terrain (strip / tile path) | `terrain/mars/ground_strip_frost` | Runtime/View2D/GroundStrip.cs:24 | yes | OK |
| terrain (strip / tile path) | `terrain/mars/hematite` | Runtime/Art/ArtKeys.cs:68 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/mars/ice` | Runtime/Art/ArtKeys.cs:69 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/mars/regolith` | Runtime/Art/ArtKeys.cs:66 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/mercury/backwall` | Runtime/Terrain/TerrainBlockPalette.cs:97 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/mercury/basalt` | Runtime/Art/ArtKeys.cs:71 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/mercury/ground_strip` | Runtime/View2D/GroundStrip.cs:28 | yes | OK |
| terrain (strip / tile path) | `terrain/mercury/ground_strip_slate` | Runtime/View2D/GroundStrip.cs:28 | yes | OK |
| terrain (strip / tile path) | `terrain/mercury/ice` | Runtime/Art/ArtKeys.cs:73 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/mercury/regolith` | Runtime/Art/ArtKeys.cs:70 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/mercury/sulfide` | Runtime/Art/ArtKeys.cs:72 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/venus/backwall` | Runtime/Terrain/TerrainBlockPalette.cs:97 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/venus/basalt` | Runtime/Art/ArtKeys.cs:74 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/venus/ground_strip` | Runtime/View2D/GroundStrip.cs:96 | yes | OK |
| terrain (strip / tile path) | `terrain/venus/ground_strip_deck` | Runtime/View2D/GroundStrip.cs:96 | yes | OK |
| terrain (strip / tile path) | `terrain/venus/sulfur` | Runtime/Art/ArtKeys.cs:75 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/venus/tessera` | Runtime/Art/ArtKeys.cs:76 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| terrain (strip / tile path) | `terrain/venus/vent_glass` | Runtime/Art/ArtKeys.cs:77 | yes | tile sheet: routed by path (ArtRules.cs:43), no json by design |
| tools | `props/rig/beam` | Runtime/Rig/RigModule.cs:19 | yes | OK |
| tools | `props/rig/builder` | Runtime/Rig/RigModule.cs:22 | yes | **no json** (legacy v2 colour / normal / emission): see Findings |
| tools | `props/rig/grapple` | Runtime/Rig/RigModule.cs:20 | yes | OK |
| tools | `props/rig/survey` | Runtime/Rig/RigModule.cs:21 | yes | **no json** (legacy v2 colour / normal / emission): see Findings |
| tree | `icons/nodes/asc_climb_1` | SkillTree.json node 'asc_climb_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/asc_grapple_1` | SkillTree.json node 'asc_grapple_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/asc_grapple_2` | SkillTree.json node 'asc_grapple_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/asc_grapple_3` | SkillTree.json node 'asc_grapple_3' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/asc_jet_1` | SkillTree.json node 'asc_jet_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/asc_jet_2` | SkillTree.json node 'asc_jet_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/asc_jet_3` | SkillTree.json node 'asc_jet_3' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/asc_ladder_1` | SkillTree.json node 'asc_ladder_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/asc_ladder_2` | SkillTree.json node 'asc_ladder_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/asc_recall` | SkillTree.json node 'asc_recall' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/asc_winch` | SkillTree.json node 'asc_winch' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/dig_brush_1` | SkillTree.json node 'dig_brush_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/dig_brush_2` | SkillTree.json node 'dig_brush_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/dig_core_bit` | SkillTree.json node 'dig_core_bit' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/dig_heatsink` | SkillTree.json node 'dig_heatsink' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/dig_power_1` | SkillTree.json node 'dig_power_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/dig_power_2` | SkillTree.json node 'dig_power_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/dig_power_3` | SkillTree.json node 'dig_power_3' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/dig_power_4` | SkillTree.json node 'dig_power_4' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/dig_power_5` | SkillTree.json node 'dig_power_5' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/dig_rhythm_1` | SkillTree.json node 'dig_rhythm_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/dig_rhythm_2` | SkillTree.json node 'dig_rhythm_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/end_air_1` | SkillTree.json node 'end_air_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/end_air_2` | SkillTree.json node 'end_air_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/end_air_3` | SkillTree.json node 'end_air_3' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/end_air_4` | SkillTree.json node 'end_air_4' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/end_deep_1` | SkillTree.json node 'end_deep_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/end_deep_2` | SkillTree.json node 'end_deep_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/end_fall_1` | SkillTree.json node 'end_fall_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/end_fall_2` | SkillTree.json node 'end_fall_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/end_heat_1` | SkillTree.json node 'end_heat_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/end_heat_2` | SkillTree.json node 'end_heat_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/end_suit_mk3` | SkillTree.json node 'end_suit_mk3' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/haul_compact` | SkillTree.json node 'haul_compact' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/haul_dirt_1` | SkillTree.json node 'haul_dirt_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/haul_light_1` | SkillTree.json node 'haul_light_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/haul_light_2` | SkillTree.json node 'haul_light_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/haul_magnet_1` | SkillTree.json node 'haul_magnet_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/haul_pack_1` | SkillTree.json node 'haul_pack_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/haul_pack_2` | SkillTree.json node 'haul_pack_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/haul_pack_3` | SkillTree.json node 'haul_pack_3' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/haul_pack_4` | SkillTree.json node 'haul_pack_4' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/haul_pack_5` | SkillTree.json node 'haul_pack_5' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/haul_sorter` | SkillTree.json node 'haul_sorter' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/sur_cartographer` | SkillTree.json node 'sur_cartographer' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/sur_deep_eye` | SkillTree.json node 'sur_deep_eye' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/sur_depth_1` | SkillTree.json node 'sur_depth_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/sur_preview_1` | SkillTree.json node 'sur_preview_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/sur_preview_2` | SkillTree.json node 'sur_preview_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/sur_rare` | SkillTree.json node 'sur_rare' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/sur_scan_1` | SkillTree.json node 'sur_scan_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/sur_scan_2` | SkillTree.json node 'sur_scan_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/sur_scan_3` | SkillTree.json node 'sur_scan_3' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/sur_scan_4` | SkillTree.json node 'sur_scan_4' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/sur_vault` | SkillTree.json node 'sur_vault' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/voy_dray` | SkillTree.json node 'voy_dray' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/voy_hold_1` | SkillTree.json node 'voy_hold_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/voy_hold_2` | SkillTree.json node 'voy_hold_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/voy_price_1` | SkillTree.json node 'voy_price_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/voy_price_2` | SkillTree.json node 'voy_price_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/voy_price_3` | SkillTree.json node 'voy_price_3' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/voy_skip_1` | SkillTree.json node 'voy_skip_1' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/voy_skip_2` | SkillTree.json node 'voy_skip_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/voy_thrust_2` | SkillTree.json node 'voy_thrust_2' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/voy_thrust_3` | SkillTree.json node 'voy_thrust_3' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `icons/nodes/voy_trader` | SkillTree.json node 'voy_trader' → Runtime/UI/SkillTreePanel.cs:272 | yes | OK |
| tree | `ui/skilltree/chart` | Runtime/UI/SkillTreePanel.cs:269 | yes | OK |
| tree | `ui/skilltree/cost_tag` | Runtime/UI/SkillTreePanel.cs:217 | yes | OK |
| tree | `ui/skilltree/emblem_ascent` | Runtime/UI/SkillTreePanel.cs:181 | yes | OK |
| tree | `ui/skilltree/emblem_dig` | Runtime/UI/SkillTreePanel.cs:181 | yes | OK |
| tree | `ui/skilltree/emblem_endurance` | Runtime/UI/SkillTreePanel.cs:181 | yes | OK |
| tree | `ui/skilltree/emblem_haul` | Runtime/UI/SkillTreePanel.cs:181 | yes | OK |
| tree | `ui/skilltree/emblem_survey` | Runtime/UI/SkillTreePanel.cs:181 | yes | OK |
| tree | `ui/skilltree/emblem_voyage` | Runtime/UI/SkillTreePanel.cs:181 | yes | OK |
| tree | `ui/skilltree/hub` | Runtime/UI/SkillTreePanel.cs:269 | yes | OK |
| tree | `ui/skilltree/link_bought` | Runtime/UI/SkillTreePanel.cs:269 | yes | OK |
| tree | `ui/skilltree/link_locked` | Runtime/UI/SkillTreePanel.cs:269 | yes | OK |
| tree | `ui/skilltree/link_open` | Runtime/UI/SkillTreePanel.cs:269 | yes | OK |
| tree | `ui/skilltree/node_available` | Runtime/UI/SkillTreePanel.cs:269 | yes | OK |
| tree | `ui/skilltree/node_bought` | Runtime/UI/SkillTreePanel.cs:269 | yes | OK |
| tree | `ui/skilltree/node_cap_available` | Runtime/UI/SkillTreePanel.cs:269 | yes | OK |
| tree | `ui/skilltree/node_cap_bought` | Runtime/UI/SkillTreePanel.cs:269 | yes | OK |
| tree | `ui/skilltree/node_cap_locked` | Runtime/UI/SkillTreePanel.cs:269 | yes | OK |
| tree | `ui/skilltree/node_locked` | Runtime/UI/SkillTreePanel.cs:269 | yes | OK |
| tree | `ui/skilltree/select` | Runtime/UI/SkillTreePanel.cs:269 | yes | OK |

### Present in the D1 folders, requested by nothing

| Folder | Keys | Count |
|---|---|---|
| `ui/hud/` | depth_marker, gauge_pack, pack_full, rank_slot, scrip_tag | 5 |
| `ui/hints/` | arrow, climb_up, dig_down, pack_full, sell, skill_tree, surface_line | 7 |
| `ui/rank/` | certificate, expedition_badge, expedition_badge_laurel, insignia_10, insignia_1, insignia_2, insignia_3, insignia_4, insignia_5, insignia_6, insignia_7, insignia_8, insignia_9 | 13 |
| `ui/skilltree/` | panel | 1 |
| `ui/panels/` | grain | 1 |
| `fx/rare/` | pocket_pop, sparkle_t2, sparkle_t3, sparkle_t4, sparkle_t5 | 5 |
| `fx/ui/` | expedition_seal, node_bought, rank_up, scrip_shower | 4 |
| `fx/beam_ray/` | mk1, mk2, mk3, mk4, mk5 | 5 |
| `props/rig/` | beam_mk1, beam_mk2, beam_mk3, beam_mk4, beam_mk5, grapple_mk1, grapple_mk2, grapple_mk3, jetpack_mk2, jetpack_mk3 | 10 |
| `props/dig/` | grapple_hook, grapple_line, ladder_bottom, ladder, ladder_top, recall_beacon, winch_post | 7 |
| `terrain/earth/` | dig_puff_sand, dig_puff_snow, dig_puff_stone, ground_decor_1, ground_decor_2, ground_decor_3, ground_decor_4, ground_decor_5, ground_decor_6, ground_decor_sand_1, ground_decor_sand_2, ground_decor_sand_3, ground_decor_snow_1, ground_decor_snow_2, ground_decor_snow_3, ground_decor_stone_1, ground_decor_stone_2, ground_decor_stone_3, ground_lip, ground_lip_sand, ground_lip_snow, ground_lip_stone, ground_strip_sand, ground_strip_soil, ground_strip_stone | 25 |
| `terrain/mars/` | dig_puff_basalt, dig_puff_frost, ground_decor_1, ground_decor_2, ground_decor_3, ground_decor_4, ground_decor_5, ground_decor_6, ground_decor_basalt_1, ground_decor_basalt_2, ground_decor_basalt_3, ground_decor_frost_1, ground_decor_frost_2, ground_decor_frost_3, ground_decor_talus_1, ground_decor_talus_2, ground_decor_talus_3, ground_lip_basalt, ground_lip, ground_lip_frost, ground_lip_talus | 21 |
| `terrain/mercury/` | dig_puff_ice, ground_decor_1, ground_decor_2, ground_decor_3, ground_decor_4, ground_decor_5, ground_decor_6, ground_decor_ice_1, ground_decor_ice_2, ground_decor_ice_3, ground_lip, ground_lip_ice | 12 |
| `terrain/venus/` | dig_puff_tessera, dig_puff_vent, ground_decor_1, ground_decor_2, ground_decor_3, ground_decor_4, ground_decor_5, ground_decor_6, ground_decor_tessera_1, ground_decor_tessera_2, ground_decor_tessera_3, ground_decor_vent_1, ground_decor_vent_2, ground_decor_vent_3, ground_lip, ground_lip_tessera, ground_lip_vent | 17 |
