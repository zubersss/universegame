# MERIDIAN art style v6: cel on painted (D-199)

Owner, 2026-11-10: "Make the art style the exact same as the 1967 animated film The Jungle Book. I don't care for
the animal aspect too much, just the art style."

This is the working guide for that look. It describes how the look is made, in our own words, from published
accounts of the film's production and from twelve stills kept for study in `docs/reference/v6_study/` (local only,
git-ignored, never committed, never used as a texture and never traced). We take the technique. We take no
character, design, composition or frame from the film: every MERIDIAN design stays our own.

## 1. The one idea

Two kinds of picture are laid over each other and never mixed:

- **The cel**: everything that acts (the surveyor, creatures, tools, the ship, things you pick up, build or dig
  loose). A drawn pencil line and flat paint. No texture, no gradient.
- **The painting**: everything that is stage (sky, far and near backdrops, the ground and what is under it, plants
  and rocks that only stand there). Brush paint, soft and hard edges, light and shadow. No drawn outline at all.

What can be touched has a line; what is scenery has none. That is the look, and it is also the game's best
readability rule.

## 2. The cel (characters and acting objects)

How the film made it: the animators' pencil drawings were photocopied straight onto the cels, so the line on screen
is the animator's own pencil line, not a traced ink line; on this film it was kept tighter and cleaner than on the
studio's earlier photocopied features. The cels were then painted flat on the back.

Rules:
1. **The line is a pencil line.** Dark charcoal, not pure black. One confident stroke with pressure in it: it
   swells and thins along its length (about ±40 %), its ends taper, its edge is slightly dry and broken, and it may
   stop short of closing a shape. At the game's 1080p zoom its mean width is 1.5 px (D-198's resolution rule
   stands: drawn at 512 px per metre, only ever shrunk).
2. **Few lines.** A line where a form turns or overlaps, quick flicks for tufts, folds and whiskers. No hatching,
   no stitching rows, no outline round a colour patch that can be a paint edge instead.
3. **Flat paint.** One opaque colour per area. At most one flat shadow shape per form, a step darker in the same
   hue, with a clean edge. No gradients, no painted highlights but a single flat one on glass or metal, no paper
   grain on a cel.
4. **Paint edges without line.** Markings, patches, a muzzle, a suit's coloured panel: two flat colours meeting
   with no line between them.
5. **Cel colours are mid-value and a little warm**, chosen so the figure reads as one clear shape against the
   painting behind it. Each place and time of day re-keys the whole figure's colours (night: every colour shifted
   toward the scene's blue), never by a tint laid over line and paint alike.
6. **The line lives.** Hand-drawn frames never repeat exactly. A rigged figure gets this back with two or three
   alternate line passes per part cycled on the 12 Hz clock (a boil of under a pixel).

## 3. The painting (backgrounds, ground, scenery)

How the film made it: opaque watercolour backgrounds, painted to a muted, natural palette and an airy, light
jungle; soft and impressionistic behind, firm in front, always leaving a quiet, lighter stage where the figures act.

Rules:
1. **No drawn line anywhere in a painting.** Edges are paint: soft and wet far away, crisp near.
2. **Three depths by value and edge.** Far: pale, cool, low contrast, soft blobs that only suggest shapes. Middle:
   clear silhouettes in two or three values of one hue. Near: dark, saturated, crisp shapes that frame the view,
   with a few lighter brush strokes on their lit sides.
3. **Brush marks show.** Shapes are built from visible strokes and dabs with slightly uneven colour; rocks and
   trunks from flat planes of three or four values; ground from broken dabs (litter, pebbles, tufts) rather than a
   flat fill. A fine paper tooth lies over the whole painting, nothing coarser.
4. **Light in pools.** Warm, lighter patches where light falls and cool violet-blue shadow between, dappled across
   the ground. The lightest, quietest area sits where the figures will be.
5. **A muted palette.** Olive and grey-greens, ochre, dusty pink and lavender in the light, blue-violet in shadow.
   Strong colour is kept for the cels and for a few accents.
6. **The ground is painting too.** Its surface edge is a painted edge (grass, litter, a crumbling lip), not an ink
   line. What the player digs into is painted earth: strata as soft bands with broken edges, stones and roots as
   brushed shapes. A dug hole is darker painted earth with a soft inner shadow.

## 4. How the two meet in the game

- A figure never takes the painting's texture, and a painting never takes a line. The film grain, dust, scratches
  and iris of the 1930s look are not part of v6 (a faint, even grain over the whole frame at most).
- Things that become interactive (a rock that can be dug out, a plant that reacts) are cels: line and flat paint,
  sitting on the painting. The player learns the rule in the first minute.
- Effects (dust, clods, sparks, the dig's cracks) are cel effects: flat shapes with a pencil line or none.
- Motion: full drawn animation on twos (12 drawings a second) with squash, stretch, overlap and follow-through; the
  rig's joints are hidden by overlapping flat shapes, never by a painted blend.

## 4a. Draughtsmanship and level of detail (added after the owner's first look, D-200)

The owner on the first style test: "I like the colours but the details I don't like ... this still looks like a
1930s cartoon, big circle head and eyes. Make it look like the reference photos: the same style and the same level
of detail, from the proportions to everything." Sections 2 and 3 say how the picture is made. This section says how
it is DRAWN, from a second look at the stills (twelve of twenty-two viewed).

**Figures**
1. **Natural proportions, caricatured lightly.** A person stands about five to five and a half heads tall, with
   lean limbs. Nothing is a ball on a body.
2. **Built, not outlined.** The head is a skull and a jaw; the body has shoulders, a rib cage, hips; limbs have
   elbows, wrists, knees, ankles. Hands have a palm, a thumb and fingers that grip; feet have a heel and toes or a
   shoe built on them. Forms overlap, and a short line shows where one passes in front of another.
3. **Small features.** An eye is about a fifth of the head's width at most, with an upper lid and a brow that
   carry the expression; a nose and an ear are drawn. No disc eyes, no dot-and-arc faces.
4. **Hair, fur and cloth as designed masses** with a few tuft or fold flicks at their edges and where they bend.
5. **A thin, sure line.** Long confident curves, thin against the figure's size; inside lines only where they
   describe form (a shoulder, a belly's overlap, a knuckle). The line on a figure filling half the frame is about
   two pixels wide.
6. **Animals** by the same rules: real anatomy first (the shoulder blade, the haunch, the hock), then the
   character. No rubber-hose limbs anywhere.
7. **It moves as drawings.** Every frame is its own drawing, on twos, with the silhouette changing through a
   move (a twist, a reach, a bend). A figure cut into fixed parts and hinged cannot do this, so v6 figures ship as
   drawn frames, not as a runtime puppet.

**Scenery**
1. **Things, not shapes.** A near or middle layer is made of plants one can name: a broad-leaved bush with each
   leaf painted in two or three values and a midrib stroke, a palm with separate fronds, bamboo with its nodes, a
   grass clump of single blades. A tree has a trunk with weight, roots, branches that taper.
2. **The brush follows the form.** Bark strokes wrap the trunk; a rock is turned by strokes that follow its
   planes; one light direction holds across the whole picture.
3. **Dense near, quiet behind the action.** The near layer frames the view with overlapping foliage; the middle
   is a thicket; the far layers are haze and soft silhouettes. The stage where the figures act stays simple.
4. **Painted accents, not pencil.** Near foliage and rocks may carry darker painted contours and veins laid by
   the brush. That is still painting: it is never the cel's pencil line.
5. **Ground cover.** The ground is covered: leaves, litter, low plants, stones half in the earth, light and
   shadow across them.

## 4b. Detail: as close to the reference as we can get (D-204, the owner's third word)

The owner, after the forest frame and the first frame sets: "I don't like the art style actually. Can you make it a
lot more detailed, as close as your system can handle, as close to the reference as possible." Sections 2 to 4a
stand as the METHOD (a pencil-line cel on a painting). What failed is the AMOUNT: our frame is sparse and flat
beside any still. This section sets the amount, from two stills looked at again beside our frame
(blender/preview/b251/forest_frame_96_plates.png). Where it disagrees with an earlier section, this one wins.
Still true: technique only; no character, design, composition or frame of the film is copied or traced.

**What our frame lacks, named**
- Figure: a thick, even outline round tube limbs; a cream suit with almost nothing drawn inside it; one face.
- Scenery: one flat mid-green; the same few plants repeated with gaps between; far trees as hard-edged cut-outs;
  the ground and the earth as flat bands with grey polygons for stones.
- Props (the crates, the smelter): flat toy shapes with no construction.

**Figures (cels)**
1. **A scratchy pencil line, thin and dark warm grey.** The mean width stays 1.5 px at the game's zoom (D-198),
   but the line is SKETCHED: it varies from a hair to twice the mean, breaks, overshoots a corner a little, and is
   doubled or tripled where the hand searched (hair, a shoulder, a fold). §2 rule 2 ("few lines") is withdrawn:
   few lines is not few details.
2. **Drawn inside the silhouette.** Anatomy shows through: the collar bone and neck cords, the shoulder and
   elbow, the wrist bone, knuckles and finger joints, the knee cap, the ankle. Cloth is cloth: folds where it
   bends (armpit, elbow, waist, crotch, knee, ankle), seams, a collar, cuffs, pocket flaps, buttons or buckles,
   boot welts, laces and soles. Kit is built: straps with buckles, stitched panels, dents, a coiled wire.
3. **Hair in loose overlapping tufts** with strand flicks and stray hairs breaking the outline.
4. **A face that acts.** Brows, upper lids, pupils that look somewhere, a nose with a nostril, an ear with its
   inner line, a mouth that opens with teeth. At least five expressions tied to what the body does (rest, effort
   at the dig's contact, strain on the lever, surprise, pleased).
5. **Organic shapes.** Limbs swell and taper with muscle and bone; no limb is a tube of one width; the two sides of
   a form are never parallel. The silhouette of every drawing is asymmetrical.
6. **Still flat paint** (that is the cel): no gradient, no texture; one flat shadow shape at most.
7. **Measure:** the idle drawing carries at least three times the interior line length of slice 1's (B-250);
   state both numbers.

**Scenery (paintings)**
1. **Every near and middle plant is modelled.** A leaf has three to five values, a light midrib and side veins, a
   lit edge the light comes through, and a dark brushed contour on its shade side (4a's "painted accents" are now
   the rule, not the exception). Near leaves are big: up to a metre.
2. **Trunks are portraits.** Bark pattern wrapped round the form (rings, scars, flakes, cracks), moss and lichen
   in yellow-green and pink-grey patches, roots that grip the ground, vines with their own leaves.
3. **Far layers are airbrushed.** Two or three veils of mist with soft-edged silhouettes of palms and fronds,
   each paler and bluer; no hard-edged cut-out shape behind the middle layer.
4. **The ground is littered and lit.** A warm pool of light where the figures act, cool shadow under the trees,
   and across both: fallen leaves, twigs, pebbles, grass tufts, low seedlings, each with its own small shadow.
   Underground the same care: strata with broken edges, roots, stones turned by three or four values, pockets of
   darker loam; no flat band anywhere.
5. **Colour variety.** Yellow-green in light, blue-green in shade, lavender shadow on trunks, and accents of
   new red-pink foliage, yellow leaves and pale blossoms. Never one green.
6. **Measure:** at 96 px per metre no 200 × 200 px square of the near or middle layer is one flat tone; the
   lightest, quietest area is still the stage where the figures act.

**Props and acting objects (cels)**: drawn with their construction: planks with grain flicks and nail heads, rope
and strap, dents and scuffs, rivet rows and seams on metal, soot round a flue. No flat toy shape.

**How it is made:** code alone reaches its ceiling early (B-251 showed a painted plate is better drawn than any
rule). So scenery is assembled from PAINTED MATERIAL (whole plants, trunks, ground patches, far veils made with an
image generator and credited, D-202), placed, re-keyed and lit by code; code-only painting fills what no plate
covers. Figures stay drawn by code from poses (they must move), with the detail above built into the drawing.

## 5. What v6 does not change

Original designs only (D-087, D-101: no faces on plants or objects). No combat. The solar system, the digging game,
every rule and number. The art contract's keys, sizes and budgets, until a v6 contract section replaces them.

## 6. How it arrives

1. A style test first (milestone C5, re-scoped). The first test (the surveyor of B-231 round 3 and the Earth camp
   frame of B-248) went to the owner on 11-10: the colours were liked, the drawing was not (§4a). The second test:
   a model sheet of the redesigned surveyor and a specimen sheet of scenery, then one frame of Earth's forest edge
   at two camera sizes, on one page beside today's game.
2. On the owner's yes: the v6 surveyor as drawn frames (U-199), then Earth's stage, then planet by planet. The
   shipped v3 / v4 art keeps shipping until each piece is replaced.

Where sections 2 and 3 come from: search summaries of Smithsonian Magazine's article on the photocopied line, of
Andreas Deja's published notes on the film's line, palette and background painters, of the film's pressbook (760
painted backgrounds) and of auction catalogue descriptions of the production art's media; two of Deja's posts
fetched; and LEAD's own look at five of the twelve study stills. No book on the film was read.
