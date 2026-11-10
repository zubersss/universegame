# UNITY performance report 2026-11-10 11:51

BudgetGate v3 (U-014; U-086 with the D-077 limits): `BudgetGateTests.EarthSpaceMarsStayWithinBudgets`. Graphics: Intel(R) UHD Graphics. Memory rows read the Editor process, an upper bound for the built game.
- Load during measurement (D-019/D-083): none; free RAM at start 2229 MB (in-Editor now 321 MB); Unity Editor processes 2
- Machine memory (LEAD 2026-11-09): at the start free 2.18 GB, compression store 430 MB, largest private: claude 916 MB, claude 831 MB, claude 762 MB, MsMpEng 420 MB; up 24.1 h, 4.4 min since the last Unity job's log; at the end free 2.76 GB, compression store 1290 MB, largest private: claude 1013 MB, claude 807 MB, claude 766 MB, MsMpEng 416 MB; up 24.1 h, 0 min since the last Unity job's log
- GC rows: Unity's 'GC Allocated In Frame'; the control (a 65536 B array) read 65858 B; the Editor's and the test runner's own floor 88247 B per 300 frames (294 B a frame), read with every root object inactive

| Budget (Bible §11.1) | Limit | Measured | Result |
|---|---|---|---|
| Boot settle · Earth | the first 2 s after boot: max frame ≤ 50 ms (gates); p99 ≤ 25 ms (recorded in 0.5.1, gates from U-179) (D-177) | 314 frames: max 16.8 ms, p99 14.9 ms (rendered 1920×1080) | green |
| First visible frame · Earth | ≤ 50 ms (U-028) | 3.3 ms (warm-up 116 ms at load) | green |
| Frame time · Earth | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 5.51 ms, p99 15.09 ms, max 18.4 ms (rendered 1920×1080) | green |
| Draw calls · Earth | ≤ 250 | 112 | green |
| Geometry · Earth | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 3.3 k triangles, 0 shadow casters | green |
| 2D lights visible · Earth | ≤ 8 (hard cap 12) | 2 | green |
| Particles alive · Earth | ≤ 1500 (v3) | 0 | green |
| GC per 300 frames, settled · Earth | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | -777 B of the game's own (87470 B in the window of 300 frames, the floor 88247 B) | green |
| GC in the first 300 frames after the scene is ready · Earth | reported (U-211; LEAD sets the limit): the game's own bytes in the first window after the scene is ready, before the settled one | -647 B of the game's own (87600 B in the window of 300 frames, the floor 88247 B) | info (U-211: no limit yet) |
| Memory · Earth (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 865 MB, system 865 MB, textures 520 MB, meshes 1 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| Chunk generation · Earth streaming 200 m | ≤ 2 ms main thread in ≥ 99% of frames; no hitch > 33 ms (D-019) | p99 1.88 ms, 2/400 over 2 ms, worst frame 10.5 ms | green |
| Transition · launch (side → top-down) | ≤ 1.5 s | 0.90 s | green |
| First visible frame · Space | ≤ 50 ms (U-028) | 7.1 ms (warm-up at boot) | green |
| Frame time · Space | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 2.59 ms, p99 8.30 ms, max 9.5 ms (rendered 1920×1080) | green |
| Draw calls · Space | ≤ 80 | 11 | green |
| Geometry · Space | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 16.6 k triangles, 0 shadow casters | green |
| 2D lights visible · Space | ≤ 8 (hard cap 12) | 1 | green |
| Particles alive · Space | ≤ 1500 (v3) | 0 | green |
| GC per 300 frames, settled · Space | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | -881 B of the game's own (87366 B in the window of 300 frames, the floor 88247 B) | green |
| GC in the first 300 frames after the scene is ready · Space | reported (U-211; LEAD sets the limit): the game's own bytes in the first window after the scene is ready, before the settled one | 525598 B of the game's own (613845 B in the window of 300 frames, the floor 88247 B) | info (U-211: no limit yet) |
| Memory · Space (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 839 MB, system 839 MB, textures 519 MB, meshes 3 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| Planet load · Mars entry | ≤ 5 s (v3) | 1.63 s (scene load 66 ms, configure 540 ms, tile sheets 335 ms, warm-up 47 ms, total 988 ms) | green |
| Transition · entry (top-down → side) | ≤ 1.5 s in the dev-build transition rows (D-136 (2): the Editor transition row is info, like the Editor memory rows) | 1.63 s (Editor) | info |
| Residency · after Mars entry | previous planet released within 5 s; only the current planet + common/ui/icons/space resident (v3) | planet_earth handles 0 after 0.0 s (holders: none); resident: common, icons, planet_dig, planet_mars, planet_space, planet_warden, planet_waystation, space, ui | green (pending U-091) |
| First visible frame · Mars | ≤ 50 ms (U-028) | 4.3 ms (warm-up 47 ms at load) | green |
| Frame time · Mars | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 3.60 ms, p99 6.42 ms, max 7.7 ms (rendered 1920×1080) | green |
| Draw calls · Mars | ≤ 250 | 14 | green |
| Geometry · Mars | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 0.4 k triangles, 0 shadow casters | green |
| 2D lights visible · Mars | ≤ 8 (hard cap 12) | 2 | green |
| Particles alive · Mars | ≤ 1500 (v3) | 1 | green |
| GC per 300 frames, settled · Mars | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | -1143 B of the game's own (87104 B in the window of 300 frames, the floor 88247 B) | green |
| GC in the first 300 frames after the scene is ready · Mars | reported (U-211; LEAD sets the limit): the game's own bytes in the first window after the scene is ready, before the settled one | 134248 B of the game's own (222495 B in the window of 300 frames, the floor 88247 B) | info (U-211: no limit yet) |
| Memory · Mars (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 861 MB, system 861 MB, textures 661 MB, meshes 4 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| First visible frame · Mars dust storm | ≤ 50 ms (U-028) | 4.9 ms (warm-up 47 ms at load) | green |
| Frame time · Mars dust storm | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 4.23 ms, p99 8.05 ms, max 19.8 ms (rendered 1920×1080) | green |
| Draw calls · Mars dust storm | ≤ 250 | 35 | green |
| Geometry · Mars dust storm | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 0.6 k triangles, 0 shadow casters | green |
| 2D lights visible · Mars dust storm | ≤ 8 (hard cap 12) | 2 | green |
| Particles alive · Mars dust storm | ≤ 1500 (v3) | 1 | green |
| GC per 300 frames, settled · Mars dust storm | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | -829 B of the game's own (87418 B in the window of 300 frames, the floor 88247 B) | green |
| GC in the first 300 frames after the scene is ready · Mars dust storm | reported (U-211; LEAD sets the limit): the game's own bytes in the first window after the scene is ready, before the settled one | 5825 B of the game's own (94072 B in the window of 300 frames, the floor 88247 B) | info (U-211: no limit yet) |
| Memory · Mars dust storm (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 863 MB, system 863 MB, textures 669 MB, meshes 4 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| First visible frame · Mars FX peak | ≤ 50 ms (U-028) | 2.3 ms (warm-up 47 ms at load) | green |
| Frame time · Mars FX peak | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 5.59 ms, p99 9.86 ms, max 11.1 ms (rendered 1920×1080) | green |
| Draw calls · Mars FX peak | ≤ 250 | 81 | green |
| Geometry · Mars FX peak | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 1.0 k triangles, 0 shadow casters | green |
| 2D lights visible · Mars FX peak | ≤ 8 (hard cap 12) | 2 | green |
| Particles alive · Mars FX peak | ≤ 1500 (v3) | 49 | green |
| GC per 300 frames, settled · Mars FX peak | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | -1143 B of the game's own (87104 B in the window of 300 frames, the floor 88247 B) | green |
| GC in the first 300 frames after the scene is ready · Mars FX peak | reported (U-211; LEAD sets the limit): the game's own bytes in the first window after the scene is ready, before the settled one | -43 B of the game's own (88204 B in the window of 300 frames, the floor 88247 B) | info (U-211: no limit yet) |
| Memory · Mars FX peak (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 824 MB, system 824 MB, textures 669 MB, meshes 4 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| First visible frame · Earth C0 (cartoon) | ≤ 50 ms (U-028) | 3.7 ms (warm-up 17 ms at load) | green |
| Frame time · Earth C0 (cartoon) | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 5.02 ms, p99 7.79 ms, max 9.6 ms (rendered 1920×1080) | green |
| Draw calls · Earth C0 (cartoon) | ≤ 250 | 136 | green |
| Geometry · Earth C0 (cartoon) | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 3.1 k triangles, 0 shadow casters | green |
| 2D lights visible · Earth C0 (cartoon) | ≤ 8 (hard cap 12) | 2 | green |
| Particles alive · Earth C0 (cartoon) | ≤ 1500 (v3) | 0 | green |
| GC per 300 frames, settled · Earth C0 (cartoon) | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | -725 B of the game's own (87522 B in the window of 300 frames, the floor 88247 B) | green |
| GC in the first 300 frames after the scene is ready · Earth C0 (cartoon) | reported (U-211; LEAD sets the limit): the game's own bytes in the first window after the scene is ready, before the settled one | -359 B of the game's own (87888 B in the window of 300 frames, the floor 88247 B) | info (U-211: no limit yet) |
| Memory · Earth C0 (cartoon) (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 940 MB, system 940 MB, textures 669 MB, meshes 5 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| Working set · Earth C0 (v4, D-089) | < 2.0 GB (warn 1.7); the dev-build probe rows decide (D-114 / D-116, P-28 / D-120) | 940 MB (Editor process: an upper bound of the build) | info (within) |
| Animated objects · Earth C0 | ≤ 40 on screen (Bible §9.6) | 36 Animators running (flora full rate 35, cheap idle 7, plants 42) | green |
| Sprite atlases · Earth | ≤ 8 per planet (contract §11.8) | 1 planet_earth* atlases on disk | green |
| Textures | BC7 color (the back walls RGBA32, D-192), BC5 normals, mips on POT world sprites (NPOT: none, D-061) | 1640 textures: 0 color not BC7 (a back wall: not RGBA32), 0 normals not BC5, 0 POT world sprites without mips (71 NPOT without, D-061; 605 v3 without by rule, contract §11.8) | green |
| Atlases | ≤ 2048² | 16 atlases, 0 allow more than 2048 | green |
| Audio | Vorbis; loops streamed, SFX compressed in memory | 7 clips, 0 off-rule | green |
| Asset size caps | contract §2/§4; importer rejects oversize | enforced by ArtImporter (EditMode tests RejectsOversize…, FileSizeLimit…) | green (tests) |

Largest loaded textures at the end of the route (849 textures, 669 MB in all, Editor's own included):

| Texture | Size | Format | MB |
|---|---|---|---|
| BlockColor_Earth | 512×512 | Texture2DArray | 28.7 |
| BlockNormal_Earth | 512×512 | Texture2DArray | 28.7 |
| BlockMask_Earth | 512×512 | Texture2DArray | 28.7 |
|  | 1920×1080 | RT ARGB32 | 23.7 |
| GizmoIconAtlas_pix32 | 2048×1024 | RGBA32 | 21.3 |
| waystation_mars_color | 2048×2048 | BC7 | 10.7 |
| waystation_mars_normal | 2048×2048 | BC5 | 10.7 |
| waystation_mars_emission | 2048×2048 | BC7 | 10.7 |
| waystation_mars_mask | 2048×2048 | BC7 | 10.7 |
| waystation_color | 2048×2048 | BC7 | 10.7 |
| waystation_normal | 2048×2048 | BC5 | 10.7 |
| waystation_emission | 2048×2048 | BC7 | 10.7 |
| waystation_mask | 2048×2048 | BC7 | 10.7 |
| disc_color | 1976×1976 | BC7 | 7.4 |
| side_color | 1956×1956 | BC7 | 7.3 |
