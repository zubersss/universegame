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

## 5. What v6 does not change

Original designs only (D-087, D-101: no faces on plants or objects). No combat. The solar system, the digging game,
every rule and number. The art contract's keys, sizes and budgets, until a v6 contract section replaces them.

## 6. How it arrives

1. A style test first (milestone C5, re-scoped): the surveyor (B-231 round 3) and one style frame of the Earth
   camp (B-248) in this look, shown to the owner on one page beside today's game.
2. On the owner's yes: the rigged surveyor (U-199), then Earth's stage, then planet by planet. The shipped v3 / v4
   art keeps shipping until each piece is replaced.

Where sections 2 and 3 come from: search summaries of Smithsonian Magazine's article on the photocopied line, of
Andreas Deja's published notes on the film's line, palette and background painters, of the film's pressbook (760
painted backgrounds) and of auction catalogue descriptions of the production art's media; two of Deja's posts
fetched; and LEAD's own look at five of the twelve study stills. No book on the film was read.
