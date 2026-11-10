# U-211: what the game allocates, by scene (2026-11-10, written 12:50, readings 3 and 4 and the save's time added 13:03)

Measure: Unity's "GC Allocated In Frame" (every thread), after a control (a 65 536 B array read 65 858 B), less the Editor's and
the test runner's own floor read in the same run. Causes: the Editor Profiler's hierarchy read back by sample path
(AllocByMarkerTests, run alone at 11:5x and 12:40). All figures are Editor figures (batch mode, about 1 ms a frame unless a
row says "60 fps step"); the game's managed code is the player's own, the Editor adds its floor and a few Editor-only paths,
named where they appear.

## 1. The gate's rows, before and now

Before = build 0.6.3's report (one window of 300 frames from the frame the scene is ready: arrival and steady play mixed).
Now = the gate's two rows a scene: "settled" (the Bible's row: 300 frames, 600 frames after the scene is ready, the ship held,
the terrain settled) and "first 300 frames after the scene is ready" (arrival; reported, no limit yet).

| scene | before, 0.6.3 (08:36 / 08:53) | settled now (11:38 / 11:51 / 12:59 / 13:02) | arrival now (11:38 / 11:51 / 12:59 / 13:02) |
|---|---|---|---|
| Earth | 166 / 166 B | 522 / -777 / 574 / 470 B | 644 / -647 / 858 / 806 B |
| Earth C0 | 402 / 166 B | 470 / -725 / 470 / 522 B | 828 / -359 / 652 / 772 B |
| Space | 619 985 / 208 577 B | 598 / -881 / 470 / 418 B | 160 867 / 525 598 / 570 015 / 526 917 B |
| Mars | 131 818 / 79 163 B | 6 174 / -1 143 / 104 / 104 B | 75 649 / 134 248 / 82 176 / 72 689 B |
| Mars dust storm | 7 284 / 1 300 B | 418 / -829 / 104 / 522 B | 1 256 / 5 825 / 1 264 / 1 368 B |
| Mars FX peak | 822 / 1 084 B | 989 040 / -1 143 / 156 / 208 B | 7 180 / -43 / 1 204 / 1 252 B |

READINGS 3 AND 4 (12:59 and 13:02, gate_reading3.md / gate_reading4.md) are the two on the final code (D-152): part 2's
fixes in, the floor the least frame of the run times 300 (290 B a frame, 87 000 B in both; the floor window's own sum was
the same 87 000 B). BUDGETGATE GREEN both times: every settled row between 104 and 574 B against the 1 KB limit, in all six
scenes.

- The 11:38 reading's two reds (Mars 6 174 B, FX peak 989 040 B) were the terrain streaming under the ship still descending in
  the "settled" window, not the scenes' steady play: from 11:51 the ship is held and the terrain waited for, and every settled
  row is at the floor. The effects pool allocates nothing (two windows with the pool full, 48 alive: 0 B of the game's).
- The negative figures at 11:51: the floor (every root object inactive) read about 1 KB higher than a live scene's window in
  that run. From 12:59 the floor is the least frame of the run times 300, and no row reads under it.
- Readings 11:38 and 11:51 are in gate_reading1.md / gate_reading2.md; they predate part 2's fixes below.
- Space's arrival figure moves threefold between readings (161 / 526 / 570 KB) because the art still loading lands in the
  window's first frame in one run and before it in another (section 3).

## 2. Causes found and fixed

| where | what | size | state |
|---|---|---|---|
| TerrainStreamer.CurveAt (every scene with smooth ground) | a delegate made a call | 6-115 KB a frame while streaming | fixed, in 0.6.3 |
| ArtMaterials.SocketFor | a tuple key boxed a call | 88 B a frame | fixed, in 0.6.3 |
| SpaceMap.Landed / LandedFlag (Space) | the flag's name built each frame | 161 B a frame | fixed (1482880b) |
| SkipDrive (Space) | the well's refusal line built each physics step | 116 B a step | fixed (1482880b) |
| TerrainStreamer wall tops (Mars, any planet entered second) | the tops array made in a frame of play | 484 KB in one frame | fixed: made behind the cover, handed on between planets (1482880b) |
| SmoothGround.Build (every rebuild: a dug cell, a chunk streamed in, the decor arriving) | a closure and up to four delegates a build | 1 272 B a rebuild; 66 KB in Mars' arrival window (52 rebuilds) | fixed (4cbd79fb): at 12:40 the path is gone from that window. A build that first uses a texture still makes its material (0.4-1.6 KB, once a texture) |
| GroundContour's trace scratch | a set a chunk (33 KB at the chunk's making, grown again a pooled chunk) | 33 KB a chunk | fixed (4cbd79fb): one static set |

## 3. What still allocates, by path (12:40, after the fixes)

Steady play, every scene: nothing of the game's. What is left in every frame is not ours: the test runner 40 B a frame and
Unity's 2D Animation package 32 B a frame (DeformationManagerUpdater.LateUpdate: it would run in the player too).

Arrival:

| window | bytes | by path |
|---|---|---|
| Space, first 281 frames | 548 647 B, of which 527 013 B in frame 0 | Addressables' DelayedActionManager.LateUpdate 364 572 B (loads completing and their callbacks); SpaceMap.LateUpdate 55 468 B (the map built on its first frame); one UI Text's first enable 54 032 B; TransitionDirector.Launch's last step 43 873 B (the autosave runs there); the floor's 20 KB |
| Space, 300 frames later | 20 016 B | the runner and the package only |
| Mars, first 281 frames | 90 737 B, of which 65 309 B in frame 0 | TransitionDirector.Enter's last step 65 237 B (the autosave); Terrain.Outline.Nodes 2 688 B; TerrainStreamer.Update 2 580 B once; the floor's 20 KB |
| Mars, 300 frames later | 22 752 B | the floor, and Terrain.Outline.Nodes 2 688 B (384 B a chunk) |
| Mars as the game runs, 4.7 s at a 60 fps step, window 1 (the ship still streaming new ground) | 1 216 402 B | Terrain.Outline.Contour 779 200 B in 11 frames (the most 123 008): a pooled chunk's fill lists growing on its first busy ground, about 70 KB a chunk; SmoothGround's shared build lists growing once (Bands 319 648 B, Body 32 800 B, Back 30 984 B); Editor-only material drawers 28 200 B |
| the same, windows 2 and 3 | 29 480 / 20 618 B | the floor; a material's first use 1 962 B; nothing else |

My 11:5x guess for Space ("the frame the transition ends in is the autosave") was mostly wrong: the autosave is 44 KB of
Space's 527 KB. The larger part is art still arriving (365 KB) and the map's and a label's first frame.

## 4. Found beside the rows: what a TRANSITION allocates (behind the iris, not in any gate row)

| transition | bytes in its last 300-520 frames | largest paths |
|---|---|---|
| launch (Earth to Space) | 5 902 950 B | DockingBay.Start: its UI Texts' first enable (Text.OnEnable) 4 569 108 B in one frame, its other components 0.7 MB |
| entry (Space to Mars) | 17 804 701 B | CraftingPanel.Start 5 507 436 B; CataloguePanel 1 789 884 B; TerrainChunk constructors 1 511 328 B; SellPanel 1 284 556 B; InventoryPanel 1 120 504 B; loads 2.5 MB; SkillTreePanel 426 660 B; HudToolSlot 385 480 B; SideHud 324 192 B |

Nearly all of each panel's figure sits under one path, UnityEngine.UI.Text.OnEnable: a legacy UI Text's first enable. The one
Text enabled alone in Space's window read 54 032 B, so a Text looks like about 54 KB of managed memory; I have NOT counted
the panels' Texts nor found what inside Unity's Text allocates it, and I do not know that the player pays the same (these
are Editor figures). The panels are built afresh, closed, on every planet entered and every launch: about 10 MB of the
entry's 17.8 MB and 4.6 MB of the launch's 5.9 MB. It is behind the iris, so no frame of play pays for it; it is transition
time and heap growth on a machine short of memory. The TerrainChunk figure was taken with part 2's static scratch already in.

## 5. Not yet measured

- Creature AI's first-time frame (about 1.4 ms once a process, no allocation): not named; CreatureDirector.LastAiAllocBytes
  still reads the dead counter.
- A dug cell's first opening (116 862 B, then 19 450 B, then 1.1-1.3 KB a cell at 11:0x): not re-read since the rebuild fix.

## 5a. The autosave's time (12:56, measured)

The autosave runs on the main thread in the FIRST FRAME AFTER THE IRIS HAS OPENED (TransitionDirector raises Completed after
iris.Open; SaveSystem saves on it), and every five minutes of play. Its steps, named for the Profiler, in the Editor with the
Profiler recording, on this machine's disk (one reading each; disk times move):

| after | the save, whole | terrain files | state.json | backups rotated | capture | bytes |
|---|---|---|---|---|---|---|
| the launch (Earth's edits written) | 61.8 ms | 44.7 ms | 6.6 ms | 3.9 ms | 6.7 ms | 43.8 KB |
| the entry to Mars | 36.9 ms | 6.9 ms | 17.6 ms | 12.2 ms | 0.1 ms | 65.3 KB |

So the first frame of play after every launch and every entry is two to four frames long at 60 fps. The first save of a
process pays one-off costs in it (the launch's capture 6.7 ms against 0.1 ms; the binary writer's first use), and the
terrain file's time is the disk's. Not read in the player.

## 6. Proposals (LEAD rules)

1. THE ARRIVAL ROW'S LIMIT. Frame 0 of the window is the frame the transition ends in; it holds the autosave and whatever
   art is still landing. I propose the row be read from frame 1, limit 16 KB a 300 frames of the game's own, judged on the
   larger of two readings; and frame 0 reported on its own line, no limit. On today's figures with frame 0 out: Space about
   1.5 KB, Mars about 5.3 KB, storm 1.3-5.8 KB, FX peak up to 7.2 KB (its frame 0 not yet split out), Earth under 1 KB: all
   green, and a new per-frame or streaming allocation in the first seconds would show.
2. THE AUTOSAVE BEHIND THE IRIS: raise the save just before iris.Open instead of after it (the scene is loaded and the ship
   placed by then). It takes 37-62 ms (section 5a) and 44-65 KB out of the first frame of play after every transition. One
   event in TransitionDirector, one subscription in SaveSystem. What I must check before it is safe: after a launch the old
   planet's scene is still unloading during the iris, so the save's capture must not read the departed surveyor's position
   as if it were current. The five-minute autosave in mid-play keeps its 37-62 ms frame either way; writing the files off
   the main thread would cure both, and is a larger change (the load, the next save and the tests read those files).
3. THE PANELS (section 4): build each closed panel on its first opening instead of at the scene's start, or keep them across
   planets. It is the largest single allocation in the game by two orders, but it is behind the iris: I would put it on its
   own card after U-212 / U-213 with the transition's seconds measured before and after, not into U-211.
4. A CHUNK'S FILL LISTS (70 KB a pooled chunk on its first busy ground; about 0.8 MB in the first seconds over new ground,
   once a planet): the contour lays a quad a full quarter-metre sub-cell; laying them in runs along a row would cut the
   vertices severalfold (less memory a chunk, a shorter rebuild, smaller meshes). It changes the fill's triangles, not its
   shape; it wants its own check against GroundFieldTests' areas and a capture. Not started.
