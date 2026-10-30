# MERIDIAN — Project Bible (single source of truth)

Owner: LEAD. Workers read; only LEAD edits. Changes are logged in `coordination/DECISIONS.md`.
Version: 1.3 (Sun well k_sun, cycle 8). The Lead bumps the version on every edit.

Sections: 1 Vision · 2 Setting and story · 3 The solar system in game · 4 Physics and
numbers · 5 Views and transitions · 6 Controls · 7 The eight planets · 8 Systems →
milestones · 9 Art style guide · 10 Technical architecture · 11 Performance budgets ·
12 Milestone plan · 13 Glossary

---

## 1. Vision and pillars

**Pitch.** A 2D survival-exploration game with the breadth of a modern space sandbox, set
in our real solar system. Eight landable planets, each a different world because the real
physics make it one.

**Pillars** (when two rules conflict, the higher pillar wins):
1. **Real physics you can feel.** Gravity ratios are exact. A jump on Mars is 2.6× an
   Earth jump; on Jupiter you need a jetpack to clear a step. Fuel, thrust, heat, cold,
   pressure, and radiation follow the real planet.
2. **Every world matters.** Each planet has a resource, a creature, and an activity found
   nowhere else, so the player goes everywhere.
3. **Realistic 2D.** Rendered, lit, normal-mapped art. Painterly-photographic, not pixel
   art, not cartoon.
4. **Runs on an 8 GB laptop at 60 FPS.** Realism from technique (baked maps, 2D lights,
   streaming), never from brute force.
5. **The player is never stuck.** Every hard state (no fuel, stranded on Jupiter, dead on
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
| Saturn  | A ring-mining rig: they refined skip fuel from helium rain.         | Skip Drive Mk2             |
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

**Ship speeds (top-down).** Cruise 80 u/s · Boost 160 u/s (uses main fuel) · Skip Drive
1,200 u/s after a 3 s spool, consumes skip fuel per second, disabled inside a Gravity Well.
Earth → Mars ≈ 7 s cruise; Earth → Neptune ≈ 11 s skip.

---

## 4. Physics and numbers

### 4.1 Gravity (exact ratios; absolute values may be tuned together, never separately)

| Planet  | g (m/s²) | × Earth | Escape velocity (km/s) | Launch fuel cost (% of 100-unit tank) = round(1.5 × v_esc) |
|---------|----------|---------|------------------------|---------------------------------------------------------------|
| Mercury | 3.70     | 0.38    | 4.3                    | 6                                                             |
| Venus   | 8.87     | 0.90    | 10.4                   | 16                                                            |
| Earth   | 9.81     | 1.00    | 11.2                   | 17                                                            |
| Mars    | 3.72     | 0.38    | 5.0                    | 8                                                             |
| Jupiter | 24.79    | 2.53    | 59.5                   | 89                                                            |
| Saturn  | 10.44    | 1.06    | 35.5                   | 53                                                            |
| Uranus  | 8.69     | 0.89    | 21.3                   | 32                                                            |
| Neptune | 11.15    | 1.14    | 23.5                   | 35                                                            |

`PlanetConfig` ScriptableObjects hold these values; an EditMode test asserts every ratio to
±0.5%. `Physics2D.gravity` is set per planet on load. Gravity affects the player, creatures,
dropped items, projectiles, debris, and the ship in side view; in top-down it drives well pull.

### 4.2 Movement (side view)

Jump impulse is fixed; gravity is real; upgrades scale the impulse, never gravity.

| Quantity                               | Value / formula                                 |
|----------------------------------------|-------------------------------------------------|
| Walk / sprint speed                    | 4.0 / 6.5 m/s on every planet                   |
| Jump take-off speed v₀                 | 7.00 m/s (Earth jump height 2.5 m)              |
| Jump height h                          | v₀² / 2g → Mercury 6.6 m, Venus 2.8, Earth 2.5, Mars 6.6, Jupiter 1.0, Saturn 2.4, Uranus 2.8, Neptune 2.2 |
| Servo upgrades (Envirosuit)            | Mk1 +15% v₀, Mk2 +30%, Mk3 +45% (Jupiter: Mk2 clears a 1 m step reliably) |
| Fall damage                            | None below 12 m/s impact; lethal at 24 m/s (unupgraded). Safe drop = 72/g m: Earth 7.3 m, Mars 19.4, Jupiter 2.9 |
| Terminal velocity (m/s, play layer)    | Mercury 60 (no air; design cap), Venus 20, Earth 50, Mars 55, Jupiter 45, Saturn 48, Uranus 50, Neptune 50 |
| Coyote time / jump buffer              | 0.10 s / 0.12 s                                 |

**Jetpack** (thrust in m/s² while fuel lasts; net lift = thrust − g; recharges in 2 s on ground):

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
| Can launch from      | Mk1: Mercury, Venus, Earth, Mars, Uranus · Mk2: + Saturn, Neptune · Mk3: + Jupiter |
| Launch burn          | Fuel cost from §4.1 is consumed over the first 3 s of thrust from rest on the surface; flight inside the atmosphere is then free |
| Tank Mk1/Mk2/Mk3     | 100 / 200 / 400 units of Launch Fuel                                  |
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

Camera: orthographic, default size 9 (18 m tall), zoom 6–14 with the mouse wheel. The
world is a horizontal cylinder (wraps). Coordinates are tiles = meters.

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
altitude, vertical speed, fuel, and thrust-to-weight.

### 5.2 Launch: side → top-down

Trigger: the ship's center crosses the Escape Line with upward velocity.
1. 0.3 s: input locked, camera eases out, HUD fades.
2. 0.5 s: fade through white (atmosphere glare). `PlanetSide` scene unloads; `Space` scene
   is already loaded (Core keeps it resident but inactive) and activates.
3. Ship placed on the planet's Atmosphere Ring at the angle matching its longitude
   (longitude = x / width × 360° plus the planet's current rotation), velocity 20 u/s
   outward, 1 s invulnerability, top-down HUD on.
Total ≤ 1.5 s; player state (hull, fuel, cargo) is carried in `GameState`, never re-read
from disk.

### 5.3 Entry and landing: top-down → side

Trigger: the ship's center crosses a landable planet's Atmosphere Ring with inward radial
velocity (or the player holds **F** inside the ring to begin a controlled entry).
1. 0.8 s: heat shimmer, camera pushes in, fade through white.
2. `PlanetSide` loads with that planet's `PlanetConfig`; the longitude is the entry angle
   minus the planet's rotation; the terrain streams around that x.
3. Ship placed at Escape Line altitude + 20 m, descending at 15 m/s, planet gravity on,
   fuel unchanged. The player flies down and lands (§4.3). Non-landable bodies have no
   Atmosphere Ring; the Sun kills.
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
|            | Rig module                 | 1 Beam · 2 Lance · 3 Survey · 4 Builder; Q/E cycle |
|            | Interact / board ship      | F                                         |
|            | Build menu / Inventory / Map / Catalogue | B / Tab / M / N              |
|            | Float cell toggle (giants) | V                                         |
| Ship, side | Main thrust / retro        | W / S                                     |
|            | Lateral                    | A, D                                      |
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
  dioxide (dry ice), sulfur, **Perchlorate** (the cheapest launch oxidizer; halves fuel
  crafting cost), nickel-iron meteorites.
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
  cold, so Cryo-charged Lance rounds (made from Mercury ice) are its counter.
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
- **Hazards.** Radiation 3 everywhere above Deck 2 (the belts; Mk3 brings it to 1; Deck 2
  and below are shielded by the atmosphere to 1), lightning (Deck 2–3), gravity 2.53×
  (fall damage above 2.9 m; jetpack Mk3 required; Thruster Mk3 required to launch),
  Cryo 2 in Deck 1, Thermal 2 in Deep. The **Great Red Spot** is a 600 m wide zone where
  wind pushes 12 m/s and floes spin.
- **Resources.** Hydrogen, helium, ammonia ice, phosphorus pigments (Red Spot floes),
  **Metallic Hydrogen** (Deep only, forms in pressure "veins" of hardened floe cores —
  the fuel and conductor for every endgame drive and weapon).
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
  **Helium-3 Condensate** (helium rain collected in Deck 2–3 traps — the only efficient
  skip fuel; deuterium from water works at one-third efficiency).
- **Creatures.** Helium jelly (floats up when hit), Hex drake (winged, rides the hexagon
  walls), Ringmite (space, swarms), Floe moth. **Apex: Polar Hydra** — six-headed cloud
  serpent of the Hexagon's eye; each head is destroyed by crossing a different wall with
  its lure; the body drops the Hexacore (Aerostat Mk3 buoyancy core).
- **Activities / POIs.** Top-down ring mining lanes (density varies with distance; gaps
  are safe), the ring-mining rig with the Saturn beacon, Saturn Waystation (Halcyon's
  largest market), Titan and Enceladus in the sky, skip-fuel refining.
- **Only here.** Helium-3 Condensate; ring mining; Skip Drive Mk2 blueprint.
- **Gate.** Cryo Mk2, Pressure Mk2, Thruster Mk2, Float cell Mk1. **Look.** Pale gold and
  butter bands, the ring plane as a bright line across the sky, soft low sunlight.

### 7.8 Uranus — the sideways winter
- **Hazards.** Cryo 3 (coldest atmosphere, −224 °C: Mk3 required), gravity 0.89×, dim
  light (sunlight 0.25 of the in-game clamp), **seasons**: the lit hemisphere is one half of
  the world's x range and swaps every 6 game days; the dark half has Cryo 3 even with Mk3
  (needs suit heater fuel), methane hail, **Diamond rain** below Deck 3 (falling 5–20 cm
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
  the final fight uses every system (anchors, Float cells, Lance, ship support).
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
| Tools     | Multitool: mining beam, scanner, weapons, upgrades   | **Rig** with modules **Beam** (mine/dig), **Lance** (weapon), **Survey** (scan), **Builder**, **Grapple** (M4) | M1 Beam/Builder, M3 rest |
|           | Terrain digging and building                         | 1 m tiles; dig with Beam; place blocks and modules with Builder | M1        |
| Economy   | Resources, refining, crafting, tech tree             | Resources (§7); **Smelter** and **Refinery** stations; **Blueprint Tree** | M3        |
|           | Inventory upgrades, trading                          | Slot-based suit/ship/cargo; **Scrip** currency; vendors at **Waystations** | M3        |
| Ship      | Launch fuel, landing, fast travel                    | Launch Fuel (hydrogen + oxidizer); landing rules §4.3; **Skip Drive** | M1 fuel/landing, M4 Skip Drive |
|           | Shields, weapons, cargo, upgrades, multiple ships    | Hull shield, Pulse cannon, cargo bays; ships **Pilgrim** (start), **Dray** (hauler), **Shrike** (fighter), **Vagabond** (deep-range) | M5        |
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

---

## 9. Art style guide

**Target.** Rendered realism in 2D: the look of a nature documentary still, with painterly
softness in haze and clouds. No outlines, no pixelation, no cel shading.

| Rule                 | Specification                                                                                |
|----------------------|----------------------------------------------------------------------------------------------|
| Scale                | PPU 128 (1 m = 128 px source). A human is 1.8 m = 230 px. Default on-screen density ≈ 60 px/m |
| Lighting             | Color maps are unlit albedo; Unity 2D lights do all shading via normal maps. Each planet has a sunlight intensity (clamped): Mercury 1.6, Venus 1.2, Earth 1.0, Mars 0.75, Jupiter 0.45, Saturn 0.35, Uranus 0.25, Neptune 0.2, and an ambient color |
| Palettes             | Earth greens/blues/ochres · Mars rust/salmon · Mercury white/black/violet · Venus orange-cream/black · Jupiter cream/rust/brick · Saturn pale gold · Uranus cyan fog · Neptune indigo/white · Space near-black with a Milky Way band and warm Sun |
| Readability          | Every creature silhouette reads at 60 px/m against its planet's background; interactive props have a 10% brighter rim in the mask map |
| Atmosphere           | 3 parallax layers per planet (far sky/clouds, mid terrain, near detail) plus a haze gradient; gas giants add band layers that scroll at different speeds |
| Creatures            | Grounded anatomy with one alien exaggeration per species; materials match the planet (silicate, sulfur, ice) |
| Ships                | Industrial-realistic, worn, legible thrusters and lights; emission maps for engines and windows |
| UI                   | Thin HUD, planet-tinted accents, numerals in a monospace OFL font, one-line tooltips      |
| Fonts                | OFL-licensed only (candidates: Inter, JetBrains Mono); logged in `docs/credits/unity.md`   |
| Forbidden            | Any name, logo, silhouette, or story element from existing games; anything that reads as pixel art or a cartoon |

---

## 10. Technical architecture

### 10.1 Stack
Unity 6 LTS (exact build pinned in §12), URP with the 2D Renderer, Input System,
Addressables, Unity Test Framework, Cinemachine (2D), TextMeshPro. Blender LTS (pinned in
§12), Eevee for sprites, Cycles for planet bakes, all scripted in Python.

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
Data: 1 m tiles in 32 × 32 chunks, generated from a seed by `IWorldGenerator`
implementations: `SolidWorldGenerator` (Earth, Mars, Mercury, Venus) and
`CloudColumnGenerator` (giants). Generation runs on a worker thread, applied on the main
thread within 2 ms per frame. Rendering: Unity Tilemap per chunk with RuleTiles that carry
normal maps (secondary texture), random variants, and an edge-blend overlay tilemap for soft
transitions. Collision: `TilemapCollider2D` + `CompositeCollider2D` per chunk; only the
edited chunk rebuilds. Persistence: only player changes are saved as `(chunk, index, tileId)`
diffs. Only chunks within 2 of the camera stay in memory; others are pooled.

### 10.5 Lighting and materials
Sprite material `Sprite_LitEmissive` (Shader Graph): albedo, `_NormalMap`, `_EmissionMap`,
`_MaskTex` (R = rim strength). Planet discs use `PlanetDisc` (equirect texture → sphere
projection on a disc, rotation offset, terminator from the Sun direction, atmosphere rim,
optional cloud layer). Lights: one global light per scene, the Sun as a far light, ≤ 8
visible local lights (player lamp, thrusters, vents, lightning), light textures for haze.

### 10.6 Art pipeline (summary; the contract is authoritative)
Blender renders every asset to `Assets/_Game/Art/<key>_<map>.png`. `ArtImporter`
(`Assets/_Game/Code/Editor/ArtImporter.cs`, an `AssetPostprocessor`) applies import settings
per category, links secondary textures, slices frame sheets from the `.json` manifest,
assigns the Addressable address = asset key, adds the sprite to the right atlas, and
retires the matching file in `Placeholders/`. Code loads art only by key through
`ArtKeys` constants, never by path.

### 10.7 Save format
`%USERPROFILE%/AppData/LocalLow/<company>/MERIDIAN/saves/slot<N>/` holds `state.json`
(player, ship, inventory, story, catalogue, bases, timers) and one `terrain_<planet>.bin`
per visited planet (diffs). Autosave on every transition and every 5 minutes; three
rotating backups. Version field; migrations on load.

### 10.8 Tools (PowerShell, in `tools/`)
`unity_compile.ps1` (batch compile, zero-error gate), `unity_test.ps1 [EditMode|PlayMode]`
(writes `logs/tests_<date>.xml` and a summary to `coordination/reports/unity/`),
`unity_build.ps1` (Windows build to `Build/MERIDIAN_<version>/`), `unity_profile.ps1`
(runs the BudgetGate scenes and writes `coordination/reports/unity/perf_<date>.md`),
`unity_art_preview.ps1 <key>` (renders the asset under 2D lights to `logs/preview_<key>.png`),
`blender_render.ps1 <key|category|all> [-Preview]`. All read `tools/paths.json` for the
Unity and Blender executables and exit non-zero on failure.

### 10.9 Tests (owned by UNITY unless noted; LEAD adds QA tests in `Tests/LeadQA/`)
EditMode: gravity ratios, launch fuel formula, well-pull formula, PlanetConfig
completeness, ArtImporter rules, asset-key ↔ placeholder coverage. PlayMode: jump height
per planet (±3%), fall damage thresholds, launch transition (state carried, ≤ 1.5 s),
entry transition, save → load → identical state and terrain, chunk persistence after
digging, BudgetGate (frame time, GC, light and particle caps, memory).

---

## 11. Performance budgets (requirements, not goals)

### 11.1 The game — enforced by BudgetGate (`Assets/_Game/Tests/Unit/BudgetGateTests.cs` plus the runtime `BudgetMonitor`, owned by UNITY; LEAD confirms numbers at every review)

| Budget                        | Limit                                                             |
|-------------------------------|-------------------------------------------------------------------|
| Frame time                    | ≤ 16.6 ms at 1080p on the dev laptop; target ≤ 12 ms average      |
| RAM (built game)              | ≤ 2.5 GB working set; ≤ 600 MB textures loaded; ≤ 60 MB audio     |
| Draw calls                    | ≤ 150 side view, ≤ 80 top-down (atlases, batching)                |
| 2D lights visible             | ≤ 8 (hard cap 12); shadows only on the player lamp                |
| Particles alive               | ≤ 600; every emitter pooled                                       |
| GC allocation (steady state)  | ≤ 1 KB per 300 frames; zero per-frame allocations in gameplay code |
| Chunk generation              | ≤ 2 ms main-thread per frame; no hitch > 33 ms during streaming   |
| Planet load                   | ≤ 4 s; space ↔ planet transition ≤ 1.5 s                          |
| Textures                      | BC7 (color), BC5 (normals), mipmaps on world sprites; atlases ≤ 2048² |
| Audio                         | Vorbis, streamed for music, compressed in memory for SFX          |
| Asset size caps               | Per the contract (§4 there); the importer rejects oversize files  |

### 11.2 The dev workflow — enforced by HeavyJobLock (LEAD schedules; everyone complies)

| Resource                               | Limit                                                                  |
|----------------------------------------|------------------------------------------------------------------------|
| Unity Editor (interactive or batch)    | ≤ 3.5 GB; only one instance per project exists, so batch jobs never run while the Editor is open |
| Blender heavy render (> 512 px or batch) | ≤ 2.5 GB; never while `Unity.exe` is running; headless; exits after each batch |
| Claude Code sessions (3)               | ≈ 1 GB total; keep logs terse, read large files by section            |
| Free RAM                               | ≥ 1 GB headroom; browsers closed during work                          |
| Heavy jobs                             | Serialized through `coordination/locks/heavy_<role>.lock` (CLAUDE.md rule 6) |

If the laptop's RAM is upgraded, LEAD raises only this section and logs the decision.

---

## 12. Milestone plan (each ends with a build in `Build/` and a plain-language report in `coordination/reviews/M<n>_REPORT.md`)

| Milestone | Scope                                                                                       | Exit criteria                                                                                                                                      |
|-----------|---------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| **M0 Setup and audit** | Repo verified; old build archived (`archive/meridian-v1`, tag `meridian-v1-final`); versions pinned here; Unity URP-2D project at root compiles clean; `render.py` renders the calibration asset; `ArtImporter` imports it; `.claude/settings.json` verified; ≥ 5 Ready tasks per worker; USER_ACTIONS complete | All of the above confirmed in `REVIEW_LOG.md`                                                                    |
| **M1 Core loop (placeholders)** | Earth and Mars with placeholder art: walk, jump (real g), dig, place, board **Pilgrim**, launch past the Escape Line with fuel cost, top-down flight, Mars well pulls, entry, manual landing; save/load; tests in §10.9 | Loop playable start to finish twice without console errors; all tests green; BudgetGate green; user playtest |
| **M2 Earth, Mars, space — final art and feel** | Real terrain materials, parallax, planet discs, Sun, Pilgrim, player, 2 creatures per planet, day/night, Mars dust storm, basic Cryo, placeholder audio | Screenshots match §9; budgets green; 30-minute play without errors                          |
| **M3 Inner planets complete** | Mercury and Venus full designs; Envirosuit hazards; all Rig modules; Smelter/Refinery/Blueprint Tree; inventory; Waystations and trading; Wardens basic; Catalogue; bases | Each inner planet's "only here" obtainable; apexes killable; tests for hazards and economy |
| **M4 The giants**       | Cloud-column generator; floes, Float cells, Aerostats, Crush Line; Skip Drive; belt and ring mining; all four giants' hazards, creatures, apexes; Thruster Mk2/Mk3 | Full progression Earth → Neptune completable by LEAD's QA script; budgets green on Jupiter |
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
- **Rig** — the hand tool; modules Beam, Lance, Survey, Builder, Grapple.
- **Skip Drive** — fast in-system travel.
- **The Sowing** — the engineered life seeded by the *Meridian* crew.
- **Task ID** — `L-###`, `U-###`, `B-###` on the task board.
- **Wardens** — enforcement drones (Drone, Sentry, Enforcer).
- **Waystation** — an orbital station with vendors and services.
