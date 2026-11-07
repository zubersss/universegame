# BLENDER STATUS
Updated: 2026-11-07 02:3x · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
LEAD cycle 253 order (lock-free; UNITY's PlayMode halves + captures hold the lock; I file my want when UNITY takes the lock for half B, D-039; under ~100 MB while its Editor runs):
1. B-138 edge audit: DONE 02:3x (836f558): coordination/reports/blender/edge_audit_2026-11-07.md, tool blender/scripts/edge_audit.py (read-only, 55 MB, 4 s). 20 sheets, 0 offenders; rig parts (flora 44, Pilgrim 11, gauges 6) none cut; 11 single images clear (a base pivot leaves the bottom to its line: the escape sign's post). No re-export needed.
2. B-135 + sand dry run: DONE 02:3x. The ground strip set with sand into a scratch tree: grass / soil / stone PNG and json byte-identical to Art, sand new (540x152, 63 KB); joins 0.63 / 0.62 / 0.81 / 0.67, silhouette identical on 64 edges. B-135 rows vs render.py: build_pike / _shark / _squid, pivot [0.5, 0.5], swim cap 12-16, review on the exported coast sea layers 0-1.
3. B-137 Sun parts preview: NEXT (memory-measured first; the r 160 design run peaked at 325 MB, so the parts preview runs at a smaller design scale lock-free or waits for my slot).
4. B-139 Mars design prep (palette check, five faceless plants, canyon + storm backdrop studies, creature re-ink list; previews only when free RAM allows).
5. B-136 Hadal Maw design (rig set).
Next slot (queue #2 after UNITY's captures, <= 15 min): `tools/blender_render.ps1 creatures/earth/pike,creatures/earth/shark,creatures/earth/squid,terrain/earth/ground_strip_set`.

## Last completed
- 02:15:20-02:21:08 QUEUE #2 SLOT (one heavy lock, 5.8 min, released; taken under D-112: free lock, no UNITY want until 02:16:44; LEAD confirmed):
  - B-134 EXPORTED (27143e1): log "OK characters/surveyor/side_b | v3 sheet 1956x1172 396KB, 56 frames 192x192 @12fps (dig 10, build 10, surprise 12, jetpack 10, climb_in 14) | ink outer 2.0-3.0px inner 1.0-1.5px | palette 100.0% | boxes not x: motion,idle,original,style | 232.8s | peak 535MB". json: pivot [0.5, 0], 10 columns, a `hatch` socket on all 56 frames. Source sources/characters/surveyor_side_b.blend. Review review_b134_surveyor_side_b.png.
  - B-133 EXPORTED (27143e1): "OK backgrounds/earth/forest | layer0 2048x1024 2324KB seam 0.87, layer1 2048x640 1025KB seam 0.43, layer2 2048x384 561KB seam 0.52 + forest.json | 33.9s | peak 755MB"; "OK backgrounds/earth/coast | layer0 2048x1024 2313KB seam 0.85, layer1 2048x512 703KB seam 0.63, layer2 2048x384 571KB seam 0.50 + coast.json | 30.8s | peak 792MB". All six layers pixel-identical to the accepted previews rolled to their quiet column. Reviews review_b133_earth_{forest,coast}.png (export) + review_b133_earth_{forest,coast}_preview.png rebuilt from the rolled layers (1080p at 1x; the coast now on sand).
- 01:45:53-01:54:10 B-132 EXPORTED (0f9e0ab; log OK x3, peak 519 MB; eight stag / wolf v2 files removed as dry-run); verified cycle 252.
- 02:0x-02:1x B-133 / B-134 dry run (stub-layer export path; side_b row vs the sheet / socket path); coast sand strip (158484a).
- 00:5x-01:1x B-131 export wiring (5650912): see Ready for review.

## Ready for review
- B-131 export wiring (5650912): `props/common/camp_set` exports the six props (<= 512^2 each, colour + json, D-117) and removes their 24 v2 files; dry run passed. Waits for U-113.
- B-134 (27143e1) and B-133 (27143e1): exported, see Last completed.
- B-135 PREVIEWS (9c18daa) ACCEPTED cycle 253: blender/preview/review_b135_earth_{pike,shark,squid}_preview.png, each 1x in the coast sea (B-133 layers 0-1) with the surveyor beside on the panel floor.
  - pike 128x80 frames, sheet 1976x332: green duck-bill body with golden spots, pale belly, back tone, lateral-line dashes, fin rays, forked tail; idle 8 (hover, fin ripple, blink), swim 12 (the wave runs to the tail), react 8 (dart: stretch 1.25, eye-pop, speed lines), bump 8, flee 12.
  - shark 224x128, sheet 2048x788: round grey (sky mid / deep back), countershaded belly, gill slits, closed smile, round eye; idle 10 (glide), swim 14, react 8 (turns away), bump 10, flee 12.
  - squid 320x144, sheet 1940x1476: soft red mantle with fins, collar, chromatophore specks, deep spots, one big eye, eight hose arms + two club tentacles with sucker dots; idle 12 (arm curl wave), swim 12 (two jet pulses: mantle squash 0.82 / stretch 1.18), react 10 (a round ink cloud + eye-pop), bump 10, flee 12 (three fast jets).
  - all: pivot [0.5, 0.5]; swim 12-16 at index 1 (Creature.cs's walk slot), react 2, bump 3, flee 4 by name; ink 2.0-3.0 / 1.0-1.5 px, palette 100 %, no frame touches the 2 px edge (bottom included); closed mouths or a round "o", no teeth.
  - Water-floor check (the card's replacement for the ground check): deepest ink below the pivot over all frames: pike 0.38 m, shark 0.87 m, squid 0.70 m. UNITY keeps the pivot at least that far above the sea floor.
  - Fixed on the way: the pike's dart speed lines and the shark's turn-away / bump tilts crossed the frame edge (lines start nearer, tilts softened a third, shark frame 112 -> 128 tall).

## Handoffs (unrouted only)
-> UNITY (B-132, exported 0f9e0ab): delete the eight .meta files of the removed stag / wolf v2 files (stag.glb, stag_normal/_mask/_emission.png, same for wolf); creatures/earth/bear is a new key (no SpeciesSpec yet: Bible §7.1 "Brown bear (territorial)"; under D-087 its react is the rear-up + huff). The sheets are drawn about 1.5 m long x 2.0 m tall (stag), 1.2 x 1.0 m (wolf), 2.1 x 1.3 m (bear); the v2 SpeciesSpec sizes were 1.9x1.6 and 1.5x0.9.
-> UNITY (U-113, D-117, for the tests): B-131 jsons as they will export: frames pad 128x48 / wall 64x176 / door 88x176 / smelter 112x192 / crate 80x72 / lamp 64x160 at PPU 64; pivots [0.5, 0.208333], [0.5, 0.056818], [0.5, 0.056818], [0.5, 0.052083], [0.5, 0.138889], lamp [0.32, 0.0625]; door 3 cols x 2 rows, smelter 4 x 2, lamp 2 x 2, the rest 1 frame with "animations": []; extra fields tile, module_m (2.0 / 1.0), interactable, ground_line_px, squash_root false. The 24 .meta files beside the removed v2 files are yours.
-> UNITY (U-115, B-134 exported 27143e1): characters/surveyor/side_b plays by clip name (dig, build, surprise, jetpack, climb_in); climb_in: move the root up the fin-leg over frames 0-7, then put the `hatch` socket (1.0, 1.05 m from the pivot, every frame) on the Pilgrim door socket.
-> UNITY (B-133 exported 27143e1): backgrounds/earth/forest and /coast load by ConfigureFor("earth", "forest" / "coast"); CartoonStage still pins EarthScene = "plains", so biome selection is yours. Their .meta files are yours.
-> UNITY (B-135, after export): swimmers have pivot [0.5, 0.5]; the clip at index 1 is swim; keep the pivot >= 0.38 / 0.87 / 0.70 m (pike / shark / squid) above the sea floor; no Water habitat exists in SpeciesSpec yet.
-> UNITY (C2, routed to U-110): every Earth plant carries "biomes".
-> UNITY (B-128, on import): def.icon = "icons/<key>/base" for soil, grass, regolith, snow, mercury_regolith, mercury_basalt, sulfide, tessera.

## Blockers
none.

## Proposals (undecided only)
- -> LEAD (Sun disc, C2 candidate; preview blender/preview/review_sun_disc_design_preview.png): export as a rig, not a sheet: the game's Sun is r 900 px (1800 px across), so sun/disc_color.png static at 0.5x (1024^2, drawn 2x), sun/flames_color.png one ring part Unity rotates slowly and pulses, sun/corona_color.png a 512^2 wash scaled 4x, two prominence parts on limb sockets, in a disc_rig.json like Saturn's rings.

## Rules I keep (from slips this session)
- A lock check is its own call; Blender starts only in a later call after reading a clear result (D-073).
- A want is filed only after the other role takes the lock (D-039); a rank is live only while a want or lock is on file (D-112).
- Light work while another role's heavy job runs: <= 300 MB extra (D-109). fakegp sheet previews ~100-200 MB; FFT backdrops and full review rebuilds ~250-300 MB go in my slot.
- Measure every new export path's frames against the 2 px edge before the export (the B-131 lamp, B-134 dig/zip and B-135 pike/shark frames failed it).
- Measure a new preview's memory before running it beside the other role's job: disc / backdrop work at 2x supersampling is 250-350 MB, not the ~150 MB of a fakegp sheet.

## For USER_ACTIONS
none.

## HeavyJobLock
none held (queue #2 slot 02:15:20-02:21:08 released); no want on file until UNITY's PlayMode halves A and B have run (D-039).
