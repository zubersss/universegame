# MERIDIAN art v7: the living painting (D-205)

Supersedes docs/STYLE_V6.md as the target. v6 stays in the repo as history; nothing of it ships.

## 1. What the owner asked for (2026-11-10, 13:3x)

"You dont have to draw it. Find another way, look everywhere, every method, and use the one that will get you the
best and closest results. It doesnt have to be exactly like the jungle book. I just want it to look like an animated
movie or a book came to life: highly detailed drawing and painting like art that looks realistic and moves like a
realistic world with wind and physics, but its a painting. A walking, highly detailed living painting."

So the target is no longer one film. It is:
1. **A painting**: brushwork, painted light, no photo look, no vector look, no pixel look.
2. **Highly detailed and realistic**: real anatomy, real plants, real materials, real light and shadow.
3. **Alive**: wind in every leaf, things that swing, fall, bend and settle by physics, light that moves.

## 2. The method, and why this one

Looked at (LEAD, 13:3x; sources in coordination/REVIEW_LOG.md):
- **Drawing by code (v6's way).** Reached its ceiling: flat, sparse, stiff. Dropped.
- **AI-painted pieces** (B-251). Better drawn than any rule, but one generator, the owner's credits are spent, it
  cannot make a figure that moves, and its light is baked. Kept as a SUPPLEMENT for scenery.
- **Real-time 3D with a paint filter over the whole screen.** The laptop's graphics chip is an integrated Intel one:
  a full-screen paint filter every frame is the costliest way and the easiest to make shimmer. Not first.
- **Real 3D, rendered and painted in Blender, played as 2D** (how "painting come to life" games such as Ori and the
  Blind Forest were made: characters modelled and animated in 3D and rendered to sprites, on painted layers with
  heavy parallax). CHOSEN. Real models give real anatomy, cloth, bark and leaves for free; a film-style light rig
  gives real light and shadow; Blender's compositor turns each render into paint (the anisotropic Kuwahara filter,
  then brush and canvas texture); the game pays nothing for it at run time; the team already has the tool and a
  role named after it.

## 3. The pipeline

**Figures (the surveyor, later every creature)**
1. A real 3D figure: a CC0 human base mesh (candidates: Blender Studio's human base meshes; MPFB / MakeHuman's
   CC0 assets) with the suit, boots, pack, antenna and tools modelled on it. Original design; no likeness.
2. A skeleton; the clips keyed on it from B-250's pose tables (the timings, contact frames, ground speeds, hand
   sockets and stow table stand), with cloth, straps, hair and the antenna SIMULATED and baked (follow-through
   comes from physics, not from a rule).
3. Rendered from the side camera under the scene's light, larger than shown, through the paint pass, to frame
   sheets: colour, plus a normal map so the game's lights can touch the figure.
4. The paint pass must hold still between frames where the figure holds still (no crawling noise); a small
   brush "boil" is welcome, a shimmer is a fault.

**Scenery**
1. Real 3D plants, trunks, roots, rocks and ground from CC0 scan libraries (Poly Haven lists tropical plants, ferns,
   trees, dead trunks, roots, grass, mossy rocks), at modest texture sizes, set dressed in Blender like a film set.
2. One sun, one sky, haze by depth. Rendered in depth layers with clean alpha, each through the paint pass
   (broader strokes far away, finer near).
3. Every near plant is ALSO rendered alone, with its pivot at the root, so the game can move it.
4. AI-painted plates and the stroke sheets (docs/art_sources/v6_painted/) may be mixed in where they read better.
5. Underground: scanned earth, rock and root textures through the same paint pass, as tiles on today's sizes.

**Alive, in the game (UNITY)**
1. A wind field (slow gusts crossing the screen) that bends every plant sprite from its root, more at the tips;
   the surveyor passing through pushes leaves aside.
2. Physics: hanging vines and lianas as chains, grass that springs back, loose things that fall and settle.
3. Air: drifting leaves, pollen and dust in the light; shafts of light that breathe; cloud shadow sliding
   over the ground.
4. Light: the game's 2D lights on normal-mapped sprites (time of day, the smelter's glow, the Beam).
5. Many parallax layers. All of it inside the frame and memory budgets, measured on the built player.

## 4. Rules that carry over

Original designs only; nothing of any film copied or traced (the study stills stay git-ignored). D-087 (a tool,
never a weapon) and D-101 (no faces on plants or objects). Every outside asset is CC0 or better, listed with its
source, licence and hash in the credits; raw scans never ship, only our renders of them. Figures and scenery are
drawn large and only ever shrunk (D-198). No pixel art, no enlarged pixels.

## 5. Honest limits

- It will look like a painted, lit, moving picture book, not like hand animation: the motion is as good as the
  keys and the simulation.
- The laptop has 7.6 GB and an integrated graphics chip: renders are small jobs done one at a time, and the live
  effects are bought with frame time that must be measured.
- More frames (smoother motion) cost texture memory; the pilot states the price of 12 and of 24 drawings a second.

## 6. How it arrives

A PILOT first (B-258 + U-216), judged beside the old frame, then shown to the owner MOVING (a short clip on a
page). Only after the owner's yes: the surveyor's full clip set, the camp's stage, then the rest of Earth.
