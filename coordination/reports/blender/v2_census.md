# B-193: the v2 model census (every .glb under Assets/_Game/Art/)

BLENDER, 2026-11-08 14:1x (reassigned from UNITY's U-152; files only, no Blender). 80 .glb files, each with its own v2 sidecar json (`"format": "glb"`, contract v2.2), so no key carries both a model and a v3 sheet under one name.

## How it was read

- **Code**: every key string, and every composed key, under `Assets/_Game/Code/Runtime` and `Code/Editor`: ArtKeys.cs, DepthBands / StageLayers, PoiCatalog / PoiPlacer, CreatureSpecies / Creature, Sentinel / WardenDirector, SpaceWorld, Waystation / DockingBay, PlayerView, ShipLegsView, Residency / ArtLoad.
- **Addressables**: every .glb is addressed under its own key in its planet or region group. ArtImporter.Models.cs:98 / 116-121 does this; 262 entries across 27 groups in AssetGroups/*.asset (glb + generated .mat + placeholder). Being addressed is not being loaded. The only label-wide loader is `ArtLoad.Assets` at StageLayers.cs:164, on the 3D path only.
- **Residency / prefetch**: Residency.cs tracks handles by group (ArtKeys.GroupOf). It has no prefetch list of model keys; TerrainTileSet.Prefetch covers terrain sheets only.
- **Which path runs**: `CartoonStage.Enabled = true` (CartoonStage.cs:18), and `Converted()` is true for all eight planets (CartoonStage.cs:20). PlanetSideRoot.cs:124-146 skips the 3D backdrop, DepthBands and StageLayers on the cartoon path. Nothing in Runtime sets Enabled false; tests do (BackdropTests.cs:18, StageLayerTests.cs:24, SceneCapture's U-076 evidence).
- **The model-key rule** that matters for B-174: while `<key>.glb` exists, the key is a model key. Its colour map is un-addressed and the key's 2D loaders get its placeholder (ArtImporter.cs:106-116, 833-845). A folder holding any .glb treats its `atlas_*` maps as model maps.

## Summary

| Verdict | Count | Keys |
|---|---|---|
| loaded, the player sees it | 13 | asteroids x6, waystations x2, Earth POI props x5 |
| loaded (unsure): LEAD to rule | 5 | characters/surveyor/base, ships/pilgrim/base, planets/saturn/ring_mesh, creatures/warden/sentinel, characters/calibration/base |
| 3D path only (tests switch it on; no player sees it) | 37 | ridge_mid x15, skyline_far x5, earth_flora x11, mars_flora x6 |
| orphaned (no code, no test) | 25 | mercury_scenery x8, venus_scenery x6, mars_flora ice / stalactite / stalagmite x4, solarite_crusted / _cut, warden/hunter, mercury/cinderhulk, veil_serpent_head / _body / _tail |

## The table

### Loaded: the player sees a v2 3D model (13)

| Key | Loaded by | What a player sees |
|---|---|---|
| props/space/asteroid_01 .. asteroid_06 (6) | SpaceWorld.cs:503-505 (`LoadBeltArt`, always called at SpaceWorld.cs:660) | The Space map's belt: 3D rocks instanced over the belt, space-lit. Tests: SpaceArtTests.cs:108, ArtImporterTests.cs:592 |
| props/space/waystation | Waystation.cs:30 / 56-66, created at DockingBay.cs:47 (`Market.Stations`) | Earth's orbital waystation in Space, a 3D model |
| props/space/waystation_mars | as above (Waystation.cs:30) | Mars's waystation in Space |
| props/earth/archive_door | PoiCatalog.cs:83 → PoiPlacer.cs:94 (`ModelSwap.Attach`); PoiPlacer runs on every path (PlanetSideRoot.cs:97-99) | The Survey Archive POI (Earth x 184): a v2 3D door over the 2D world. No v3 sheet exists for the key |
| props/earth/archive_terminal | PoiCatalog.cs:84 → PoiPlacer.cs:94 | Survey Archive: a 3D terminal |
| props/earth/beacon | PoiCatalog.cs:85 → PoiPlacer.cs:94 | Survey Archive: a 3D beacon |
| props/earth/launch_gantry | PoiCatalog.cs:109 → PoiPlacer.cs:94 | The Launch Complex POI (Earth x 2048): a 3D gantry |
| props/earth/launch_tower_ruin | PoiCatalog.cs:110 → PoiPlacer.cs:94 | Launch Complex: a 3D tower ruin |

### Loaded (unsure): LEAD to rule (5)

| Key | Loaded by | What a player sees / why unsure |
|---|---|---|
| characters/surveyor/base | PlayerView.cs:67 (`Model.Load` in `Start`); PlayerView.cs:55 also asks for the key as a sheet at tier 0 | The v3 `characters/surveyor/side` sheet (CartoonStage.cs:22 / 461-465). CartoonStage.cs:457-460 disables PlayerView and hides the player's renderers. Unsure: whether `Start` has already run, and so loaded the .glb, before that. Tests: ArtCompressionTests.cs:19, ArtImporterTests.cs:368, HazardV2PlayTests.cs:108, ModelViewPlayTests.cs:29 |
| ships/pilgrim/base | ShipLegsView.cs:83 (`ArtKeys.Ships.PilgrimModel`), only in `LoadLegacy` (ShipLegsView.cs:70), which runs when `ships/pilgrim/rig/json` is missing | The drawn Pilgrim rig (ships/pilgrim/rig exists, so the legacy path never runs). A fallback only |
| planets/saturn/ring_mesh | SpaceWorld.cs:437 (`AddRings`, SpaceWorld.cs:146) | The painted rings (planets/saturn/disc + rings_back / rings_front). SpaceWorld.cs:439 throws the mesh away once Saturn is a disc body (SpaceWorld.cs:233). A load that is discarded or hidden; nothing shows |
| creatures/warden/sentinel | Sentinel.cs:19 / 44-45 (`FxSheet.Get(ArtKey)`, the key as a sprite sheet); the .glb is never instantiated | The Warden sentinel's 2D placeholder: the .glb makes this a model key, so its 1024² colour map is un-addressed (ArtImporter.cs:833-845). Caution: deleting only the .glb would let that v2 model map import as one 1024² sprite. The wardens need a v3 sheet (a BLENDER card?) before or with any removal |
| characters/calibration/base | Editor only: GlbCalibrationCheck.cs:16 (an import calibration check) and ModelImportTests.cs:22 | Nothing in play; an editor / test fixture |

### 3D path only: reached only when a test sets `CartoonStage.Enabled = false` (37)

No player sees these: all eight planets run the cartoon path, and PlanetSideRoot.cs:124-146 never configures DepthBands or StageLayers there.

| Key | Loaded by (3D path) | Tests that name it |
|---|---|---|
| backgrounds/earth_plains/ridge_mid | DepthBands.cs:88 (`RidgeFor`) | none by key |
| backgrounds/earth_desert/ridge_mid | DepthBands.cs:89 | DepthBandsTests.cs:16 |
| backgrounds/earth_coast/ridge_mid | DepthBands.cs:90 | DepthBandsTests.cs:15 |
| backgrounds/earth_taiga/ridge_mid | DepthBands.cs:91 | none by key |
| backgrounds/earth_tundra/ridge_mid | DepthBands.cs:92 | none by key |
| backgrounds/earth_forest/ridge_mid | DepthBands.cs:93 | DepthBandsTests.cs:14, ArtImporterTests.cs:531 / 540, ResidencyMappingTests.cs:58, U076SceneTests.cs:110 |
| backgrounds/mars_plains/ridge_mid | DepthBands.cs:84 | DepthBandsTests.cs:17 |
| backgrounds/earth/skyline_far | DepthBands.cs:98 (`SkylineFor`) | DepthBandsTests.cs:19 |
| backgrounds/mars/skyline_far | DepthBands.cs:98 | DepthBandsTests.cs:20 |
| backgrounds/mars_tharsis/skyline_far | StageLayers.cs:140 (`backgrounds/{region}/skyline_far`) | none by key |
| backgrounds/{mars_canyon, mars_polar, mars_tharsis, mercury_day, mercury_twilight, mercury_night, venus_deck, venus_surface}/ridge_mid (8) | no code names them. (unsure) The StageLayers region set: ArtImporter labels each region's entries (ArtImporter.cs:1020-1029), and StageLayers.cs:164 loads the label's assets | none by key |
| backgrounds/mercury/skyline_far, backgrounds/venus/skyline_far (2) | no code names them. DepthBands.SkylineFor covers Earth and Mars only. (unsure) StageLayers.cs:140 if a region resolves to the planet | none by key |
| props/earth_flora/{tree_oak, tree_birch, bush_a, bush_b, rock_a, rock_b, rock_c, grass, cactus, dead_tree, tree_spruce} (11) | DepthBands.cs:111-116 (the 3D path's flora tables) | ArtImporterTests.cs:535 (tree_oak) |
| props/mars_flora/{boulder_a, boulder_b, boulder_c, rock_a, rock_b, dust_bush} (6) | DepthBands.cs:117 | ResidencyMappingTests.cs:56 names `mars_flora/cactus` (no such model: a group-mapping string only) |

The cartoon path draws its own flora from the v3 rig sets (`flora/<planet>/rigset`, CartoonStage's Flora). These .glb flora are the 3D path's.

### Orphaned: no code loads them and no test names them (25)

| Key | Notes |
|---|---|
| props/mercury_scenery/{boulder_a, boulder_b, boulder_c, glass_shard_a, glass_shard_b, solarite_outcrop, rim_rock, ice_pocket} (8) | No key, composed key or label anywhere in Code. The folder's shared atlas_* maps (4) go with them |
| props/venus_scenery/{column_a, column_b, tessera_slab, sulfur_crust, vent_chimney, lava_blister} (6) | Same; the folder's atlas_* maps (4) go with them |
| props/mars_flora/{ice_a, ice_b, stalactite, stalagmite} (4) | Not in DepthBands' Mars table (DepthBands.cs:117) or anywhere else. The folder's atlas stays while boulder / rock / dust_bush remain |
| props/mercury/solarite_crusted, props/mercury/solarite_cut (2) | SolariteCrystals and the Solarite POI use `props/mercury/solarite_cluster` (a v3 sheet, PoiCatalog.cs:248-249) |
| creatures/warden/hunter | WardenDirector spawns Sentinels only (`SentinelState.Hunt` is a state of the sentinel, Sentinel.cs:19); no key names hunter |
| creatures/mercury/cinderhulk | The species uses the v3 `cinderhulk_day` / `cinderhulk_night` (CreatureSpecies.cs:138) |
| creatures/venus/veil_serpent_head, _body, _tail (3) | The species uses the v3 `creatures/venus/veil_serpent` (CreatureSpecies.cs:155); no code composes the part keys |

## For B-174 (the removal, after LEAD's rulings)

1. Per orphaned key, remove `<key>.glb`, `<key>.json` and the key's own maps (`<key>_color / _normal / _mask / _emission.png` where they exist). Never a .meta: UNITY deletes those (D-016).
2. A shared `atlas_*` set goes only when its folder has no .glb left (mercury_scenery, venus_scenery). With one .glb left, the atlas is still a model map; with none, ArtImporter would import the atlas as a sprite sheet.
3. creatures/warden/sentinel must not lose only its .glb (its 1024² v2 map would become a sprite). It needs a v3 sheet first, or the .glb and its maps go together and the sentinel stays on its placeholder.
4. The 37 3D-path models stay as long as UNITY keeps the 3D-path tests (DepthBandsTests, BackdropTests, StageLayerTests, U076SceneTests, the ArtImporter / Residency mapping tests). Retiring them belongs with retiring the 3D path; that's LEAD's / UNITY's call.
5. Each removal leaves dangling Addressables entries (glb + generated .mat + placeholder). That's UNITY's import step, as for B-131's v2 prop removals.
