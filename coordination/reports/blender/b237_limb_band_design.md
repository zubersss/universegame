# B-237 option C · The giants up close as a painted limb band: design note (BLENDER, 2026-11-09 22:0x; updated 23:3x)

**UPDATE 23:3x: sections 10 and 11 at the end carry LEAD's rulings and what the previews (B-240 Jupiter, B-241 Saturn /
Uranus / Neptune) changed. Where they differ from sections 3 to 6, sections 10 and 11 stand.** In short: the limb band is
512 x 16 (ink only); belt edges and storms are as below, but the ink marks are placed by `close.json`, not by the strips;
each giant has a 128 x 128 pigment tile; the limb follows the far disc's lumpy rim; the contract text is section 11.

Written files-only for LEAD to card (LEAD 21:5x): the art half, UNITY's half and the contract section. No drawing source
exists and nothing here was rendered; every number is computed from the sources named, and the estimates say so.
Background and the rejected options: `b237_giants_close_view.md` (15:5x). This note replaces that note's sketch of option C;
section 7 says what changed and why.

## 1. In short

Above the zoom where a giant's far disc shows texel steps, stop magnifying a picture. Draw the close view from the same
few facts the far disc is painted from (a circle, six to eight flat belts, a night crescent, one storm), and put the
hand-drawn part where the eye reads it: narrow painted strips along the limb and along each belt's edge, mapped at about
one texel per screen pixel at every zoom. The ink line stays 2-3 px and hand-jittered from the swap zoom to the 33x
extreme; no texture grows; the far discs are untouched.

## 2. What the far disc is (the look the close view continues)

From `blender/scripts/build_discs_v3.py` and `Space/DiscSprite.cs`:
- The far discs are imported at 3 px per space unit. Radii: Jupiter 106 u (318 px), Saturn 96 u (288 px), Uranus 57 u
  (171 px), Neptune 56 u (168 px).
- A giant's face is FLAT tones in horizontal belts with hard edges: `bands()` takes a list of (v_top, colour), v from +1
  (north) to -1 (south) in disc radii; each edge wobbles as `wob * sin(freq * pi * u + phase) * (1 - v^2)` (Jupiter
  wob 0.045, freq 4; Saturn 0.025, 3; Uranus 0.02, 3; Neptune 0.03, 3); the phase turns once per idle loop.
- Jupiter: 8 belts and the Red Spot (a red blob at v -0.38, radius 0.13, drifting 0.35 of a turn per loop). Saturn: 5 belts.
  Uranus: 3. Neptune: 4, a dark storm (v -0.25, radius 0.12) and its pale companion cloud.
- A night crescent at the lower left (outside a circle of radius 1.06 centred at (0.30, 0.30)): the tones one shade darker.
- Ink: the 2.5 px outline (2.0-3.0 with its jitter) on a 2-texel soft limb; a few short ink dashes on belt edges (1.25 px).
- Saturn's rings are two separate parts (rings_back, rings_front; tilt 0.30) with a wobble in `disc_rig.json`.
- DiscSprite swaps to a `<key>_near` frame above 6 screen px per far texel and back under 5; the giants have no near frame
  (D-128), so today they magnify the far disc up to about 33 px per texel.

On screen (1 unit = 3 x magnification px):

| | at the swap (6 px per far texel) | at the extreme (33) |
|---|---|---|
| px per space unit | 18 | 99 |
| Jupiter's radius on screen | 1,908 px | 10,494 px |
| Uranus's radius on screen | 1,026 px | 5,643 px |
| how much of Jupiter a 1920 x 1080 view holds | 107 x 60 units: half its diameter across | 19 x 11 units: 9 % of its diameter across |
| a Jupiter belt edge's wobble (4.8 u high, one wave per 53 u) | 86 px high, 954 px long | 472 px high, 5,247 px long |

So up close the view holds an arc of the limb and one to four belts whose edges are long gentle waves. That is little
enough to draw as geometry.

## 3. What is drawn in the close view

Back to front, all in the disc's own frame (it turns and scales with the far disc's transform):
1. **Belts: flat tones, no texture.** Each belt is a strip between its upper and lower edge curves, coloured by vertex
   colour from `close.json` (the far disc's own tones).
2. **Belt edges: a painted strip.** `belt_edge` laid along every belt boundary: a ragged brushed cut between the tone
   above and the tone below (the strip is a mask; the two tones come from the vertices), with one short ink dash per
   repeat (the far disc's dashes).
3. **The storm (Jupiter's Red Spot, Neptune's dark storm and its cloud):** a flat oval in its tone with `spot_rim`
   round it (a brushed rim and a thin ink arc), at its latitude, drifting as in the far clip.
4. **The night crescent:** the same crescent region drawn as a darkening overlay (multiply) with `belt_edge` along the
   terminator, so its edge is brushed, not a ramp.
5. **The limb band.** `limb_band` round the visible arc of the circumference: the outline's ink on its pivot row with
   the hand jitter, a rim wash inside it that covers the belts' polygon ends, transparent outside.
6. **Saturn only: the rings**, by the same means: each ring a flat-toned elliptical strip, `ring_edge` along its inner
   and outer edges, back half under the body and front half over it, following `disc_rig.json`'s wobble.
7. **Paper grain** over the planet in SCREEN space (one small tile, multiply), so the grain does not magnify.

Every strip is mapped at screen scale: its width on screen is its texture height, its length repeats every texture
width, whatever the zoom.

## 4. BLENDER's half (art; numpy, light)

| Key | Size | What | json |
|-----|------|------|------|
| `planets/<giant>/limb_band` (x4) | 512 x 64, tiles in x | the outline: 2.5 px ink with its jitter on row 16 (the pivot), a rim wash below it fading by row 56, transparent above; in each giant's palette | `tile_x`, `ink_row`, `pivot` |
| `planets/common/belt_edge` (2 variants) | 1024 x 24, tiles in x | a mask: R = how much of the lower tone shows (a ragged brushed cut, +-3 px), A = ink (one dash about 110 px long per repeat). Variant 0 firm (Jupiter, Saturn), variant 1 faint and streaky (Uranus, Neptune) | `tile_x`, `variants`, `channels` |
| `planets/jupiter/spot_rim`, `planets/neptune/spot_rim` | 512 x 24, tiles in x | the storm's rim: a brushed edge and a thin ink arc; Neptune's companion cloud a 128 x 64 sprite (`planets/neptune/cloud`) | `tile_x` |
| `planets/saturn/ring_edge` | 512 x 16, tiles in x | a ring's edge: a brushed cut and a 1.25 px ink line | `tile_x` |
| `planets/common/close_grain` | 256 x 256, tiles both ways | the paper grain as a multiply tile (mean 1.0) | `tile_x`, `tile_y` |
| `planets/<giant>/close` (json only, x4) | - | the facts UNITY draws from: `radius_u`; `belts` [{v_top, tone_hex}]; `edge_wobble` {amp, freq, loop_frames}; `night` {centre, radius, mul_hex}; `storms` [{name, v, radius, tone_hex, drift_turns_per_loop}]; Saturn's `rings` [{r_in, r_out, tone_hex}], `ring_tilt`; `swap` {above 6, below 5} | - |

- About 0.3 megapixels in all for the four giants (4 x 32,768 + 2 x 24,576 + 2 x 12,288 + 8,192 + 8,192 + 65,536), against
  4.2 megapixels for ONE 2048^2 near frame (option B).
- The tones and edge constants in `close.json` must be the far disc's own. `build_discs_v3.paint` holds them inline today,
  so the first art step is to lift the four giants' specs into one table both builders read, and to prove the far discs
  come out byte-identical after it.
- The preview is a software render of UNITY's mapping (section 5's formulas in numpy): each giant at 6, 12 and 33 px per
  far texel in a 1920 x 1080 frame, beside today's magnified far disc at the same zoom, and the swap frame pair (far at
  5.9, close at 6.0) side by side. LEAD judges the look on that sheet before UNITY builds anything. Jupiter first.
- Checks I would run: palette share per strip; seam score of each tiling strip; ink 2.0-3.0 px on the band's pivot row;
  no face read at 2x-4x (a storm oval beside a cloud is two round shapes side by side: Neptune's pair needs the look).

## 5. UNITY's half

- **A component beside DiscSprite** (say `GiantCloseView`), on bodies that have a `planets/<name>/close.json`. It shows
  when DiscSprite's own rule says near (`WantsNear`, 6 up / 5 down) and hides the far renderer then; the cut happens on
  the 12 Hz cartoon clock, as the near-frame swap does. Below the swap nothing changes.
- **Geometry only for what the camera sees.** Take the camera rect in disc space (units of the radius), grown by a margin.
  Sample x across it every 32 screen px.
  - A belt edge at v_top: y(x) = v_top - amp * sin(freq * pi * x + phase) * (1 - v_top^2), phase = 2 pi * frame /
    loop_frames with DiscSprite's own frame, so the edges move exactly as the far clip's.
  - A belt = the strip between two edges, clipped to |x| <= sqrt(1 - y^2); vertex colour = its tone. One unlit
    vertex-colour material, one draw call.
  - Strips (belt edges, the limb, storm rims, ring edges, the terminator): a ribbon along the curve, its half-width =
    texture height / 2 screen px, u = arc length in screen px / texture width, v across. The limb ribbon's pivot row sits
    on the circle. One material over a small atlas of the strips, one more draw call. The grain is a third (or a
    shader keyword on the first two).
- **Holding the strips still.** A strip mapped in screen px would swim as the camera zooms. So quantise: the strip scale
  s = 2^(round(2 * log2(zoom)) / 2) (steps of root 2), the repeat count round the whole curve an integer at each step, u
  anchored at a fixed angle of the body. Inside one step the strip is fixed to the planet and its ink is 2.1-3.0 px
  (2.5 x 0.84 to 2.5 x 1.19); at a step it re-lays on the next 12 Hz tick, which reads as the line's boil.
- **Cost (estimates, not measured):** at most about 9 belts x 62 samples x 2 vertices, the same again for their edge
  ribbons, 150 for the limb: under 3,000 vertices, rebuilt at 12 Hz and when the camera moves; 2-3 draw calls; the
  strips are 0.29 megapixels for all four giants (about 1.1 MB as plain RGBA, about 0.3 MB at one byte a pixel). It only
  exists while a giant is above the swap zoom.
- **Tests:** the pure parts (the visible x-range, a belt edge's y(x), the scale step and repeat count, the ink width
  inside 2-3 px at every zoom from 6 to 33); a capture per giant at 6, 12 and 33 and the swap pair, judged against my
  preview sheet.

## 6. The contract section it needs (proposed text, a new 11.5.1 under "Planet discs")

> **11.5.1 Giants' close view (D-128's painted close-up band).** A gas or ice giant has no `disc_near` frame. Above
> DiscSprite's near zoom it is drawn from `planets/<giant>/close.json` (the far disc's own belts as `[v_top, tone_hex]`
> from +1 north to -1 south, the edge wobble, the night crescent, storms, Saturn's rings) as flat-toned geometry, with
> tiling strips mapped at one texel per screen pixel (within a root-2 step): `planets/<giant>/limb_band` (512 x 64, the
> ink outline on `ink_row`, transparent above), `planets/common/belt_edge` (1024 x 24 mask: R = lower tone's share, A =
> ink), `planets/<giant>/spot_rim` (512 x 24), `planets/saturn/ring_edge` (512 x 16) and the screen-space
> `planets/common/close_grain` (256^2). Every strip tiles in x with a seam score <= 1.6; ink on the limb 2.0-3.0 px at
> every zoom; no faces (D-101); the tones in `close.json` equal the far disc's (one table feeds both builders). No texture
> of the close view exceeds 1024 px on a side.

## 7. What changed from the 15:5x note

That note drew the inside of the disc from a 512 x 1024 `limb_fill` texture (latitude washes). Checked against the
numbers it does not hold: 1024 px pole to pole is 4.8 px per unit on Jupiter, only 1.6 times the far disc, so at the
33x extreme one fill texel is about 20 screen px. A hard belt edge would show 20 px stairs, a soft one a smooth digital
ramp, which the style forbids. The far disc's belts are flat tones with hard wobbling edges, so the inside needs no
picture at all: flat belts plus a strip along each edge give the same face at any zoom. The fill texture is dropped; the
edge strip, the storm rims, the terminator and the screen-space grain are new.

## 8. For LEAD to rule before carding

1. **Saturn's rings in the same card?** I recommend yes (section 3.6): a sharp body inside far-resolution rings would
   read worse than today. It adds one strip and the ring table to `close.json`, and an elliptical ribbon on UNITY's side.
2. **The grain in screen space:** it needs one line in a shader (or a third draw call). Without it the close view is
   clean flat tones beside grained far art; with a baked grain it would magnify into blotches. I recommend the tile.
3. **How close can the player get to a giant in play?** D-128 called the close view "a named limit until a milestone
   lets the player park at one". If the ship never passes about 12 px per far texel near a giant, the root-2 stepping and
   the 33x tests can be cut from UNITY's half.
4. **The swap is a cut on a tick,** as the inner planets' near swap is. If a blend is wanted it is UNITY's cost.

## 9. Order of work once carded

1. BLENDER: lift the giants' specs into a shared table; far discs byte-identical (one light run, 8 discs).
2. BLENDER: Jupiter's strips, `close.json` and the software preview at 6 / 12 / 33 and the swap pair → LEAD.
3. BLENDER: Saturn (with rings, if ruled), Uranus, Neptune on the accepted look → LEAD → export.
4. UNITY: `GiantCloseView`, its tests, the captures against the preview sheet.
5. BLENDER: the art read of those captures (B-228's method).

Done so far: step 1 (B-239, with the inner set in B-240 (1): all 16 exported pngs reproduced byte for byte), step 2
(B-240, accepted), step 3's previews (B-241: Saturn accepted; Uranus and Neptune drawn). Nothing is exported until the
UNITY half is carded (LEAD: after U-207 / U-197).

## 10. Rulings and what the previews changed (23:3x)

LEAD's rulings on section 8 (22:0x): (1) Saturn's rings are in the same card; (2) the grain is a screen-space tile; (4) the
far / close swap is a cut on a 12 Hz tick; (3) how close the player gets is asked of UNITY: until it answers the previews
use 12 px per far texel as the closest, and if the flight never passes about 12 the root-2 stepping and the 33x tests
leave UNITY's half.

What drawing the previews found, each ruled by LEAD (23:1x) unless marked:

1. **The far limb is not a circle.** `Disc` draws a lumpy rim: r(angle) = 1 + 0.012 sin(3 angle + ph3) + 0.008 sin(5 angle
   + ph5), two phases per body: up to 2 % of the radius, 38 px on screen at the swap. `close.json` carries it as `rim`
   and the close view's limb and fill follow it. RULED: yes.
2. **A pigment tile per giant** (`planets/<giant>/close_pigment`, 128 x 128, over the far frame's square, a multiplier):
   the far disc's own slow tone variation (its coarse grain and pigment fields; its 0.8 px fibre is the screen grain's
   job). Without it each belt's tone shifts by a few per cent at the swap. RULED: yes.
3. **`limb_band` is 512 x 16, the ink alone.** Section 4's 64-row band with a rim wash is dropped: the far disc has no
   inner shade, and nothing new should appear at the swap. RULED: drop.
4. **The ink marks are placed by `close.json`, not by the strips.** The far disc's dashes are not on the belt edges: two
   per listed edge at fixed places, each riding its own gentler wave (its `ink_marks.dashes`), plus two groups of three
   hatches in the night crescent (`ink_marks.night_hatches`). A dash baked into the edge strip sat on the strip's rhythm
   and crossed the Spot. So `belt_edge`'s A channel is a thin ink LINE its whole length, and a mark is a short ribbon of
   it laid along the mark's own curve, over everything, as on the far disc. The far builder reads the same numbers
   (`giants_v3.MARKS`); both proofs were re-run after that change.
5. **The 2-3 px rule is the line's mean.** With root-2 zoom steps the limb's mean width stays 2.1-3.0 px; the far disc's
   own hand jitter (plus or minus 20 %) rides on top, so single spots reach about 1.7 and 3.6 px at the worst step.
   Measured in the previews: 2.34-2.59 px (Jupiter), 2.48-2.55 (Saturn), 2.49-2.53 (Neptune), 2.51 (Uranus). RULED:
   accepted as built; 11.5.1 says "mean".
6. **The outline's jump at the swap** (about 15 soft px for the far line magnified 6 times, to 2.5 crisp px; the dashes
   7.5 to 1.25) is the same jump the inner planets' near frames make today. RULED: accepted.
7. **Saturn's rings** (B-241, accepted): three flat-toned bands in the ring's own radius, the Cassini gap open to what is
   behind it; `ring_edge` (512 x 16) along every edge: a cut in tone where two bands touch, a cut in alpha at the inner
   edge and the gap's two edges; the thin ink line on the inner edge and the limb band's ink on the outer edge, as the far
   ring parts have. The upper half goes under the globe, the lower half over the globe and its outline. No grain on the
   rings (the far rings have none).
8. **Neptune's companion cloud is ONE streak up close** (B-241; mine, not yet ruled). The far disc draws it as a chain of
   17 small blobs; at the far size its scallops are under a pixel, but drawn crisply at the swap they made a segmented
   grub beside the dark storm. `close.json` gives the storm a `streak` (a capsule from the first blob to the last, the
   blobs' radius) and the close view draws that instead of the blobs. The far disc is untouched.
9. **Uranus has no tilt in the art** (B-241; for LEAD's note): `build_discs_v3` draws its three belts level, so the close
   view does too. A tilted Uranus would be a change to the far disc first.
10. **The marks' and edges' strips are fixed to the planet**: u = arc length along the edge from the body's own left, with
    a whole number of repeats round the limb, so nothing swims while the zoom holds inside one root-2 step.

11. **The flight's closest zoom is known** (UNITY's reading, via LEAD 23:5x): 6.0 screen px per far texel at the wheel's
    closest and 9.0 at the end of the entry's push-in; it never passes 12 in play. So the root-2 zoom stepping and the 33x
    tests LEAVE UNITY's half: one strip scale serves 6 to 9 (a strip texel is 1 px at 6 and 1.5 px at 9 if the scale is
    held, so the limb's mean ink runs 2.5 to 3.75 px; laid at 1.22 px per texel it runs 2.05 to 3.07 across the range).
    The previews' 12 px views show more than the game will. Neptune's cloud (point 8) was since ruled: a tapered streak
    with belt_edge's ragged edge (`streak.end_radius_share` 0.3), accepted.

The key list as it now stands (previews in `blender/preview/b240/` and `b241/`; nothing exported):

| Key | Size | What |
|-----|------|------|
| `planets/common/limb_band` | 512 x 16, tiles in x | the outline's ink alone, its centre line on row 8 (one band serves all four: every disc's ink is the same tone) |
| `planets/common/belt_edge` (variants 0, 1) | 1024 x 24, tiles in x | RGB = the lower tone's share across a ragged cut on row 12; A = a thin ink line. 0 firm (Jupiter, Saturn), 1 faint and streaky (Uranus, Neptune) |
| `planets/common/spot_rim` | 512 x 24, tiles in x | a storm's rim: the same kind of cut, rounder, no ink |
| `planets/saturn/ring_edge` | 512 x 16, tiles in x | a ring edge: a nearly clean cut on row 8; A = the thin ink line |
| `planets/common/close_grain` | 256 x 256, tiles both ways | the paper's fine grain, a multiply tile (value / 127.5), in screen space |
| `planets/<giant>/close_pigment` (x4) | 128 x 128 | the far disc's slow tone variation over the far frame's square (value / 127.5) |
| `planets/<giant>/close` (json, x4) | - | `radius_u`, `loop_frames`, `fps`, `belts` [{v_top, tone_hex, night_hex}], `edge_wobble`, `rim`, `night`, `storms` [{..., blobs, streak?}], `ink_marks` {dashes, night_hatches}, `rings` (Saturn), `swap` |

About 0.21 megapixels in all (8,192 + 2 x 24,576 + 12,288 + 8,192 + 65,536 + 4 x 16,384 = 208,896). Section 4's table
and its "0.29 megapixels" are superseded by this one.

UNITY's half (section 5) stands with these changes: the limb and the fill's clip follow `rim`; the tone is multiplied by
the pigment tile (sampled in the far frame's square) and the screen grain; ink marks are ribbons from `ink_marks`; Saturn
adds the ring bands and their edges; a storm with a `streak` is a capsule. The working reference is
`blender/scripts/build_giant_close_v3.close_view` and `ring_layer` (numpy, per pixel; UNITY's mesh is its own design).

## 11. The contract section, as ruled (replaces section 6's draft)

> **11.5.1 Giants' close view (D-128's painted close-up band).** A gas or ice giant has no `disc_near` frame. Above
> DiscSprite's near zoom it is drawn from `planets/<giant>/close.json`, which holds the far disc's own facts: `belts`
> (`v_top` from +1 north to -1 south, `tone_hex`, `night_hex`), `edge_wobble`, the lumpy limb `rim`, the `night` crescent,
> `storms`, `ink_marks`, Saturn's `rings`, and the `swap` zooms. Belts, storms and ring bands are flat-toned geometry;
> the hand-drawn part is tiling strips mapped at one strip texel per screen pixel within a root-2 zoom step:
> `planets/common/limb_band` (512 x 16, the ink outline), `planets/common/belt_edge` (1024 x 24, two variants: RGB = the
> lower tone's share, A = an ink line that marks are cut from), `planets/common/spot_rim` (512 x 24),
> `planets/saturn/ring_edge` (512 x 16); the tone is multiplied by `planets/<giant>/close_pigment` (128 x 128, over the far
> frame's square) and by the screen-space `planets/common/close_grain` (256 x 256). Every strip tiles in x with a seam
> score <= 1.6. The limb's ink is 2-3 px wide as the line's MEAN at every zoom (the far disc's plus or minus 20 % hand
> jitter rides on it). The close view adds nothing the far disc lacks and moves by the far disc's own formulas, so the
> swap is a cut on a 12 Hz tick. No faces (D-101). The tones and numbers in `close.json` come from the table the far disc
> is painted from (`giants_v3`); a change to either is proven by rebuilding the exported far discs byte for byte.
