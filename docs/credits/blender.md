# Art credits (BLENDER)

Every external input used in MERIDIAN art: asset key(s), source, URL, license.
Assets not listed here are original work made in Blender from scripts in `blender/scripts/`.

| Asset key(s) | Input | Source / URL | License |
|--------------|-------|--------------|---------|
| planets/earth/surface | Blue Marble Next Generation, December 2004, topography + bathymetry, 5400×2700 (Reto Stöckli, NASA Earth Observatory / GSFC) | https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73909/world.topo.bathy.200412.3x5400x2700.jpg | Public domain (NASA imagery, credit "NASA Earth Observatory") |
| planets/mars/surface | Mars Viking MDIM 2.1 colorized global mosaic, 1 km (USGS Astrogeology / NASA); Wikimedia Commons 3840 px rendition of the original 21339×10670 file | https://commons.wikimedia.org/wiki/File:Mars_Viking_MDIM21_ClrMosaic_1km.jpg (downloaded from https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Mars_Viking_MDIM21_ClrMosaic_1km.jpg/3840px-Mars_Viking_MDIM21_ClrMosaic_1km.jpg) | Public domain (US federal government work; USGS lists "Public domain", no use constraints) |
| planets/mercury/surface | Mercury complete mono basemap, 2500 m/px, equirectangular (NASA / JHU-APL / Carnegie, MESSENGER MDIS); Wikimedia Commons 3840 px rendition | https://commons.wikimedia.org/wiki/File:Mercury_-_complete_mono_basemap_2500mpp_equirectangular.png | Public domain (NASA work; Commons lists PD-USGov-NASA) |
| planets/jupiter/surface | PIA07782 "Cassini's Best Maps of Jupiter: Cylindrical Map", Dec 2000 (NASA/JPL/Space Science Institute) | https://photojournal.jpl.nasa.gov/catalog/PIA07782 (file via https://commons.wikimedia.org/wiki/File:Jupiter_Cylindrical_Map_-_Dec_2000_PIA07782.jpg) | Public domain (NASA/JPL imagery; Commons lists PD-USGov-NASA) |
| planets/earth/clouds | Cloud combined 2048 (NASA Visible Earth, Blue Marble clouds) | https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57747/cloud_combined_2048.jpg | Public domain (NASA imagery, credit "NASA Goddard Space Flight Center") |

## UI (B-046)

- ui/title/logo: MERIDIAN wordmark built from hand-drawn geometric letterforms (signed-distance strokes in blender/scripts/build_title.py). No font file or third-party typeface is used.
- ui/title/background: composed only from the project's own exported art (Earth parallax layers, Pilgrim, landing pad, thruster and dust FX); no external images.


## Lettering in exported art (B-151, B-170; D-090)

| Asset key(s) | Input | Source / URL | License |
|--------------|-------|--------------|---------|
| ui/titlecards/{earth,mars,mercury,venus,jupiter,saturn,uranus,neptune} | the planet name drawn from Limelight Regular's glyph outlines (Eben Sorkin, Sorkin Type) and the subtitle from Patrick Hand Regular's (Patrick Wagesreiter), read from UNITY's committed TTFs `Assets/_Game/Fonts/Limelight/Limelight-Regular.ttf` and `Assets/_Game/Fonts/PatrickHand/PatrickHand-Regular.ttf` by blender/scripts/build_ui_v3.py and baked as ink into each card's color PNG (no font file under Art/) | https://github.com/google/fonts/tree/main/ofl/limelight, https://github.com/google/fonts/tree/main/ofl/patrickhand (logged as files in docs/credits/unity.md) | SIL Open Font License 1.1; images rendered from an OFL font are not Font Software, so the cards carry no OFL condition |
| backgrounds/jupiter/deep (layer2: the CRUSH band) | the word CRUSH from Limelight Regular's outlines, cream with a drawn ink edge, baked by blender/scripts/build_backdrop_v3.py (crush_band; B-155) | as above | SIL OFL 1.1 (rendered image; no OFL condition) |
| ui/map/minimap_frame (the N), ui/map/title_cartouche (THE SOLAR SYSTEM) | letters from Limelight Regular's outlines, baked as ink by blender/scripts/build_map_v3.py (B-209) | as above | SIL OFL 1.1 (rendered image; no OFL condition) |
| ui/hud/pack_full, ui/hints/pack_full (PACK FULL) | the stamp's lettering from Limelight Regular's outlines, baked in red ink by blender/scripts/build_hud_d1_v3.py (B-211); ui/hints/pack_full carries the same stamp at half size (build_hints_v3.py, B-213) | as above | SIL OFL 1.1 (rendered image; no OFL condition) |

All other UI exported to date leaves its words to UNITY at runtime (json `"lettering": "runtime"`); review sheets letter samples in the same fonts but are not shipped.

## Upkeep checks

- 2026-11-08 (session 10, B-178 to B-192): every asset exported this session is original, drawn from scripts with no external input (no images, fonts, scans or downloads). Covered: the ground band variants, lips, biome bands and fills (B-178 / B-180 / B-181); the painted backdrops (B-179 / B-183 / B-185 / B-186 / B-187 / B-188 / B-189: blender/scripts/build_backdrop_v3.py, gen_painted_bg.py); the dig puffs (B-184 / B-190 / B-191); the fills' buried details (B-192: build_ground_variants_v3.py). Nothing to add to the tables above.
- 2026-11-08 (session 10, B-193 to B-214): every asset exported is original, drawn from scripts with no external images, scans or downloads: the item and Skill Tree node icons (B-199 / B-204: build_icons_items_v3.py, build_icons_nodes_v3.py), the depth tiers (B-203), the Skill Tree kit (B-204), the Rig's tools and beam rays (B-205), the Rank set (B-206), the flat panels and grain (B-208), the space maps (B-209), the underwater backdrop (B-202), the surveyor's climb clips and the dig props (B-210), the D1 HUD (B-211), the rare-find and reward FX (B-212 / B-214), the hint cards (B-213). The only third-party input is the Limelight lettering baked into the four keys added to the lettering table above (the map's N and cartouche, the PACK FULL stamp twice) plus B-155's CRUSH band, found missing in this check.
