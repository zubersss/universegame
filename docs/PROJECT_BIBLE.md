# MERIDIAN — Project Bible (single source of truth)

Owner: LEAD. Workers read; only LEAD edits. Changes are logged in `coordination/DECISIONS.md`.
Version: 5.4 (D-207, 2026-11-10, the owner: "pass it if you can": §11.1's texture line rises from 512 MB to 1,024 MB loaded for art v7, bounded by the unchanged 2.0 GB working set, measured on the built player). 5.3 (D-175: no Skill Tree undo except a New Expedition (prestige) at Rank 10, with a permanent stat multiplier; §8.1). 5.2 (D-174, 2026-11-08, the owner's 0.5.0 playtest: a progression digging game: the dig run, the Surface Line, depth tiers, the planet ladder, the Skill Tree; §8.1). 5.1 (D-162: digging stays, reimagined as round cartoon carving with buried finds). 5.0 (D-161, 2026-11-08: the owner drops the Terraria layer: smooth cartoon ground, mining by resource nodes; D-158: the flight with weight). 4.1 (D-100..D-105, 2026-11-06: owner C0 feedback: thinner, more detailed ink with two shadow tones; faces only on people and animals; the Pilgrim stands upright; fully manual flight with no fuel of any kind (launch or skip), control never leaves the player). 4.0 = art direction v4 (D-086..D-091); 3.x = stage and feel (D-076..D-085); 2.x = 3D rehaul (D-062). The Lead bumps the version on every edit.

> **v5.0 (owner, 2026-11-08, D-161). This block overrides anything below that says otherwise.** MERIDIAN is a cartoon space game, not a block sandbox. (a) The ground on every planet is a smooth, continuous drawn curve: rolling hills, gentle slopes up to ~35° that you walk, cliffs with rounded lips, the ground's body drawn below the surface; no tiles, stair steps or block faces are ever drawn, and collision follows the curve. (b) Digging stays, reimagined (D-162): the hidden grid is drawn and collided as one smoothed outline, so the Rig carves round, ink-rimmed scoops and tunnels (never squares) into a drawn cartoon cross-section (strata, pebbles, roots, ice lenses, fossils), and "place" piles earth back as rounded mounds, ramps and bridges; there is no hotbar of block types and no free-form block building. (c) Resources come from cartoon resource nodes on the surface and from buried finds the Survey scan marks (ore and crystal pockets, ice lenses, relics and data caches, Warden vault doors) that you dig up; item ids, yields and prices are unchanged, and each planet keeps its only-here (Mercury's Solarite is cut by the Beam in the twilight window). (d) Building is placing cartoon camp pieces and the Builder kit on the ground (props). (e) The gas giants' floes are rounded cloud-ice islands with painted haze below. (f) The flight has weight (D-158): a throttle spool, the tilt's inertia, air drag that thins to nothing at the Escape Line, a sound barrier; the ship view is 30 m tall, widening with speed. Gravity ratios stay exact (pillar 1).

> **v4.1 (owner C0 feedback, D-100..D-104).** Keep the look (watercolour meadow, layered clouds, the surveyor). Ink at half the C0 weight with finer interior detail and a second shadow tone (§9.1, §9.7). Faces only on people and animals: plants, rocks, crates, the ship and the planets have none (§9.3). The Pilgrim is an upright rocket on its tail (§4.3). The player flies the ship by hand from the first second to orbit and back, with no fuel requirement and no moment where control is taken away (§4.3, §5.2, §5.3, §6). Gravity ratios stay exact.

Sections: 1 Vision · 2 Setting and story · 3 The solar system in game · 4 Physics and
numbers · 5 Views and transitions · 6 Controls · 7 The eight planets · 8 Systems →
milestones · 9 Art style guide · 10 Technical architecture · 11 Performance budgets ·
12 Milestone plan · 13 Glossary

---

> **Art direction v4 (owner, D-086, 2026-11-06). This notice overrides every older line below.**
> MERIDIAN now looks and moves like a 1930s hand-inked rubber-hose cartoon (the era and its
> techniques, never any existing game's characters, logos, fonts or assets). §9 is the new art
> bible. Systems stay: the 8 planets, real gravity, side view on planets, top-down space, Escape
> Lines, digging/building, exploration, creatures, activities, survival meters.
> **Superseded by v4:** the 3D look (D-062: PBR, glb models, the perspective rail, block meshes,
> §10.4–10.6 and §10.10 as written); pillar 3 "Realistic 2D"; every "realism" or "no cartoon"
> rule. Art is 2D again: sprites, sprite sheets, painted parallax PNGs, 2D bones (§9, contract §11).
> **Cancelled (D-087): all combat.** No weapons (the Lance, Pulse cannon), parry, hit stop, fight
> zoom, bosses or boss phases, bullet patterns, health bars, kills, bounties, space combat, the
> Shrike fighter, hull/suit shields. Creatures are friendly or neutral. Replacements:
> - A creature or hazard **bump** knocks the player 0.8 m with dizzy stars; it never subtracts
>   health (there is none). Hazards (heat, cold, pressure, radiation, toxic, falls ≥ 24 m/s) drain
>   **Suit power**; at 0 the surveyor **conks out**: dizzy stars, iris-out, wake at the last base or
>   ship with the cargo kept (pillar 5). Suit power and oxygen are the only meters.
> - **Apexes become Grand creatures**: a non-combat encounter solved with the planet's systems
>   (hazard modules, Grapple, Float cells, light, the ship), ending in a full Survey scan. The
>   reward (Datacore, "only here" resource) is unchanged. Read "kill/hunt/fight" in §7 that way.
> - **Wardens** stay as over-mining enforcement but never shoot: they ring a bell, then tow the
>   player out of the area and lock the Beam there for 5 min.
> - **Red Hollow** become rival salvagers (races, deliveries, trades), never a fight.
> - Rig modules: Beam, Survey, Builder, Grapple (slot 2 retired). The air dash stays (movement).
> Milestones: R1 closes as is (D-088); S1, R2, R3 and the 3D M4 row are superseded by C0–C4
> (§12); M3–M6 gameplay scope stands minus combat.
> Where an older sentence says "model", "glb", "PBR", "lit" or "rail camera", read §9/§10 v4.

## 1. Vision and pillars

**Pitch.** A 2D survival-exploration game with the breadth of a modern space sandbox, set
in our real solar system. Eight landable planets, each a different world because the real
physics make it one.

**Pillars** (when two rules conflict, the higher pillar wins):
1. **Real physics you can feel.** Gravity ratios are exact. A jump on Mars is 2.6× an
   Earth jump; on Jupiter you need a jetpack to clear a step. Thrust, heat, cold,
   pressure, and radiation follow the real planet.
2. **Every world matters.** Each planet has a resource, a creature, and an activity found
   nowhere else, so the player goes everywhere.
3. **A living 1930s cartoon (v4, D-086).** Hand-inked rubber-hose characters, flat cel colour,
   painted watercolour backgrounds, a gentle film treatment; everything on a surface moves.
   Original designs only, never mistakable for any existing cartoon or game.
4. **Runs on an 8 GB laptop at 60 FPS, under 2 GB in play.** The look comes from technique
   (animating on twos, shared rigs, small tiled overlays, one post pass), never brute force.
5. **The player is never stuck.** Every hard state (a thruster too weak for Jupiter, dead on
   Venus) has a recovery path.

---

## 2. Setting and story (original)

**Year 2318.** Humanity lives on Earth and a handful of Waystations; the rest of the
system is wild. 112 years ago the survey ship *Meridian* left on an eight-planet expedition
and vanished. Since then, engineered life appeared on every planet ("the Sowing"), guarded
by autonomous drones called **Wardens** that punish anyone who strips a world bare.

**You** are a newly licensed Surveyor for **the Survey**, the catalogue guild that pays in
**Datacores** for scans and **Scrip** for contracts. Your first scan on Earth picks up a
*Meridian* beacon on Mars.

**Main story — "The Meridian Line".** One beacon per planet, found in order of physical
difficulty. Each decode is a story chapter and unlocks one blueprint:

| Planet  | Chapter beat (one line)                                             | Blueprint unlocked         |
|---------|---------------------------------------------------------------------|----------------------------|
| Earth   | The Survey's archive: *Meridian* was carrying seed vaults.          | Survey module (Rig)        |
| Mars    | First beacon: the crew began the Sowing deliberately.              | Perchlorate oxidizer       |
| Mercury | Flare-scarred log: half the crew died testing heat shielding.      | Solarite capacitor         |
| Venus   | A floating station still running: the Wardens were built here.     | Float cell Mk1             |
| Saturn  | A ring-mining rig: they wound Skip Drive coils from helium-rain condensate. | Skip Drive Mk2             |
| Uranus  | Diamond-rain ballast logs: the crew split over going on.            | Deep-diamond Rig tip       |
| Jupiter | Radiation-fried vault: the captain's choice to stay with the Sowing. | Thruster Mk3               |
| Neptune | *Meridian* itself, alive in the Great Dark Spot, broadcasting.       | Ending choice              |

**Ending choice.** Broadcast the truth (Wardens stand down; worlds open to mining; factions
contest them) or keep the Sowing (Wardens stay; ecosystems thrive; the Survey gains power).
Two short epilogues; the sandbox continues either way.

**Factions.** The Survey (missions, cataloguing, Datacores) · Halcyon Freight (traders; run
the Waystations; cargo contracts) · Red Hollow (outlaws in the asteroid belt; pirates,
bounties, black market) · Wardens (not joinable; automated enforcement).

---

## 3. The solar system in game

**Time.** 1 real second = 72 game seconds (an Earth day is 20 real minutes). Each planet
rotates at its real rate except where noted:

| Planet  | Real solar day | In-game cycle | Note                                                        |
|---------|----------------|---------------|-------------------------------------------------------------|
| Mercury | 176 d          | override      | Terminator advances 1 m per 6 s real so the twilight band moves within a session |
| Venus   | 117 d          | 80 min        | Uses the cloud-top super-rotation (4 Earth days), where the player lives |
| Earth   | 24 h           | 20 min        |                                                             |
| Mars    | 24.6 h         | 20.5 min      |                                                             |
| Jupiter | 9.9 h          | 8.3 min       | Fast sky cycles                                             |
| Saturn  | 10.7 h         | 8.9 min       |                                                             |
| Uranus  | 17.2 h         | 14.3 min      | Axial tilt 98°: seasons change which hemisphere sees the Sun |
| Neptune | 16.1 h         | 13.4 min      |                                                             |

**Top-down layout (compressed).** Distances and radii are compressed with a 0.6 power law
relative to Earth so everything fits on one map while keeping the order and feel.
Positions are static in M1; slow orbital drift (1 orbit per 6 real hours for Earth,
scaled by real period) is added in M5.

| Body     | Orbit radius (units) | Visual radius R (units) | Atmosphere Ring 1.2R | Gravity Well 4R | Landable |
|----------|----------------------|-------------------------|----------------------|-----------------|----------|
| Sun      | 0                    | 300                     | —                    | 1200 (kill zone < 360) | No |
| Mercury  | 1,150                | 14                      | 17                   | 56              | Yes      |
| Venus    | 1,650                | 24                      | 29                   | 96              | Yes      |
| Earth    | 2,000                | 25                      | 30                   | 100             | Yes      |
| Mars     | 2,550                | 17                      | 20                   | 68              | Yes      |
| Belt     | 3,200–4,000          | asteroids 1–6           | —                    | —               | No (mine)|
| Jupiter  | 5,400                | 106                     | 127                  | 424             | Yes      |
| Saturn   | 7,700                | 96 (rings to 220)       | 115                  | 384             | Yes      |
| Uranus   | 11,800               | 57                      | 68                   | 228             | Yes      |
| Neptune  | 15,400               | 56                      | 67                   | 224             | Yes      |

Moons (Luna, Phobos, Deimos, Io, Europa, Titan, Triton…) are rendered bodies with small
wells (R 3–8 units, well 3R) and are not landable. Waystations: Earth orbit (start), Mars
orbit, Belt (Red Hollow black market), Saturn orbit (Halcyon).

**Ship speeds (top-down).** Cruise 80 u/s · Boost 160 u/s (no fuel, D-103) · Skip Drive
1,200 u/s after a 3 s spool, no fuel (D-105: the spool and a 10 s cool-down after each skip are its only limits), disabled inside a Gravity Well.
Earth → Mars ≈ 7 s cruise; Earth → Neptune ≈ 13 s skip (layout distance / 1,200 u/s; D-054).

---

## 4. Physics and numbers

### 4.1 Gravity (exact ratios; absolute values may be tuned together, never separately)

| Planet  | g (m/s²) | × Earth | Escape velocity (km/s) | Thruster that climbs (§4.3; no fuel, D-103) |
|---------|----------|---------|------------------------|---------------------------------------------|
| Mercury | 3.70     | 0.38    | 4.3                    | Mk1                                         |
| Venus   | 8.87     | 0.90    | 10.4                   | Mk1                                         |
| Earth   | 9.81     | 1.00    | 11.2                   | Mk1                                         |
| Mars    | 3.72     | 0.38    | 5.0                    | Mk1                                         |
| Jupiter | 24.79    | 2.53    | 59.5                   | Mk3 (Mk2's 20 m/s² cannot lift off)         |
| Saturn  | 10.44    | 1.06    | 35.5                   | Mk1 (net 1.56 m/s², slow; Mk2 comfortable)  |
| Uranus  | 8.69     | 0.89    | 21.3                   | Mk1                                         |
| Neptune | 11.15    | 1.14    | 23.5                   | Mk1 (net 0.85 m/s², a crawl; Mk2 comfortable) |

`PlanetConfig` ScriptableObjects hold these values; an EditMode test asserts every ratio to
±0.5%. `Physics2D.gravity` is set per planet on load. Gravity affects the player, creatures,
dropped items, projectiles, debris, and the ship in side view; in top-down it drives well pull.

### 4.2 Movement (side view)

Jump impulse is fixed; gravity is real; upgrades scale the impulse, never gravity.

| Quantity                               | Value / formula                                 |
|----------------------------------------|-------------------------------------------------|
| Walk / sprint speed                    | 4.0 / 6.5 m/s on every planet                   |
| Jump take-off speed v₀                 | 7.00 m/s (Earth jump height 2.5 m)              |
| Jump height h                          | v₀² / 2g → Mercury 6.6 m, Venus 2.8, Earth 2.5, Mars 6.6, Jupiter 1.0, Saturn 2.3, Uranus 2.8, Neptune 2.2 |
| Servo upgrades (Envirosuit)            | Mk1 +15% v₀, Mk2 +30%, Mk3 +45% (Jupiter: Mk2 clears a 1 m step reliably) |
| Fall damage                            | None below 12 m/s impact; lethal at 24 m/s (unupgraded). Safe drop = 72/g m: Earth 7.3 m, Mars 19.4, Jupiter 2.9 |
| Terminal velocity (m/s, play layer)    | Mercury 60 (no air; design cap), Venus 20, Earth 50, Mars 55, Jupiter 45, Saturn 48, Uranus 50, Neptune 50 |
| Coyote time / jump buffer              | 0.10 s / 0.12 s                                 |

**Feel (v3, D-076/D-078): snappy, readable, physically honest.** Everything below changes
velocities, timers and the *visual* root only; gravity, v₀ and the jump heights above are
untouched, and `FeelTests` proves every planet's jump height to ± 1 cm.

| Quantity | Value |
|----------|-------|
| Ground acceleration / braking | 60 / 80 m/s² (walk speed in 0.07 s; stop in 0.05 s); a turn flips facing at once and reverses velocity within 0.08 s |
| Air acceleration | 30 m/s² |
| Jump cut | releasing Space while rising caps the remaining upward speed to 40 % (variable height; the maximum height is unchanged) |
| Air dash | Shift tapped while airborne: 9 m/s in the facing direction for 0.18 s (1.62 m on every planet); vertical speed held at 0 for those 0.18 s, then real g resumes at once; one per airtime, refreshed by landing or a successful parry; 0.35 s cooldown; no invulnerability |
| Parry | C: active window 0.12 s, whiff recovery 0.40 s (no cancel), on the ground and in the air. A parried melee attack does 0 damage and staggers the attacker for 1.2 s; a parried projectile (Warden bolt, thrown shard, spit) is reflected along the aim; a parry refreshes the air dash and gives 0.3 s of flash |
| Hit stop | none (D-087). Bumps and conk-outs never pause the clock; the squash on the visual root is the whole reaction |
| Hit reaction (player) | knocked 0.8 m away from the hit over 0.12 s, a 2-frame white flash, the `hit_react` clip; `hurt` stays for environmental damage |
| Hit reaction (creature) | knocked 0.5 m, flash, squash 0.85 for 0.12 s, `hit_react` clip; a staggered creature plays `stagger` |
| Squash and stretch (visual root only, volume-preserving: width = 1/√height) | crouch anticipation 0.8 tall over the first 0.06 s of the jump (the body leaves the ground on the input frame; the crouch is drawn over the first frames of the rise, never as an input delay, D-084); take-off stretch 1.25 for the next 0.08 s; landing squash 0.7 at ≥ 6 m/s impact (scaled linearly from 1.0 at 2 m/s) recovering in 0.18 s with one overshoot to 1.05; dash stretch 1.3 along the dash; hit squash 0.85. Colliders, the Rigidbody and gravity never scale |
| Clip timing | surveyor and apex clips at 60 fps, creatures at 30 fps; every action clip has 2–4 frames of anticipation and an overshoot key on the follow-through; a hit reads within 2 frames |

**Jetpack** (thrust in m/s² while its charge lasts; net lift = thrust − g; recharges in 2 s on ground; a charge, not a fuel, D-105):

| Mark | Thrust | Burn | Mercury | Venus | Earth | Mars  | Jupiter | Saturn | Uranus | Neptune |
|------|--------|------|---------|-------|-------|-------|---------|--------|--------|---------|
| Mk1  | 14     | 3 s  | +10.3   | +5.1  | +4.2  | +10.3 | −10.8*  | +3.6   | +5.3   | +2.9    |
| Mk2  | 20     | 4.5 s| +16.3   | +11.1 | +10.2 | +16.3 | −4.8*   | +9.6   | +11.3  | +8.9    |
| Mk3  | 30     | 6 s  | +26.3   | +21.1 | +20.2 | +26.3 | +5.2    | +19.6  | +21.3  | +18.9   |

\* Negative net lift slows falls but cannot climb; Jupiter requires Mk3 (story-gated at the
Uranus beacon). **Float cells** (giants only) add constant buoyancy: Mk1 +6 m/s², Mk2 +12,
usable only below the Datum where the air is dense enough.

### 4.3 Ship in side view

| Quantity             | Value                                                                 |
|----------------------|-----------------------------------------------------------------------|
| Thruster Mk1/Mk2/Mk3 | 12 / 20 / 35 m/s² vertical; lateral 60% of vertical                   |
| Climbs where         | thrust > g, by physics alone (D-106): Mk1 climbs everywhere but Jupiter (a crawl on Neptune and Saturn), Mk2 climbs those two comfortably, Mk3 is the only thruster that lifts off Jupiter. No gate on top of the physics; the HUD shows thrust-to-weight and warns in amber below 1.2 |
| Fuel                 | None (D-103). The ship always has thrust; the only limit is thrust-to-weight: it climbs only where the thruster's acceleration exceeds g (Jupiter needs Mk3). Launch Fuel, tanks and the launch burn are removed |
| Orientation          | Upright (D-102): the rocket stands on its tail on the ground and flies nose-up inside the atmosphere. Thrust acts along the ship's own up axis; **A/D tilt** it up to ±35° for sideways travel; it hovers where thrust = g, climbs above, sinks below. Legs at the tail |
| Control              | Manual from the first second (D-103): the player presses thrust and lifts off; no auto-launch, no cutscene, no input lock at any point, including both transitions (§5.2, §5.3). Launch and landing are the same flight in opposite directions |
| Landing              | Legs deploy below 10 m altitude. Touchdown ≤ 6 m/s vertical: clean. 6–15 m/s: hull damage proportional. > 15 m/s: crash (ship survives, 30% hull, cargo intact) |
| Stranded safeguard   | HUD warns before landing when thrust < g. A Distress Beacon summons Halcyon recovery to the nearest Waystation for 500 Scrip or 10% of cargo |

### 4.4 Top-down gravity wells

Inside a planet's Gravity Well (r ≤ 4R) the ship is pulled toward the center with
`a(r) = k_well × g_planet × (R / r)²`, `k_well = 1.63` (chosen so Earth pulls 1.0 u/s² at its
well edge). At the Atmosphere Ring Earth pulls 11.1 u/s², Jupiter 28.1 u/s². Top-down
thrust: Mk1 30 u/s², Mk2 45, Mk3 70; a Mk1 ship always escapes any planet's well from outside 1.6R and the Sun's from outside r ≈ 810 (≈ 2.7 R☉).
The Sun's well pulls with g = 274 m/s² but uses its own k_sun = 0.80 instead of k_well (D-022): 14.9 u/s² at Mercury's orbit (half of Mk1 thrust), 30 u/s² at r ≈ 810, 152 u/s² at 1.2R; it kills the ship inside 1.2R (360).

---

## 5. Views and transitions

### 5.1 Side view (on a planet)

**Stage camera (v3, D-076).** A perspective rail (FOV 35°, `SideView`, U-072) that frames the
play plane 18 m tall at 1080p (60 px/m; the mouse-wheel zoom, 12–28 m tall, stays as a player
option). The camera behaves like a theatre set seen from the stalls: it follows sideways
smoothly and holds its height; the player moves within the frame, not the frame around the player.

| Rule | Value |
|------|-------|
| Horizontal follow | dead zone ± 1.5 m around the frame centre; outside it the camera eases with a 0.25 s critically damped follow; look-ahead 2 m in the facing direction eased over 0.6 s; camera speed never exceeds player speed + 2 m/s |
| Vertical hold | the frame bottom sits 3 m below the *stage floor*: the ground height under the player, sampled from the terrain and smoothed over 0.8 s. Jumps (≤ 6.6 m) and jetpack hops never move the camera. The camera moves vertically only when the player leaves the middle 60 % of the frame, at ≤ 6 m/s; a fall longer than 10 m switches to a 0.4 s follow until landing |
| Fight zoom | ≥ 2 hostile creatures within 14 m, or an apex within 25 m: the frame grows to 22 m tall (apex: 26 m) over 1.0 s and returns over 2.0 s after 3 s of calm; the stage-floor rule holds throughout |
| Impact | a hit on the player: 0.15 m shake for 0.10 s (position only, never rotation); no other shake (no kills, no hit stop, D-087) |
| Digging and building | unchanged: the frame holds while the player digs down until the 60 % rule moves it |
| Photo mode | `P` orbit (U-080) unchanged |

The world is a horizontal cylinder (wraps). Coordinates are tiles = meters.

| Planet  | Width (tiles) | Height | Datum y (surface or 1-bar cloud top) | Escape Line altitude above Datum | Escape Line y | Crush Line y |
|---------|---------------|--------|--------------------------------------|----------------------------------|---------------|--------------|
| Mercury | 2048          | 500    | 320                                  | 120                              | 440           | —            |
| Venus   | 4096          | 1000   | 320 (habitable cloud deck at y 770)  | 600                              | 920           | —            |
| Earth   | 4096          | 800    | 320 (sea level)                      | 400                              | 720           | —            |
| Mars    | 3072          | 640    | 320                                  | 250                              | 570           | —            |
| Jupiter | 4096          | 2000   | 1100                                 | 800                              | 1900          | 100          |
| Saturn  | 4096          | 2000   | 1100                                 | 700                              | 1800          | 100          |
| Uranus  | 4096          | 2000   | 1100                                 | 600                              | 1700          | 100          |
| Neptune | 4096          | 2000   | 1100                                 | 650                              | 1750          | 100          |

The **Escape Line** is drawn in-world as a faint, slowly scrolling band of light with the
label "ESCAPE" and on the HUD as a marker on the altitude bar. The ship's HUD shows
altitude, vertical speed, tilt, and thrust-to-weight.

### 5.2 Launch: side → top-down

Trigger: the ship's center crosses the Escape Line with upward velocity, under the player's
own thrust (D-103: there is no auto-launch).
1. 0.35 s: the iris closes on the ship while the player keeps flying it; input is never
   locked, the HUD stays until the screen is black.
2. ≤ 0.5 s black: `PlanetSide` scene unloads; `Space` scene is already loaded (Core keeps it
   resident but inactive) and activates.
3. Ship placed on the planet's Atmosphere Ring at the angle matching its longitude
   (longitude = x / width × 360° plus the planet's current rotation), velocity 20 u/s
   outward, heading outward, 1 s invulnerability; top-down controls and HUD are live on the
   first visible frame while the iris opens (0.35 s).
Total ≤ 1.5 s; player state (hull, cargo) is carried in `GameState`, never re-read from disk.
The player's held inputs carry across: a held thrust key keeps thrusting in space.

### 5.3 Entry and landing: top-down → side

Trigger: the ship's center crosses a landable planet's Atmosphere Ring with inward radial
velocity (or the player holds **F** inside the ring to begin a controlled entry).
1. 0.35 s: the iris closes on the ship while the player keeps steering (no input lock, no
   fade); the camera may push in behind the iris.
2. `PlanetSide` loads while the screen is black with that planet's `PlanetConfig`; the
   longitude is the entry angle minus the planet's rotation; the terrain streams around that x.
3. Ship placed upright at Escape Line altitude + 20 m, descending at 15 m/s, planet gravity
   on; side controls live on the first visible frame while the iris opens. The player flies
   down and lands (§4.3). Non-landable bodies have no Atmosphere Ring; the Sun kills.
Both transitions are covered by PlayMode tests (§10.9).

---

## 6. Controls (keyboard and mouse; controller mapped through the Input System, optional)

| Context    | Action                     | Default                                   |
|------------|----------------------------|-------------------------------------------|
| On foot    | Move / sprint              | A, D / Shift                              |
|            | Jump / jetpack             | Space (tap / hold)                        |
|            | Drop through platform / crouch | S                                     |
|            | Aim                        | Mouse                                     |
|            | Rig primary / secondary    | Left click / Right click                  |
|            | Rig module                 | 1 Beam · 2 Grapple · 3 Survey · 4 Builder; Q/E cycle (D-087) |
|            | Interact / board ship      | F                                         |
|            | Build menu / Inventory / Map / Catalogue | B / Tab / M / N              |
|            | Float cell toggle (giants) | V                                         |
|            | Air dash                   | Shift (tap while airborne)                |
| Ship, side | Thrust (hold)              | W or Space                                |
|            | Tilt left / right          | A, D (returns to upright when released)   |
|            | Exit ship (landed)         | F                                         |
| Ship, top  | Thrust / retro / rotate    | W / S / A, D                              |
|            | Boost / Skip Drive         | Shift / hold J                            |
|            | Fire / target-scan         | Left click / Right click                  |
|            | System map / Inventory     | M / Tab                                   |
| Always     | Pause / Photo mode         | Esc / P                                   |

---

## 7. The eight planets

Common format: **World type** · **Hazards** (Thermal, Cryo, Radiation, Toxic, Pressure on a
0–3 scale; 0 none, 3 lethal within 30 s unprotected) · **Resources** (common; **unique**
in bold) · **Creatures** (roster; **apex**) · **Activities and points of interest** ·
**Only here** · **Progression gate** · **Look**.

### 7.1 Earth — the starting world
- **World type.** Solid terrain, biomes by longitude: temperate forest (spawn), plains,
  desert, taiga, tundra, ocean basins with trenches to depth 250. Sea level is the Datum.
- **Hazards.** None at the surface. Cryo 1 in tundra at night; Pressure 1–2 below 120 m of
  water; Toxic 1 in swamps. Weather: rain, thunderstorms (lightning strikes exposed metal),
  snow, fog. Day/night 20 min.
- **Resources.** Iron, copper, carbon (wood, coal), silica, water, oxygen, clay, aluminium
  (bauxite), **Living Seed** (crops and biomass; Earth is the only farm in the system —
  all food and all organic polymers trace back here).
- **Creatures.** Stag (grazer, flees), Grey wolf (pack, night), Brown bear (territorial),
  River pike, Gulls; ocean: Reef shark, Giant squid (depth 150+). **Apex: Hadal Maw** —
  a 40 m trench ambusher that lights its lure in the dark; killing it needs Pressure Mk2
  and yields the only Abyssal Lure (a Survey module that reveals creatures through terrain).
- **Activities / POIs.** Tutorial (walk, jump, dig, build a shelter, craft the Beam, board
  the ship, first launch); home base; farming; fishing; the Survey Archive (story start);
  abandoned coastal launch complex (ship parts); cave networks; Earth Waystation in orbit.
- **Only here.** Living Seed; farming; the cheapest repairs; the Archive.
- **Gate.** None. **Look.** Documentary-naturalistic; soft daylight; green/blue/ochre.

### 7.2 Mars — the first off-world base
- **World type.** Solid terrain: rust plains, dune seas, Valles Marineris (a canyon 6 km
  wide in game, 180 m deep, with layered walls), Olympus Mons (a 3 km wide, 300 m tall
  shield with a caldera), polar ice caps (CO₂ over water ice), lava-tube caves (natural
  radiation shelters).
- **Hazards.** Cryo 1 day / 2 night, Pressure 1 (thin air: suit required, no jetpack
  penalty), Radiation 1 at the surface (0 in lava tubes), dust storms (visibility 15 m,
  Cryo +1, static discharges, 2–6 min, planet-wide every 4–7 game days with a 60 s warning).
- **Resources.** Iron oxide (hematite), silica, water ice (poles, subsurface), carbon
  dioxide (dry ice), sulfur, **Perchlorate** (an oxidizer for crafting and a trade good;
  no launch fuel exists, D-103), nickel-iron meteorites.
- **Creatures.** Dustskater (small scavenger), Scree stalker (pack hunter in canyons),
  Lava-tube lurker (ambusher), Polar crawler (slow, armored). **Apex: Tharsis Worm** — a
  60 m burrower under Olympus Mons that surfaces during dust storms; its plates are the
  only source of Wormplate (hull armor tier 2).
- **Activities / POIs.** First beacon (story), building a pressurized base, ice mining,
  canyon traversal with 2.6× jumps, Mars Waystation, crashed Halcyon hauler (Dray parts),
  Warden outpost.
- **Only here.** Perchlorate; Wormplate; the low-gravity jump playground.
- **Gate.** Cryo Mk1 recommended for nights. **Look.** Butterscotch sky, long shadows,
  rust/umber/salmon; thin haze; sharp stars at dusk.

### 7.3 Mercury — the twilight run
- **World type.** Solid, cratered terrain; a very low Escape Line (120 m). The world has
  a day side (Thermal 3), a night side (Cryo 3), and a ~400 m wide **twilight band** that
  creeps 1 m per 6 s. Polar craters at the world's two "cold traps" (x ranges) hold
  permanent shadow and water ice.
- **Hazards.** Thermal 3 in sunlight (Mk2 shielding makes it 1; Mk3 → 0), Cryo 3 in
  darkness, Radiation 2 always (no magnetic field, no air), Pressure 0, **solar flares**:
  a 45 s warning, then 20 s of Radiation 3 — survive in shadow, underground, or inside
  a flare shelter.
- **Resources.** Iron, nickel, sulfur, graphite, polar water ice, **Solarite** (crystals
  fused by flares on the day side, harvestable for 90 s after each flare — the capacitor
  material for every tier-3 energy tech).
- **Creatures.** Glassback (silicate grazer riding the twilight band), Flarewing (flyer
  that feeds on flares, aggressive during one), Shadewyrm (ice burrower in polar craters),
  Cinderling (small, swarms at dawn). **Apex: Cinderhulk** — an armored colossus whose
  shell glows white on the day side; it is vulnerable only during the 2 minutes after it
  crosses into night, when the shell cools and cracks.
- **Activities / POIs.** Racing the terminator for Solarite; polar ice expeditions; the
  Mercury beacon inside a flare shelter; a Warden-guarded Sowing vault; speed-launch
  challenges off the lowest Escape Line.
- **Only here.** Solarite; flares; the moving safe zone.
- **Gate.** Thermal Mk1 and Cryo Mk1 (both; the twilight band still bites), Radiation Mk1.
  **Look.** Pitch-black sky with a huge Sun, blinding regolith, violet twilight.

### 7.4 Venus — the dive world
- **World type.** Hybrid. The surface (Datum y 320) is volcanic plains, tesserae
  highlands, and active vents: Thermal 3, Pressure 3, Toxic 2 — a place for 3–6 minute
  dives. The **habitable cloud deck** at y 770 ± 60 (Earth-like pressure and temperature)
  holds floating stations, your Aerostat base, and sulfur-cloud creatures.
- **Hazards.** Cloud deck: Toxic 1 (acid haze, suit corrosion ticks), lightning. Below
  y 650: Thermal rises to 3 and Pressure to 3 by the surface; acid rain evaporates at
  y 600. Super-rotation winds (constant lateral push, 80-minute cycle).
- **Resources.** Sulfur, carbon dioxide, basalt, **Vitriol Glass** (acid-vitrified silica
  from vent fields — the only material for acid-proof hull and base plating), iron
  pyrite "frost" on highland peaks.
- **Creatures.** Sulfur drifter (gasbag filter feeder), Acidmoth (swarms near lights),
  Pressure crab (surface, armored, slow), Vent eel (surface, heat-seeking). **Apex: Veil
  Serpent** — a 300 m ribbon that swims the acid haze and wraps stations; it flees from
  cold, so a Cryo lantern (made from Mercury ice) keeps it at a distance (D-087: no weapons).
- **Activities / POIs.** Aerostat building (buoyancy budget), timed surface dives for
  Vitriol Glass, the *Meridian* station (Venus beacon; Warden origin), vent-field mining
  under Thermal pressure, Red Hollow smugglers hiding in the clouds.
- **Only here.** Vitriol Glass; the dive loop; Float cell Mk1 blueprint.
- **Gate.** Toxic Mk1 for the deck; Thermal Mk2 + Pressure Mk2 for dives. **Look.**
  Orange-cream haze, backlit cloud towers, black glassy surface lit by vents.

### 7.5 The giants: the cloud-column world type (Jupiter, Saturn, Uranus, Neptune)
There is no ground. The side view is a 4096 × 2000 column. From the top:
- **Space edge → Escape Line.** Thin sky, stars visible.
- **Datum (y 1100, 1 bar).** The upper cloud tops; the ship can hover here. Float cells work
  only below the Datum.
- **Deck 1 (y 1100–900)** ammonia-ice clouds (Jupiter/Saturn) or methane haze
  (Uranus/Neptune): floating **ice floes** — solid, mineable platforms that sublimate 30–90 s
  after the player disturbs them; buoyant derelicts from the *Meridian* expedition;
  creature husks big enough to stand on.
- **Deck 2 (y 900–600)** ammonium-hydrosulfide or hydrogen-sulfide clouds: denser floes,
  stations, the planet's beacon, lightning.
- **Deck 3 (y 600–300)** water clouds: warm, storms, the big creatures.
- **Deep (y 300–100)** Pressure 2→3, Thermal rising; rare resources; brief forays.
- **Crush Line (y 100).** Lethal. Drawn as a pulsing dark band with the label "CRUSH".
Players move by jumping between floes, jetpack, Float cells, grapple (Rig module, M4),
and built **Aerostat** platforms whose buoyancy must exceed their load (each module lists
mass and lift; the HUD shows the margin). Digging becomes harvesting floes and husks.
Falling off a floe means a long fall through decks; Float cells and the jetpack arrest it;
the Crush Line ends it (respawn at the last Aerostat or the ship, cargo kept, 20% Scrip
recovery fee).

### 7.6 Jupiter — the storm giant
- **Hazards.** Radiation 3 everywhere above Deck 2 (the belts; Mk3 brings it to 0; Deck 2
  and below are shielded by the atmosphere to 1), lightning (Deck 2–3), gravity 2.53×
  (fall damage above 2.9 m; jetpack Mk3 required; Thruster Mk3 required to launch),
  Cryo 2 in Deck 1, Thermal 2 in Deep. The **Great Red Spot** is a 600 m wide zone where
  wind pushes 12 m/s and floes spin.
- **Resources.** Hydrogen, helium, ammonia ice, phosphorus pigments (Red Spot floes),
  **Metallic Hydrogen** (Deep only, forms in pressure "veins" of hardened floe cores —
  the conductor for every endgame drive).
- **Creatures.** Stormglider (manta floater), Lightning eel (electric, Deck 2), Ballast
  tortoise (huge, slow, a walkable husk when killed), Belt wasp (radiation-adapted swarm,
  Deck 1). **Apex: Vortex Whale** — a 500 m floater living in the Great Red Spot; its song
  stuns; killing it is a multi-stage hunt (harpoon anchors, ride it below the belts) and
  drops the Stormheart (Skip Drive Mk3 core).
- **Activities / POIs.** Belt-diving for Metallic Hydrogen, Red Spot floe-riding, the
  Jupiter beacon in a radiation-fried vault, Warden swarms, Io's volcanoes and Europa seen
  in the sky (sky objects, not landable).
- **Only here.** Metallic Hydrogen; the Stormheart; the Thruster Mk3 blueprint.
- **Gate.** Radiation Mk3, Thruster Mk3, Jetpack Mk3, Pressure Mk2. **Look.** Cream, rust,
  and brick bands rolling past; lightning under the floor; a sky that cycles every 8 minutes.

### 7.7 Saturn — the ring world
- **Hazards.** Cryo 2 (Deck 1), Pressure (as all giants), gravity 1.06×, **Ring Mites**
  (space) chew hull during ring mining, the **North Polar Hexagon**: a 900 m wide zone of
  six wind-walls that rotate; crossing a wall costs hull/suit integrity; the eye is calm.
- **Resources.** Ring ice and ring rock (space mining; silicates, water ice, iron), helium,
  **Helium-3 Condensate** (helium rain collected in Deck 2–3 traps — the coil material of
  the Skip Drive Mk2 blueprint; a crafting ingredient, never a fuel, D-105).
- **Creatures.** Helium jelly (floats up when hit), Hex drake (winged, rides the hexagon
  walls), Ringmite (space, swarms), Floe moth. **Apex: Polar Hydra** — six-headed cloud
  serpent of the Hexagon's eye; each head is destroyed by crossing a different wall with
  its lure; the body drops the Hexacore (Aerostat Mk3 buoyancy core).
- **Activities / POIs.** Top-down ring mining lanes (density varies with distance; gaps
  are safe), the ring-mining rig with the Saturn beacon, Saturn Waystation (Halcyon's
  largest market), Titan and Enceladus in the sky, Skip Drive coil crafting.
- **Only here.** Helium-3 Condensate; ring mining; Skip Drive Mk2 blueprint.
- **Gate.** Cryo Mk2, Pressure Mk2, Thruster Mk2, Float cell Mk1. **Look.** Pale gold and
  butter bands, the ring plane as a bright line across the sky, soft low sunlight.

### 7.8 Uranus — the sideways winter
- **Hazards.** Cryo 3 (coldest atmosphere, −224 °C: Mk3 required), gravity 0.89×, dim
  light (sunlight 0.25 of the in-game clamp), **seasons**: the lit hemisphere is one half of
  the world's x range and swaps every 6 game days; the dark half has Cryo 3 even with Mk3
  (needs the Mk3 suit heater, which draws Suit power), methane hail, **Diamond rain** below Deck 3 (falling 5–20 cm
  diamonds, 15 damage each, also the resource).
- **Resources.** Methane ice, ammonia, hydrogen, water, **Deep Diamond** (the hardest
  material; Rig tip Mk3 and the only drill for Neptune's Superionic Ice).
- **Creatures.** Frostwisp (luminous, leads you to warmth or danger), Methane ray (glides
  between floes), Hailcrab (shell catches diamonds), Tiltbird (migrates with the season).
  **Apex: Diamondback Colossus** — armored in diamond at the rain layer; only its joints
  take damage, visible when it reaches to feed; drops Prism plates (the Mk3 Rig tip).
- **Activities / POIs.** Diamond-rain catching (umbrella platforms), seasonal migration
  hunts, the Uranus beacon on a tilted derelict, ice-geyser moon Miranda in the sky.
- **Only here.** Deep Diamond; seasons; Jetpack Mk3 story gate (the Jupiter chapter).
- **Gate.** Cryo Mk3, Pressure Mk2, Float cell Mk1. **Look.** Featureless cyan fog that
  reveals bands only with the Survey module; dim; crystalline sparkle below.

### 7.9 Neptune — the endgame
- **Hazards.** **Wind** (constant lateral force 8–20 m/s, gusts to 35; wind anchors are
  needed to build), Cryo 3, gravity 1.14×, **Dark Storms**: 400 m zones that drift,
  pull everything inward 10 m/s, and host the apex; Pressure, lightning, Thermal in Deep.
- **Resources.** Methane, ammonia, hydrogen, **Superionic Ice** (black "hot ice" in Deep,
  drillable only with Deep Diamond — the capacitor for the *Meridian* decode and the top
  shield tier).
- **Creatures.** Windrider (sail-finned floater), Shadow shoal (dark, fast, hunts in
  storms), Pressure phantom (translucent, Deck 3), Anchor worm (holds floes against wind).
  **Apex: Umbral Leviathan** — lives in the Great Dark Spot around the *Meridian* herself;
  the final encounter, a full Survey of the Grand creature (D-087), uses every system (anchors, Float cells, Grapple, ship support).
- **Activities / POIs.** Reaching the *Meridian* (final beacon, ending choice), storm
  running, Triton in the sky with its geysers, the hardest Warden tier.
- **Only here.** Superionic Ice; the ending; Leviathan Core (best ship shield).
- **Gate.** Everything Mk3, Deep Diamond drill. **Look.** Deep indigo, white wisps streaking,
  a storm you can see breathing.

---

## 8. Systems → milestones (original names in bold)

| Area      | System (adapted pattern)                             | MERIDIAN name / rule                                           | Milestone |
|-----------|------------------------------------------------------|----------------------------------------------------------------|-----------|
| Survival  | Life support                                         | **Envirosuit** oxygen + power; refill from oxygen, ice, or any base | M3 (meter), M5 (full) |
|           | Hazard protection (heat, cold, radiation, toxic, pressure) | Thermal / Cryo / Radiation / Toxic / Pressure modules Mk1–Mk3 | M3 inner, M4 giants |
|           | Shields                                              | Suit shield (recharges), hull shield (ship)                    | M3 / M5   |
| Tools     | Multitool: mining beam, scanner, grapple, upgrades   | **Rig** with modules **Beam** (mine/dig), **Grapple** (slot 2, D-087), **Survey** (scan), **Builder** | M1 Beam/Builder, M3 rest |
|           | Terrain digging and building                         | 1 m tiles; dig with Beam; place blocks and modules with Builder | M1        |
| Economy   | Resources, refining, crafting, tech tree             | Resources (§7); **Smelter** and **Refinery** stations; **Blueprint Tree** | M3        |
|           | Inventory upgrades, trading                          | Slot-based suit/ship/cargo; **Scrip** currency; vendors at **Waystations** | M3        |
| Ship      | Manual flight, landing, fast travel                  | No fuel of any kind (D-103, D-105); thruster classes and landing rules §4.3; **Skip Drive** (spool + cool-down, M4) | C1 flight, M4 Skip Drive |
|           | Cargo, upgrades, multiple ships (no shields or weapons, D-087) | Cargo bays, thruster and hull upgrades; ships **Pilgrim** (start), **Dray** (hauler), **Vagabond** (deep-range) | M5        |
| Space     | Top-down flight and combat, pirates                  | Red Hollow raiders, bounties                                   | M1 flight, M5 combat |
|           | Space stations with vendors                          | **Waystations** (Earth, Mars, Belt, Saturn)                     | M3        |
|           | Asteroid mining                                      | Belt and Saturn's rings; Ring Mites                             | M4        |
| World     | Enforcement drones vs over-mining                    | **Wardens**: a per-area extraction meter; tiers Drone → Sentry → Enforcer | M3 basic, M5 tiers |
|           | Scan and catalogue creatures, plants, minerals       | **Catalogue** (N); Datacores for first discoveries              | M3        |
|           | Weather, storms, day/night                           | Per-planet weather tables §7; day/night §3                      | M2 day/night, M3+ weather |
|           | Points of interest                                   | Crash sites, ruins, outposts, caves, beacons, Sowing vaults     | M2–M4     |
| Progress  | Base building, teleporters                           | Bases on any planet (Aerostats on giants); **Gates** link bases | M3 bases, M5 Gates |
|           | Missions, main story, side quests, factions          | Survey contracts, Halcyon deliveries, Red Hollow bounties, **The Meridian Line** | M5 |
|           | Save and load                                        | JSON save, terrain diffs, autosave on transitions               | M1        |
| Audio     | Music and sound                                      | CC0/royalty-free, sourced by UNITY; licenses in `docs/credits/unity.md` | M2 placeholder, M5 full |

> **v5.2 (owner, 2026-11-08, D-174): §8.1 below is the game's core loop and overrides the table above where they differ** (the Blueprint Tree's tool / suit / ship upgrades become the Skill Tree; Wardens no longer meter general digging).

### 8.1 The dig run (D-174, milestone D1)

**The loop.** Land at a planet's camp, dig down (the shovel first, then the Beam), fill your pack with what you dig, climb back above the **Surface Line**, sell the haul for Scrip, spend it in the **Skill Tree**, dig deeper. Deeper ground is harder and holds rarer, more valuable material. Harder planets hold rarer material still.

**The Surface Line.** An inked dashed line with small marker pegs, 2 m under the drawn surface everywhere on a solid planet, drawn in the cutaway whenever the camera is below the surface. With your feet above it you are **topside**: the Sell panel and the Skill Tree open anywhere (no shop to walk to); below it they are closed and the HUD shows your depth (0 at the line). The challenge is getting back up with a full pack.

**Depth tiers** (every solid planet; names shared, materials per planet; depth below the Surface Line):

| Tier | Name     | Depth      | Hardness (× the planet's base) | Material |
|------|----------|------------|----------------|----------|
| 1    | Topsoil  | 0–10 m     | × 1            | common: the planet's soil, clay, coal / regolith |
| 2    | Subsoil  | 10–40 m    | × 2            | the base metals (iron, copper, hematite, nickel) |
| 3    | Stone    | 40–100 m   | × 4            | crystals and light metals (silica, aluminium, sulfur) |
| 4    | Deep     | 100–200 m  | × 8            | the rare: graphite, the planet's signature (solarite, vitriol glass, water ice lenses) |
| 5    | Core     | 200 m to the world floor | × 16 | the rarest: deep diamond, the planet's core sample |

Each tier's fill is drawn differently (colour, texture, the buried details), so you can see how deep you are. Buried pockets (D-162 (5)) carry their tier's rarest items and are worth a detour; Survey reveals them. Surface resource rocks stay as small topside income.

**The shovel and the Beam (D-182, owner 11-09).** Every surveyor starts with a **shovel**: half the Beam's speed, a 2 m reach, a visible scoop. The **Beam** is the Dig branch's first node (250 Scrip, bought after the first haul) and replaces the shovel for good; a New Expedition starts you on the shovel again.

**Digging speed.** A Beam stroke takes 0.25 s × planet base × tier hardness ÷ Beam power, never more than 8 s (a shovel scoop 0.5 s on the same terms, never more than 12 s). There is **no hard gate**: a starting Beam can dig the Core, slowly; upgrades make it fast.

**The planet ladder** (base hardness; rarer materials up the ladder): Earth 1 → Mars 1.6 → Mercury 2.5 → Venus surface 4 (heat and pressure with depth). The giants have no solid ground: their rare finds (metallic hydrogen, helium-3, superionic ice, deep diamond from the floes' cores and the deep) feed the Skill Tree's outer rings.

**Selling.** Every dug material has a Scrip value by planet and tier (rarer and deeper = more); sell topside from the pack. Selling at a Waystation pays a little more (the Voyage branch raises it).

**The pack.** A weight limit (each material has a weight); a full pack takes no more. Weight slows the climb: jetpack lift, grapple reel and climbing speed scale with the load. Haul big or climb fast: your choice.

**Ways back up** (no single right one; each upgradeable, none required): climbing your own carved ramps (≤ 35°); Builder mounds, ramps and ladders from dug dirt; the jetpack (suit power, never fuel, D-103); the Grapple (anchor and reel); later a winch line from the Surface Line and a one-use recall beacon.

**The Skill Tree.** Six branches round a centre, five rings each; every ring has two or three nodes; a node links outward in its own branch and some link sideways into a neighbour, so paths weave and no two players need the same route. Costs: Scrip, and from ring 3 a rare material from further up the planet ladder (ring 5: a giant's find or a Datacore). Every branch keeps getting better to its end; a whole tree costs far more than one planet's early income, so choices matter. A bought node cannot be undone (D-175), except by a New Expedition. The branches:
- **Dig** — Beam power (stroke time), brush radius, strike rhythm (consecutive strokes speed up), heat sink.
- **Haul** — pack weight limit, lighter loads, a magnet that pulls nearby drops in, compacted ore.
- **Ascent** — jetpack thrust and suit-power use, grapple length and reel speed, climbing speed and grip, cheaper Builder ladders.
- **Survey** — scan radius and depth, rare-pocket reveal, a preview of the next tier's materials, depth warnings.
- **Endurance** — oxygen time, heat and pressure resistance with depth, a softer landing from falls.
- **Voyage** — rocket thrust classes to land on harder planets, Waystation prices, cargo hold, the Skip Drive.

**Rank and the New Expedition (prestige, D-175).** Your **Surveyor Rank** (1–10) rises with the Scrip you earn in the current expedition. At Rank 10, topside, you may start a **New Expedition**: every bought node, your Scrip, your Rank and every material you carry or store are wiped and you start again at Earth's camp, keeping the Catalogue, the story, Datacores, discovered planets and buildings, and gaining a permanent **+25 % to every Skill Tree stat** per expedition (expedition n: × (1 + 0.25 × (n − 1))), shown as an expedition badge. It is never forced, and it is the only way to undo the tree.

**The stroke and the hole (D-183, owner 11-09).** Every stroke that opens a cell throws clods in the ground's tint, kicks the camera a hair, and flies the material's icon to the pack with a tick. A dug hole reads as cut earth: the back wall darkens with depth and away from the opening, every dug edge has a soft rim shadow, and each tier's back wall shows drawn roots, stones and strata.

**Ground that holds (D-184, owner 11-09).** A solid cell stays up if it rests on solid ground, a built piece or the world floor, or sits within 3 m sideways of a cell that does. Dig all the way under a ledge and the unsupported part shakes for 0.6 s, then falls as rubble: loose cells that dig in one stroke and still pay. Pads, the camp, built pieces and bedrock never fall; rubble never buries the surveyor (it lifts them onto its top).

**What stays.** Crafting (consumables, base pieces, ladders and anchors), the Catalogue, Datacores (relic and vault rewards; a few notable nodes need one), no combat (D-087). Wardens meter digging only within 48 m of a Warden site (amends D-052).

---

## 9. Art bible (v4, 1930s rubber-hose cartoon; owner direction, D-086)

> **v5 is coming (owner, 2026-11-09, D-185): a modern hand-drawn cartoon.** Kept: drawn or painted (never digital-looking or 3D), original designs, faces only on people and animals, no combat, painted backgrounds, the film pass, the budgets. Changed: jointed limbs and natural cartoon proportions instead of rubber hoses and pie-cut eyes; painted shading on characters; rigged cut-out characters and creatures (bones + IK) with crouch, bent-knee jumps and more secondary motion; key moves at 24 fps. The style test (C5, §12) defines it; this section is rewritten as v5 only after the owner accepts that test. Until then, v4 below stays the rule for everything shipping in 0.6.x.

The era and its techniques, our own designs. Every asset passes the §9.7 checklist before LEAD
accepts it, and the approved **style test** (C0, §12) is the reference everything else matches.

### 9.1 The look
| Rule | Specification |
|------|---------------|
| Linework | Every character, creature, plant, ship and prop has a slightly wobbly ink outline, as if drawn with a fine pen. Ink colour `#1E1A17`. At 1x (v4.1, D-100): outer silhouette **2–3 px**, interior lines **1–1.5 px**, thickness jittered ±20 % along the stroke. **Interior detail is required**: folds, seams, rivets, leaf veins, feather and fur marks, plus small texture marks (a few hatch strokes, dots, scuffs) so things read as drawn, not as stickers. No perfect geometry: circles a little lumpy, straight lines bow slightly |
| Colour | Flat cel colour inside the lines, **up to two shadow tones per colour** (a mid shadow and a deep shadow, v4.1). No gradients, no realistic lighting, no normal maps, no specular |
| Palette | Muted and slightly aged: warm off-whites (never `#FFFFFF`), soft reds, mustard yellows, teal, dusty greens. Each planet has its own 6–8 colour palette from this family, written into its first planet task and stored as `ui/palettes/<planet>` (one 8×1 strip). **Earth (C0):** off-white `#F2E6CF`, soft red `#C8553D`, mustard `#D9A93F`, teal `#3E8A86`, dusty green `#7A9A5B`, faded sky `#9FB7B9`, shadow brown `#5B4636`, ink `#1E1A17` |
| Characters | Era cues: pie-cut eyes (black pupil with a wedge cut out), white gloves, round bodies, big simple expressions |
| Backgrounds | Painted watercolour: soft edges, visible paper texture, slight colour bleed, **no ink outlines** (characters must pop off them). 3–5 parallax layers per surface scene (replaces the seven-layer stage of v3). Space: a painted starfield with soft hand-painted nebulas |
| Film treatment | One full-screen pass: subtle grain, slight vignette, faint drifting dust specks and hairline scratches, a very gentle brightness flicker (≤ ±2 %), slight warm/sepia grade. Comfortable for hours. **Settings → "Film effects" toggle** (default on) |
| UI and text | Vintage hand-lettered feel from OFL fonts only: titles **Limelight**, body and HUD **Patrick Hand** (D-090; never a font from an existing game). Panels look like aged paper or painted signs. Planet title cards slide in like old intertitles |

### 9.2 The motion
| Rule | Specification |
|------|---------------|
| Rubber hose | Limbs have no joints: arms, legs, tails, antennae, vines and ship exhaust bend like soft tubes. Hands and feet stay big and round |
| Squash and stretch | On everything that moves: jumps, landings, bounces, engine thrust, ground impacts. Exaggerate, then pull back 20 % if it looks broken. It lives on the visual root; physics (§4) never changes |
| On twos | Character, creature, flora and prop animation plays at **12 fps** (each drawing held 2 frames of 24). Rigged flora bones are sampled stepped at 12 Hz. Camera, parallax and UI move smoothly at the real frame rate |
| Everything is alive | Nothing on a planet surface is static: plants sway and breathe, rocks bob, props wobble, trees bounce. Every idle is a rhythmic bob to an unheard beat (one shared beat per planet, 100–120 bpm) |
| Secondary motion | Ears, leaves, petals, hoses and antennae drag behind and overshoot on stops |
| Walk / run | Bouncy walk, head bob on every step, big arm swings; running leans the whole body forward |
| Era tricks | Eye-pops on surprise, smear frames on fast moves, multiple-limb blur, smoke puffs on landing, dizzy stars on bumps (never combat), pausing to look at the camera |
| Transitions | Planet ↔ space and entering an area use an **iris-out / iris-in** circle wipe (0.35 s each way, inside the §11 1.5 s transition budget) |

### 9.3 What gets the style
- **Player (the surveyor):** an original rubber-hose character: a big round fishbowl helmet with an expressive face inside, gloves, boots, rubber-hose limbs.
- **Faces only on people and animals (D-101).** The surveyor, NPCs and creatures have faces. Plants, rocks, crates, tools, the ship, the planets and every other object never get eyes or mouths; their character comes from shape, colour and motion.
- **Ship (Pilgrim):** a bendy vintage rocket standing upright on its tail (D-102), no face; a porthole, panel seams and rivets for detail, fins that wobble, exhaust in round cartoon puffs. Thrust = stretch, cut thrust = squash.
- **Planets (space view):** painted watercolour discs with ink outlines; character through colour, bands, storms, caps and rings (Jupiter's bands swirl and its spot drifts, Saturn's rings wobble, Neptune's dark storm wanders). No faces or expressions. They must still read as the real planets.
- **Flora (the priority):** each planet has its own original flora with personality through motion only: rubber-hose stems that sway, petals and leaves that act like hands, flowers that yawn open and shut, cacti that shiver, vines that curl and uncurl. No eyes or mouths. Plants react when the player passes within 3 m (turn, bounce, shiver, open). Gas-giant cloud layers get cloud-plants and floating puffball flora.
- **Creatures:** the existing §7 roster redrawn in the style, friendly or neutral (D-087), pie-cut eyes and bouncy idles. Grand creatures (the former apexes) included.
- **Props and resources:** minerals, crystals, collectibles and tools get wobble idles and drawn detail, never faces.
- **HUD:** cartoon gauges for Suit power, oxygen and the gravity readout; the Escape Line is a hand-painted dotted line with a little sign on it.

### 9.4 Pipeline (detail in contract §11)
- **BLENDER:** Grease Pencil for frame-by-frame 2D drawing. Existing 3D models (ships, planets) may be reused through Grease Pencil Line Art or Freestyle plus a flat two-tone toon shader, rendered to 2D frames with jittered line thickness. Every animated asset ships as a transparent PNG **sprite sheet + JSON** (frame size, count, fps 12, loops). Backgrounds ship as separate painted parallax PNG layers. UI frames, title cards and film overlays (grain, dust, scratches) ship as tileable PNGs. **Hero assets** (player, ship) are full frame-by-frame; **background flora and props** use a **simple rig**: a few bendable parts on one sheet, animated in Unity with bones.
- **UNITY:** 2D sprites with the Animator and Sprite Atlas; character animators at 12 fps; the rubber-hose rig path with Unity 2D Animation (sprite bones + skinning) so one texture serves hundreds of plants; **one** full-screen post shader (grain + vignette + dust/scratches + flicker + warm grade in a single pass; no Bloom, no volumetrics, no HDR); the iris wipe as a cheap shader cutout; the Film effects toggle; art replaced planet by planet as sheets arrive, old assets moved to `Assets/_Game/Archive/` (never deleted).

### 9.5 Scale and camera (v4)
1 Unity unit = 1 m; **PPU 64** for all v4 art, drawn and rendered at 1x for 1920×1080 (never 4K
sources in the build). The side view is an orthographic camera 16.875 m tall (1080 / 64) with
the §5.1 follow rules (dead zone, look-ahead, vertical hold); fight zoom is cancelled. The
surveyor stands about 2.0 m (≈ 128 px) with the helmet. Gameplay numbers in §4 are unchanged.

### 9.6 Budgets for art (hard rules; LEAD enforces; also §11)
- Sprite atlases ≤ 2048×2048, compressed (BC7, or DXT5 Crunch). **≤ 8 atlases loaded per planet.**
- Frame caps: idle 8–12, walk/run 12–16, jump/land 8–10, one-off specials ≤ 16. Mirror by flipping at runtime; never draw a mirror version.
- Only the current planet's assets are loaded; the previous planet unloads before the next loads. Space keeps only the planet discs and starfield.
- ≤ 40 animated objects on screen; beyond that, distant flora switches to a 3-frame cheap idle or a static frame. Idle start times are staggered.
- Rigged flora share one texture and one animator controller per planet.
- Film overlays are small tiled textures (512×512), never full-screen images.
- The game stays **under 2 GB RAM in play** and 60 fps on integrated graphics; profile after every planet is converted.
- Workflow: BLENDER never runs a heavy render batch while UNITY has the Editor open with a scene loaded; LEAD schedules render windows (D-091). One asset per `.blend`, no 4K textures.

### 9.7 Acceptance checklist (LEAD, every asset)
- [ ] Hand-inked outline 2–3 px outer / 1–1.5 px interior with jitter, finer interior line work and texture marks, no perfect geometry (v4.1)
- [ ] Flat cel colour, up to two shadow tones, muted aged palette (v4.1)
- [ ] Faces only on people and animals; no eyes or mouths on plants, objects, the ship or planets (D-101)
- [ ] Animated on twos, within the frame caps
- [ ] Visible squash and stretch, rubber-hose limbs, secondary motion
- [ ] Has an idle loop (nothing sits still)
- [ ] Original design, not recognizable as any existing character
- [ ] Sprite sheet + metadata delivered per the asset contract
- [ ] Fits the atlas and RAM budget after import
- [ ] Looks consistent with the approved style test

LEAD records the ten boxes per asset in `REVIEW_LOG.md`; one unchecked box sends it back to In Progress. The C0 assets were accepted on the nine-box v4.0 list; their v4.1 re-inks (B-124..B-127) are judged on this list.

### 9.8 Originality (forbidden)
Borrow the era (1928–1938 studio cartoons) and its techniques, never a property. Forbidden: any
character, silhouette, logo, font, title-card wording or layout, UI, boss or map from Cuphead or
any other game or cartoon; cup-, mug-, teacup- or dice-headed characters; straws on heads; round
black mouse ears; any recognisable studio mascot. Pie-cut eyes, white gloves and rubber-hose
limbs are era conventions and allowed, but every combined design must be our own. Each new
character design ships with a one-line "what makes it ours" note on its review sheet.

---

## 10. Technical architecture

### 10.1 Stack
Unity 6 LTS (exact build pinned in §12), URP with the **Universal (3D) Renderer, Forward+**,
Input System, Addressables, Unity Test Framework, `CameraFollow` on a perspective side rail
(FOV 35°, z = −28.5 m for 60 px/m; D-064; Cinemachine not required), TextMeshPro. Physics stays **Physics2D** on the x–y plane. Blender LTS (pinned in §12): models
and rigs exported as glTF (`.glb`), textures baked in Cycles/Eevee, all scripted in Python.

### 10.2 Repo layout
```
Assets/_Game/Code/Runtime, Code/Editor   C# (UNITY)        Assets/_Game/Art/            exports (BLENDER)
Assets/_Game/Scenes  Prefabs  Settings    (UNITY)           Assets/_Game/Placeholders/   (UNITY)
Assets/_Game/Shaders  UI  Audio          (UNITY)           Assets/_Game/Tests/Unit/     (UNITY)
Assets/_Game/Tests/LeadQA/               (LEAD)            blender/sources scripts render.py manifest.json preview/ (BLENDER)
tools/unity_*.ps1 (UNITY)  tools/blender_render.ps1 (BLENDER)  tools/paths.json (LEAD)
coordination/  docs/  (LEAD, with per-role status/report folders)   logs/ Build/ (ignored)
```
Only `Assets/` and `Packages/` are imported by Unity; `.blend` files never go under `Assets/`.

### 10.3 Scenes and loading
- `Core.unity` (persistent): `GameState`, `SceneDirector`, `TimeSystem`, `SaveSystem`,
  `AudioDirector`, UI canvas, `Space.unity` kept loaded but inactive.
- `Space.unity` (additive): top-down world, planet discs, stations, belt, wells.
- `PlanetSide.unity` (additive, one scene for all planets): receives a `PlanetConfig` and
  builds terrain, sky, weather, spawners from it.
- Per-planet assets live in Addressables groups `planet_<name>` and load when the planet
  loads and unload when it unloads; `common` (player, ship, UI, FX) stays resident.

### 10.4 Terrain
Data (unchanged): 1 m tiles in 32 × 32 chunks, generated from a seed by `IWorldGenerator`
implementations (`SolidWorldGenerator`, `CloudColumnGenerator`); generation on a worker
thread, applied on the main thread within 2 ms per frame; only player changes are saved as
`(chunk, index, tileId)` diffs; chunks within 2 of the camera stay in memory.
Rendering (v2): each chunk builds one **block mesh**: 1 m cubes, 1 m deep, only faces exposed to
air are emitted, greedy-meshed, UVs into a per-planet `Texture2DArray` (top and side texture per
tile material, tileable at 2 m); a back-wall quad 1 m behind the play plane carries the
planet's rock material; a dig or place rebuilds only that chunk's mesh within the same frame.
Edge blending between materials comes from the shader (height-blend on the array layers), not
from overlay tiles. Collision (unchanged): `TilemapCollider2D` + `CompositeCollider2D` per chunk
on the x–y plane; the Tilemap stays as the collision and data carrier, with its renderer off.

### 10.5 Lighting and materials
Materials are URP Lit (base colour sRGB, normal, metallic (R) + smoothness (A), emission) through
the `ArtMaterials` registry; the terrain uses a `TerrainBlocks` shader (array textures, height
blend). Planet discs in space are spheres with the equirect `PlanetDisc` textures (atmosphere rim,
clouds, terminator from the Sun). Lights: one directional Sun per scene driven by `TimeSystem`
(angle, colour, intensity per §9), a per-planet ambient gradient (sky/equator/ground), ≤ 8 visible
point lights, soft Sun shadows (one cascade, 30 m), bloom on emission, SSAO off by default (budget).
Haze: per-planet distance fog matching the v1 haze gradient.

### 10.6 Art pipeline (summary; the contract is authoritative)
Blender exports every model to `Assets/_Game/Art/<category>/<name>/<variant>.glb` with its
textures beside it; 2D categories (icons, ui, planet equirects, fx billboards) stay PNG.
`ArtImporter` (UNITY) applies import settings per category, names and loops animation clips,
assigns materials from the textures, sets the Addressable address = asset key, and retires the
matching placeholder. Code loads art only by key through `ArtKeys`, never by path. Views play
clips by the same names as the v1 sheet clips, so gameplay code does not change.

### 10.7 Save format
`%USERPROFILE%/AppData/LocalLow/<company>/MERIDIAN/saves/slot<N>/` holds `state.json`
(player, ship, inventory, story, catalogue, bases, timers) and one `terrain_<planet>.bin`
per visited planet (diffs). Autosave on every transition and every 5 minutes; three
rotating backups. Version field; migrations on load.

### 10.8 Tools (PowerShell, in `tools/`)
`unity_compile.ps1` (batch compile, zero-error gate), `unity_test.ps1 [EditMode|PlayMode]`
(writes `logs/tests_<date>.xml` and a summary to `coordination/reports/unity/`),
`unity_build.ps1` (Windows builds: the probed development player to `Build/MERIDIAN_<version>_dev/`, the release player to `Build/MERIDIAN_<version>/`; U-143, D-155), `unity_profile.ps1`
(runs the BudgetGate scenes and writes `coordination/reports/unity/perf_<date>.md`),
`unity_art_preview.ps1 <key>` (renders the asset under 2D lights to `logs/preview_<key>.png`),
`blender_render.ps1 <key|category|all> [-Preview]`. All read `tools/paths.json` for the
Unity and Blender executables and exit non-zero on failure.

### 10.9 Tests (owned by UNITY unless noted; LEAD adds QA tests in `Tests/LeadQA/`)
EditMode: gravity ratios, thruster class per planet (no fuel, D-103), well-pull formula, PlanetConfig
completeness, ArtImporter rules, asset-key ↔ placeholder coverage. PlayMode: jump height
per planet (±3%), fall damage thresholds, launch transition (state carried, ≤ 1.5 s),
entry transition, save → load → identical state and terrain, chunk persistence after
digging, BudgetGate (frame time, GC, light and particle caps, memory).

---

### 10.10 Stage layers (v3, D-079)
Per region, `StageLayers` (the v3 `DepthBands`) builds the stack below from Addressable keys under
`backgrounds/<planet>_<region>/` (contract §10 names the files and caps). Parallax is real depth on
the perspective rail; the painted-stage look comes from authored set-pieces, per-layer haze tint
and composition, not from scrolling sprites. Digging and building act on the play plane only; no
layer has collision.

| # | Layer | Depth z | Source | Tiling / placement |
|---|-------|---------|--------|--------------------|
| 0 | Foreground | −3 … −1.5 m | `props/<planet>_foreground/*` (6 pieces per planet) | 1 per 12 m, never within 6 m of the spawn, a POI or a landing pad; may cover the player ≤ 0.5 s at run speed; shadows off |
| 1 | Play plane | 0 | terrain blocks, props, creatures | unchanged |
| 2 | Near flora | 2 … 6 m | `props/<planet>_flora/*` | unchanged (D-071) |
| 3 | Near rocks | 8 … 14 m | `rocks_near.glb` | period 128 m |
| 4 | Mid ridge | 20 … 60 m | `ridge_mid.glb` | period 256 m |
| 5 | Far hills | 80 … 140 m | `hills_far.glb` | period 512 m |
| 6 | Far mountains | 150 … 400 m | `skyline_far.glb` (composed peaks) + `setpiece_<a|b|c>.glb` | skyline period 1024 m; set-pieces at the `stage.json` longitudes (fraction of the region width), scale and mirror per entry |
| 7 | Sky | 500 m / dome | `clouds_color.png` strip scrolling 0.5 m/s; `skydome_color.png` | strip period 2048 m |

Streaming: the current region's layers and the adjacent region's are resident (the adjacent set
preloads when the player is within 200 m of the border and unloads 5 s after it is two regions
away); each set is one Addressable label `stage_<planet>_<region>`. Layer textures per planet
(all its regions) ≤ 700 MB stored (contract §10). *Superseded by D-089 / D-110: ≤ 512 MB of all textures per planet, enforced by ArtImporter (U-091); §10.10 is a frozen v3 section.*

## 11. Performance budgets (requirements, not goals)

### 11.1 The game — enforced by BudgetGate (`Assets/_Game/Tests/Unit/BudgetGateTests.cs` plus the runtime `BudgetMonitor`, owned by UNITY; LEAD confirms numbers at every review)

| Budget                        | Limit (v3, D-077; measured in the dev build, D-058)               |
|-------------------------------|-------------------------------------------------------------------|
| Frame time                    | ≤ 16.6 ms p99 at 1080p on the dev laptop; ≤ 12 ms average         |
| RAM (built game)              | **v4 (D-089): < 2.0 GB working set in play** (warning line 1.7 GB) with the Editor closed; ≤ 512 MB textures loaded for today's art, **≤ 1,024 MB for art v7 (D-207, the owner 2026-11-10), and never past the 1.7 GB warning line whichever comes first**; ≤ 8 sprite atlases (≤ 2048², BC7 or DXT5 Crunch) per planet; ≤ 150 MB audio; ≤ 40 animated objects on screen. (v3's 4.5 GB / 2.0 GB textures / 600 MB meshes is retired) |
| Residency                     | Only the current planet's Addressable groups (+ `common`, `ui`, `space`) are loaded; the previous planet's groups release within 5 s of a transition; stage layers per §10.10 |
| Geometry (v3)                 | ≤ 500 k triangles on screen; ≤ 500 draw calls (SRP batcher on); ≤ 150 shadow casters; one shadow cascade; layers beyond z 20 m cast no shadows |
| Draw calls                    | ≤ 250 side view, ≤ 80 top-down (atlases, batching)                |
| Lights visible                | ≤ 8 point lights (hard cap 12); shadows only from the Sun and the player lamp |
| Particles alive               | ≤ 1500; every emitter pooled                                      |
| GC allocation (steady state)  | ≤ 1 KB per 300 frames; zero per-frame allocations in gameplay code |
| Chunk generation              | ≤ 2 ms main-thread per frame; no hitch > 33 ms during streaming or at a region border |
| Planet load                   | ≤ 5 s, measured from the entry start (or the boot load) until the terrain is settled and no load into the planet's Addressables groups is pending (U-091, D-110); space ↔ planet transition ≤ 1.5 s (no input lock inside it, D-103). Resident groups on a planet: that planet's own, `common`, `ui`, `space`, `planet_space`, `planet_warden`, `planet_waystation`, `planet_rig`, `icons`, `session`; the previous planet's groups and bundles close within 5 s. Terrain sheets used by more than one planet live in `common`, unpacked. Sprite packing stays off through C1: the atlas row counts resident sheet textures ≥ 1024² per planet (≤ 8) |
| Textures                      | BC7 (colour), BC5 (normals); mips on every 3D world texture; v4 cartoon assets (sidecar `style: v3`: sheets, rig sets, painted layers, discs, overlays, palette strips) import without mips (contract §11.8) and are counted apart; atlases ≤ 2048², ≤ 8 sprite atlases per planet, ≤ 512 MB textures per planet (D-089; ≤ 1,024 MB for an art v7 planet, D-207: compressed wherever the paint survives it, uncompressed only where U-217's A/B shows it does not); mip streaming on with a 512 MB budget |
| Animation                     | surveyor and apexes 60 fps clips, others 30 fps; ≤ 2 ms skinning per frame with 20 creatures |
| Audio                         | Vorbis, streamed for music, compressed in memory for SFX          |
| Asset size caps               | Per the contract (§4, §9, §10 there); the importer rejects oversize files |

How the 4.5 GB was set (D-077): the laptop shows 7.6 GB; Windows plus the three Claude Code
sessions take about 3 GB; the dev workflow keeps ≥ 1 GB free. The budget is spent on what the
player sees and feels (stage layers, 60 fps clips, resident adjacent regions), never on waste:
compression, atlases, pooling and per-planet groups stay mandatory. If a feature cannot fit,
UNITY proposes the closest alternative in its status file and LEAD decides; nothing is dropped
silently.

### 11.2 The dev workflow — enforced by HeavyJobLock (LEAD schedules; everyone complies)

| Resource                               | Limit                                                                  |
|----------------------------------------|------------------------------------------------------------------------|
| Unity Editor (interactive or batch)    | ≤ 3.5 GB; only one instance per project exists, so batch jobs never run while the Editor is open |
| Blender heavy render (> 512 px or batch) | ≤ 2.5 GB; never while `Unity.exe` is running; headless; exits after each batch |
| Claude Code sessions (3)               | ≈ 2 GB total (1.7 GB measured 2026-11-06 with six claude.exe); keep logs terse, read large files by section |
| Free RAM                               | ≥ 1 GB headroom at all times; heavy jobs start only above the gate (1.5 GB; 2.0 GB for 2048² bakes, D-026/D-066); browsers closed during work |
| Built game during a dev smoke          | runs only after the Editor batch has exited, never beside it; ≤ 4.5 GB per §11.1 (D-080) |
| Heavy jobs                             | Serialized through `coordination/locks/heavy_<role>.lock` (CLAUDE.md rule 6) |

If the laptop's RAM is upgraded, LEAD raises only this section and logs the decision.

---

## 12. Milestone plan (each ends with a build in `Build/` and a plain-language report in `coordination/reviews/M<n>_REPORT.md`)

| Milestone | Scope                                                                                       | Exit criteria                                                                                                                                      |
|-----------|---------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| **M0 Setup and audit** | Repo verified; old build archived (`archive/meridian-v1`, tag `meridian-v1-final`); versions pinned here; Unity URP-2D project at root compiles clean; `render.py` renders the calibration asset; `ArtImporter` imports it; `.claude/settings.json` verified; ≥ 5 Ready tasks per worker; USER_ACTIONS complete | All of the above confirmed in `REVIEW_LOG.md`                                                                    |
| **M1 Core loop (placeholders)** | Earth and Mars with placeholder art: walk, jump (real g), dig, place, board **Pilgrim**, launch past the Escape Line (its fuel cost removed later, D-103), top-down flight, Mars well pulls, entry, manual landing; save/load; tests in §10.9 | Loop playable start to finish twice without console errors; all tests green; BudgetGate green; user playtest |
| **M2 Earth, Mars, space — final art and feel** | Real terrain materials, parallax, planet discs, Sun, Pilgrim, player, 2 creatures per planet, day/night, Mars dust storm, basic Cryo, placeholder audio | Screenshots match §9; budgets green; 30-minute play without errors                          |
| **M3 Inner planets complete** | Mercury and Venus full designs; Envirosuit hazards; all Rig modules; Smelter/Refinery/Blueprint Tree; inventory; Waystations and trading; Wardens basic; Catalogue; bases | Each inner planet's "only here" obtainable; apexes killable; tests for hazards and economy |
| **M4 The giants**       | Cloud-column generator; floes, Float cells, Aerostats, Crush Line; Skip Drive; belt and ring mining; all four giants' hazards, creatures, apexes; Thruster Mk2/Mk3 | Full progression Earth → Neptune completable by LEAD's QA script; budgets green on Jupiter |
| **R1 3D pipeline proof (Earth)** | The 3D renderer and side-rail camera; block-mesh terrain with PBR materials; Sun + lamps in 3D; the surveyor, the Pilgrim, Earth props batch 1 and two Earth creatures as animated models; sky dome, ridges and near props replace the parallax layers | `M1LoopTests`, `SmokeTests` and the M2/M3 gameplay tests pass unchanged; §11.1 (incl. the geometry row) green on Earth; captures match §9 v2; owner playtest |
| **C0 Style test (Earth) — v4, first and alone** | One small Earth surface scene: the new surveyor, one plant with a face and a sway idle, one critter, a painted 3-layer background, the film shader, an iris transition | LEAD passes every asset on the §9.7 checklist and the scene against §9; the capture becomes the reference (`coordination/reviews/C0_STYLE_REFERENCE.md`); budgets < 2 GB; owner look-over |
| **C1 Player, ship, space** | The v4.1 re-ink of the C0 set (B-124..B-127); the surveyor's full clip set; the upright faceless Pilgrim (side + top) with fully manual, fuel-free flight from the ground to orbit and back (D-102, D-103); planet discs for all 8 without faces; the painted starfield; the cartoon HUD gauges and Escape Line sign | §9.7 per asset; M1LoopTests pass with the new art; Space < 2 GB, 60 fps |
| **C2 Planets in cartoon** | In order: Earth, Mars, Mercury, Venus cloud layer, then the gas-giant cloud layers (Jupiter, Saturn), then Uranus and Neptune. Each planet: flora, creatures, props, 3–5 background layers, palette | Per planet: §9.7 on every asset; the planet passes §11.1 v4 (profile after each); gameplay tests unchanged |
| **C3 UI** | Menus, planet title cards (intertitle slide-in), settings with the Film effects toggle, paper/sign panels, Limelight + Patrick Hand | §9.7; every menu reachable by keyboard; toggle persists in the save |
| **C4 Profile and playtest build** | Full profile on the laptop, a playtest build | Every planet green on §11.1 v4; owner playtest |
| **C5 Style v5 test (Earth camp)** — D-185 | One Earth camp scene in the v5 look: the surveyor as a rigged cut-out (idle, walk, run, crouch, jump with bent knees, dig with the shovel and the Beam), one creature, one plant, one painted background band, one dug hole with D-183's back wall; the rig pipeline (BLENDER part sheets + bone JSON → Unity 2D Animation bones + IK) proven end to end | LEAD passes every asset against D-185's kept / changed list; crouch and jump read with bending knees in a capture at 1×; the scene stays inside §11.1; the owner's look-over accepts the look; then §9 is rewritten as v5 and the contract bumps to v4 |
| **C6 The v5 rollout** | The game redrawn in v5 planet by planet, Earth first (surveyor, creatures, flora, props, the Pilgrim, UI), each planet's gameplay tests unchanged | Per planet: every asset passes §9 v5; §11.1 green; owner playtest per planet build |
| ~~**S1 Stage and feel (Earth)**~~ *Cancelled by D-086/D-087: its non-combat parts (stage camera, air dash, squash) carry into C0–C1.* | The stage camera (§5.1), snappy movement with air dash, parry, squash-and-stretch and hit reactions (§4.2 Feel), the seven-layer stage per Earth region with set-pieces and foreground (§10.10), 60 fps surveyor clips, budgets v3 (§11.1) with adjacent-region streaming | `M1LoopTests`, `SmokeTests` and the M2/M3 gameplay tests pass unchanged; jump heights per planet unchanged ± 1 cm; StageCamera, Feel, SquashStretch, StageLayer and Residency tests green; §11.1 v3 green on Earth, Space and Mars (frame time, 4.5 GB, 2.0 GB textures); stage sheets match §9 v3; owner playtest of `Build/MERIDIAN_0.5.0/` |
| **R2 Earth, Mars, space in 3D** | All M2 content as models and materials: Mars terrain, creatures, props, POIs; planets as spheres in space; day/night and dust storms in 3D; Mars stage layer sets and set-pieces (§10.10) | As M2's exit, plus `M2SoakTests`                                                            |
| **R3 Inner planets in 3D** | Mercury and Venus, stations, Wardens, both apexes, bases and lamps as models; Mercury and Venus stage layer sets and set-pieces (§10.10) | As M3's exit: `M3InnerTests` pass twice; owner playtest                                   |
| **M4 The giants (3D)** | As the M4 row, built 3D from the start; the cloud decks as the stage layers (§10.10); the 2D M4 tasks are re-cut after R3 | As the M4 row                                                                             |
| **M5 Full systems**     | Story and factions; missions; space combat and Red Hollow; four ship classes; Gates; weather; Warden tiers; full audio; orbital drift | Story completable; both endings; every §8 row Done                                         |
| **M6 Polish, optimization, Windows build** | Profiling pass on every planet; load times; settings menu; credits from `docs/credits/`; zip build | All budgets green on every planet; 60-minute session with zero errors; user sign-off      |

**Pinned versions (L-005, 2026-10-30; D-013, D-014).** Unity: `6000.6.5f1` (Unity 6.6, Supported stream) · Blender: `5.2.2 LTS` · URP:
`17.6.0` · Addressables: `2.11.2` · Input System: `1.20.0` · Test Framework: `1.8.0` · Cinemachine: `6.6.0` (bundled core package) · Claude Code: `2.1.314`. Windows builds use the Mono scripting backend (D-014).

---

## 13. Glossary (one term per concept; use these exact words everywhere)

- **Aerostat** — a buoyant base platform on a giant; lift must exceed load.
- **Atmosphere Ring** — top-down circle at 1.2R; crossing inward starts entry.
- **Asset key** — `category/name/variant` string that names an art asset everywhere.
- **Beacon** — a *Meridian* expedition relay; one per planet; story chapters.
- **BudgetGate** — the test suite and runtime monitor that enforce §11.1.
- **Catalogue** — the scan record of creatures, plants, and minerals.
- **Crush Line** — y 100 on giants; lethal pressure.
- **Cycle** — one unit of work ending in a verifiable output.
- **Datacores / Scrip** — currency for tech unlocks / currency for goods.
- **Datum** — y of the surface (sea level) or the 1-bar cloud top.
- **Deck** — a pressure layer on a giant (1, 2, 3, Deep).
- **Envirosuit** — the player's suit: life support, hazard modules, servos, jetpack, Float cells.
- **Escape Line** — side-view altitude that triggers the switch to top-down.
- **Float cell** — suit buoyancy module, giants only, below the Datum.
- **Floe** — a floating ice platform on a giant; sublimates after disturbance.
- **Gate** — base-to-base teleporter.
- **Gravity Well** — top-down pull zone at 4R.
- **HeavyJobLock** — the lock-file protocol serializing heavy jobs (§11.2).
- **PlanetConfig** — the ScriptableObject holding one planet's numbers.
- **Placeholder** — a UNITY-made stand-in under `Assets/_Game/Placeholders/` with the real asset key.
- **Rig** — the hand tool; modules Beam, Grapple, Survey, Builder (the Lance was cancelled, D-087).
- **Skip Drive** — fast in-system travel.
- **The Sowing** — the engineered life seeded by the *Meridian* crew.
- **Task ID** — `L-###`, `U-###`, `B-###` on the task board.
- **Wardens** — enforcement drones (Drone, Sentry, Enforcer).
- **Waystation** — an orbital station with vendors and services.
