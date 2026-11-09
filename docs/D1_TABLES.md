# D1 tuning tables (L-013; Bible 5.2 §8.1; D-174)

Owner: LEAD. UNITY loads these as data (json / ScriptableObject), never as code constants, so LEAD can retune
without a code change. Numbers are starting values for the owner's next playtest; tune from play, not by feel
in code. Item ids are the existing ItemRegistry ids; none is new.

## 1. Digging

- **Stroke time** = 0.25 s × planet base hardness × tier hardness ÷ Beam power, capped at **8 s**. No depth gate.
- **Planet base hardness**: Earth 1 · Mars 1.6 · Mercury 2.5 · Venus surface 4.
- **Tier hardness** (depth below the Surface Line): T1 Topsoil 0–10 m ×1 · T2 Subsoil 10–40 m ×2 · T3 Stone 40–100 m ×4 · T4 Deep 100–200 m ×8 · T5 Core 200 m to the world floor ×16.
- **Beam power**: 1 at the start; the Dig branch raises it (§5).
- **What a dug tile gives**: either **dirt** (the tile's matrix: soil, regolith, stone, basalt …) into the **dirt store**, or a **material** into the pack, by the tier's material chance: T1 5 % · T2 9 % · T3 11 % · T4 12 % · T5 12 %. A material roll picks from the planet's tier table (§3) by weight.
- **Dirt store**: weightless, 60 tiles at the start (Haul raises it); the Builder spends it on mounds, ramps and ladders; not sellable. Full: dug dirt is dropped as a puff, nothing lost but the dirt.
- **Pockets** (U-158, D-162 (5)): unchanged in placement; a pocket gives 3 of its tier's **rarest** item (the last row of the tier's table).
- **Surface resource rocks**: unchanged (1 item per stroke × 3, regrow a game day); small topside income.

## 2. Materials: Scrip value and weight

Sell topside from the pack at these values; a Waystation pays +25 % (Voyage raises it, §5).

| Item | Scrip | kg |  | Item | Scrip | kg |
|------|------:|---:|--|------|------:|---:|
| clay | 2 | 1 |  | silica | 24 | 1.5 |
| carbon | 4 | 1 |  | nickel | 30 | 2.5 |
| hematite | 9 | 1.5 |  | aluminium | 36 | 2 |
| water_ice | 10 | 1.5 |  | polar_ice | 40 | 1.5 |
| iron | 12 | 2 |  | graphite | 60 | 1 |
| perchlorate | 12 | 1 |  | phosphorus_pigment | 80 | 0.5 |
| sulfide | 14 | 1.5 |  | vitriol_glass | 140 | 1 |
| sulfur | 14 | 1 |  | deep_core_sample | 150 | 3 |
| copper | 16 | 2 |  | solarite | 160 | 1 |
|  |  |  |  | deep_diamond | 300 | 0.5 |

The giants' finds (not dug; floe cores and deep dives; they pay the Skill Tree's outer rings), Scrip / kg: ring_rock 25 / 2 · ring_ice 30 / 1.5 · methane_ice 20 / 1.5 · ammonia_ice 25 / 1.5 · superionic_ice 400 / 2 · helium3_condensate 500 / 1 · metallic_hydrogen 600 / 2.

These replace Trade/Market.cs's raw-material base prices (its crafted goods keep theirs).

## 3. Tier tables (material weights within a tier; the last row of each tier is its pocket item)

| Tier | Earth (×1) | Mars (×1.6) | Mercury (×2.5) | Venus (×4) |
|------|-----------|-------------|----------------|------------|
| T1 | clay 60, carbon 40 | hematite 60, perchlorate 40 | iron 30, sulfide 70 | sulfide 30, sulfur 70 |
| T2 | carbon 20, iron 45, copper 35 | water_ice 25, iron 35, hematite 40 | iron 20, sulfide 30, nickel 50 | aluminium 20, sulfur 40, nickel 40 |
| T3 | aluminium 25, nickel 35, silica 40 | perchlorate 25, silica 35, nickel 40 | nickel 25, aluminium 35, silica 40 | silica 25, sulfide 30, aluminium 45 |
| T4 | aluminium 20, phosphorus_pigment 25, graphite 55 | phosphorus_pigment 25, graphite 35, aluminium 40 | graphite 35, polar_ice 25 (cold traps only; graphite elsewhere), solarite 40 | phosphorus_pigment 25, graphite 30, vitriol_glass 45 |
| T5 | graphite 30, deep_core_sample 55, deep_diamond 15 | graphite 25, deep_core_sample 50, deep_diamond 25 | solarite 30, deep_core_sample 40, deep_diamond 30 | vitriol_glass 30, deep_core_sample 30, deep_diamond 40 |

Mercury's buried solarite has no twilight window (only the surface clusters keep U-059's window).

## 4. The pack and the climb

- **Pack limit**: 30 kg at the start (Haul raises it). Full: no more pickups, a HUD cue; the drop stays on the ground.
- **Load factor**: climb speed, jetpack lift and grapple reel × (1 − k × load ÷ limit), k = 0.5 at the start (Haul lowers it to 0.35 and 0.2).
- **Starting ways up**: walking ramps ≤ 35°; the jetpack Mk1 (suit power); Builder mounds from the dirt store. The Grapple and ladders open in Ascent ring 1.

## 5. The Skill Tree

Six branches, five rings, two nodes per ring (three at ring 3); 66 nodes. A node needs one bought node linked to it (ring 1 links to the centre). "↔" marks a sideways link into the neighbouring branch (the branch order round the circle: Dig · Haul · Ascent · Survey · Endurance · Voyage · back to Dig). Costs: Scrip + materials. Effects stack additively unless marked ×.

**Links (revised 17:1x, B-204)**: laid out for a crossing-free radial chart (BLENDER's check: 0 crossings); each border between neighbouring branches carries exactly one sideways link at ring 3 and one at ring 5; a comma in the links column means any one of them.

**Costs by ring**: R1 60–100 Scrip · R2 250–400 · R3 900–1 300 + 4–6 of a Mars / Mercury material · R4 3 000–4 500 + 3–4 of vitriol_glass, solarite or deep_core_sample · R5 10 000–15 000 + 2 of a giant's find or 1 Datacore.

### Dig
| id | R | effect | cost | links |
|----|---|--------|------|-------|
| dig_power_1 | 1 | Beam power +0.5 | 80 | centre |
| dig_brush_1 | 1 | brush radius +0.1 m | 100 | centre |
| dig_power_2 | 2 | Beam power +1 | 300 | dig_power_1 |
| dig_rhythm_1 | 2 | each consecutive stroke on the same face −10 % time (max −30 %) | 350 | dig_power_1, dig_brush_1 |
| dig_power_3 | 3 | Beam power +1.5 | 1 100 + hematite 6 | dig_power_2 |
| dig_heatsink | 3 | no Beam cool-down | 1 200 + perchlorate 5 | dig_rhythm_1 |
| dig_brush_2 | 3 | brush radius +0.2 m | 1 000 + sulfide 5 | dig_rhythm_1 ↔ haul_magnet_1 |
| dig_power_4 | 4 | Beam power +2 | 3 800 + solarite 3 | dig_power_3 |
| dig_rhythm_2 | 4 | rhythm max −50 % | 4 000 + vitriol_glass 3 | dig_heatsink, dig_brush_2 |
| dig_power_5 | 5 | Beam power +3 | 12 000 + metallic_hydrogen 2 | dig_power_4 ↔ voy_dray |
| dig_core_bit | 5 | tier hardness counts one tier lower (T5 as T4) | 15 000 + deep_diamond 2 + Datacore 1 | dig_rhythm_2 |

### Haul
| id | R | effect | cost | links |
|----|---|--------|------|-------|
| haul_pack_1 | 1 | pack +15 kg | 70 | centre |
| haul_dirt_1 | 1 | dirt store +40 | 60 | centre |
| haul_pack_2 | 2 | pack +25 kg | 280 | haul_pack_1 |
| haul_light_1 | 2 | load factor k → 0.35 | 400 | haul_pack_1, haul_dirt_1 |
| haul_pack_3 | 3 | pack +40 kg | 1 000 + hematite 5 | haul_pack_2 |
| haul_magnet_1 | 3 | drops within 3 m fly into the pack | 1 100 + sulfide 4 | haul_light_1 ↔ dig_brush_2 |
| haul_sorter | 3 | the pack auto-drops the lowest-value item when full and a better one comes | 1 300 + perchlorate 5 | haul_light_1 |
| haul_pack_4 | 4 | pack +60 kg | 3 500 + deep_core_sample 2 | haul_pack_3 |
| haul_light_2 | 4 | k → 0.2 | 4 200 + vitriol_glass 3 | haul_magnet_1, haul_sorter |
| haul_pack_5 | 5 | pack +100 kg | 11 000 + helium3_condensate 2 | haul_pack_4 ↔ asc_recall |
| haul_compact | 5 | ores weigh half | 14 000 + superionic_ice 2 | haul_light_2 |

### Ascent
| id | R | effect | cost | links |
|----|---|--------|------|-------|
| asc_grapple_1 | 1 | the Grapple: 12 m line | 90 | centre |
| asc_ladder_1 | 1 | Builder ladders (2 dirt per metre) | 70 | centre |
| asc_jet_1 | 2 | jetpack thrust ×1.3 | 320 | asc_grapple_1, asc_ladder_1 |
| asc_climb_1 | 2 | climbing speed ×1.3, no slide on ≤ 40° | 260 | asc_ladder_1 |
| asc_grapple_2 | 3 | line 24 m, reel ×1.5 | 1 100 + hematite 5 | asc_jet_1 |
| asc_jet_2 | 3 | jetpack power use ×0.7 | 1 200 + perchlorate 5 | asc_jet_1 |
| asc_ladder_2 | 3 | ladders 1 dirt per metre, placed 3 m at once | 900 + sulfide 4 | asc_climb_1 ↔ sur_scan_2 |
| asc_jet_3 | 4 | thrust ×1.6, power use ×0.5 | 4 000 + solarite 3 | asc_jet_2 |
| asc_grapple_3 | 4 | line 40 m, reel ×2, two anchors | 3 600 + vitriol_glass 3 | asc_grapple_2, asc_ladder_2 |
| asc_winch | 5 | a winch line from the Surface Line: reel straight up from any depth | 13 000 + metallic_hydrogen 2 | asc_grapple_3 |
| asc_recall | 5 | one recall beacon per run (topside in 5 s, pack kept) | 15 000 + Datacore 1 | asc_jet_3 ↔ haul_pack_5 |

### Survey
| id | R | effect | cost | links |
|----|---|--------|------|-------|
| sur_scan_1 | 1 | scan radius +10 m | 70 | centre |
| sur_depth_1 | 1 | the HUD shows the next tier's depth | 60 | centre |
| sur_scan_2 | 2 | scan reveals pockets 2 m deeper | 300 | sur_scan_1 ↔ asc_ladder_2 |
| sur_preview_1 | 2 | the HUD lists the current tier's materials | 250 | sur_depth_1 |
| sur_scan_3 | 3 | radius +20 m, depth +4 m | 1 000 + hematite 5 | sur_scan_2 |
| sur_rare | 3 | rare items glint through 1 m of ground | 1 200 + sulfide 5 | sur_scan_2, sur_preview_1 |
| sur_preview_2 | 3 | the next tier's materials too | 900 + perchlorate 4 | sur_preview_1 |
| sur_scan_4 | 4 | radius +30 m, depth +8 m, scan cool-down ×0.5 | 3 400 + solarite 3 | sur_scan_3 |
| sur_vault | 4 | Warden vaults and relics show on the map | 4 200 + deep_core_sample 2 | sur_rare, sur_preview_2 |
| sur_deep_eye | 5 | pockets anywhere on screen show through the ground | 12 000 + superionic_ice 2 | sur_scan_4 |
| sur_cartographer | 5 | dug tunnels stay on the map with their best finds | 10 000 + Datacore 1 | sur_vault ↔ end_suit_mk3 |

### Endurance
| id | R | effect | cost | links |
|----|---|--------|------|-------|
| end_air_1 | 1 | oxygen +30 % | 80 | centre |
| end_fall_1 | 1 | fall damage −30 % | 60 | centre |
| end_air_2 | 2 | oxygen +50 % | 300 | end_air_1 |
| end_heat_1 | 2 | heat and pressure from depth −25 % | 380 | end_air_1, end_fall_1 |
| end_air_3 | 3 | oxygen +80 % | 1 000 + water_ice 6 | end_air_2 |
| end_heat_2 | 3 | heat and pressure from depth −50 % | 1 300 + sulfide 5 | end_heat_1 |
| end_fall_2 | 3 | no fall damage under 15 m | 900 + hematite 5 | end_fall_1 ↔ voy_hold_2 |
| end_deep_1 | 4 | Venus T4–T5 heat halved | 4 400 + vitriol_glass 4 | end_heat_2, end_fall_2 |
| end_air_4 | 4 | oxygen ×2 | 3 200 + polar_ice 4 | end_air_3 |
| end_deep_2 | 5 | no depth hazard on any planet | 14 000 + helium3_condensate 2 | end_deep_1 |
| end_suit_mk3 | 5 | the Mk3 envirosuit (every hazard −1) | 12 000 + Datacore 1 | end_air_4 ↔ sur_cartographer |

### Voyage
| id | R | effect | cost | links |
|----|---|--------|------|-------|
| voy_price_1 | 1 | Waystation +10 % | 90 | centre |
| voy_hold_1 | 1 | rocket hold: 100 kg stored between runs | 80 | centre |
| voy_thrust_2 | 2 | thruster Mk2 (a faster climb with a heavy hold) | 400 | voy_price_1, voy_hold_1 |
| voy_price_2 | 2 | Waystation +20 % | 320 | voy_price_1 |
| voy_hold_2 | 3 | hold 300 kg | 1 000 + hematite 5 | voy_thrust_2 ↔ end_fall_2 |
| voy_skip_1 | 3 | the Skip Drive (spool −30 %) | 1 300 + solarite 2 | voy_thrust_2 |
| voy_price_3 | 3 | Waystation +35 % | 1 100 + perchlorate 5 | voy_price_2 |
| voy_thrust_3 | 4 | thruster Mk3 (lifts off the giants) | 4 500 + vitriol_glass 4 | voy_skip_1, voy_hold_2 |
| voy_trader | 4 | sell from orbit at the Waystation's price | 3 800 + deep_core_sample 2 | voy_price_3 |
| voy_skip_2 | 5 | Skip Drive spool −70 %, cool-down −50 % | 12 000 + metallic_hydrogen 2 | voy_thrust_3 |
| voy_dray | 5 | the Dray hauler: hold 1 000 kg | 15 000 + Datacore 1 | voy_trader ↔ dig_power_5 |

## 6. The first hour (Earth, a new player; the check on the numbers)

- Dig rate at power 1: T1 stroke 0.25 s, T2 0.5 s; a stroke opens about 2.5 tiles → 4–10 tiles a second.
- T2 income: 9 % materials × ~13 Scrip ≈ **5 Scrip a second of digging**; the 30 kg pack (≈ 15 items at 2 kg) fills in ~35 s → **~200 Scrip a run**; a run (dig, fill, climb 20–40 m, sell) ~2–3 min.
- Ring 1 nodes (60–100) after the first run; ring 2 (250–400) every 2 runs. After ~20 runs (≈ 1 hour), ~4 000 Scrip: most of rings 1–2 in two or three branches, not all six: choices matter.
- Ring 3 needs Mars or Mercury materials → the player flies on (the starting thruster reaches all four inner planets; the giants need voy_thrust_3 to lift off again).
- T3 on Earth at power 2.5: stroke 0.4 s, ~12 Scrip a second; the pack (now ~70 kg) ≈ 500 Scrip a run.

## 7. Rank and the New Expedition (D-175)

- **Surveyor Rank** by the Scrip earned (sales only, not spending) in the current expedition: Rank 1 at 0 · 2 at 300 · 3 at 800 · 4 at 1 800 · 5 at 3 500 · 6 at 7 000 · 7 at 14 000 · 8 at 28 000 · 9 at 50 000 · 10 at 80 000 (about a third of the whole tree's cost: Rank 10 comes with rings 1–3 well filled and some of ring 4).
- **New Expedition**: available topside at Rank 10. Wipes: bought nodes, Scrip, Rank, the pack, the rocket's hold, base storage. Keeps: Catalogue, story chapters, Datacores, discovered planets, buildings. Returns the player to Earth's camp.
- **Multiplier**: expedition n multiplies every Skill Tree stat by (1 + 0.25 × (n − 1)): Beam power, brush radius, pack limit, dirt store, climb / jetpack / reel speed, scan radius and depth, oxygen, hazard resistance (the load factor k and the stroke cap are not multiplied). Scrip prices are not multiplied.
- The tree has no other respec.

## 8. Tuning rules

LEAD owns these numbers (D-174). A worker who finds a number that breaks play (a run under 30 s or over 6 min, a ring unreachable) reports it with its measurement; LEAD retunes here, never in code.
