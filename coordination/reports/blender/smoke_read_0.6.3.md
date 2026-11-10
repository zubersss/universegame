# Art read of 0.6.3's player smoke (BLENDER, B-245) — READ 2026-11-10 11:0x-11:2x (the skeleton written 09:5x, before the smoke)

**VERDICT: first hour GO for 0.6.3 as built; one gap: the smoke has no still of the dig landing (section 5).**
Sections 1 and the "Expected" columns are the skeleton, written before the smoke; sections 2 (last column), 3, 4
and 5 are the read.

Source (when it lands): `coordination/reports/unity/smoke_0.6.3/`. B-228's method: every shot read at 1:1 with the read
tool only (no lock, no interpreter); the changed shots at 4x (`blender/scripts/crop_png.py` through `tools/blender_locked.ps1`,
only when no lock or want of UNITY's is up; crops named `blender/preview/crop_smoke063_<shot>_<what>_4x.png`). LEAD cuts the
4x crops of every tool-in-hand frame and the dig strips (`coordination/reports/unity/u209/`); my read is the smoke.
Art defects only (wrong keys, placeholders, v2 leftovers, seams, floating or sunk art, palette breaks, weapon-like or
face-like reads, illegible ink); HUD layout goes to UNITY via LEAD. The owner's page waits for this read and it outranks
everything else of mine that hour. Order: section 1, then section 2's rows on their shots, then every other shot for
regressions. One row per shot in section 3, written as each is read; a finding gets a number (H1, H2, ...) only when I can
name the shot, the place in px and what is wrong.

"Expected" is what the commits, the cards and LEAD's rulings say should show. It is not an observation: every row is
open until its shot is read. The shot names are 0.6.2's (BuildSmoke.cs and BuildSmokeD1.cs carry the same list today); a
shot UNITY adds or renames gets its row when the folder lands.

NOT in 0.6.3 (the board, 11-10 09:1x: U-211, U-199, U-197, U-198, U-210, U-208 come after it; LEAD confirmed 10:0x), so NONE of it should show:
the collapse and its rubble (fx/rubble/base is imported, unused); the five Grand catalogue icons (B-247; imported, the
panel reads them in U-210); the giants' close view (B-243's strips); the v6 surveyor and scenery (previews only); B-247's
parked repaints. If any of it shows, that is a finding.

## 1. What changed since 0.6.2 (read first)

### 1a. The dig as one motion (U-209 + B-246): every shot with a dig tool in hand

Shots: smoke_47 first dig, smoke_65 shovel mid-swing, smoke_66 shovel flick, smoke_3b Earth dig, smoke_54-58 (pack full,
jetpack, ladder, winch, grapple), smoke_67 tool slot Beam, smoke_18 Mars shelter (the Beam), smoke_31 scoop, smoke_37
pocket dug, smoke_42 valley, smoke_2 / 2b (the shovel at rest), smoke_46a-d (the walk), and any other frame where a tool
is held. For each, the six things below; "n/a" where the frame cannot show one.

| What | Expected in 0.6.3 | Art / code | Check (1x, then 4x) |
|------|-------------------|------------|---------------------|
| THE BRACKETS (the reticle) | Whenever a dig tool is in hand: four hand-inked brackets on the brush's circle (0.9 m radius and up) on smooth ground, or on the 1 m cell on block ground, with a pip on the contact point. In reach: white. Clamped at the reach's edge: mustard, the brackets 0.09 m wider. Nothing to dig: red, 0.2 m wider, no pip. Dimmed to 40 % after 1.5 s of a still cursor. Unlit. Hidden in menus and transitions | fx/dig_reticle/base (B-246, b351f2d8); RigToolView | the brackets sit ON the circle or the cell (not inside, not floating off the ground's face); their ink about the world's line weight (not heavier, not hairline); crisp at 4x (no upscale blur); the state's colour reads on tan soil AND on grey stone AND on a dark back wall; not darkened underground; nothing of it over a hint card, the tool slot or a title card; it reads as a surveyor's mark, NEVER as a gun sight (D-087): no cross-hair, no centre dot inside a ring; no face (two brackets and the pip as eyes and a nose at 2x) |
| THE CRACKS (the chip stages) | A target being worked shows crack stage 1, 2 or 3 growing from the contact point (round decal with the brush, cell decal inside its cell on block ground), tinted by the dug cell's tone as the clods are. Drawn only on the ground's side of the face. Kept 1.5 s, then healed | fx/dig_chip/round, fx/dig_chip/cell (B-246); DigFeel.Chip; D-190's tone_hex | the cracks start at the blade's tip, not at the cell's centre or in the air; nothing of the decal over the open air beside the face or over the grass band; inside one cell on block ground (nothing crosses its edge); the tint is the soil's (brown-tan on Topsoil, grey in Stone), no cream untinted crack; a stage keeps the one before; no face or glyph in the crack pattern at 2x-4x; not a spider's web or a bullet hole (a round star of cracks round a dark dot) |
| THE SWISH | On a downward or an upward swing: a three-drawing smear arc behind the blade, ending on the blade at the contact drawing. None on the forward clips | fx/shovel_swish/base (B-246); pivoted on the contact drawing's tool origin | the arc's end meets the blade (not a detached crescent); it trails BEHIND the swing; pale and thin, read after the tool; gone by the follow-through; not a blade's flash (nothing sword-like) |
| THE BODY'S CLIPS | The swing by direction from side_dig: dig_down, dig_fwd (dig_fwd_near for a target under about 1 m), dig_up: five drawings at 12 Hz, the contact on drawing 2 with the arm at full reach and the weight in it. The shovel rides the glove with the fist over it, drawn in front of the body, and its blade's tip is ON the contact point on the contact drawing (the tool slides back through the glove for a near target; the body lunges up to 0.25 m for a far one). The surveyor faces the target; a lean in and a small recoil | characters/surveyor/side_dig + props/rig/grip_fist (B-246, 56bbfa4d; dig_up slide_max 0.75, d0899819); RigToolView, DigPose | the blade's tip within a few px of the scoop / the crack's origin on a contact frame; the glove closed on the shaft (no shaft through the palm, no gap between fist and shaft, no second hand drawn under the fist); the dig sheet's head, helmet and proportions match the side sheet's (no pop in size or line weight between a walk frame and a dig frame); the feet on the ground through the lunge (no slide into the air, no sinking); no limb through the body; knees and back bend with the stroke; a tool, nothing weapon-like (no overhead two-handed chop read) |
| THE TOOL AT REST | After the last swing: the READY pose (the tool low in front of the body, the fist over it) for 1.5 s, then STOWED behind the body (the shaft hidden by the torso, the blade up behind the helmet). No cursor tracking while the button is up | side_dig.json's carry poses; RigToolView | stowed: the blade behind the helmet does not read as a horn, a crest or an antenna, and does not hide the face; it follows the walk's bob (smoke_46a-d) without sliding off the back; ready: the tool does not cut through the thigh or the ground; no shovel held up like a flag (0.6.1's F18) on the jetpack, ladder, winch or grapple |
| THE BEAM | The aim pose by direction (aim_up, aim_up45, aim_fwd, aim_down45, aim_down), the ray from the tool to the contact, and at the hit a six-drawing glow with flying grit; the cell opens when the work completes | side_dig's aim poses; fx/beam_contact/base (B-246); the ray | the arm points along the ray (no elbow break, no ray from the chest); the glow sits ON the ground's face at the ray's end; grit flies away from the surface; a mining tool, never a gun (D-087): no muzzle flash at the tool, no bolt, no impact burst that reads as an explosion; the ray's tone and the glow's agree |

Also for every dig frame: the debris leaves from the contact point along the follow-through (clods in the fill's tone,
the dust low and pale behind them, as accepted in 0.6.2); the scoop still reads as a hole with its back wall.
Known limits to expect, not findings: dig_up clears a 2.0 m ceiling, not a 1.8 m tunnel (the glove would pass into the
roof: a lower glove drawing is owed if a shot shows it); the forward pair is picked by the smaller miss, so a mid-range
target may show either clip; sounds are placeholders until U-198 (not mine).

### 1b. The other changed shots

| Shot | What should show in 0.6.3 | Art / code | Check |
|------|---------------------------|------------|-------|
| smoke_10 waystation | THE PILGRIM ON ITS CRADLE (0.6.2's G1): the ship as its own sprite standing on the cradle's hazard plate at layer1.json's "ship_ground", in front of the clamps and behind the railing; the v3 bay around it as in 0.6.2 | U-192 (9e3bc26e, 936dcf05); B-223 | the ship's feet ON the deck plate at the cradle's centre (about x 660 of 1920), not floating and not sunk; drawn once; the clamps' jaws beside the fins, not through them; the ship's ink weight and scale agree with the bay's; the porthole, BAY 2 and HALCYON FREIGHT not covered by it; the market list still inside its panel |
| smoke_11 catalogue | THE SITE ICONS (0.6.0's #17): Camp shows its icon (the pad, crates, a lantern post); every other surveyed Site on the page shows its own icon by label (Earth: Survey archive, Launch complex), an unsurveyed one its silhouette | U-192's Site branch; B-223 camp + B-233's ten (icons/catalogue/<label>) | no empty icon slot beside a "· SITE ·" row; each icon readable at its row size beside its neighbours; the right icon on the right row; ink weight as the creature and mineral icons; no placeholder square. If a rig creature is surveyed on this page (the Hadal Maw): its icon is still one body part (G14, U-210 after 0.6.3): noted, not new |
| smoke_16 Venus station | THE SERPENT AT 1x (0.6.2's G6): the veil serpent drawn at its sheet's size (about 224 px long, a 3.5 m serpent), a gentle drifter clear of the station | U-192 (the scale and the temper); B-224 | at 4x its outline about as heavy as the station's rigging (about 1-1.5 px, crisp), not 5-6 px and soft; it does not overlap or bump the station; the calm eye pair and closed smile still read at that size; nothing weapon-like or menacing |
| a dig in SAND, a dig in BASALT (smoke_38 desert, smoke_4 if a pit shows; Mars wherever the surface is basalt) | The two variant fills have their own back wall: sand's a warm shaded tan with fine ripple bedding, shell fans and pebbles; basalt's dark grey with stacked column joints and bubble trails | B-242 (068a2918); 568634e3, 70220e18 (RGBA32) | the hole reads as a hole against the cream sand / the red-brown basalt; the wall is not the fill's flat copy and not concrete-grey behind sand; no plank read in the basalt's joints; where a trench crosses a fill border the two walls fade into each other with the fills. If no smoke shot digs in either fill: said so, and UNITY's b242/ captures (LEAD viewed them 01:4x) stand in |
| smoke_21 title card, Mars (and Mercury, Venus) | NO PALE BOX (0.6.2's G8, 0.6.1's F14): the camp gull is spawned on Earth only | U-206 (3f3ed7f8) | Mars: nothing at (1342-1386, 660-692) or anywhere 7 m right and 3.5 m above the player; the same look on the Mercury and Venus cards; no other placeholder rectangle on any card. Earth's card keeps its gull |
| smoke_18 Mars shelter | G5'S TWO OBJECTS (a dark rounded lump about 42 px and a tan grooved mound about 62 px behind the Beam's tip, drawn soft in 0.6.2 while all beside them was crisp). Open in U-205: UNITY was to name them and say why they draw from a low-resolution copy; no fix is recorded | U-205 (open part) | a 4x crop of (860-1060, 600-720) again: are both there, are they crisp now. THE NAMES come from the smoke's own log (LEAD 10:0x: UNITY never named them; the smoke prints "[MERIDIAN] smoke G5 near the surveyor" lines): copy the keys and sizes from there into this row. Still soft = still open, with the crop. Also here: the Beam's aim pose and ray (1a) |
| smoke_36 Earth scan X (and smoke_37, 41, 43) | THE POCKET WITHOUT THE SMUDGE (0.6.2's G12): the tier border's wobble is now one long gentle roll (0.4 m, waves 12-30 m long), the same on the fill and the wall: no dark soft-edged region low in the frame, no isolated bumps | U-205 part 3 (7e679a8d) | smoke_36 / 37: nothing at (1500-1920, 980-1080) but the fill and a clean border line; smoke_41: (0-1000, 930-1080); smoke_43: (0-330, 850-1080); the border, where it shows, a single near-straight line that follows the slope |
| smoke_54-58 the shaft | THE WALL'S THREE SEAMS GONE (G2, G3, G4): the wall's tier border one near-level line across the shaft (a tilt of up to 0.6 m is allowed, a trough is not); no hard horizontal step in the darkening; the wall tile's repeat broken (no pebble on one line every 4 m) | U-205 part 3; the walls imported RGBA32 (D-192, 0405d4e1) | smoke_57: no V at (850, 255)-(975, 315)-(1100, 270); smoke_54 / 55 / 56 / 58: no step at y 525 (57: y 690); smoke_55: no pebble column at x 883 (270, 527, 783); the walls' paper grain as fine as before or finer, no blocky compression in the dark tones |
| smoke_3b, 3d, 29, 59, 67 the camp's staged dig | AN OPEN BOWL (G7): the smoke digs from the surface as a player does: the grass band is opened above the pocket | U-205 (the staging) | no closed disc under unbroken grass; the bowl's rim and back wall as a player's scoop (smoke_31) |
| smoke_43 Earth sea | THE SHALLOWS UNDER THE SURFACE (B-225; 0.6.2 still showed a flat pale tint): a rippled light ceiling about 2 m deep under the water line with slanting shafts, and within 40 m of the shore a shallow seabed (sand ripples, shells, sea grass) that fades out as the camera sinks below its ground line | B-225; U-205 part 2 (layer3 128 px, layer4 "shore_m" 40) | the band meets the water line with no gap or double line; the seabed layer does not stand as a flat sand wall behind a swimmer; no hard sand edge in frame; the Hadal Maw still holds off the shallows (F17) |
| smoke_61 Mars T4 room | No red mark on the PACK bar at 0 / 30 (G10) | U-205 (the rooms shot with the pack flights landed) | (1265-1285, 33-43) clean (HUD; a line for UNITY if not) |
| smoke_33 Earth mound | Two bears no longer on one spot (G11): the spawner keeps a body and a half between a creature and its kind (two walking onto one spot later is left as is) | U-205 | no two-headed animal at (1525-1655, 598-680) or elsewhere |

## 2. The 0.6.2 read's findings: expected state in 0.6.3

| # | 0.6.2 finding | Expected in 0.6.3 | Where to look | Read: fixed / still there |
|---|---------------|-------------------|---------------|---------------------------|
| G1 | the bay's cradle empty | fixed (U-192: the Pilgrim on "ship_ground") | smoke_10 | **FIXED**: the ship on the plate between the clamps |
| G2 | the wall's tier border dips in a V inside a shaft | fixed (the border's wobble a long roll, the same on fill and wall) | smoke_54-58 | **FIXED**: one level line across the shaft (y 125 in 54 / 56 / 58, y 285 in 57) |
| G3 | a hard horizontal step in the wall's darkening | fixed (the term eases out) | smoke_54-58 | **FIXED**: no step at y 525 (57: y 690) |
| G4 | the wall tile's 4 m repeat down a tall shaft | fixed (the repeat offset) | smoke_55 | **FIXED**: the pebbles at four different x, no column |
| G5 | two soft Mars ground pieces beside the surveyor | OPEN, expected unknown: never named; the names are in the smoke's log ("[MERIDIAN] smoke G5 near the surveyor") | smoke_18, a 4x crop + the log's lines | **STILL THERE**, same place, still soft (crop g5_18_two_shapes_4x.png: a brown lump of three rounded lobes and a tan mound with dark zigzag points, both in blocks of about 5 px with a thick blurred outline, beside a crisp lamp post: a texture drawn about five times its size). **THE LOG DOES NOT NAME THEM**: its probe (logs/player_smoke.log, lines 59-62) lists what is within 3 m of the surveyor (two shelter walls and the lamp, all from mip 0), and the two shapes stand about 4-5.5 m to the surveyor's left, outside it. Still unnamed: a wider probe (8 m) in the next smoke. My guess only (low): painted detail of a backdrop layer at ground level, or a decor sprite drawn from a small copy |
| G6 | the veil serpent drawn 2.7x its art size | fixed (U-192: 1x of its sheet) | smoke_16, a 4x crop | **FIXED**: about 200 px long, a thin crisp line |
| G7 | the staged camp pocket a closed disc under grass | fixed (the smoke's dig an open bowl) | smoke_3b, 3d, 29, 59, 67 | **FIXED** in all five |
| G8 | a pale flat box behind the Pilgrim on Mars | fixed (U-206: the gull on Earth only) | smoke_21 Mars, Mercury, Venus | **FIXED** on all three cards |
| G9 | a cluster of dark balls in Mars's fill | CLOSED, no fault: terrain/mars/fill_decor_3 (hematite spherules). It may show anywhere in Mars's fill; a lighter tone only if LEAD asks | smoke_21 Mars, 61 | seen again in smoke_21 Mars (1815-1860, 965-1010): closed |
| G10 | a red mark on the PACK bar at 0 / 30 | fixed (the staging) | smoke_61 | **FIXED** |
| G11 | two bears on one spot | fixed at spawn | smoke_33 | **FIXED**: two deer a body apart |
| G12 | a dark soft-edged region low in the frame (F7's residue) | fixed (the long roll); LEAD closed it on u205's shaft, smoke_36's pocket to be seen here | smoke_36, 37, 41, 43 | **MILDER, STILL THERE**: a dark soft-edged region low in the frame in all four, now one smooth roll parallel to the slope: no peaks, no isolated bumps. It reads as the next tier beginning under a wide soft edge (in 54-58 the same border is a crisp line). LEAD's to call closed |

Logged between the two builds (LEAD's and my looks at UNITY's captures), for the same read:

| # | Finding | Expected in 0.6.3 | Where |
|---|---------|-------------------|-------|
| G13 | on Olympus's 31-degree slope the Mars backdrop's near layer continues downward as a flat tone over half the frame | still there (the repaint is PARKED with B-247 until the owner rules on v6); only if a smoke shot stands on that slope | any steep Mars shot |
| G14 | a rig creature's catalogue icon is one body part (the Hadal Maw as a cropped rectangle) | still there (the five Grand icons are imported; the panel reads them in U-210, after 0.6.3) | smoke_11 if the Maw is surveyed |
| G15 | the Venus deck backdrop does not cover the frame: a teal strip about 12 px tall along the bottom, a pale line with a notch along the top | still there (U-191, Ready) | smoke_16, 17 |

Older rows still open in 0.6.2, for the same read:

| # | Finding | Expected in 0.6.3 | Where |
|---|---------|-------------------|-------|
| F8 | Saturn up close: a stepped edge, no bands | unchanged (B-243's strips are exported; the close view is U-208, after 0.6.3) | smoke_7 |
| F15 | a soft upright band where two biome fills meet | unchanged (Backlog) | smoke_41 |
| #1, #4 | Jupiter decks: streaks below the floes, a flat block under them | unchanged (U-191, Ready) | smoke_21 Jupiter, 23-26 |
| #8 | Mercury / Venus stepped block terrain | unchanged (U-177) | smoke_13, 15, 17 |
| #13, #14 | Mars canyon / Mercury twilight / Venus deck continue rows not repeated | unchanged (U-191) | smoke_5, 6, 14, 16 |
| #17 | the catalogue's Camp without an icon | FIXED IN 0.6.3 (the Site branch) | smoke_11 |
| (0.6.2 note) | smoke_18 is named "night_lamp" and shows the day's light | unchanged unless UNITY renamed it | smoke_18 |

Read 11-10: G13: no shot stands on Olympus; smoke_5 / 6 show the same family on the canyon's slope (the backdrop's
lower field flat with upright streaks, (1500-1700, 640-1080)), unchanged. G14: seen (the Maw's entry is its lure:
a hooked line with a ringed blob). G15 / #14: the flat slab under the Venus deck (y 955-1080) still there; the top
edge not looked at closely. F8, F15, #1 / #4, #8, #13: all unchanged, as expected. #17: FIXED. smoke_18 still
carries "night_lamp" in its name under the day's light.

## 3. Every shot read

One row a shot, in the order read: 1a's shots, 1b's shots, then the rest. "ok" = nothing wrong in the art at 1x.
H-numbers point to section 4 (H1, H2, H4 = the smoke's staging, U-212, not the game). Boxes are px at 1x.

| Shot | Read |
|------|------|
| smoke_47 first dig, DIG DOWN | ok for the card (the shovel picture), SHOVEL's plate clear above it, the first scoop's bowl with its wall (1020-1150, 890-965). The shovel is STOWED: a small grey blade behind the back shoulder at (920, 797), clear of the face. Dim RED brackets in the air right of the scoop, round (1230, 885): the cursor has nothing to dig. No swing, no crack, no clod in this frame |
| smoke_65 shovel mid-swing | The shovel is in the glove, held level in front of the body, the blade at about (1045, 848), 40 px above the ground. **RED brackets (nothing to dig) at full strength round about (1040, 922)**: the smoke swings at the bowl it already opened. No clods, no dust, no crack: a whiff. The fist is on the shaft; nothing weapon-like. H1 |
| smoke_66 shovel flick | The shovel is raised overhead (blade at about (1028, 742)): a wind-up. RED brackets as in 65. **No clods and no dust** (0.6.2's 66 had both). One small pale smear at the feet (985-1030, 880-890), apart from the blade in this still: the swish of the stroke before, or misplaced: H2. H1 |
| smoke_3b Earth dig | ok: the camp's staged dig is an OPEN shaft with its Topsoil wall (790-925, 890-1005): G7 fixed. The shovel stowed; dim red brackets in the air round (1075, 855). The gull, the camp as before |
| smoke_54 pack full | ok. Inside the shaft the wall's Topsoil / Subsoil border is one level line at y 125 (G2 fixed), no step in the darkening (G3 fixed), pebbles not on one line (G4 fixed). The fill's border outside is a clean diagonal. The card clear of the slot's name. The shovel stowed (920, 795); dim brackets with the pip at the cursor (1228, 885) |
| smoke_55 jetpack | ok: no shovel held up, the flame and puffs; grey pebbles at (985, 270), (900, 425), (995, 682), (918, 783): no column (G4 fixed); no step (G3 fixed) |
| smoke_56 ladder | ok: the ladder and the surveyor read on the wall; the border level at y 125; no step, no column |
| smoke_57 winch | ok: the wall's border one near-level line at y 285 across the shaft (0.6.2: a V here): G2 fixed; the line reads on the wall. Left of the shaft a thin soft dark lens along the fill's border (330-850, 245-270): the long roll's faint lens LEAD accepted on u205 |
| smoke_58 grapple reel | ok: the hook in the rock at the lip, the line to the hand, GRAPPLE in the slot; the wall's border level at y 125, no step at y 525 |
| smoke_67 tool slot, the Beam | BEAM MK1 with its icon; the Beam held low at the hip (975, 853), no ray (the button is up). **WHITE brackets at full strength with a "+" pip, (1105-1200, 865-960), pip (1152, 913)**: crisp, on the ground's face; four arcs round a cross read as a targeting reticle: H3. The camp's staged dig an open shaft (750-885, 890-1005): G7 fixed |
| smoke_18 Mars shelter | Both stacks meet the slope (F16 holds). The Beam held low at (1270, 592); white brackets round (1245, 685) under the surveyor's feet, partly over the wall's foot. **G5's two objects are still there and still soft**: the dark lump (888-945, 640-688) and the grooved tan mound (940-1005, 628-690), blurred with stepped edges beside the crisp lamp post. The day's light under the name "night_lamp" (unchanged). A Mars bug at the far left (0-50, 760-800), ok |
| smoke_31 Earth scoop | ok: the scoop's bowl with its wall (1140-1260, 570-650), the Surface Line and pennants. The shovel stowed (920, 428). Dim pale brackets with the pip at the cursor (1228, 885), 7 m from the surveyor inside solid ground: H4 (a question for UNITY) |
| smoke_37 Earth pocket dug | ok: a U-bottomed shaft with its wall (roots above, darker below), three grey crumbs on its floor, PACK FULL in red. Low at the right a dark soft-edged wedge (1230-1920, 990-1080) rising to the right: see G12 in section 2 |
| smoke_42 forest valley | ok: no empty depth tag; PACK 0 / 30; the shovel stowed; the valley as in 0.6.2 |
| smoke_2 earth day | ok: the DIG DOWN card with the shovel picture, SHOVEL's plate clear; the camp, the gull; the shovel stowed; dim red brackets in the air round (1085, 860) |
| smoke_32 Earth tunnel | ok: the tunnel and its chamber with the Topsoil wall (roots); the Surface Line and pennants across it; the shovel stowed; the gull at (1740, 410). H4 |
| smoke_49 T1 room | ok: the room's Topsoil wall; the shovel stowed (922, 797); a dug pocket at the upper left with its wall. H4 |
| smoke_50 T2 room | ok: the Subsoil wall, dark with pebbles; the dim brackets read faintly on the dark bands |
| smoke_51 T3 room | ok: the Stone wall, dark grey with cracks; the dim brackets are grey on grey: just visible |
| smoke_53 T5 room | ok: the Core wall, black with teal veins; the dim brackets read on the black |
| smoke_61 Mars T4 room | ok: Mars's Deep wall (dark brown, pale seams); **no red mark on the PACK bar** (G10 fixed). The Beam held low; WHITE brackets with the "+" pip at full strength (1180-1280, 835-935): the clearest view of the reticle in the smoke: H3 |
| smoke_36 Earth scan X | ok: the red X (960, 372), the buried pocket's marker (920-1000, 630-690), the copper node. The same dark soft wedge low at the right (1230-1920, 995-1080) with a small notch at (1830, 1000): G12 in section 2 |
| smoke_46b downhill walk | ok: the feet on the ground line; the stowed shovel rides lower, behind the pack (855, 805), blade down; dim brackets in the air |
| smoke_10 waystation | **THE PILGRIM IS ON ITS CRADLE** (G1 fixed): its three feet on the hazard plate at (515 / 660 / 805, 882), drawn once, between the clamps (the jaws at (510-530, 690-745) and (785-805, 690-745) beside the fins, not through them), under the truss with its nose at y 145. BAY 2, HALCYON FREIGHT, the porthole with Earth and Luna and the crane's crate are all clear of it. The market list inside its panel (goods 1-22 of 30, PREV / NEXT). The ship's line is a little finer than the bay's heaviest lines; it reads as the same world |
| smoke_11 catalogue | **Camp shows its icon** (the pad, crates, a lantern post) at (1320-1380, 572-625), "Camp · SITE · 50 DC" (#17 fixed); the two unsurveyed sites show their silhouettes (a bunker (580-640, 668-718), a gantry (950-1010, 660-718)). An unsurveyed creature shows as a hooked line with a ringed blob (950-1010, 385-435): the Hadal Maw's first body part, its lure (G14, as expected until U-210). The grey rounded square (585-635, 588-628) is the Snow silhouette (F11, closed) |
| smoke_16 Venus station | **The veil serpent at 1x** (G6 fixed): about 200 px long at (900-1100, 360-405), a thin crisp line like the balloons' rigging, an eye pair at its head, drifting between the two balloons clear of the station: a gentle ribbon. The flat grey-green slab under the deck (y 955-1080): #14 / G15, still open (U-191). Two small red bracket ends under the deck at (1165-1240, 895-910) |
| smoke_21 title card, Mars | **No pale box** (G8 fixed): the far ridge is clean at (1342-1386, 660-692). No hint arrow. The Beam held forward, the arm along it (aim_fwd). The hematite cluster (G9, named) at (1815-1860, 965-1010). A dim bracket arc beside the helmet at (905-935, 778-800): the reticle drawn over the surveyor (H5) |
| smoke_21 title card, Mercury | **No pale box** (G8 fixed here too). Two solarite cones beside the surveyor; stepped terrain (#8) |
| smoke_21 title card, Venus | **No pale box** (G8 fixed). The cream box over the surveyor's helmet (935-985, 575-610) is the vent harvester's head on its tripod with its hose, not a placeholder |
| smoke_41 Earth coast cliff | ok for the lip and the shells. The two fills still meet in soft upright bands at x 880-1000 and x 1380-1460 (F15, unchanged as expected). Low at the left a dark brown soft-edged mass (0-1000, 950-1080), its top a long gentle roll (y 955 at x 650, about 990 at x 100): G12 in section 2 |
| smoke_43 Earth sea | **The shallows are in** (B-225): a pale band under the water line (y 420-445), sea grass in six tufts and a pebble on a sand floor at y 640. The shark mid-water. **The Hadal Maw is drawn in front of that sand floor**: its body (1765-1920, 560-850) reaches 210 px below the painted floor's line, so it reads as a giant fish half sunk in a sand flat; its lure at the water line (1660, 458): H6. A dark soft wedge at the lower left (0-330, 850-1080): G12 |
| smoke_2b depth | ok: the DIG DOWN card; bones and ammonites in the fill; the shovel stowed; dim brackets on the soil under the surveyor (965-1065, 600-700) |
| smoke_46d downhill walk | ok: the feet on the ground line; the stowed shovel's blade up behind the pack (787, 822) with its shaft down to the pack; dim red brackets in the air |
| smoke_3d landing squash | ok for the squash; the camp's staged dig an open bowl with its wall (790-925, 890-1005): G7 fixed. In the squash the stowed shovel does not squash with the body: its blade stands a blade's height above the helmet's left (915-945, 762-790), beside the antenna (low; one frame) |
| smoke_29 Earth camp curve | ok: the staged dig an open bowl (535-640, 685-775): G7 fixed; the shovel stowed |
| smoke_59 sell | ok: the scroll, five item icons at list size; the open bowl below it (745-885, 890-1005): G7 fixed |
| smoke_33 Earth mound | ok for the tunnel and the mound. **Two deer stand a body apart** at (1640-1735, 560-685) and (1845-1920, 565-690): no two-headed animal (G11 fixed). A grey pointed stone is drawn in front of the surveyor's legs (962-1005, 525-570) (a surface rock; low) |
| smoke_38 Earth desert | ok: the sand hill, the buttes, the cactus; the shovel stowed; a red-crystal node. **No dig in this shot**: B-242's sand wall is not shown anywhere in the smoke. A camp gull flies in the desert (1385-1450, 575-635), 1.5 km from the camp (low: a gull on every Earth stage) |
| smoke_4 desert, Launch Complex | ok: the gantry, the ruin; the SELL card clear of the slot's name; PACK 30 / 30 in red (staged); the shovel stowed. No dig |
| smoke_1 menu | ok: the v3 title, the logo and four buttons over the calm left third; the Pilgrim, the smelter, the surveyor. A ladder shaft at the right (1655-1740, 800-1080) is flat near-black with no back wall (the menu's own scene; low) |
| smoke_2c bump | The bump frame beside the wolf. **Dim RED brackets sit round the wolf** (1015-1140, 795-915): the cursor's empty state over an animal reads as a target on it: H5. In the bump pose the stowed shovel's blade stands on top of the helmet (920-955, 768-795), where the antenna is (one frame; as 3d) |
| smoke_3 camp by day | ok: the camp, the gull, the shovel stowed; dim red brackets in the air (1015-1140, 795-915) |
| smoke_48 Surface Line | ok: the card, its arrow up, "DEPTH 2 m · TOPSOIL"; the shaft and the small scoop both show the Topsoil wall (roots) inside a dark rim; the shovel stowed. H4 |
| smoke_3c ship airborne | ok; dim red brackets in the air (1005-1115, 940-1050) |
| smoke_5 Mars canyon | ok: the tier border a clean straight edge parallel to the slope. The vertical streaks under the far ridge (1500-1700, 640-1080): #13, still open (U-191). No brackets seen (the zoomed-out view) |
| smoke_6 Mars canyon, storm | as smoke_5; the DUST STORM cue |
| smoke_7 space, Saturn | unchanged: the stepped edge, no bands (F8; U-208 after this build) |
| smoke_8 inventory | ok: six items, six icons |
| smoke_12 Warden outpost | ok: the obelisk, the mast, the drone; the Beam held low; white brackets on the slope's foot (1060-1160, 795-890) |
| smoke_13 Mercury day | ok; stepped terrain (#8). **No brackets visible** with the Beam in hand: H7 |
| smoke_14 Mercury twilight shelter | ok; the backdrop's hard edge over flat cream at (1445-1920, 810): #13, still open |
| smoke_15 shadewyrm burrow | ok: the shadewyrm's segments beside the surveyor; stepped terrain (#8). No brackets visible: H7 |
| smoke_17 Venus vent | ok: the vent harvester on its tripod over the surveyor; stepped terrain (#8). No brackets visible: H7 |
| smoke_22 Mars hauler | ok: the wreck in its basin, the crate. Dim MUSTARD brackets with the pip on the basin's floor (1055-1150, 780-870), 2.4 m from the surveyor and not at the smoke's cursor: the clamped state, the only one in the smoke; it reads on the brown floor |
| smoke_23 Jupiter floe kit | ok for the kit, the tortoise and the Pilgrim. Under the floes the flat block (810-1470, 750-812) and the streaks below: #1 / #4, still open (U-191) |
| smoke_9 crafting, page 1 | ok: recipes 1-17 of 29, every row's icons at list size |
| smoke_64 crafting | ok: the four-ingredient rows clear of FABRICATOR; "after Float cell Mk1" on the tile; thruster Mk2's steel bell |
| smoke_19 pause | ok |
| smoke_20 settings | ok: no "Fire: LMB" |
| smoke_21 title card, Earth | ok: no hint arrow over the card; the gull. Red brackets beside the surveyor at the bottom left (100-220, 1005-1030): staging (H4) |
| smoke_21 title card, Jupiter | ok; under it the flat block (810-1470, 750-812) and the streaks (#1, #4, still open: U-191) |
| smoke_24 Jupiter storm deck | ok for the painted deck; the flat block under the floes (810-1830, 750-872) and the streaks (#1 / #4). By the feet two or three small tan dashes on the floe's top (985-1055, 628-634): the reticle on block ground: H7 |
| smoke_25 Jupiter deep, CRUSH | ok: the CRUSH band reads; streaks below (#1). The same dashes by the feet (985-1050, 628-634): H7 |
| smoke_26 Jupiter red spot, the whale | ok: the Vortex Whale overhead, the red floes; the flat block (810-1410, 752-812): #1 / #4. The same dashes (985-1055, 628-634): H7 |
| smoke_27 climb boost | ok |
| smoke_28 sound barrier | ok: the vapor cone, the shock ring |
| smoke_30 Earth hill | ok; the shovel stowed. H4 |
| smoke_34 Earth node, full | ok |
| smoke_35 Earth node, harvested | ok |
| smoke_39 Earth taiga | ok |
| smoke_40 Earth tundra | ok |
| smoke_44 Survey Archive | ok: the bunker, the beacon; the funnel and the room below show the Topsoil wall with roots; "DEPTH 6 m · TOPSOIL". The surveyor stands below the frame's bottom edge (only the antenna's tip at (953, 1075)): the shot's framing (UNITY, low) |
| smoke_45 Launch Complex | ok |
| smoke_52 T4 room | ok: the Deep wall, dark with gold seams; the dim brackets read on the fill's bands |
| smoke_60 skill tree | ok |
| smoke_62 space, minimap | ok; the minimap's labels crowd each other as before (HUD, low) |
| smoke_63 system map | ok |
| smoke_46a, 46c downhill walk | ok: the feet on the ground line. The stowed shovel swings with the walk: in 46a its shaft stands out behind the shoulder (868-905, 783-835), in 46c it lies close (812-835, 800-830): it reads as carried on the back |

All 79 shots read at 1x, 11-10 from 11:0x (the smoke's files 10:51-10:57, the release player, build 6edc5562).

## 4. Findings

Owner = who would fix it. Boxes are px at 1x as (x0-x1, y0-y1). Every finding carries its shot and a crop (the card's
Accept); a finding I could not crop says so.

Crops are in coordination/reports/blender/smoke_read_0.6.3_crops/ (cut 11:17-11:18, thirteen files). LEAD's routing
(11:1x) is in the Owner column. H1, H2 and H4 were my first numbers for what UNITY then traced to the smoke's own
staging; they are named once here and are NOT findings about the game.

| # | Shot | What | Where | Owner | Confidence | Crop |
|---|------|------|-------|-------|------------|------|
| H1, H2, H4 | smoke_65, 66; 30-32, 34-40, 45, 48-54 and every shot with dim brackets far from the surveyor | **SMOKE STAGING (U-212), not the game.** The smoke clears the rig's owner round its scripted digs, so: the brackets sit at the smoke's cursor (always screen (1228, 885), 4-7 m off, in solid ground or in the air) instead of on the next contact; 65 and 66 swing at the already opened bowl with red brackets, no clods, no dust, no crack; 66's swish lies at the feet apart from the blade. In play the reticle at rest sits on the next contact (UNITY, b4ad405c) | as listed | UNITY: U-212 (a working-contact shot on fresh ground, a Beam shot mid-dig, in the next build's smoke) | settled | staging_65_whiff_3x.png |
| H3 | smoke_61, 67 (any Beam shot at full strength) | **The pip makes the brackets a gun sight.** Four cream arcs round a small "+" at their centre: with the Beam in hand it reads as a targeting reticle, not a surveyor's mark (D-087). My own art (B-246's pip), passed on the sheet, wrong in the game | smoke_61 (1180-1280, 835-935); smoke_67 (1105-1200, 865-960) | BLENDER: B-249 (the two pip frames of fx/dig_reticle/base redrawn as a ground tick; next build) | high | h3_61_reticle_pip_4x.png, h3_67_reticle_pip_4x.png |
| H5 | smoke_2c | The red (nothing to dig) brackets frame the wolf: four red arcs round an animal read as a target on it. Cursor-bound here; the question is whether in play the empty state can come to rest over a creature (or over the surveyor: a dim arc beside the helmet in smoke_21 Mars at (905-935, 778-800)) | smoke_2c (1015-1140, 795-915) | UNITY: U-212 | medium that it reads so; whether play shows it is UNITY's to say | h5_h8_2c_wolf_brackets_blade_3x.png |
| H6 | smoke_43 | The Hadal Maw is drawn in front of B-225's shallow seabed: the painted sand floor's line is at y 640 and the Maw's body reaches y 850, so it reads as a giant fish half sunk in a sand flat, its lure at the water line | the Maw (1765-1920, 560-850); the floor's line y 640 | UNITY: U-212 (where the Maw holds against layer4's "shore_m", or the layer's fade near it); no art change asked | medium | h6_43_maw_on_seabed_2x.png |
| H7 | smoke_13, 15, 17 (Mercury, Venus); smoke_23-26 (Jupiter's floes) | On block ground the reticle does not read as brackets. On a floe: two small mustard corner marks and an upright tick standing on the ground line by the feet, their lower parts hidden (the cell's brackets drawn behind the ground). On Mercury: one faint tan box about 14 x 6 px on the ground line | smoke_24 (985-1055, 624-634); smoke_13 (1008-1022, 694-700) | UNITY: U-212 (the cell state's sorting and size); BLENDER if the cell bracket art needs a larger drawing | high that it does not read | h7_24_block_reticle_4x.png, h7_13_block_reticle_4x.png |
| H8 | smoke_2c, 3d | In the bump and the landing-squash frames the stowed shovel does not follow the body: its blade stands on top of the helmet over the antenna. At 3x it reads as a horn or a feather on the helmet (in idle and the walk it is right, behind the shoulder) | smoke_2c (920-955, 768-795); smoke_3d (915-945, 762-790) | UNITY (the stow rides the squash root or hides in those clips); BLENDER if the two clips want their own stow socket in side_dig.json | medium; one or two frames each | h5_h8_2c_wolf_brackets_blade_3x.png |
| H9 | smoke_33 | A grey pointed surface stone is drawn in front of the surveyor's legs | (962-1005, 525-570) | UNITY (sorting), low | low | none cut |
| H10 | smoke_1 | The menu's ladder shaft is flat near-black with no back wall, beside ground that has the full fill | (1655-1740, 800-1080) | UNITY (the menu's scene), low | low | none cut |
| H11 | smoke_44 | The surveyor stands below the frame's bottom edge (the antenna's tip only) | (953, 1075) | UNITY (the shot's framing; U-212) | low | none cut |
| G5 | smoke_18 | Still there (section 2): two soft, blocky shapes on the ground 4-5.5 m left of the surveyor; the log's 3 m probe does not reach them | (888-1005, 628-690) | UNITY: U-212 (a wider probe names them) | high that they are soft; the cause unknown | g5_18_two_shapes_4x.png |
| G12 | smoke_36, 37, 41, 43 | Milder (section 2): a soft tier edge, one smooth roll. CLOSED by LEAD 11:1x as accepted | as section 2 | closed | - | g12_37_soft_edge_2x.png |

Crops of what was seen fixed: g1_10_pilgrim_on_cradle_2x.png, g6_16_serpent_4x.png (an outline of about 1.5 px,
crisp, the eye pair and the closed smile readable), n17_11_camp_icon_4x.png, g8_21mars_no_box_4x.png.
I looked at seven of the thirteen at their size (h3_61, g5_18, h7_13, h7_24, g6_16, h5_h8_2c, and smoke_43 whole);
the other six were cut for LEAD and not viewed by me.

## 5. Summary (11:1x, all 79 shots read at 1x)

**Does the art of 0.6.3 hold? Yes, in everything the smoke shows. First hour: GO for the build as it is**, with one
gap named (LEAD made 0.6.3 the owner's build on this at 11:1x, USER-45).

- **Why go.** In no shot is the art broken, missing or regressed. No placeholder, no empty slot, nothing of the
  collapse, the rubble or any card that is not in this build. Every first-hour screen holds: the menu, the camp, the
  DIG DOWN and SELL cards clear of the tool slot, the open bowl with its wall, the shafts, the rooms T1-T5, the
  scroll, the skill tree, crafting, the catalogue, the launch.
- **THE GAP: the smoke does not show the dig as one motion.** No still has a working contact, a crack stage, a clod,
  dust, the Beam's ray or its glow; smoke_65 and 66 are whiffs with red brackets (smoke staging, U-212). The go covers
  what the stills show. That the blade meets its contact rests on LEAD's look at UNITY's u209 strips, not on this read.
- **The dig's art as far as shown.** The stowed shovel reads right in about twenty shots (a small blade behind the
  back shoulder, clear of the face; behind the pack on the walk). In the swing the fist is on the shaft and nothing is
  weapon-like. The brackets are crisp and sit on the ground's face; red, mustard (smoke_22) and white all read.
- **The 0.6.2 findings.** Fixed and seen fixed: G1, G2, G3, G4, G6, G7, G8 (three cards), G10, G11, and 0.6.0's
  #17. Still there: G5 (unnamed still). Milder and closed by LEAD: G12. As expected: G14, G15 / #14, F8, F15,
  #1 / #4, #8, #13.
- **New, none a first-hour blocker:** H3 the pip (mine: B-249, next build); H5 the red brackets round an animal; H6
  the Maw in front of the shallow sand floor; H7 the reticle on block ground; H8 the stowed blade on the helmet in
  the bump and squash frames; H9-H11 low.
- **Not shown anywhere:** B-242's sand and basalt walls (no shot digs in either fill; UNITY's b242/ captures, viewed
  by LEAD 01:4x, stand in); the white in-reach brackets under a shovel; the swish on a blade; the cracks; the
  Beam's ray and contact glow; clods and dust.
- **Not checked:** motion (stills only); sound; six of my thirteen crops at their size; the Venus deck's top edge.

The bar I wrote before the smoke, and how each line fared (said plainly: two of the five could not be judged
from this smoke, which is the gap above; the go is on what is shown):
- the shovel is in the glove through the swing: YES (65, 66). Its blade meets the ground where the cracks and the
  scoop are: NOT SHOWN (the smoke's swings are whiffs);
- the brackets read as a surveyor's mark on every ground they are shown on: YES with the shovel and dimmed; NO at
  full strength with the Beam (the pip: H3) and not on block ground (H7). Nothing else in the dig reads as a weapon;
- cracks, clods and dust in the soil's own tone: NOT SHOWN in any shot. The hole reads as a hole: YES, everywhere;
- no placeholder, no missing sprite, no art from a card that is not in this build: YES;
- the hint cards and the tool slot clear of each other and of the new reticle: YES.
