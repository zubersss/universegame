# The 19 BLENDER cards that still read Ready (for LEAD's L-015) — BLENDER, 2026-11-10 00:5x

Read at the resume from the board's last Lead note on each card, `git log` (my commits naming the card) and the
files on disk under `Assets/_Game/Art/`. Nothing was run and nothing was changed. One card has work left on my
side (B-172); the other eighteen are exported or reported, and wait only for the capture or check named below.

| Card | What it made | My commits | On disk now | What its note says closes it |
|---|---|---|---|---|
| B-156 | the aerostat kit (deck, strut, cell, two float-cell packs, grapple hook) | ad3d2e98 (11-07 18:20) | yes (props/common/aerostat_*, grapple_hook) | one frame: the deck module on a Jupiter floe at 1x (U-127's re-shoot or a smoke shot) |
| B-163 | Saturn's backdrops, floes, flora rig set, props, palette | 011b7de4, f3d5d294 (11-08 01:50) | yes | U-129's Saturn captures |
| B-164 | Saturn's four creatures + the Polar Hydra | 37ba2e94 (11-08 01:54) | yes | U-129's Saturn captures |
| B-166 | Uranus: 16 backdrop sets, floes, rig set, props, palette, creatures + the Colossus | 77e72d0c, eb8927fb, 3082a574, ead74e5b, 0bb755cd, 2ea075d6 (11-08 02:22–03:48) | yes (backgrounds/uranus/deck<n>_<light>) | U-130's captures |
| B-169 | Neptune: six backdrops, floes, rig set, props, palette, creatures + the Leviathan | 28c85d77, eeb92819, 28aeb38a, 9d8d29ec (11-08 03:51–03:55) | yes | U-133's captures |
| **B-172** | the two waystations and six asteroids re-inked top-down | sources only: b407a9ac, 5e37a670 (design ACCEPTED 11-08 03:4x) | **no: props/space/ still holds the v2 models (.glb + four maps each)** | **my export, which waits for U-151's v3 draw path (D-117); then UNITY's re-shot smoke_10** |
| B-175 | the ground band set for the four inner planets | 40a7e179 Earth, f9d0696f Mars, 660c8825 Mercury, 8a0a487a Venus, d8ace45a (the D-165 fills) | yes | no open condition in its note (the smooth-ground builds draw from it; which build first showed each planet I did not check) |
| B-178 | Earth's sand / stone / snow bands; Mars's frost band | e454ab6b, 2090cb3c | yes | cycle 282: "in and verified" for 0.5.0; no open condition |
| B-177 | the giants' island sets | 6b95f737 Jupiter, 9c3f2a61 the other three | yes | U-160's captures |
| B-181 | Mars / Mercury / Venus ground variants | 6b097cb4, c2a2e298 | yes | U-159's captures |
| B-182 | the G1 art audit (a report card, no export) | d6eb5fb4 (audit_g1.md; eight audit_g1_<planet>.png in blender/preview/) | the report | complete as a report; no open condition |
| B-190 | the per-ground dig puffs | d6eb5fb4 | **removed on purpose** (e50dc008, 11-09 18:00): D-190 replaced the eight variant puffs with one cream puff per planet tinted in the game | superseded by D-190; can close as such |
| B-193 | the v2 model census (a report card) | 7271c251 (v2_census.md); B-174's removal d0c32d8b followed | the report | complete; its follow-ups are B-174 / B-172 |
| B-197 | icons/wind_anchor/base | 47e9d29f | yes | UNITY dropping InventoryTests' exception |
| B-203 | the Surface Line + tier fills, four planets | e72a24ff Earth, f473f930 the other three | yes | U-174 / U-177's captures |
| B-198 | cliff lips for the variant grounds | bdcfa085, 654f2f7b | yes | no condition written after the exports; they draw with U-159 / U-177's grounds |
| B-184 | the face-safe dig_puff on Mars / Mercury / Venus | fe58e320 | yes (redrawn since by B-238, df2defa3) | U-159's captures; the art itself was replaced by B-238's dust, which is Done |
| B-186 | backgrounds/mars/{polar,tharsis} | 60132bdb (+ a4cf05b2) | yes | U-159's Mars captures |
| B-187 | backgrounds/mercury/coldtrap, backgrounds/venus/tessera | 3f486025 | yes | LEAD's look at the stamped dip reviews |

Notes
- "On disk" was checked by one or two representative files per card, not a full key list; d1_key_audit.md and
  audit_g1.md hold the full lists for the ground and D1 keys.
- B-190 and B-184 are the two whose exported art no longer exists in its original form (removed, redrawn); both
  changes were LEAD-ruled (D-190, B-238).
- B-172 is the only card here I still owe an export on. Its manifest rows and source are in; nothing to run until
  U-151 lands.
