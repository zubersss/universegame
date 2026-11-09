# C5 style notes: art v5 as the surveyor's source draws it (BLENDER, 2026-11-09 14:4x)

For LEAD's C5 look-over page. Source: `blender/scripts/build_surveyor_v5.py` (B-231, D-185). **Nothing here has been
rendered yet**: these are the rules the source encodes; the first design sheet may move a number. Written files-only beside
UNITY's U-194 chain.

## 1. v5 in plain words

**The line.** The same warm black ink as v4 (#1E1A17), drawn thinner and cleaner. At the size the parts are drawn (the
surveyor 256 px tall) the outer line is 3.5 px and inner lines 1.75 px; in the game at today's zoom (the surveyor 128 px
tall) that is about 1.75 px and 0.9 px, against v4's 2.5 px and 1.25 px: roughly a third lighter. Each stroke's width still
wobbles by up to a fifth along its length, so it reads as drawn by hand, never ruled.

**Shapes and joints.** No rubber hoses. Arms and legs are tapered segments with a slight padded bulge and round ends, so
an elbow or a knee can bend without a gap opening. The body bends at the shoulder, elbow, wrist, hip, knee, ankle, neck and
waist; the helmet rides on the head; the plumb-bob antenna is a spring of its own; the pack hangs on the back.

**The face.** A grown-up's warm, curious face inside the helmet: an oval eye with an iris, a pupil and a catch-light; an
eyebrow; a nose; a soft cheek; a small smile; an ear; a mustard hair tuft with a cowlick. One head in profile, one in
three-quarter view. v4's pie-cut eyes and bulb nose are gone.

**Paint.** Every part is flat colour first, then painted:
- the light comes from above (LEAD's ruling, 14:5x: the rig is mirrored when the surveyor turns, so a side light would
  swap sides at every turn), leaning only slightly to the upper left, the side today's props and icons are lit from;
- a shadow shape on the underside of each form, about a fifth of the part deep, with a ragged dry-brush edge instead of
  a smooth fade; a cast shadow where one part sits over another (the helmet's ring on the shoulders, the belt on the hips);
- the shadow is cooler, not just darker: it leans toward a blue-grey mixed from the palette's sky and brown;
- a thin lit rim along the top edges;
- short brush streaks across all the colour and a light paper grain;
- the ink is never painted over;
- limbs on the far side of the body are one step darker and cooler, so near and far read apart;
- the helmet is a clear bubble: a faint sky tint inside its rim and two white glints on its top.

**The blink.** One closed-eye swap part per facing (a small patch shown over the eye for a few frames), so the face can
look alive; the rest of the expressions come as a face-swap set after the surveyor is accepted.

**Colour.** Earth's eight palette colours, as now. New in v5: materials may be an in-between mix of two palette colours
(skin is off-white with a little red; the suit's shadow is off-white with some sky; knee pads, belt, steel ring, boot sole
the same way), and the paint then varies them. No colour comes from outside the palette's range.

**Proportions.** 2.0 m to the top of the helmet, as v4, so the game's collider does not change: legs 0.88 m, torso 0.56 m,
head and helmet 0.55 m (the bubble is 0.61 m across), arms 0.66 m with the hands at mid-thigh; about three and a half heads
tall. The antenna and its plumb bob add 0.3 m.

**Suit detail.** Shoulder and side seams, a zip seam, knee and elbow pads, a belt with a brass buckle and a pouch, a steel
neck ring, boot cuffs, laces and soles with treads, a lid and a vent on the pack, its air hose to the helmet.

**How it moves.** A rigged cut-out: 17 drawn parts (plus 7 darker far-side copies) on one small sheet, 18 bones per facing
(side, front three-quarter), four IK chains (elbows bend back, knees bend forward), sockets for the tool in the near hand
and the helmet's top. Poses are bone angles: the sheet shows idle, crouch (a deep forward tuck with a 0.92 squash, under a
1 m ceiling line), the jump's apex with tucked knees, and a two-handed dig on B-226's shovel. D-185: key moves at 24 fps.

**Memory.** The whole surveyor is one part sheet of about 512 x 204 px. v4's surveyor is 170 frames of 192 px on two sheets
(about 6 megapixels): v5 needs roughly a fiftieth of the texture.

## 2. Kept from v4, and changed

| Kept | Changed |
|------|---------|
| Hand-drawn ink and paint; nothing that reads digital or 3D | Jointed limbs on a rig, not rubber hoses drawn frame by frame |
| The surveyor's marks: the fishbowl helmet, the plumb bob on its springy antenna, the teal MERIDIAN stripe and compass badge on the off-white suit, the soft-red float pack, white gloves with mustard cuffs, brown boots | A natural cartoon face (oval eyes, eyebrow, nose) instead of pie-cut eyes |
| An original character; no combat; faces only on people and animals | Painted shading and brush texture instead of flat cel colour with up to two shadow tones |
| Earth's palette and the ink colour | A thinner, cleaner line; in-between colour mixes |
| The 2.0 m height and the collider | Suit detail (seams, pads, belt, treads); crouch and bent-knee jump from the rig; far less texture memory |
| The painted backgrounds (D-185) | Characters now carry painted light, so the band behind them gets a matching pass (section 4) |

## 3. The four points, as LEAD ruled them (14:5x, before the first sheet)

1. **The light: from above.** I had proposed the upper right. Ruled: v5 characters are lit from above, at most a slight
   lean to the upper left (the side the v3 props and icons are already lit from, so nothing existing is re-shaded). The
   source is changed to it; the sheet shows the surveyor facing both ways beside two v3 camp props so the light can be
   seen to read the same. Contract v4 will state the light (neither the Bible nor the contract does today).
2. **The palette check: accepted.** Every flat colour is a palette colour or a named mix of two (the source's TONES),
   checked before the paint pass.
3. **Drawing size: accepted.** Rig parts are drawn at 128 px per metre, twice the game's 64.
4. **Expressions: one blink now**, a closed-eye swap part per facing (in the source and the bone JSON's `swaps`); the
   rest of the face-swap set after acceptance.

One thing the rig could add later, not drawn on the sheet because it would be UNITY's work: a contact shade, a darkened
copy of each part 2-3 px straight down and one sorting step under it, which would put a moving shadow under the arms and
the pack whichever way the surveyor faces.

## 4. C5's other three pieces (ACCEPTED by LEAD 14:5x as B-234 / B-235 / B-236 in the Backlog, promoted when the owner accepts the surveyor; no drawing source before that)

LEAD's notes: the band is a C5-only preview key (the shipped band untouched), lit from above too, sway cards only if the
scene stays inside Bible 11.1; U-162 is the stag's flee AI only, independent of the rig; UNITY confirms the camp's scene
key at U-199.

### The creature: the stag (`creatures/earth/stag`)

Why: it lives on grass, so it stands at the camp; it is peaceful; and it has the most joints of any Earth land animal,
on long thin legs where a bending knee and hock read clearly at 1x: the owner's "knees that actually bend", on an animal.
Today it is a v3 frame sheet (52 frames, 192 x 176 px). U-162 is its flee AI only, independent of the rig (LEAD).

- **Size:** 1.5 m at the shoulder, antler tips at 2.0 m (as now), drawn at 128 px per metre; one sheet of about 512 x 300 px.
- **Parts (17 drawn + 9 far-side copies):** haunch, barrel, lower neck, upper neck, head, jaw, ear, antler, tail base,
  tail tip; foreleg upper, foreleg lower, fore hoof; hind thigh, hind gaskin, hind cannon, hind hoof. Far copies: the seven
  leg parts, the ear, the antler.
- **Bones (26):** haunch (root) -> barrel -> lower neck -> upper neck -> head -> jaw, two ears, two antlers; haunch -> tail
  base -> tail tip; barrel -> foreleg upper -> foreleg lower -> fore hoof (near, far); haunch -> hind thigh -> gaskin ->
  cannon -> hind hoof (near, far).
- **Joints that bend:** shoulder, front knee (forward), fetlock; hip, stifle, hock (back), fetlock; the spine between
  haunch and barrel; the neck's base and middle; the head; the jaw; the ear roots; the tail's base and middle.
- **IK:** four leg chains (hooves planted while it walks), a look-at on the head toward the surveyor.
- **Moves on its own:** each ear flicks, the tail flicks, the jaw chews while it grazes, the barrel breathes.
- **Clips for the test:** idle (grazing), walk, react (head up, ears forward, a look at the surveyor).

### The plant: the nodbell (`flora/earth/rigset`, today 4 bones)

A bellflower with more to move, no face parts (D-101).

- **Parts (7 drawn + 1 far copy):** stem low, stem mid, stem arch; a leaf (and its far copy); an open bell, a half-open
  bell; a bud.
- **Bones (9):** root -> stem mid -> stem arch -> bud; two leaves off the stem; three bells, each on its own short stalk
  off the arch.
- **Joints:** the stem's base and its two bends, the leaf roots, the three bell hinges.
- **Moves on its own:** the wind's sway travels up the stem a beat late per segment, the bells swing behind it, the
  leaves flutter; brushed by the surveyor it bends away and the bells swing wide.

If the camp's meadow shows another plant more often, the curlfrond takes its place (five fronds of two segments each).

### The background band: the camp scene's near band (`backgrounds/earth/plains/layer2`, 2048 x 480, 64 continue rows)

D-185 keeps the painted backgrounds, so this is a matching pass, not a new look: the same watercolour masses, paper and
no ink, tileable as now, plus the v5 brush streaks in the washes and two values per mass (a painted shadow shape under each
tree crown and on the undersides of the masses, lit from above as the characters), so the painted surveyor does not
look pasted onto flat washes. UNITY confirms at U-199 which scene the camp shows (else the same pass on its scene).

- **Parts:** the band; optionally three sway cards cut from it (two tree crowns, a row of grass tufts).
- **Joints:** one pivot per sway card (the trunk's top, the tufts' base), a slow sway of about two degrees. Optional: it
  adds three draw calls, so it rides only if the scene stays inside Bible 11.1.
