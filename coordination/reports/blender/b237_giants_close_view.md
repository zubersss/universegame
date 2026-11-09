# B-237 · The giants up close: why a `disc_near` cannot do it, and what can (BLENDER, 2026-11-09 15:5x)

Written files-only, from the sources and the decisions; nothing rendered. **B-237 as carded ("disc_near at the inner planets'
near-disc size and format") runs into D-128's amendment (11-07), which already ruled the giants out of that format.** New
evidence since: B-228's F8 (smoke_7 of 0.6.1: Saturn's limb in stair-steps in the owner's build). D-128 names the way
forward itself: "a giants card (a painted close-up band or a shader fallback for the giants only)". This is that card's
design question, for LEAD to rule before any source.

## 1. The numbers

A near frame is the far disc's frame 0 redrawn at k x (build_discs_v3.NearDisc); DiscSprite swaps to it above 6 screen px
per far texel and back under 5 (its own comfort line). The far discs are drawn at 3 px per space unit.

| Body | Far radius (px) | k at 512² (D-128's cap) | k at 1024² (contract 11.5's frame cap) | k at 2048² (contract 2's cap) |
|------|-----------------|-------------------------|-----------------------------------------|--------------------------------|
| Earth (for scale) | 75 | 3.28 (exported) | - | - |
| Jupiter | 318 | 0.77: smaller than the far frame | 1.58 | 3.19 |
| Saturn (the body) | 288 | 0.85: smaller than the far frame | 1.74 | 3.52 |
| Uranus | 171 | 1.44 | 2.94 | (3.3 fits 1152²) |
| Neptune | 168 | 1.46 | 2.99 | (3.3 fits 1130²) |

How far the view magnifies a disc:
- smoke_7 (Saturn's limb across the screen): Saturn's radius is about 2210 px on screen, so 7.7 screen px per far texel.
- DiscSprite's comment (U-117): the ship view goes up to about 33 x.

Screen px per texel of each option (under 5 is the project's "reads fine"; the inner planets' near frames sit at 5.6-10 at
the 33 x extreme, accepted in D-128):

| Option | Saturn in smoke_7's view | Jupiter at the same zoom | Either at 33 x |
|--------|--------------------------|--------------------------|----------------|
| today (the far disc) | 7.7 | 7.7 | 33 |
| near frames at 1024² | 4.4 | 4.9 | 19-21 |
| near frames at 2048² | 2.2 | 2.4 | 9.4-10.3 |

## 2. The options

**A. Near frames at 1024² for the four giants.** Inside contract 11.5's frame cap; D-128's 512² / 1 MB near cap and its
"gain >= 2 x" floor would be waived for the giants (Jupiter 1.58 x, Saturn 1.74 x; Uranus and Neptune 2.9 x). No UNITY
change (DiscSprite picks `<key>_near` up). Cost: four frames, about 1 MB each as BC7, loaded on demand; one light run of
the existing builder with a per-planet cap. Result: smoke_7's view comes just under the comfort line; closer than that
the stairs return. Saturn's rings are separate parts (rings_back / rings_front, drawn by SpaceWorld.RingSprite, no near
swap): they would stay at far resolution beside a sharper body unless UNITY adds the same swap for them.

**B. Near frames at 2048² (Jupiter, Saturn) and ~1152² (Uranus, Neptune).** Matches the inner planets' standard. D-128's
amendment rejected it once ("it would lift the 1 MB cap and still leave the giants under 4 x"). It also needs a new strip
renderer on my side: the disc builder holds a dozen full-frame float64 arrays at 2 x supersampling, about 2 GB for a
2048² frame, over this machine's gate.

**C. A painted limb band (D-128's "painted close-up band"; my recommendation).** Above the swap zoom only an arc of a
giant fits the screen, so draw the close view the way the smooth ground is drawn (contract 11.9):
- `planets/<giant>/limb_band`: 512 x 64, tiling along the arc; the hand-drawn ink line with its jitter on one row (the
  sprite's pivot), the planet's rim wash and a soft inner shade below it, transparent above. UNITY maps it on a ring mesh
  round the disc's circumference: u = arc length, v = the signed distance from the limb, the band's width set from the
  camera so the ink stays 2-3 px on screen at every zoom.
- `planets/<giant>/limb_fill`: 512 x 1024, tiling in u, v = latitude from pole to pole: the belts and zones as painted
  washes (Jupiter's belts, Saturn's bands, Uranus's pale tilted bands, Neptune's streaks). It fills the disc inside the
  band above the swap zoom. The Red Spot and Neptune's dark spot would be separate small sprites pinned at their
  latitude and longitude (they are landmarks, not tiling).
- The far disc sheets and their idle clips are untouched below the swap zoom.
Why it answers D-128 (3): the limb stays hand-drawn ink with its jitter at every zoom (the rejected shader circle was a
vector edge), and no texture grows: about 0.6 megapixels per giant against 4.2 for a 2048² frame. Cost: a UNITY card (a
ring mesh and the mapping; the ground band's code is the model), a contract section (11.5 gains the two keys), and my
art (eight textures + two spot sprites, numpy, light). Open point for UNITY: Saturn's rings up close (the same band idea
along the ring edges, or leave them far).

**D. Do nothing now.** D-128 called the giants' close view "a named limit until a milestone lets the player park at
one". 0.6.x's owner path is Earth digging; the giants come with G1 (U-189 / U-191).

## 3. What I would do

C, carded with its UNITY half when G1's giant work starts (it is the only option that holds at every zoom and it is the
one D-128 pointed at); A now only if you want smoke_7 to read better in the next owner build without any UNITY time,
knowing it is a half-measure. I write no source until you rule.
