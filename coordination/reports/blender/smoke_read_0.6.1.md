# B-228 · Art read of 0.6.1's player smoke (BLENDER) — PREP, written 2026-11-09 12:5x before the smoke

Source (when it lands): `coordination/reports/unity/smoke_0.6.1/` (U-194, ~79 shots). Read at 1:1 with the read tools only, no lock. Art defects only (wrong keys, v2 leftovers, seams, floating or sunk art, palette breaks, weapon-like or face-like reads, illegible ink); HUD layout goes to UNITY via LEAD. The 0.6.1 changes are read first, then every other shot for regressions.

## 1. The 0.6.1 changes (read first)

| Shot | What should show | Art | Check |
|------|------------------|-----|-------|
| smoke_1 | B-221's v3 title: Earth's camp at dusk, the Pilgrim on its pad, the smelter, crates and surveyor, the dug shaft with a ladder through the dashed Surface Line; the logo and four buttons over the calm left third | `ui/title/background` (ea3f75fb) | no v2 conifers / grey hull / pixel dirt; nothing busy behind the logo or buttons; the image unstretched (1920x1080) |
| smoke_18 | The built shelter walls seated on Mars's slope at night (was ~40 px afloat) | `props/common/shelter_wall`, `shelter_door` | each base on the drawn ground, no gap, no sinking past the foot |
| smoke_64 | Crafting with thruster Mk2's icon: a steel bell with a brass collar, before Mk3's red | `icons/thruster_mk2/base` (02462247) | not the flat teal square; reads at the panel's size beside mk1 / mk3 |
| smoke_65 / 66 | A new game digging with the shovel at camp: the shovel in the glove mid-swing, the flick tinted to the ground | `props/rig/shovel`, `fx/shovel_flick/base` (ab1c524f) | the D-grip in the hand (pivot), the blade toward the dig point, nothing weapon-like; the flick's clod arcs up and back, tinted brown on Earth |
| smoke_67 | The HUD tool slot: the shovel, then The Beam Mk1 after the buy | `icons/tools/shovel`; `icons/tools/beam` if B-227 exported before the build | reads at 48 px in the slot; the Beam a cutting emitter (D-087); a placeholder if B-227 missed the build (expected then, not a defect) |

## 2. The 0.6.0 findings (B-201): expected state in 0.6.1

| # | 0.6.0 finding | Expected in 0.6.1 | Why |
|---|---------------|-------------------|-----|
| 1 | Jupiter decks: vertical streaks below the floes | still open | B-220 / U-191 come after 0.6.1 |
| 2 | sea from below a flat grey-blue | fixed (0.6.0 release, U-188) | keep checking: no regression |
| 3 | a bear swimming in the sea | fixed (0.6.0 release) | no land animals or birds under water |
| 4 | a flat block under the floes, cap-to-cap gaps | still open | U-191 |
| 5 | the SURFACE LINE hint during the ship's climb | fixed (0.6.0 release: hints only on foot) | |
| 6 | mica_book read as a dark vent grate | fixed (b47759a4: a pale layered slab) | check T3 rooms |
| 7 | root_knot read as a spider | fixed (b47759a4: a pale root tangle) | check T2 rooms |
| 8 | Mercury / Venus stepped block terrain | still open | U-177 |
| 9 | "×1.00" into the skill tree's border | fixed (0.6.0 release) | |
| 10 | the v2 title scene | FIXED IN 0.6.1 (B-221) | smoke_1 |
| 11 | the unthemed 3D docking bay | still open | B-223 / U-192 after 0.6.1 (the v3 bay replaces the same keys) |
| 12 | thruster Mk2 a flat teal square | FIXED IN 0.6.1 (B-222) | smoke_64 |
| 13 | Mars canyon / Mercury twilight continue_rows not repeated | still open | U-191 |
| 14 | venus/deck without continue_rows | still open | B-220 (venus/deck included) / U-191 |
| 15 | the sky serpent in the pre-v3 style | still open | B-224 / U-192 |
| 16 | shelter walls floating on the slope | FIXED IN 0.6.1 (U-194) | smoke_18 |
| 17 | the catalogue's Camp without an icon | still open | B-223 (icons/catalogue/camp) / U-192 (IconOf has no Site branch) |

## 3. Every shot read

(filled when the smoke lands)

## 4. Findings

(filled when the smoke lands: shot, defect, where, owner)
