# blender/vendor_cc0: raw CC0 downloads (art v7, D-205)

The raw files are NOT in git (this folder is git-ignored except this manifest) and NEVER ship: only our own renders of
them go into the game. Every file is listed here with where it came from, its licence, its SHA-256 and its size, so the
folder can be rebuilt and checked on any machine. Each asset sits in its own folder; models are taken as glTF (data
only: no script can ride in it); Blender opens them with `--disable-autoexec` (tools/blender_scene.ps1).

Fetched with a generic client name ("blender-asset-fetch/1.0") through Poly Haven's public API
(https://api.polyhaven.com/files/<id> and /info/<id>); nothing about the project or its owner was sent.

## Poly Haven (https://polyhaven.com): every asset CC0 1.0 (https://polyhaven.com/license)

### calathea_orbifolia_01: "Calathea Orbifolia 01" by Rob Tuytel and Rico Cilliers
https://polyhaven.com/a/calathea_orbifolia_01 · glTF, 1k textures · downloaded 2026-11-10 13:37 · used by B-258 part 1 (the plant)

| File (under blender/vendor_cc0/calathea_orbifolia_01/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| calathea_orbifolia_01.gltf | 9309 | 399130c01bfff6b493f885652112c3c841c3814b024a3d3c87773e0c5ab4f156 | https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/calathea_orbifolia_01/calathea_orbifolia_01_1k.gltf |
| calathea_orbifolia_01.bin | 407968 | df1668bcb44914abac046217bbdae9867a3702198f7c374135f2b4456df8b038 | https://dl.polyhaven.org/file/ph-assets/Models/gltf/8k/calathea_orbifolia_01/calathea_orbifolia_01.bin |
| textures/calathea_orbifolia_01_diff_1k.jpg | 455819 | a105a093d74317a3853319a06fdc78cad2a13e353962298d2094195720b9b4a0 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/calathea_orbifolia_01/calathea_orbifolia_01_diff_1k.jpg |
| textures/calathea_orbifolia_01_nor_gl_1k.jpg | 581558 | 52aac88c18bf42c369aad9b2b5e41dbe58b015ca2fac7ff6ed4cb21147cb49c8 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/calathea_orbifolia_01/calathea_orbifolia_01_nor_gl_1k.jpg |
| textures/calathea_orbifolia_01_arm_1k.jpg | 421555 | df4ea4dfc74a6965476200cffea69886ac26d3c089f356a7b69518149ef585e0 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/calathea_orbifolia_01/calathea_orbifolia_01_arm_1k.jpg |

### rock_moss_set_01: "Rock Moss Set 01" by Kless Gyzen
https://polyhaven.com/a/rock_moss_set_01 · glTF, 1k textures · downloaded 2026-11-10 13:37 · used by B-258 part 1 (the mossy rock)

| File (under blender/vendor_cc0/rock_moss_set_01/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| rock_moss_set_01.gltf | 9987 | c36675aca9c6b2be7785c2534cf413b03ec82a5a2a5407a2b1c0cdb0346c9727 | https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/rock_moss_set_01/rock_moss_set_01_1k.gltf |
| rock_moss_set_01.bin | 1466380 | de8360e6175879aaf02c171911069cf5f1852547f9ca7f10e440085dbcc3315e | https://dl.polyhaven.org/file/ph-assets/Models/gltf/8k/rock_moss_set_01/rock_moss_set_01.bin |
| textures/rock_moss_set_01_diff_1k.jpg | 168099 | 40cea65d8aa4ee73a93b04af19963834d061eee9779c3fc2c1cba76eef812ccc | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/rock_moss_set_01/rock_moss_set_01_diff_1k.jpg |
| textures/rock_moss_set_01_nor_gl_1k.jpg | 209975 | eb4aad3f207f1dc5b624d74ae240372171626a66912bd71adf7bd3e518181d6e | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/rock_moss_set_01/rock_moss_set_01_nor_gl_1k.jpg |
| textures/rock_moss_set_01_rough_1k.jpg | 82624 | 4d6ec46623abd8e2cdb855f59c7ce31873ad61b36b60e4de579e9e776a497c6b | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/rock_moss_set_01/rock_moss_set_01_rough_1k.jpg |

Each file's size and MD5 matched the API's own listing at download (tools/blender_fetch_cc0.ps1 does not list a file that
does not). The sections below were appended by that tool on 2026-11-10 14:13 for B-258 part 3 (the frame): thirteen more
models and four ground textures (the Diffuse map as PNG). The whole folder: 104 MB in nineteen assets.

### fern_02: "Fern 02" by Rob Tuytel, Rico Cilliers
https://polyhaven.com/a/fern_02 · glTF, 1k · downloaded 2026-11-10 14:13 · used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/fern_02/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| fern_02.gltf | 6899 | 33974295ee19670af4877705fc7d91f33f42d6302f0d44a625e072271223031f | https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/fern_02/fern_02_1k.gltf |
| textures/fern_02_arm_1k.jpg | 280359 | ebfb5d76ce9cbdaec20bcd22dce9b755f0b1b8650ef29ca13555e3e6961025d7 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/fern_02/fern_02_arm_1k.jpg |
| textures/fern_02_diff_1k.jpg | 315705 | a828a6e7b4c01c826911e2eac4b3afc7457dab7b3b392a31c681ed88b7d50029 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/fern_02/fern_02_diff_1k.jpg |
| textures/fern_02_nor_gl_1k.jpg | 367222 | 45bce132c6e96a0864bc89ab5da51361ab3f4afa83a6669ae499ab5ca811f621 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/fern_02/fern_02_nor_gl_1k.jpg |
| fern_02.bin | 176176 | fe1abb762bcbbc7ad9e86925c8080437a62add257d9280e9142fdc85c226e64c | https://dl.polyhaven.org/file/ph-assets/Models/gltf/8k/fern_02/fern_02.bin |

### anthurium_botany_01: "Anthurium Botany 01" by Rob Tuytel, Rico Cilliers
https://polyhaven.com/a/anthurium_botany_01 · glTF, 1k · downloaded 2026-11-10 14:13 · used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/anthurium_botany_01/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| anthurium_botany_01.gltf | 10675 | 6b3f6b8eda6cc0edfefd6a58f6758ef6538c35b2ca2a76189383f23b246dd8c6 | https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/anthurium_botany_01/anthurium_botany_01_1k.gltf |
| textures/anthurium_botany_01_nor_gl_1k.jpg | 494107 | f0cf940590733a2a5a9b0db362bd093c39b28405c66b1d084aa203efe6f0d3fc | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/anthurium_botany_01/anthurium_botany_01_nor_gl_1k.jpg |
| textures/anthurium_botany_01_arm_1k.jpg | 542795 | 88d9ce05e4b301ae9cd5b479459262c4690a3ee2de80a8f5e18a288ff5e96bee | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/anthurium_botany_01/anthurium_botany_01_arm_1k.jpg |
| anthurium_botany_01.bin | 1744256 | 6a23daf128e297ad99e984bec11bdea3c6eab64e52d07cbdc948ace5a05b2e25 | https://dl.polyhaven.org/file/ph-assets/Models/gltf/8k/anthurium_botany_01/anthurium_botany_01.bin |
| textures/anthurium_botany_01_diff_1k.jpg | 448508 | f759421f00e848d7d2915b409d98c6311cc601e4be17d4155e0852429fa4993e | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/anthurium_botany_01/anthurium_botany_01_diff_1k.jpg |

### pachira_aquatica_01: "Pachira Aquatica 01" by Rob Tuytel, Rico Cilliers
https://polyhaven.com/a/pachira_aquatica_01 · glTF, 1k · downloaded 2026-11-10 14:13 · used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/pachira_aquatica_01/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| pachira_aquatica_01.gltf | 13730 | e73b77c0ffadd8b9fa686faabfecf37799123fe4bc756f816145a4f8c9f53364 | https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/pachira_aquatica_01/pachira_aquatica_01_1k.gltf |
| textures/pachira_aquatica_01_bark_nor_gl_1k.jpg | 723624 | 389b0f8cc3e8bf4ee78ea12c367ff3003d69d8e83de8baf908e6f2e123d1e6a8 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/pachira_aquatica_01/pachira_aquatica_01_bark_nor_gl_1k.jpg |
| textures/pachira_aquatica_01_leaves_nor_gl_1k.jpg | 490166 | 3a442aa75df0e6f37bb7410f8ae09927b419d2dba202943cda40f52a7194804c | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/pachira_aquatica_01/pachira_aquatica_01_leaves_nor_gl_1k.jpg |
| textures/pachira_aquatica_01_leaves_diff_1k.jpg | 320484 | b3211c240dd2ea7913326e7f21f9db9d029ee487b5e59d58d0e10c8cc77d203f | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/pachira_aquatica_01/pachira_aquatica_01_leaves_diff_1k.jpg |
| textures/pachira_aquatica_01_bark_arm_1k.jpg | 588614 | 7c44f930e3a6c14acb9043e50d8244da7869f8937233c58276d1b3212a3a6960 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/pachira_aquatica_01/pachira_aquatica_01_bark_arm_1k.jpg |
| textures/pachira_aquatica_01_bark_diff_1k.jpg | 592488 | 9ca175a1c105a3555c47626ebead36505c29482ea0018f4c6e9a5828ce6d7b25 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/pachira_aquatica_01/pachira_aquatica_01_bark_diff_1k.jpg |
| textures/pachira_aquatica_01_leaves_arm_1k.jpg | 372937 | 42824afde27e7f0111a2e673f0a7cfe0b18bc21d2201b85d9737fce48c1016a3 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/pachira_aquatica_01/pachira_aquatica_01_leaves_arm_1k.jpg |
| pachira_aquatica_01.bin | 2036788 | a803777635a4744cc304bd936806242d8875430cc588295c9fa2792a64747c8e | https://dl.polyhaven.org/file/ph-assets/Models/gltf/8k/pachira_aquatica_01/pachira_aquatica_01.bin |

### grass_medium_01: "Grass Medium 01" by Rob Tuytel, Rico Cilliers
https://polyhaven.com/a/grass_medium_01 · glTF, 1k · downloaded 2026-11-10 14:13 · used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/grass_medium_01/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| grass_medium_01.gltf | 27110 | 3e5e2a314c94e16de54fd7c28e41709731fbd2b1613ab539f1544f622ddb6a85 | https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/grass_medium_01/grass_medium_01_1k.gltf |
| textures/grass_medium_01_nor_gl_1k.jpg | 956166 | cae298d3d1d7ff7c7e210ad8ac772b96706e356f9315a6b04fde373ce01ccf1e | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/grass_medium_01/grass_medium_01_nor_gl_1k.jpg |
| textures/grass_medium_01_diff_1k.jpg | 395673 | 71495bd6a11fddcab0aaff38246fea1a7b802a705483f1c7cbca53955daa8050 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/grass_medium_01/grass_medium_01_diff_1k.jpg |
| textures/grass_medium_01_arm_1k.jpg | 679518 | 9a3a30f72bc02f4398967c5b08f2d20cce30bd423a2613b42a727034296fa3ae | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/grass_medium_01/grass_medium_01_arm_1k.jpg |
| grass_medium_01.bin | 1006632 | f4587cabdb96a2e96d8be644923dc954a248edfaaa717a0ff224cacb898bee1f | https://dl.polyhaven.org/file/ph-assets/Models/gltf/8k/grass_medium_01/grass_medium_01.bin |

### grass_medium_02: "Grass Medium 02" by Rico Cilliers
https://polyhaven.com/a/grass_medium_02 · glTF, 1k · downloaded 2026-11-10 14:13 · used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/grass_medium_02/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| grass_medium_02.gltf | 8864 | 7037f8d2dfc6aeec0bf72f4eeb96cfa3f6b3a5e6c6f0bc5de537c055b2fd5d04 | https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/grass_medium_02/grass_medium_02_1k.gltf |
| textures/grass_medium_02_nor_gl_1k.jpg | 118146 | 0b464550366ed72a6cad9c357e19ac4c83fc9adc87272771479138129853b300 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/grass_medium_02/grass_medium_02_nor_gl_1k.jpg |
| textures/grass_medium_02_diff_1k.jpg | 161235 | 91ae99005b449011aceb207a68a937258fd9bfd66ff367d344c50398b1df389c | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/grass_medium_02/grass_medium_02_diff_1k.jpg |
| textures/grass_medium_02_arm_1k.jpg | 241181 | f0d57bfd95bff7710526b49d47cf2326ee3796e425639d53b983d1472480b57d | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/grass_medium_02/grass_medium_02_arm_1k.jpg |
| grass_medium_02.bin | 272048 | aa8493bc1544a89e08bf440c7ba361042bfe6ea48b1fefc7e4af2dfff42fdf4a | https://dl.polyhaven.org/file/ph-assets/Models/gltf/4k/grass_medium_02/grass_medium_02.bin |

### moss_01: "Moss 01" by Rob Tuytel
https://polyhaven.com/a/moss_01 · glTF, 1k · downloaded 2026-11-10 14:13 · used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/moss_01/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| moss_01.gltf | 18481 | 36fe6cb9889abb33f4dbee402928e260a3e7dfaec043d39b80b1e3afff684f65 | https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/moss_01/moss_01_1k.gltf |
| textures/moss_01_nor_gl_1k.jpg | 388925 | 531d6bea634ac956d87b176a89740f229ec7e8137a6413e290bab640c6a8b0ec | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/moss_01/moss_01_nor_gl_1k.jpg |
| textures/moss_01_diff_1k.jpg | 170297 | 7c8d0794dd9db0a82f668a276896818d195c644cfed35f0fbf984a3260e70e50 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/moss_01/moss_01_diff_1k.jpg |
| textures/moss_01_arm_1k.jpg | 336140 | 0cf0aabfc370a51e7d330ae01e63ca380f88a9bb0fcfa94730374476183a12cf | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/moss_01/moss_01_arm_1k.jpg |
| moss_01.bin | 7260 | 440e3cadbd93ad383cdbb9b4c17c3236774924c33ff62ac409ab00b8ed622861 | https://dl.polyhaven.org/file/ph-assets/Models/gltf/4k/moss_01/moss_01.bin |

### single_root: "Single Root" by Jenelle van Heerden
https://polyhaven.com/a/single_root · glTF, 1k · downloaded 2026-11-10 14:13 · used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/single_root/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| single_root.gltf | 3023 | b88d0e4b06f710a70af3adb8dd72dea106d3b90f4d093b3e94a09c781745d92c | https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/single_root/single_root_1k.gltf |
| textures/single_root_diff_1k.jpg | 542448 | c53c68f142215139a5784c8fa080183e3e9ae8ae2f9181b3d477fd1edd3a48b5 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/single_root/single_root_diff_1k.jpg |
| textures/single_root_arm_1k.jpg | 551456 | 51dd1b1e84607e80120970533352b97075d0ff6a29ed1e2e1261a20c36b93ab7 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/single_root/single_root_arm_1k.jpg |
| single_root.bin | 1911860 | 6e047b1b10b91b2e6f08fea2daad834e0c34c0f59145a39ce71b029bce11fa69 | https://dl.polyhaven.org/file/ph-assets/Models/gltf/8k/single_root/single_root.bin |
| textures/single_root_nor_gl_1k.jpg | 836549 | 508fb34ec0c000cf4feeeb2ce9c0373ec57de5608c2f7058543c3f1ffc0ab6da | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/single_root/single_root_nor_gl_1k.jpg |

### dead_tree_trunk: "Dead Tree Trunk" by Rob Tuytel
https://polyhaven.com/a/dead_tree_trunk · glTF, 1k · downloaded 2026-11-10 14:13 · used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/dead_tree_trunk/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| dead_tree_trunk.gltf | 2812 | 8baaf1ff66ba1f79acdceed0dc3797a882990a3abb10b18abe56762f34c26e39 | https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/dead_tree_trunk/dead_tree_trunk_1k.gltf |
| textures/dead_tree_trunk_arm_1k.jpg | 724384 | 0e0f7d64ac4ee3a7e7861a48f4bbd1ec2c026facd8f48b756f6b5d4557af3fd3 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/dead_tree_trunk/dead_tree_trunk_arm_1k.jpg |
| textures/dead_tree_trunk_nor_gl_1k.jpg | 1053075 | b7c393204c93f0c67535ff3b5d723b26598f9dbb2b5110b74249ab88189f026f | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/dead_tree_trunk/dead_tree_trunk_nor_gl_1k.jpg |
| textures/dead_tree_trunk_diff_1k.jpg | 713480 | bc31d7d23db90d90cfb568c583914eeec11b29716b79096818b706a9e3e0216c | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/dead_tree_trunk/dead_tree_trunk_diff_1k.jpg |
| dead_tree_trunk.bin | 2293788 | c1ac6b3195246e8647a28eee2fbfdd4712a045c7cf2dcb4f5abcc2d40a446ca6 | https://dl.polyhaven.org/file/ph-assets/Models/gltf/8k/dead_tree_trunk/dead_tree_trunk.bin |

### dead_tree_trunk_02: "Dead Tree Trunk 02" by Jenelle van Heerden, Rico Cilliers
https://polyhaven.com/a/dead_tree_trunk_02 · glTF, 1k · downloaded 2026-11-10 14:13 · used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/dead_tree_trunk_02/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| dead_tree_trunk_02.gltf | 2849 | b486ab1f0c7f4972e0eec97b19de53b26a34d09f07da5f9c2a70f8621f9e574c | https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/dead_tree_trunk_02/dead_tree_trunk_02_1k.gltf |
| textures/dead_tree_trunk_02_diff_1k.jpg | 932059 | fac23e81ab5639dcde93db605e5dd94c65e0aa2b1fb4a303f37de9afbb9af5b4 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/dead_tree_trunk_02/dead_tree_trunk_02_diff_1k.jpg |
| textures/dead_tree_trunk_02_arm_1k.jpg | 805609 | ea15561ce36572ebd0db3c997f70d68a76d4bcbfef7efb4f91c8fd3b5f766e62 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/dead_tree_trunk_02/dead_tree_trunk_02_arm_1k.jpg |
| textures/dead_tree_trunk_02_nor_gl_1k.jpg | 1192056 | 9b26c29b89afced0ddb91dbe6f917e59038bed5ba6076dfceb8d1b4b00ca04f7 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/dead_tree_trunk_02/dead_tree_trunk_02_nor_gl_1k.jpg |
| dead_tree_trunk_02.bin | 1974352 | 2b1b7ca07d98396ddc1987e367dcff9734df16b62e997c14837512d134687ded | https://dl.polyhaven.org/file/ph-assets/Models/gltf/8k/dead_tree_trunk_02/dead_tree_trunk_02.bin |

### tree_stump_01: "Tree Stump 01" by Rob Tuytel
https://polyhaven.com/a/tree_stump_01 · glTF, 1k · downloaded 2026-11-10 14:13 · used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/tree_stump_01/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| tree_stump_01.gltf | 2793 | 9c66ba87d693f35eb404acaa96e0eeff831c295b61a0a903795584cbcc3527c9 | https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/tree_stump_01/tree_stump_01_1k.gltf |
| tree_stump_01.bin | 965380 | b4d9ca70b3c908c4a638fbd6a23ed96c84055bbbf14cf44b89e31ad59fa21e0a | https://dl.polyhaven.org/file/ph-assets/Models/gltf/8k/tree_stump_01/tree_stump_01.bin |
| textures/tree_stump_01_diff_1k.jpg | 907451 | 781ebe420ac4d84f2e44b9e9937a596e3d5d90711d978a1392f8bf3771b5bf31 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/tree_stump_01/tree_stump_01_diff_1k.jpg |
| textures/tree_stump_01_nor_gl_1k.jpg | 1238404 | 425117514b0386bb6df41cb64a61a624d2596472e05777483d4021b3285e3ceb | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/tree_stump_01/tree_stump_01_nor_gl_1k.jpg |
| textures/tree_stump_01_arm_1k.jpg | 825646 | d845cd6ab45288c546267d059ebe1f8a737e174330fe9375e5f99e753f2f95d8 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/tree_stump_01/tree_stump_01_arm_1k.jpg |

### shrub_03: "Shrub 03" by Rico Cilliers
https://polyhaven.com/a/shrub_03 · glTF, 1k · downloaded 2026-11-10 14:13 · used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/shrub_03/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| shrub_03.gltf | 7296 | b76d7c14bc027e834e82d3f984c32b5d060e62908aa90ff9420a637ca253a8ea | https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/shrub_03/shrub_03_1k.gltf |
| shrub_03.bin | 238684 | bf4df21e6d2a2bc5f00b4c9142f776171fe7da00cf960001825748067af542b6 | https://dl.polyhaven.org/file/ph-assets/Models/gltf/4k/shrub_03/shrub_03.bin |
| textures/shrub_03_arm_1k.jpg | 396238 | 3e2b16812a623037138eedace958210c5f3443a827bbe69663045bba5612f815 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/shrub_03/shrub_03_arm_1k.jpg |
| textures/shrub_03_diff_1k.jpg | 481841 | 3cadc7aba46d3aabbd7d6d2b1d04aa32e2a7da0bc87c2d38ef3cb1ee42cb03ec | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/shrub_03/shrub_03_diff_1k.jpg |
| textures/shrub_03_nor_gl_1k.jpg | 504734 | ff856bacfce859b8a7555dd9a3b92fbd36b2e775d486be71df485afb4235d6c9 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/shrub_03/shrub_03_nor_gl_1k.jpg |

### rock_moss_set_02: "Rock Moss Set 02" by Kless Gyzen
https://polyhaven.com/a/rock_moss_set_02 · glTF, 1k · downloaded 2026-11-10 14:13 · used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/rock_moss_set_02/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| rock_moss_set_02.gltf | 11608 | c3b992a7622e94f7d8da97a47277a2a5177a513af0312a127ec908d4056c97db | https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/rock_moss_set_02/rock_moss_set_02_1k.gltf |
| textures/rock_moss_set_02_nor_gl_1k.jpg | 273527 | dd2503789089fb72ef469efd14364d393e769c0de8781a251475cac7e0b6f51d | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/rock_moss_set_02/rock_moss_set_02_nor_gl_1k.jpg |
| textures/rock_moss_set_02_diff_1k.jpg | 194307 | 91dd2cc77d5198b067d77e5bdb3fa8ee7b8950aeff5aec2c1ccaddb76dcca481 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/rock_moss_set_02/rock_moss_set_02_diff_1k.jpg |
| textures/rock_moss_set_02_rough_1k.jpg | 146226 | 12252219a98a560940359973e83af831abdcfab0ead3f0a2a7b135a0143105f1 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/rock_moss_set_02/rock_moss_set_02_rough_1k.jpg |
| rock_moss_set_02.bin | 1316572 | 2df9d8eaaca4207529b0f613d4886d3962d0b9ffc0cdfd2bc4bf35dbcd391cb5 | https://dl.polyhaven.org/file/ph-assets/Models/gltf/8k/rock_moss_set_02/rock_moss_set_02.bin |

### island_tree_02: "Island Tree 02" by Rob Tuytel, Rico Cilliers
https://polyhaven.com/a/island_tree_02 · glTF, 1k · downloaded 2026-11-10 14:13 · used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/island_tree_02/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| island_tree_02.gltf | 8545 | d8c5d9ead41cdbef91a648f40ff60470faa19eb3a7010e59e44cb1a01250f75d | https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/island_tree_02/island_tree_02_1k.gltf |
| textures/island_tree_02_nor_gl_1k.jpg | 1157226 | 1580d5a42d02f4ede51bfb03972ab0aef3d8acafbd3692276879171007bb70ec | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/island_tree_02/island_tree_02_nor_gl_1k.jpg |
| textures/island_tree_02_diff_1k.jpg | 738738 | 8fc20397ab5d514c119d7a025868414d78e436138d3867a4b7ba12334a72ec3a | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/island_tree_02/island_tree_02_diff_1k.jpg |
| textures/island_tree_02_arm_1k.jpg | 688305 | ada61dd4fad023e699b6314b8b76590017b301719bf74ffc9e20b95893ed62b6 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/island_tree_02/island_tree_02_arm_1k.jpg |
| textures/island_tree_02_leaves_nor_gl_1k.jpg | 379443 | 07ba461c0c95da4e49a42981766bdb6191d4c3c4d815796c082266dcc3cecdb8 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/island_tree_02/island_tree_02_leaves_nor_gl_1k.jpg |
| textures/island_tree_02_leaves_diff_1k.jpg | 191886 | f56d762a1507754752abf164cc12acbc1e87ce87fa609ac44b98a1b0037c89d8 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/island_tree_02/island_tree_02_leaves_diff_1k.jpg |
| textures/island_tree_02_leaves_arm_1k.jpg | 489476 | 90da3a072dbcb052715b1313b9dbc69a4aa8a09a31a4b3868411a2bb51d72037 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/island_tree_02/island_tree_02_leaves_arm_1k.jpg |
| textures/island_tree_02_branches_nor_gl_1k.jpg | 819101 | 2d67393ba76a0f49cf965fa0c99d8c16268e71e87b1203d35539bfdb971a514e | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/island_tree_02/island_tree_02_branches_nor_gl_1k.jpg |
| textures/island_tree_02_branches_diff_1k.jpg | 528304 | bee5ec22196e9e31ad0c95a5a9b4636571cc0124d5bb27a92f1e307d289cc60d | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/island_tree_02/island_tree_02_branches_diff_1k.jpg |
| textures/island_tree_02_branches_arm_1k.jpg | 484806 | 9e3f82263247ce4f619692cea4c4f6fe9936ff465a86623481849062642c7d05 | https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/island_tree_02/island_tree_02_branches_arm_1k.jpg |
| island_tree_02.bin | 40686576 | 427d69ccc1ea12d1fb9c6af89691563b4a097f39a6f34c15be6e45ef5e5fd4ce | https://dl.polyhaven.org/file/ph-assets/Models/gltf/8k/island_tree_02/island_tree_02.bin |

### excavated_soil_wall: "Excavated Soil Wall" by Amal Kumar
https://polyhaven.com/a/excavated_soil_wall · the Diffuse map, PNG, 1k · downloaded 2026-11-10 14:13 · used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/excavated_soil_wall/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| excavated_soil_wall_diff_1k.png | 5378272 | 1739c552e648468132c54a50bfbe918ad2ccba6c8a1d7083e2a75d82dc24bc43 | https://dl.polyhaven.org/file/ph-assets/Textures/png/1k/excavated_soil_wall/excavated_soil_wall_diff_1k.png |

### forest_floor: "Forest Floor" by eye-candy.xyz
https://polyhaven.com/a/forest_floor · the Diffuse map, PNG, 1k · downloaded 2026-11-10 14:14 · used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/forest_floor/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| forest_floor_diff_1k.png | 6062807 | 83106f436061cf326c01175ad0d49291a4964bfd1c58a359aa1abdb983bd68b9 | https://dl.polyhaven.org/file/ph-assets/Textures/png/1k/forest_floor/forest_floor_diff_1k.png |

### brown_mud_leaves_01: "Brown Mud Leaves 01" by Rob Tuytel
https://polyhaven.com/a/brown_mud_leaves_01 · the Diffuse map, PNG, 1k · downloaded 2026-11-10 14:14 · used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/brown_mud_leaves_01/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| brown_mud_leaves_01_diff_1k.png | 5909847 | 17506c4b1c5000ed5add829f1de825e851fcd8ffc4b8ed16c45b551ade935ea1 | https://dl.polyhaven.org/file/ph-assets/Textures/png/1k/brown_mud_leaves_01/brown_mud_leaves_01_diff_1k.png |

### red_laterite_soil_stones: "Red Laterite Soil Stones" by Amal Kumar
https://polyhaven.com/a/red_laterite_soil_stones · the Diffuse map, PNG, 1k · downloaded 2026-11-10 14:14 · used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/red_laterite_soil_stones/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| red_laterite_soil_stones_diff_1k.png | 6384617 | 96f3e55c2cf202e609faea9234847805563375d8edf466fb30f06413dda1f2a1 | https://dl.polyhaven.org/file/ph-assets/Textures/png/1k/red_laterite_soil_stones/red_laterite_soil_stones_diff_1k.png |

### fern_02: its Alpha map (the cut-out of the leaf cards; not in the glTF's own file list)
https://polyhaven.com/a/fern_02 ; PNG, 1k ; downloaded 2026-11-10 14:27 ; used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/fern_02/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| textures/fern_02_alpha_1k.png | 114589 | ea3c64284c7ebdeedf484d2d816eae92825ec526140c3bb83859ddc7a64001f9 | https://dl.polyhaven.org/file/ph-assets/Models/png/1k/fern_02/fern_02_alpha_1k.png |

### anthurium_botany_01: its Alpha map (the cut-out of the leaf cards; not in the glTF's own file list)
https://polyhaven.com/a/anthurium_botany_01 ; PNG, 1k ; downloaded 2026-11-10 14:27 ; used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/anthurium_botany_01/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| textures/anthurium_botany_01_alpha_1k.png | 45560 | 74a7f17e6d9da6174a5bb0b28bc5effa1fdc07e7755ba39d8c62f79a2dfe0887 | https://dl.polyhaven.org/file/ph-assets/Models/png/1k/anthurium_botany_01/anthurium_botany_01_alpha_1k.png |

### calathea_orbifolia_01: its Alpha map (the cut-out of the leaf cards; not in the glTF's own file list)
https://polyhaven.com/a/calathea_orbifolia_01 ; PNG, 1k ; downloaded 2026-11-10 14:27 ; used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/calathea_orbifolia_01/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| textures/calathea_orbifolia_01_alpha_1k.png | 57282 | 24336cb9a92fb48e9521d8674c50f96e1b32a664265c8c0e9eda8429767d4cdf | https://dl.polyhaven.org/file/ph-assets/Models/png/1k/calathea_orbifolia_01/calathea_orbifolia_01_alpha_1k.png |

### grass_medium_01: its Alpha map (the cut-out of the leaf cards; not in the glTF's own file list)
https://polyhaven.com/a/grass_medium_01 ; PNG, 1k ; downloaded 2026-11-10 14:27 ; used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/grass_medium_01/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| textures/grass_medium_01_alpha_1k.png | 648718 | 711a8e49af758d6a6ce1f610db858899a27be19da6d1866bd35c13bc7b8ffeff | https://dl.polyhaven.org/file/ph-assets/Models/png/1k/grass_medium_01/grass_medium_01_alpha_1k.png |

### grass_medium_02: its Alpha map (the cut-out of the leaf cards; not in the glTF's own file list)
https://polyhaven.com/a/grass_medium_02 ; PNG, 1k ; downloaded 2026-11-10 14:27 ; used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/grass_medium_02/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| textures/grass_medium_02_alpha_1k.png | 110617 | 15976877b3dbd22cd496a9549f1eb7d86710846a3631fb87eedbf046519e339f | https://dl.polyhaven.org/file/ph-assets/Models/png/1k/grass_medium_02/grass_medium_02_alpha_1k.png |

### shrub_03: its Alpha map (the cut-out of the leaf cards; not in the glTF's own file list)
https://polyhaven.com/a/shrub_03 ; PNG, 1k ; downloaded 2026-11-10 14:27 ; used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/shrub_03/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| textures/shrub_03_alpha_1k.png | 79069 | daef00278879a024fd05216aaa1376067a5f25f1b911d08d9bbdc50fda4a0d66 | https://dl.polyhaven.org/file/ph-assets/Models/png/1k/shrub_03/shrub_03_alpha_1k.png |

### island_tree_02: its Alpha map (the cut-out of the leaf cards; not in the glTF's own file list)
https://polyhaven.com/a/island_tree_02 ; PNG, 1k ; downloaded 2026-11-10 14:27 ; used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/island_tree_02/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| textures/island_tree_02_leaves_alpha_1k.png | 57438 | f4341f147988dbe6b58d9ca841a8f0e4bcff25bc40d05f9877da82006d489c39 | https://dl.polyhaven.org/file/ph-assets/Models/png/1k/island_tree_02/island_tree_02_leaves_alpha_1k.png |

### pachira_aquatica_01: its Alpha map (the cut-out of the leaf cards; not in the glTF's own file list)
https://polyhaven.com/a/pachira_aquatica_01 ; PNG, 1k ; downloaded 2026-11-10 14:27 ; used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/pachira_aquatica_01/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| textures/pachira_aquatica_01_leaves_alpha_1k.png | 68381 | 2021600eca558c0b38d342168f0086550143fc7f676113b3dc5b47f56f4e3a82 | https://dl.polyhaven.org/file/ph-assets/Models/png/1k/pachira_aquatica_01/pachira_aquatica_01_leaves_alpha_1k.png |

### moss_01: its Alpha map (the cut-out of the leaf cards; not in the glTF's own file list)
https://polyhaven.com/a/moss_01 ; PNG, 1k ; downloaded 2026-11-10 14:27 ; used by B-258 part 3 (the frame)

| File (under blender/vendor_cc0/moss_01/) | Bytes | SHA-256 | URL |
|---|---|---|---|
| textures/moss_01_alpha_1k.png | 85174 | 00da5c2d0164338c2330587737ff65cefb5575de0c7019ae20bd6f60976608c0 | https://dl.polyhaven.org/file/ph-assets/Models/png/1k/moss_01/moss_01_alpha_1k.png |
