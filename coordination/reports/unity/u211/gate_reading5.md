# UNITY performance report 2026-11-10 13:35

BudgetGate v3 (U-014; U-086 with the D-077 limits): `BudgetGateTests.EarthSpaceMarsStayWithinBudgets`. Graphics: Intel(R) UHD Graphics. Memory rows read the Editor process, an upper bound for the built game.
- Load during measurement (D-019/D-083): none; free RAM at start 2229 MB (in-Editor now 344 MB); Unity Editor processes 2
- Machine memory (LEAD 2026-11-09): at the start free 2.18 GB, compression store 676 MB, largest private: claude 1011 MB, claude 876 MB, claude 867 MB, MsMpEng 409 MB; up 25.8 h, 0.4 min since the last Unity job's log; at the end free 2.08 GB, compression store 1877 MB, largest private: claude 1009 MB, claude 871 MB, claude 871 MB, MsMpEng 397 MB; up 25.9 h, 0 min since the last Unity job's log
- GC rows: Unity's 'GC Allocated In Frame'; the control (a 65536 B array) read 65858 B; the Editor's and the test runner's own floor: the least frame 290 B, so 87000 B per 300 frames (the window's sum was 87052 B), read with every root object inactive

| Budget (Bible §11.1) | Limit | Measured | Result |
|---|---|---|---|
| Boot settle · Earth | the first 2 s after boot: max frame ≤ 50 ms (gates); p99 ≤ 25 ms (recorded in 0.5.1, gates from U-179) (D-177) | 333 frames: max 15.0 ms, p99 13.9 ms (rendered 1920×1080) | green |
| First visible frame · Earth | ≤ 50 ms (U-028) | 3.1 ms (warm-up 139 ms at load) | green |
| Frame time · Earth | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 5.78 ms, p99 9.73 ms, max 17.5 ms (rendered 1920×1080) | green |
| Draw calls · Earth | ≤ 250 | 112 | green |
| Geometry · Earth | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 3.3 k triangles, 0 shadow casters | green |
| 2D lights visible · Earth | ≤ 8 (hard cap 12) | 2 | green |
| Particles alive · Earth | ≤ 1500 (v3) | 0 | green |
| GC per 300 frames, settled · Earth | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | 522 B of the game's own (87522 B in the window of 300 frames, the floor 87000 B) | green |
| GC on arrival (frames 1-299 after the scene is ready) · Earth | ≤ 16 KB of the game's own in the 299 frames after the arrival's first (U-211, LEAD 11-10; the larger of two readings) | 104 B of the game's own (86814 B in 299 frames, the floor 86710 B) | green |
| The arrival's first frame · Earth | reported, no limit yet (LEAD sets one after U-214): the bytes and the length of the frame the transition ended in | 770 B of the game's own (1060 B, the floor 290 B); 4.1 ms (Editor batch frame, not the player's) | info |
| Memory · Earth (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 693 MB, system 693 MB, textures 520 MB, meshes 1 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| Chunk generation · Earth streaming 200 m | ≤ 2 ms main thread in ≥ 99% of frames; no hitch > 33 ms (D-019) | p99 1.93 ms, 2/400 over 2 ms, worst frame 15.3 ms | green |
| Transition · launch (side → top-down) | ≤ 1.5 s | 0.95 s | green |
| First visible frame · Space | ≤ 50 ms (U-028) | 5.4 ms (warm-up at boot) | green |
| Frame time · Space | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 3.15 ms, p99 6.78 ms, max 9.7 ms (rendered 1920×1080) | green |
| Draw calls · Space | ≤ 80 | 11 | green |
| Geometry · Space | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 16.6 k triangles, 0 shadow casters | green |
| 2D lights visible · Space | ≤ 8 (hard cap 12) | 1 | green |
| Particles alive · Space | ≤ 1500 (v3) | 0 | green |
| GC per 300 frames, settled · Space | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | 546 B of the game's own (87546 B in the window of 300 frames, the floor 87000 B) | green |
| GC on arrival (frames 1-299 after the scene is ready) · Space | ≤ 16 KB of the game's own in the 299 frames after the arrival's first (U-211, LEAD 11-10; the larger of two readings) | 168 B of the game's own (86878 B in 299 frames, the floor 86710 B) | green |
| The arrival's first frame · Space | reported, no limit yet (LEAD sets one after U-214): the bytes and the length of the frame the transition ended in | 483122 B of the game's own (483412 B, the floor 290 B); 26.7 ms (Editor batch frame, not the player's) | info |
| Memory · Space (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 822 MB, system 822 MB, textures 519 MB, meshes 3 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| Planet load · Mars entry | ≤ 5 s (v3) | 2.11 s (scene load 70 ms, configure 544 ms, tile sheets 429 ms, warm-up 60 ms, total 1102 ms) | green |
| Transition · entry (top-down → side) | ≤ 1.5 s in the dev-build transition rows (D-136 (2): the Editor transition row is info, like the Editor memory rows) | 2.11 s (Editor) | info |
| Residency · after Mars entry | previous planet released within 5 s; only the current planet + common/ui/icons/space resident (v3) | planet_earth handles 0 after 0.0 s (holders: none); resident: common, icons, planet_dig, planet_mars, planet_space, planet_warden, planet_waystation, space, ui | green (pending U-091) |
| First visible frame · Mars | ≤ 50 ms (U-028) | 3.7 ms (warm-up 60 ms at load) | green |
| Frame time · Mars | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 3.78 ms, p99 6.20 ms, max 6.8 ms (rendered 1920×1080) | green |
| Draw calls · Mars | ≤ 250 | 14 | green |
| Geometry · Mars | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 0.4 k triangles, 0 shadow casters | green |
| 2D lights visible · Mars | ≤ 8 (hard cap 12) | 2 | green |
| Particles alive · Mars | ≤ 1500 (v3) | 1 | green |
| GC per 300 frames, settled · Mars | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | 156 B of the game's own (87156 B in the window of 300 frames, the floor 87000 B) | green |
| GC on arrival (frames 1-299 after the scene is ready) · Mars | ≤ 16 KB of the game's own in the 299 frames after the arrival's first (U-211, LEAD 11-10; the larger of two readings) | 5472 B of the game's own (92182 B in 299 frames, the floor 86710 B) | green |
| The arrival's first frame · Mars | reported, no limit yet (LEAD sets one after U-214): the bytes and the length of the frame the transition ended in | 4188 B of the game's own (4478 B, the floor 290 B); 6.4 ms (Editor batch frame, not the player's) | info |
| Memory · Mars (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 602 MB, system 602 MB, textures 661 MB, meshes 4 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| First visible frame · Mars dust storm | ≤ 50 ms (U-028) | 2.7 ms (warm-up 60 ms at load) | green |
| Frame time · Mars dust storm | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 4.59 ms, p99 6.36 ms, max 7.4 ms (rendered 1920×1080) | green |
| Draw calls · Mars dust storm | ≤ 250 | 35 | green |
| Geometry · Mars dust storm | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 0.6 k triangles, 0 shadow casters | green |
| 2D lights visible · Mars dust storm | ≤ 8 (hard cap 12) | 2 | green |
| Particles alive · Mars dust storm | ≤ 1500 (v3) | 1 | green |
| GC per 300 frames, settled · Mars dust storm | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | 156 B of the game's own (87156 B in the window of 300 frames, the floor 87000 B) | green |
| GC on arrival (frames 1-299 after the scene is ready) · Mars dust storm | ≤ 16 KB of the game's own in the 299 frames after the arrival's first (U-211, LEAD 11-10; the larger of two readings) | 104 B of the game's own (86814 B in 299 frames, the floor 86710 B) | green |
| The arrival's first frame · Mars dust storm | reported, no limit yet (LEAD sets one after U-214): the bytes and the length of the frame the transition ended in | 1228 B of the game's own (1518 B, the floor 290 B); 13.0 ms (Editor batch frame, not the player's) | info |
| Memory · Mars dust storm (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 617 MB, system 617 MB, textures 669 MB, meshes 4 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| First visible frame · Mars FX peak | ≤ 50 ms (U-028) | 1.5 ms (warm-up 60 ms at load) | green |
| Frame time · Mars FX peak | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 3.73 ms, p99 5.44 ms, max 10.6 ms (rendered 1920×1080) | green |
| Draw calls · Mars FX peak | ≤ 250 | 81 | green |
| Geometry · Mars FX peak | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 1.0 k triangles, 0 shadow casters | green |
| 2D lights visible · Mars FX peak | ≤ 8 (hard cap 12) | 2 | green |
| Particles alive · Mars FX peak | ≤ 1500 (v3) | 49 | green |
| GC per 300 frames, settled · Mars FX peak | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | 418 B of the game's own (87418 B in the window of 300 frames, the floor 87000 B) | green |
| GC on arrival (frames 1-299 after the scene is ready) · Mars FX peak | ≤ 16 KB of the game's own in the 299 frames after the arrival's first (U-211, LEAD 11-10; the larger of two readings) | 204 B of the game's own (86914 B in 299 frames, the floor 86710 B) | green |
| The arrival's first frame · Mars FX peak | reported, no limit yet (LEAD sets one after U-214): the bytes and the length of the frame the transition ended in | 1116 B of the game's own (1406 B, the floor 290 B); 2.3 ms (Editor batch frame, not the player's) | info |
| Memory · Mars FX peak (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 568 MB, system 568 MB, textures 669 MB, meshes 4 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| First visible frame · Earth C0 (cartoon) | ≤ 50 ms (U-028) | 4.2 ms (warm-up 7 ms at load) | green |
| Frame time · Earth C0 (cartoon) | avg ≤ 12 ms (target), p99 ≤ 16.6 ms | avg 4.31 ms, p99 6.09 ms, max 8.0 ms (rendered 1920×1080) | green |
| Draw calls · Earth C0 (cartoon) | ≤ 250 | 136 | green |
| Geometry · Earth C0 (cartoon) | ≤ 500 k triangles, ≤ 150 shadow casters (v3) | 3.1 k triangles, 0 shadow casters | green |
| 2D lights visible · Earth C0 (cartoon) | ≤ 8 (hard cap 12) | 2 | green |
| Particles alive · Earth C0 (cartoon) | ≤ 1500 (v3) | 0 | green |
| GC per 300 frames, settled · Earth C0 (cartoon) | ≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run) | 522 B of the game's own (87522 B in the window of 300 frames, the floor 87000 B) | green |
| GC on arrival (frames 1-299 after the scene is ready) · Earth C0 (cartoon) | ≤ 16 KB of the game's own in the 299 frames after the arrival's first (U-211, LEAD 11-10; the larger of two readings) | 220 B of the game's own (86930 B in 299 frames, the floor 86710 B) | green |
| The arrival's first frame · Earth C0 (cartoon) | reported, no limit yet (LEAD sets one after U-214): the bytes and the length of the frame the transition ended in | 512 B of the game's own (802 B, the floor 290 B); 3.6 ms (Editor batch frame, not the player's) | info |
| Memory · Earth C0 (cartoon) (Editor) | < 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089) | working set 600 MB, system 600 MB, textures 669 MB, meshes 5 MB, audio 3 MB (Editor process: upper bound) | info (over; the dev-build row decides, D-058) |
| Working set · Earth C0 (v4, D-089) | < 2.0 GB (warn 1.7); the dev-build probe rows decide (D-114 / D-116, P-28 / D-120) | 600 MB (Editor process: an upper bound of the build) | info (within) |
| Animated objects · Earth C0 | ≤ 40 on screen (Bible §9.6) | 36 Animators running (flora full rate 35, cheap idle 7, plants 42) | green |
| Sprite atlases · Earth | ≤ 8 per planet (contract §11.8) | 1 planet_earth* atlases on disk | green |
| Textures | BC7 color (the back walls RGBA32, D-192), BC5 normals, mips on POT world sprites (NPOT: none, D-061) | 1643 textures: 0 color not BC7 (a back wall: not RGBA32), 0 normals not BC5, 0 POT world sprites without mips (71 NPOT without, D-061; 608 v3 without by rule, contract §11.8) | green |
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
