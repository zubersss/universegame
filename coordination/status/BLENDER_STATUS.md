# BLENDER STATUS
Updated: 2026-11-07 11:13 · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
11:02-11:12 GAP (UNITY's chains ended 11:02; LEAD's pre-granted plan): lock-free, one measured run each - the Saturn smoke test (all five scenes build, 273 MB), flora 301, floes 175, helium_jelly 194, hex_drake 213, floe_moth 192, ringmite 191 (problems none in all), the Hydra 59 (rig valid, Grand), the aerostat review 127 after two fixes (f7fda8d0: the cell frame 72x152, the hook 0.9x with wider prongs); 11:06:31-11:11:03 SLOT (one lock, 272 s, 668 MB, released; UNITY told): the five Saturn deck studies - the hexagon's tilted rings + Cassini gap, deep (CRUSH + spirals), deck2 (the trap rig, drops), deck3 read; the ring line edge-on hid at the top of the sky and the Hexagon walls read as searchlight beams -> fixed in code (db4039b8), deck1 / deck2 / hexagon need a ~3 min re-run. B-158 Uranus: palette ACCEPTED (D-142, in PALETTES), flora source (0333deb8), floe strips (2ab4a982, checked 49 MB: joins 0.89 / 0.44). Next code: the Uranus scenes (three lit sets), creatures, the Colossus, props.
D-142 (LEAD): the Uranus three-set approach (sun_left / sun_right / night + a shared survey layer0; UNITY cross-fades) + the Uranus palette ACCEPTED -> in PALETTES['uranus'] + the ui/palettes/uranus row. Next code: the Uranus flora, floes, scenes (the three lit sets), creatures, the Colossus, props.
10:58: B-158 Uranus paper part DONE: the palette ALL PASS (ef1553ae: cyan fog, cold white, one ember accent, dimmer than Saturn) + c2_uranus_designs.md (52c52ee5); one proposal (the lit variants sun_left / sun_right / night per deck). Still waiting for UNITY's chain to end for the Saturn gap plan.
LEAD cycle 268: the Vortex Whale ACCEPTED; the Saturn palette ACCEPTED (D-141: in PALETTES, setdefault dropped, ui/palettes/saturn row - c91d7c16); B-158 Uranus Ready after the Saturn previews; the Mercury rows export right after UNITY's U-123 commit, one slot each. 10:45 Mercury readiness: B-148's ground strips written (fae9b7e2: white regolith + slate side, joins 0.78 / 0.71, palette 100 %, scratch export OK) - B-148 / B-149 / B-150 rows complete. Next code: B-158 palette + notes; the Saturn gap plan when UNITY's chain ends.
## Last completed
- 07:09:10-07:14:09 gated numpy runs under one lock (above).
- 05:44:51-05:45:52 SLOT (wrapper): B-131 props/common/camp_set exported, 24 v2 files removed (log OK, 60.8 s, peak 727 MB).
- 05:33:58-05:38:24 SLOT (wrapper): B-141 backgrounds/mars/canyon + storm exported (log OK x2, peaks 694 / 761 MB).
- 05:30:22-05:30:51 SLOT (wrapper): B-140 flora/mars/rigset + terrain/mars/ground_strip_set exported (log OK x2).
- 05:24:23-05:26:35 SLOT (wrapper): B-136 creatures/earth/hadal_maw exported (log OK, 115.6 s, peak 676 MB).

## Ready for review
- B-146 UI: review_b146_ui_preview.png (panels, switch, three title cards). B-147: plants, four creatures, vent_mouth den (previews in blender/preview/review_b147_*).

## Handoffs (unrouted only)
-> UNITY (B-132, exported 0f9e0ab): delete the eight .meta files of the removed stag / wolf v2 files; creatures/earth/bear is a new key (no SpeciesSpec yet; under D-087 its react is the rear-up + huff).
-> UNITY (B-133 exported 27143e1): backgrounds/earth/forest and /coast load by ConfigureFor("earth", "forest" / "coast"); CartoonStage pins EarthScene = "plains", so biome selection is yours.
-> UNITY (B-135): swimmers have pivot [0.5, 0.5]; the clip at index 1 is swim; keep the pivot >= 0.38 / 0.87 / 0.70 m (pike / shark / squid) above the sea floor.
-> UNITY (U-118, D-126): creatures/mars/tube_lurker idles and reacts behind props/mars/tube_mound on the same pivot (mound json den_for, the creature row den); dustskater + scree_stalker exports remove their v2 files (replaces_v2).
-> UNITY (B-128, on import): def.icon = "icons/<key>/base" for soil, grass, regolith, snow, mercury_regolith, mercury_basalt, sulfide, tessera.

## Blockers
none.

## Proposals (undecided only)
none (the lit variants ruled in D-142).

## Rules I keep (from slips this session)
- While another role holds the lock, run only jobs already measured <= 150 MB; a new job (or a new whole preview) is first measured in a free gap, never estimated from its parts.
- A lock check is its own call; Blender starts only in a later call after reading a clear result (D-073). The same for RAM: read it in its own call, then decide.
- A want is filed only when the queue says I am next after the running job; never while the other role's multi-lock job is between locks.
- Light work while another role's heavy job runs: <= ~150 MB; lock-free otherwise <= ~300 MB (D-109); under 0.3 GB free, code only. Measure a new path on one part / a few frames first.
- Measure every new export path's frames against the 2 px edge and the ground line before the export.
- Short jobs run in the foreground; no background waiters (the harness reaps them under memory pressure): check the locks folder each turn.

## For USER_ACTIONS
none.

## HeavyJobLock
none held, no want on file (the Saturn studies slot released 11:11:03).
