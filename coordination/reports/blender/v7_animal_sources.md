# Where v7 animals would come from (B-265)

BLENDER, 2026-11-10 15:2x. READING ONLY: six web searches, nothing downloaded, nothing rendered, no page's archive
opened. Every licence below is **as the listing or the search result states it**; none is verified from the file
itself, and that check (the licence text INSIDE each archive) comes before any download. A generic client; nothing of
the owner or the project in a request. D-208: no creature is carded as v7 before U-219 is read; this is paper.

## The finding in one paragraph

**No realistic CC0 animal, rigged or not, was found for any of Earth's eight.** What exists under CC0 is LOW-POLY,
STYLISED game art (flat-shaded meshes of a few hundred to a few thousand triangles), some of it rigged and animated.
Realistic animals exist as museum taxidermy scans (dense, one fixed pose, no rig), but the licences seen were CC BY and
CC BY-NC-SA, not CC0, and none found is one of our species. So a CC0 find gives v7 a SKELETON, PROPORTIONS AND A FEW
CLIPS to start from, never the look: the form has to be rebuilt toward a real animal and the fur, skin and feathers
painted in the materials, as for everything else in v7.

## The table

| Creature | CC0 candidate found | Licence as stated | Triangles | Rigged | Clips | A usable start? |
|---|---|---|---|---|---|---|
| wolf | Quaternius' low-poly animated animals (wolf, dog, cat, eagle, piranha): opengameart.org/content/animated-animales-low-poly; his itch.io page quaternius.itch.io/lowpoly-animated-animals (six animals) | CC0 (listing tag; itch.io licence field) | not stated (low poly) | yes | Death, Idle, Jump, Run, Walk on the itch.io pack; the wolf's own list not read | **YES: the best start of the eight** |
| shark | Quaternius' Lowpoly Animated Fish: quaternius.itch.io/lowpoly-animated-fish (tags: shark, dolphin, whale, manta ray; FBX, OBJ, Blend); also opengameart.org/content/shark-low-poly | CC0 (both listings) | not stated (low poly) | yes (the fish pack) | one swim clip each | **YES** |
| stag | "Deer (low poly, rigged)": opengameart.org/content/deer-low-poly-rigged | CC0 (listing) | not stated (low poly) | yes, simple (the author says they are new to animation) | none stated | a base: the rig to be checked or rebuilt, every clip to key |
| bear | "White Bear (Low poly)", listed in opengameart.org/content/cc0-3d-animals-creatures | the COLLECTION is titled CC0; the item's own page not read | not stated | not stated | not stated | a shape at most (and it is a polar bear) |
| gull | "Low Poly Seagull": whatever.blendswap.com/blend/7419 (for distant shots); Quaternius' eagle as a bird rig to learn from | a commenter thanks the author for CC0; the page's licence field not read; a .blend (my rule: no downloaded .blend is opened without LEAD's word) | not stated | not stated | not stated | no: a distant-shot mesh |
| pike | none by name; the Quaternius fish pack has generic fish (species not named) | CC0 (the pack) | | yes (the pack) | swim | a fish rig to reshape; or by script (below) |
| squid | none found | | | | | no |
| Hadal Maw | ours (an original creature): nothing to find | | | | | by script |

Also seen and NOT usable: CGTrader, Fab, TurboSquid, RenderHub and Blender Market packs (paid, royalty-free licences,
not CC0); museum scans on Sketchfab and MorphoSource (a river otter mount CC BY-NC-SA, a skull CC BY; a museum CC0
programme exists on Sketchfab but no bear, wolf, deer, gull, pike, shark or squid under it was found); OpenGameArt
items whose licence turned out different from the listing once the file was read (a commenter's report on a fish and
on a piranha): the reason every archive's own licence text is read before use.

## What building one takes (E: estimates in days of this role's work, renders included; nothing measured)

A v7 creature is a model, a skeleton, painted materials and its clips (today's v3 sheets: 48-66 drawings each: idle,
walk or swim, react, bump, flee, the wolf's follow). The renders are the small part: about 55 drawings x 12-19 s is one
lock of 11-17 minutes per creature (section 1 of v7_price_list.md).

| Creature | From | The model | The rig | The clips | As sheets, in all | As a rig for the impostor (U-219) |
|---|---|---|---|---|---|---|
| wolf | the CC0 base | reshaped and subdivided toward a real wolf, fur as strokes in the material and as cards: 1 day | the base's, checked | its walk and run re-timed to ours, the other four keyed: 1 day | **about 2 days** | the same model and rig; + UV maps and the painted maps baked for a live mesh: +0.5 day; no sheet renders |
| shark | the CC0 base | 0.5 day | the base's | swim re-timed, four keyed: 0.5 day | **about 1 day** | +0.5 day |
| pike | the fish base or by script (a lofted body, fins as plates) | 0.5 day | a spine chain: 0.25 day | 0.5 day | **about 1.25 days** | +0.5 day |
| stag | the CC0 base | 1 day (antlers by script) | rebuilt if the base's does not hold: 0.5 day | all keyed from the v3 gait tables: 1 day | **about 2.5 days** | +0.5 day |
| bear | by script on the stag's or wolf's skeleton (the found mesh is a polar bear's shape at most) | 1.5 days | shared quadruped: 0.25 day | 1 day | **about 2.75 days** | +0.5 day |
| gull | by script (a lofted body, wings as feather cards on three bones) | 1.5 days | 0.5 day | walk, fly, the rest: 1 day | **about 3 days** | +0.5 day |
| squid | by script (a mantle, eight arms and two tentacles as tubes on bone chains) | 1 day | 0.5 day | 1 day | **about 2.5 days** | +0.5 day |
| Hadal Maw | by script, from its v3 design (the largest, an original) | 2 days | 0.5 day | as its rig set today: 1 day | **about 3.5 days** | +0.5 day |

All eight as sheets: **about 18-19 days of this role's work**; as impostor rigs about 4 days more and about two hours of
sheet renders less. One shared quadruped skeleton (wolf, stag, bear) and one fish chain (shark, pike) save perhaps
2 days of that. Rigify ships inside Blender (nothing is installed), but turning it on is an add-on in use: LEAD's
ruling for part 2's figure covers it or it does not; these estimates assume plain bones built by script.

## Which have a usable CC0 start, and what I would do first

- A usable start: **wolf, shark** (rigged, animated, CC0 as listed), **stag** and **pike** as bases. None: **bear, gull,
  squid, the Hadal Maw**.
- FIRST, when a creature is carded: **the wolf**. It has the best start, the surveyor meets it on the surface in the
  first hour, and fur is the hardest material v7 has to paint: if the low-poly-base-to-painted-animal road fails, it
  fails here and cheaply. Then the shark (the same road under water). Only then choose, with those two measured,
  between a base and plain script for the rest.
- BEFORE any of it: read U-219's page (the impostor may make sheets the wrong form for creatures at scale), open each
  listing's page and the licence text inside its archive, and take glTF, FBX or OBJ, never a .blend.

## Sources read (search results; the pages themselves were not opened)

opengameart.org/content/cc0-3d-animals-creatures · opengameart.org/content/deer-low-poly-rigged ·
opengameart.org/content/animated-animales-low-poly · opengameart.org/content/shark-low-poly ·
quaternius.itch.io/lowpoly-animated-animals · quaternius.itch.io/lowpoly-animated-fish ·
whatever.blendswap.com/blend/7419 · roadtovr.com/sketchfab-public-domain-3d-assets (Sketchfab's CC0 museum programme) ·
sketchfab.com/FloridaMuseum (taxidermy scans; licences per item)
