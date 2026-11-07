# C2 Earth creature re-ink list (BLENDER, 2026-11-06, D-109 while-waiting item)

Basis: Bible 4.1 §7.1 Earth roster, §9.3 (creatures keep faces: pie-cut eyes, friendly or neutral,
D-087/D-101), contract v3.1 §11.2 creature clips (idle, walk — fliers fly, swimmers swim — react,
bump, flee or follow; caps idle 8-12, walk/fly 12-16, others ≤ 16) and v3.1 ink (2-3 / 1-1.5 px,
interior detail + texture marks, mid + deep tones). The proven pattern is Gus (B-113/B-127):
one `draw_<name>(d, M, pose)` function, pose tables per clip, ink-behind on small parts, a
cartoon scale that reads at 1x, and the below-ground check passing.

| # | Creature (§7.1) | Role / habitat | Cartoon size at 1x | Clips (frames) | Interior detail (v3.1) | Notes |
|---|---|---|---|---|---|---|
| 1 | Stag | grazer, flees; plains/forest | ~1.8 m tall incl. antlers (≈ 115 px) | idle 10, walk 12, run 12 (flee), react 8 (head up, ears swivel), bump 10 | fur tufts on chest and tail, antler tine seams, hoof splits, flank hatch | antlers are the secondary motion (wobble on stops); keep the face soft, big pie eyes |
| 2 | Grey wolf | pack, night; forest/taiga | ~1.0 m tall (≈ 64 px) | idle 10, walk 12, run 14, react 8 (ears up, sniff), bump 10, follow 12 | ruff fur marks, tail fur strokes, paw pads, a muzzle seam | neutral, not menacing (D-087): no bared teeth; howl as a one-off special ≤ 16 later |
| 3 | Brown bear | territorial; forest | ~1.6 m at the shoulder on all fours (≈ 100 px) | idle 12 (breathing sway), walk 12, react 10 (rears up halfway, sniffs), bump 10, flee 12 | thick fur hatch, claw lines, ear rims, belly deep tone | "territorial" reads as a huff and a bounce, never an attack; biggest land sheet: check frame size ≤ 2048 packing |
| 4 | River pike | rivers | ~0.9 m long (≈ 58 px) | idle 8 (hover, fin ripple), swim 12, react 8 (dart + eye-pop), bump 8 | scale arcs, fin rays, lateral-line seam | contract has no "swim": propose swim = the swimmer's walk (12-16, like fly), one line in §11.2 + ArtRules.ClipCap |
| 5 | Gull | coast | done (Gus, B-113/B-127) | idle, walk, react, bump, fly | done | the reference creature for this list |
| 6 | Reef shark | ocean | ~2.4 m long (≈ 154 px) | idle 10 (slow glide), swim 14, react 8 (turn away), bump 10, follow 12 | gill slits, fin seams, belly countershade as the mid tone | friendly-neutral: closed mouth, round pie eyes; same "swim" note as the pike |
| 7 | Giant squid | ocean, depth 150+ | ~4 m with arms (≈ 256 px) | idle 12 (arm curl wave), swim 12 (jet pulse = squash/stretch), react 10 (ink-puff + eye-pop), bump 10 | sucker dots along the arms, mantle fin seams, chromatophore specks | rubber-hose arms are the natural secondary motion; the ink-puff is a round cartoon cloud (no fx sheet needed) |
| 8 | Hadal Maw (Grand creature, ex-apex) | trench ambusher with a lure | ~40 m (Bible) → drawn as a set piece | idle 12 (lure bob), react 12 (lure flare, slow turn), scan-pose 8 (the full Survey scan end state, D-087) | lure filament, jaw seam, bioluminescent dots as a drawn tone (no emission) | too big for one sheet at 1x: propose a rig set (§11.3 style parts: head, jaw, body segments, lure) like the flora, under `creatures/earth/hadal_maw/rigset`; LEAD decides |

## Proposed order and budget

1. Stag, wolf, bear (the land walkers the player meets first) — one sheet each, frames ≤ 192 px
   except the bear (≈ 224 × 160), each ≤ 1 atlas.
2. Pike, reef shark, giant squid (water) — after the "swim" cap ruling.
3. Hadal Maw as a rig set — after LEAD rules on the rig approach.

Atlas budget (D-089: ≤ 8 per planet): surveyor 1, Pilgrim side 5 + puff 1 (PPU 64 plan), flora 1,
gull 1 already make 9 for an Earth scene with the ship landed. The creature sheets push this
further, so the Pilgrim PPU question (B-122 split, BLENDER_STATUS) and a shared creature atlas
(several small creatures on one 2048² sheet, per-creature json pointing at frame ranges) are the
two levers I would propose to LEAD.
