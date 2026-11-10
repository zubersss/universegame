# UNITY performance report 2026-11-10 11:56

BudgetGate v3 (U-014; U-086 with the D-077 limits): `BudgetGateTests.EarthSpaceMarsStayWithinBudgets`. Graphics: Intel(R) UHD Graphics. Memory rows read the Editor process, an upper bound for the built game.
- Load during measurement (D-019/D-083): none; free RAM at start 2445 MB (in-Editor now 144 MB); Unity Editor processes 2
- Machine memory (LEAD 2026-11-09): at the start free 2.39 GB, compression store 514 MB, largest private: claude 905 MB, claude 851 MB, claude 743 MB, MsMpEng 407 MB; up 24.2 h, 1.5 min since the last Unity job's log; at the end free 2.47 GB, compression store 1481 MB, largest private: claude 908 MB, claude 824 MB, claude 745 MB, MsMpEng 319 MB; up 24.2 h, 0 min since the last Unity job's log
- GC rows: Unity's 'GC Allocated In Frame'; the control (a 65536 B array) read 65858 B; the Editor's and the test runner's own floor: the least frame 290 B, so 87000 B per 300 frames (the window's sum was 87052 B), read with every root object inactive

| Budget (Bible §11.1) | Limit | Measured | Result |
|---|---|---|---|
| Boot settle · Earth | the first 2 s after boot: max frame ≤ 50 ms (gates); p99 ≤ 25 ms (recorded in 0.5.1, gates from U-179) (D-177) | 274 frames: max 28.4 ms, p99 13.7 ms (rendered 1920×1080) | green |
| First visible frame · Earth | ≤ 50 ms (U-028) | 4.7 ms (warm-up 249 ms at load) | green |
| Frame time · Earth | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 6.63 ms, p99 17.36 ms, max 27.4 ms (rendered 1920×1080) | RED |
| Draw calls · Earth | ≤ 250 | 111 | green |
| Geometry · Earth | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 3.3 k triangles, 0 shadow casters | green |
| 2D lights visible · Earth | ≤ 8 (hard cap 12) | 2 | green |
| Particles alive · Earth | ≤ 1500 (v3) | 0 | green |
| GC per 300 frames, settled · Earth | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | 626 B of the game's own (87626 B in the window of 300 frames, the floor 87000 B) | green |
| GC in the first 300 frames after the scene is ready · Earth | reported (U-211; LEAD sets the limit): the game's own bytes in the first window after the scene is ready, before the settled one | 2334357 B of the game's own (2421357 B in the window of 300 frames, the floor 87000 B) | info (U-211: no limit yet) |
| Memory · Earth (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 612 MB, system 612 MB, textures 520 MB, meshes 1 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| Chunk generation · Earth streaming 200 m | ≤ 2 ms main thread in ≥ 99% of frames; no hitch > 33 ms (D-019) | p99 2.10 ms, 4/400 over 2 ms, worst frame 21.2 ms | RED |
| Transition · launch (side → top-down) | ≤ 1.5 s | 1.04 s | green |
| First visible frame · Space | ≤ 50 ms (U-028) | 30.3 ms (warm-up at boot) | green |
| Frame time · Space | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 5.56 ms, p99 9.59 ms, max 41.4 ms (rendered 1920×1080) | green |
| Draw calls · Space | ≤ 80 | 11 | green |
| Geometry · Space | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 16.6 k triangles, 0 shadow casters | green |
| 2D lights visible · Space | ≤ 8 (hard cap 12) | 1 | green |
| Particles alive · Space | ≤ 1500 (v3) | 0 | green |
| GC per 300 frames, settled · Space | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | 522 B of the game's own (87522 B in the window of 300 frames, the floor 87000 B) | green |
| GC in the first 300 frames after the scene is ready · Space | reported (U-211; LEAD sets the limit): the game's own bytes in the first window after the scene is ready, before the settled one | 2893055 B of the game's own (2980055 B in the window of 300 frames, the floor 87000 B) | info (U-211: no limit yet) |
| Memory · Space (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 667 MB, system 667 MB, textures 519 MB, meshes 3 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| Planet load · Mars entry | ≤ 5 s (v3) | 2.08 s (scene load 131 ms, configure 970 ms, tile sheets 288 ms, warm-up 73 ms, total 1462 ms) | green |
| Transition · entry (top-down → side) | ≤ 1.5 s in the dev-build transition rows (D-136 (2): the Editor transition row is info, like the Editor memory rows) | 2.08 s (Editor) | info |
| Residency · after Mars entry | previous planet released within 5 s; only the current planet + common/ui/icons/space resident (v3) | planet_earth handles 0 after 0.0 s (holders: none); resident: common, icons, planet_dig, planet_mars, planet_space, planet_warden, planet_waystation, space, ui | green (pending U-091) |
| First visible frame · Mars | ≤ 50 ms (U-028) | 3.8 ms (warm-up 73 ms at load) | green |
| Frame time · Mars | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 4.58 ms, p99 8.19 ms, max 8.5 ms (rendered 1920×1080) | green |
| Draw calls · Mars | ≤ 250 | 14 | green |
| Geometry · Mars | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 0.4 k triangles, 0 shadow casters | green |
| 2D lights visible · Mars | ≤ 8 (hard cap 12) | 2 | green |
| Particles alive · Mars | ≤ 1500 (v3) | 1 | green |
| GC per 300 frames, settled · Mars | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | 260 B of the game's own (87260 B in the window of 300 frames, the floor 87000 B) | green |
| GC in the first 300 frames after the scene is ready · Mars | reported (U-211; LEAD sets the limit): the game's own bytes in the first window after the scene is ready, before the settled one | 2750216 B of the game's own (2837216 B in the window of 300 frames, the floor 87000 B) | info (U-211: no limit yet) |
| Memory · Mars (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 843 MB, system 843 MB, textures 661 MB, meshes 4 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| First visible frame · Mars dust storm | ≤ 50 ms (U-028) | 6.2 ms (warm-up 73 ms at load) | green |
| Frame time · Mars dust storm | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 6.94 ms, p99 13.25 ms, max 23.0 ms (rendered 1920×1080) | green |
| Draw calls · Mars dust storm | ≤ 250 | 37 | green |
| Geometry · Mars dust storm | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 0.7 k triangles, 0 shadow casters | green |
| 2D lights visible · Mars dust storm | ≤ 8 (hard cap 12) | 2 | green |
| Particles alive · Mars dust storm | ≤ 1500 (v3) | 1 | green |
| GC per 300 frames, settled · Mars dust storm | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | 470 B of the game's own (87470 B in the window of 300 frames, the floor 87000 B) | green |
| GC in the first 300 frames after the scene is ready · Mars dust storm | reported (U-211; LEAD sets the limit): the game's own bytes in the first window after the scene is ready, before the settled one | 2386666 B of the game's own (2473666 B in the window of 300 frames, the floor 87000 B) | info (U-211: no limit yet) |
| Memory · Mars dust storm (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 813 MB, system 813 MB, textures 669 MB, meshes 5 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| First visible frame · Mars FX peak | ≤ 50 ms (U-028) | 7.0 ms (warm-up 73 ms at load) | green |
| Frame time · Mars FX peak | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 7.13 ms, p99 12.41 ms, max 13.4 ms (rendered 1920×1080) | green |
| Draw calls · Mars FX peak | ≤ 250 | 195 | green |
| Geometry · Mars FX peak | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 5.4 k triangles, 0 shadow casters | green |
| 2D lights visible · Mars FX peak | ≤ 8 (hard cap 12) | 2 | green |
| Particles alive · Mars FX peak | ≤ 1500 (v3) | 48 | green |
| GC per 300 frames, settled · Mars FX peak | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | 260 B of the game's own (87260 B in the window of 300 frames, the floor 87000 B) | green |
| GC in the first 300 frames after the scene is ready · Mars FX peak | reported (U-211; LEAD sets the limit): the game's own bytes in the first window after the scene is ready, before the settled one | 2430084 B of the game's own (2517084 B in the window of 300 frames, the floor 87000 B) | info (U-211: no limit yet) |
| Memory · Mars FX peak (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 821 MB, system 821 MB, textures 669 MB, meshes 6 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| First visible frame · Earth C0 (cartoon) | ≤ 50 ms (U-028) | 2.8 ms (warm-up 33 ms at load) | green |
| Frame time · Earth C0 (cartoon) | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 6.01 ms, p99 10.21 ms, max 51.1 ms (rendered 1920×1080) | green |
| Draw calls · Earth C0 (cartoon) | ≤ 250 | 152 | green |
| Geometry · Earth C0 (cartoon) | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 4.2 k triangles, 0 shadow casters | green |
| 2D lights visible · Earth C0 (cartoon) | ≤ 8 (hard cap 12) | 2 | green |
| Particles alive · Earth C0 (cartoon) | ≤ 1500 (v3) | 0 | green |
| GC per 300 frames, settled · Earth C0 (cartoon) | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | 156 B of the game's own (87156 B in the window of 300 frames, the floor 87000 B) | green |
| GC in the first 300 frames after the scene is ready · Earth C0 (cartoon) | reported (U-211; LEAD sets the limit): the game's own bytes in the first window after the scene is ready, before the settled one | 2322340 B of the game's own (2409340 B in the window of 300 frames, the floor 87000 B) | info (U-211: no limit yet) |
| Memory · Earth C0 (cartoon) (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 622 MB, system 622 MB, textures 669 MB, meshes 5 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| Working set · Earth C0 (v4, D-089) | < 2.0 GB (warn 1.7); the dev-build probe rows decide (D-114 / D-116, P-28 / D-120) | 622 MB (Editor process: an upper bound of the build) | info (within) |
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
