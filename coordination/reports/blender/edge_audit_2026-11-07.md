# Edge audit 2026-11-07 (B-138)

Read-only, from the committed PNGs under Assets/_Game/Art (blender/scripts/edge_audit.py). Rule: v3.EDGE_MARGIN = 2 px with no alpha at the top, left and right of every frame (left / right skipped for sheets that tile in x), and at the bottom when the pivot is above the frame bottom; a pivot at the feet leaves the bottom to the ground line.

20 sheets audited, 0 with frames touching an edge; 24 v3 files without frames (n/a).

| key | frame | frames | pivot | edges checked | offending frames | max alpha per edge |
|---|---|---|---|---|---|---|
| characters/calibration_v3/side | 160x160 | 20 | [0.5, 0.0] | top, sides | none | - |
| characters/surveyor/side | 192x192 | 98 | [0.5, 0.0] | top, sides | none | - |
| characters/surveyor/side_b | 192x192 | 56 | [0.5, 0.0] | top, sides | none | - |
| creatures/earth/bear | 224x160 | 56 | [0.5, 0.0] | top, sides | none | - |
| creatures/earth/gull | 112x96 | 52 | [0.5, 0.0] | top, sides | none | - |
| creatures/earth/stag | 192x176 | 52 | [0.5, 0.0] | top, sides | none | - |
| creatures/earth/wolf | 160x128 | 66 | [0.5, 0.0] | top, sides | none | - |
| planets/earth/disc | 172x172 | 12 | [0.5, 0.5] | top, sides, bottom | none | - |
| planets/earth/luna | 64x64 | 12 | [0.5, 0.5] | top, sides, bottom | none | - |
| planets/jupiter/disc | 656x656 | 9 | [0.5, 0.5] | top, sides, bottom | none | - |
| planets/mars/disc | 124x124 | 12 | [0.5, 0.5] | top, sides, bottom | none | - |
| planets/mercury/disc | 104x104 | 12 | [0.5, 0.5] | top, sides, bottom | none | - |
| planets/neptune/disc | 356x356 | 12 | [0.5, 0.5] | top, sides, bottom | none | - |
| planets/saturn/disc | 596x596 | 9 | [0.5, 0.5] | top, sides, bottom | none | - |
| planets/uranus/disc | 364x364 | 12 | [0.5, 0.5] | top, sides, bottom | none | - |
| planets/venus/disc | 164x164 | 12 | [0.5, 0.5] | top, sides, bottom | none | - |
| ships/pilgrim/puff | 128x128 | 8 | [0.5, 0.96] | top, sides, bottom | none | - |
| terrain/earth/ground_strip | 64x152 | 8 | [0.5, 0.842105] | top | none | - |
| terrain/earth/ground_strip_soil | 64x152 | 8 | [0.5, 0.842105] | top | none | - |
| terrain/earth/ground_strip_stone | 64x152 | 8 | [0.5, 0.842105] | top | none | - |

## Parts and single images

Rig-set parts: alpha > 128 on a part rect's outermost row or column (a cut part). Single images (icons, Saturn's ring parts, the escape sign): any alpha in the 2 px border (the bottom skipped when the pivot is at the base: the sign's post stands on its line). Backgrounds, film overlays, the escape-line tile and the palette strip are full-bleed by design and not checked.

| key | kind | result |
|---|---|---|
| flora/earth/rigset | rig set | none of 44 parts cut |
| icons/grass/base | single image | clear |
| icons/mercury_basalt/base | single image | clear |
| icons/mercury_regolith/base | single image | clear |
| icons/regolith/base | single image | clear |
| icons/snow/base | single image | clear |
| icons/soil/base | single image | clear |
| icons/sulfide/base | single image | clear |
| icons/tessera/base | single image | clear |
| planets/saturn/disc_rig | rig set | no packed sheet (parts are separate images) |
| planets/saturn/rings_back | single image | clear |
| planets/saturn/rings_front | single image | clear |
| ships/pilgrim/rig | rig set | none of 11 parts cut |
| ui/hud/escape_sign | single image | clear |
| ui/hud/gauges | rig set | none of 6 parts cut |

Full-bleed by design (not checked): backgrounds/earth/coast/coast, backgrounds/earth/forest/forest, backgrounds/earth/plains/plains, backgrounds/space/starfield/starfield, fx/film/dust, fx/film/grain, fx/film/scratches, ui/hud/escape_line, ui/palettes/earth/strip
## Conclusion

No committed v3 export needs a re-export for the edge rule. The frames the rule caught this session were all fixed before
their exports: the B-131 smelter lever and lamp halo (B-131 is not exported yet), the B-134 dig and climb_in frames,
and the B-135 pike and shark frames (previews only). The camp props (B-131) will be audited by their own export. Re-run:
`"C:/Program Files/Blender Foundation/Blender 5.2/5.2/python/bin/python.exe" -I blender/scripts/edge_audit.py coordination/reports/blender/edge_audit_<date>.md`
(numpy only, ~55 MB, ~4 s).
