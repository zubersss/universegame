# C1 — Player, ship, space (draft at cycle 259; final on the U-106 commit)

**What you can do in this build (MERIDIAN 0.4.0).** Walk the drawn surveyor across Earth's plains among six cartoon plants, dig and build, board the hand-drawn Pilgrim and fly it yourself: thrust lifts, tilt steers, nothing burns fuel. Climb through a sky that darkens into stars, cross the Escape Line past its painted sign, fly a solar system of painted planets, and land on Mars by hand. The HUD is three painted gauges and handwritten readouts.

**How we know it works.** The core loop ran green twice under scripted input. Frame times stay between 6 and 13 ms on every scene. Memory peaks at 966 MB against a 2 GB cap, textures at 318 MB against 512. Returning to a visited planet grows memory under 9 percent. Every drawn asset passed the ten-point style check.

**Known limits.** The first boot after a fresh build loaded in 5.5 s against a 5 s budget (warm re-run pending; a cold-boot fix is carded). Up close, planets other than Earth, Luna, Mars, Venus and Mercury still show their painted texels. The camp props are grey stand-ins until C2 Earth.

**What's next.** C2 Earth: props, land and water creatures, forest and coast backdrops, the painted Sun. Then Mars, already designed.

**How to run it.** Open `Build/MERIDIAN_0.4.0/MERIDIAN.exe`. W or Space thrusts, A / D tilts, E boards and leaves the ship.
