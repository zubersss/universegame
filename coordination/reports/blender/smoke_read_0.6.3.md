# Art read of 0.6.3's player smoke (BLENDER, B-245) — SKELETON, written 2026-11-10 09:5x before the smoke

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

NOT in 0.6.3 (the board, 11-10 09:1x: U-211, U-199, U-197, U-198, U-210, U-208 come after it), so NONE of it should show:
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
| smoke_18 Mars shelter | G5'S TWO OBJECTS (a dark rounded lump about 42 px and a tan grooved mound about 62 px behind the Beam's tip, drawn soft in 0.6.2 while all beside them was crisp). Open in U-205: UNITY was to name them and say why they draw from a low-resolution copy; no fix is recorded | U-205 (open part) | a 4x crop of (860-1060, 600-720) again: are both there, are they crisp now, which decor keys are they (rock_a / rock_b, ventifact?). Still soft = still open, with the crop. Also here: the Beam's aim pose and ray (1a) |
| smoke_36 Earth scan X (and smoke_37, 41, 43) | THE POCKET WITHOUT THE SMUDGE (0.6.2's G12): the tier border's wobble is now one long gentle roll (0.4 m, waves 12-30 m long), the same on the fill and the wall: no dark soft-edged region low in the frame, no isolated bumps | U-205 part 3 (7e679a8d) | smoke_36 / 37: nothing at (1500-1920, 980-1080) but the fill and a clean border line; smoke_41: (0-1000, 930-1080); smoke_43: (0-330, 850-1080); the border, where it shows, a single near-straight line that follows the slope |
| smoke_54-58 the shaft | THE WALL'S THREE SEAMS GONE (G2, G3, G4): the wall's tier border one near-level line across the shaft (a tilt of up to 0.6 m is allowed, a trough is not); no hard horizontal step in the darkening; the wall tile's repeat broken (no pebble on one line every 4 m) | U-205 part 3; the walls imported RGBA32 (D-192, 0405d4e1) | smoke_57: no V at (850, 255)-(975, 315)-(1100, 270); smoke_54 / 55 / 56 / 58: no step at y 525 (57: y 690); smoke_55: no pebble column at x 883 (270, 527, 783); the walls' paper grain as fine as before or finer, no blocky compression in the dark tones |
| smoke_3b, 3d, 29, 59, 67 the camp's staged dig | AN OPEN BOWL (G7): the smoke digs from the surface as a player does: the grass band is opened above the pocket | U-205 (the staging) | no closed disc under unbroken grass; the bowl's rim and back wall as a player's scoop (smoke_31) |
| smoke_43 Earth sea | THE SHALLOWS UNDER THE SURFACE (B-225; 0.6.2 still showed a flat pale tint): a rippled light ceiling about 2 m deep under the water line with slanting shafts, and within 40 m of the shore a shallow seabed (sand ripples, shells, sea grass) that fades out as the camera sinks below its ground line | B-225; U-205 part 2 (layer3 128 px, layer4 "shore_m" 40) | the band meets the water line with no gap or double line; the seabed layer does not stand as a flat sand wall behind a swimmer; no hard sand edge in frame; the Hadal Maw still holds off the shallows (F17) |
| smoke_61 Mars T4 room | No red mark on the PACK bar at 0 / 30 (G10) | U-205 (the rooms shot with the pack flights landed) | (1265-1285, 33-43) clean (HUD; a line for UNITY if not) |
| smoke_33 Earth mound | Two bears no longer on one spot (G11): the spawner keeps a body and a half between a creature and its kind (two walking onto one spot later is left as is) | U-205 | no two-headed animal at (1525-1655, 598-680) or elsewhere |

## 2. The 0.6.2 read's findings: expected state in 0.6.3

| # | 0.6.2 finding | Expected in 0.6.3 | Where to look | Read: fixed / still there |
|---|---------------|-------------------|---------------|---------------------------|
| G1 | the bay's cradle empty | fixed (U-192: the Pilgrim on "ship_ground") | smoke_10 | |
| G2 | the wall's tier border dips in a V inside a shaft | fixed (the border's wobble a long roll, the same on fill and wall) | smoke_54-58 | |
| G3 | a hard horizontal step in the wall's darkening | fixed (the term eases out) | smoke_54-58 | |
| G4 | the wall tile's 4 m repeat down a tall shaft | fixed (the repeat offset) | smoke_55 | |
| G5 | two soft Mars ground pieces beside the surveyor | OPEN in U-205 (to be named by UNITY); no fix recorded | smoke_18, a 4x crop | |
| G6 | the veil serpent drawn 2.7x its art size | fixed (U-192: 1x of its sheet) | smoke_16, a 4x crop | |
| G7 | the staged camp pocket a closed disc under grass | fixed (the smoke's dig an open bowl) | smoke_3b, 3d, 29, 59, 67 | |
| G8 | a pale flat box behind the Pilgrim on Mars | fixed (U-206: the gull on Earth only) | smoke_21 Mars, Mercury, Venus | |
| G9 | a cluster of dark balls in Mars's fill | CLOSED, no fault: terrain/mars/fill_decor_3 (hematite spherules). It may show anywhere in Mars's fill; a lighter tone only if LEAD asks | smoke_21 Mars, 61 | |
| G10 | a red mark on the PACK bar at 0 / 30 | fixed (the staging) | smoke_61 | |
| G11 | two bears on one spot | fixed at spawn | smoke_33 | |
| G12 | a dark soft-edged region low in the frame (F7's residue) | fixed (the long roll); LEAD closed it on u205's shaft, smoke_36's pocket to be seen here | smoke_36, 37, 41, 43 | |

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

## 3. Every shot read

To be filled from the folder, one row a shot, in this order: 1a's shots, 1b's shots, then the rest. "ok" = nothing
wrong in the art at 1x. A crop is named where one was cut; until then "not checked at 4x" stands.

| Shot | Read |
|------|------|
| smoke_47 first dig, DIG DOWN | |
| smoke_65 shovel mid-swing | |
| smoke_66 shovel flick | |
| smoke_3b Earth dig | |
| smoke_54 pack full | |
| smoke_55 jetpack | |
| smoke_56 ladder | |
| smoke_57 winch | |
| smoke_58 grapple reel | |
| smoke_67 tool slot, the Beam | |
| smoke_18 Mars shelter | |
| smoke_31 Earth scoop | |
| smoke_37 Earth pocket dug | |
| smoke_42 forest valley | |
| smoke_2 earth day | |
| smoke_2b depth | |
| smoke_46a-d downhill walk | |
| smoke_10 waystation | |
| smoke_11 catalogue | |
| smoke_16 Venus station | |
| smoke_21 title card, Mars | |
| smoke_21 title card, Mercury | |
| smoke_21 title card, Venus | |
| smoke_36 Earth scan X | |
| smoke_41 Earth coast cliff | |
| smoke_43 Earth sea | |
| smoke_3d landing squash | |
| smoke_29 Earth camp curve | |
| smoke_59 sell | |
| smoke_61 Mars T4 room | |
| smoke_33 Earth mound | |
| smoke_38 Earth desert | |
| smoke_4 desert, Launch Complex | |
| smoke_1 menu | |
| smoke_2c bump | |
| smoke_3 camp by day | |
| smoke_3c ship airborne | |
| smoke_5 Mars canyon | |
| smoke_6 Mars canyon, storm | |
| smoke_7 space, Saturn | |
| smoke_8 inventory | |
| smoke_9 crafting, page 1 | |
| smoke_12 Warden outpost | |
| smoke_13 Mercury day | |
| smoke_14 Mercury twilight shelter | |
| smoke_15 shadewyrm burrow | |
| smoke_17 Venus vent | |
| smoke_19 pause | |
| smoke_20 settings | |
| smoke_21 title card, Earth | |
| smoke_21 title card, Jupiter | |
| smoke_22 Mars hauler | |
| smoke_23 Jupiter floe kit | |
| smoke_24 Jupiter storm deck | |
| smoke_25 Jupiter deep, CRUSH | |
| smoke_26 Jupiter red spot, the whale | |
| smoke_27 climb boost | |
| smoke_28 sound barrier | |
| smoke_30 Earth hill | |
| smoke_32 Earth tunnel | |
| smoke_34 Earth node, full | |
| smoke_35 Earth node, harvested | |
| smoke_39 Earth taiga | |
| smoke_40 Earth tundra | |
| smoke_44 Survey Archive | |
| smoke_45 Launch Complex | |
| smoke_48 Surface Line | |
| smoke_49 T1 room | |
| smoke_50 T2 room | |
| smoke_51 T3 room | |
| smoke_52 T4 room | |
| smoke_53 T5 room | |
| smoke_60 skill tree | |
| smoke_62 space, minimap | |
| smoke_63 system map | |
| smoke_64 crafting | |

## 4. Findings

Owner = who would fix it. Boxes are px at 1x as (x0-x1, y0-y1). Every finding carries its shot and a crop (the card's
Accept); a finding I could not crop says so.

| # | Shot | What | Where | Owner | Confidence | Crop |
|---|------|------|-------|-------|------------|------|
| | | | | | | |

## 5. Summary

**Does the art of 0.6.3 hold? First hour: go / no-go** (to be written last).

What "go" needs, from the first minute a player has (smoke_1, 2, 3b, 47, 65, 66, 42):
- the shovel is in the glove through the swing and its blade meets the ground where the cracks and the scoop are;
- the brackets read as a surveyor's mark on every ground they are shown on, and nothing in the dig reads as a weapon;
- cracks, clods and dust in the soil's own tone; the hole reads as a hole;
- no placeholder, no missing sprite, no art from a card that is not in this build;
- the hint cards and the tool slot clear of each other and of the new reticle.

Then: section 2's table in one line a group (fixed and seen fixed / still there / unchanged as expected), the findings
by owner, and what was not checked (motion: stills only; sound; anything I could not crop).
