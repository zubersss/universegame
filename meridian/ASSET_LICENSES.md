# Asset licenses

MERIDIAN ships **no third-party art, audio, font or texture files**. Every
visual and audio asset is generated at runtime by this project's own code:

| Asset | Source | Creator | License | Notes |
| --- | --- | --- | --- | --- |
| Spacecraft model, materials, livery and ORM textures | `src/ship/ShipModel.ts` (procedural geometry; canvas-drawn textures) | MERIDIAN project | Project license (see note) | Original design; no reference model used |
| Terrain (all three bodies), detail textures | `src/world/surface.ts`, `src/terrain/*`, `src/render/terrainTextures.ts` | MERIDIAN project | Project license (see note) | Seeded noise; periodic value/Worley detail texture generated in code |
| Vegetation and rocks (9 species) | `src/props/propMeshes.ts`, `src/props/species.ts` | MERIDIAN project | Project license (see note) | Procedural meshes with vertex colors |
| Relay masts and sample deposits | `src/world/MissionObjects.ts` | MERIDIAN project | Project license (see note) | Procedural meshes |
| Sky, atmosphere, clouds, stars, sun | `src/render/Atmosphere.ts`, `Clouds.ts`, `Space.ts` | MERIDIAN project | Project license (see note) | Shaders; seeded starfield |
| Sound (engine, wind, footsteps, scan, landing, relay, completion, ambient tones) | `src/audio/GameAudio.ts` | MERIDIAN project | Project license (see note) | Synthesized with the Web Audio API at runtime |
| UI typography | System font stacks (CSS) | — | — | No web fonts are downloaded |

Note: the repository does not yet contain a `LICENSE` file for its own code
and assets; choosing one is left to the owner. Until then, these original
assets carry the same (unspecified) terms as the code.

No asset is loaded from a CDN or any external host at runtime (no hotlinks, no
API keys). The asset tools available in the build environment were checked;
procedural construction was used because it met the art direction without
importing licensed files.

## Third-party code (npm packages bundled into `dist/`)

| Package | Version | License |
| --- | --- | --- |
| three | 0.186.1 | MIT |
| @dimforge/rapier3d-compat | 0.21.0 | Apache-2.0 |
| simplex-noise | 4.0.3 | MIT |

Their full license texts ship with the game as `THIRD_PARTY_LICENSES.txt`
(copied from each package's `LICENSE` into `public/`, so it is served from the
root of `dist/`). Development-only tools (TypeScript, Vite, Vitest, Playwright)
are not shipped.

## Scientific data (Lightspeed overhaul)

Real-world data ships as files under `src/data/`, built by the scripts in
`scripts/data/` (inputs are downloaded by the person running them; nothing is
fetched from a third-party host at runtime). Values are tagged `measured`,
`estimated` or `fictional` per field; gameplay values derive from them through
`src/world/scale.ts`.

| Data | Shipped as | Source | Terms | Attribution / notes |
| --- | --- | --- | --- | --- |
| Earth elevation (interim) | `src/data/earth/earth-elevation.bin` (int16 m, 10′ nodes) | ETOPO1 Ice Surface (NOAA NGDC; Amante & Eakins 2009, doi:10.7289/V5C8276M) as the 10 arc-minute grid by Fatiando a Terra, [earth-topography-10arcmin v1](https://github.com/fatiando-data/earth-topography-10arcmin) (doi:10.5281/zenodo.5882203), downloaded 2026-10-30, SHA-256 `e45628a3…af4cf6` (matches the published value) | ETOPO1: public domain (US Government work). The 10′ grid: CC BY 4.0 | “Topography: ETOPO1 (NOAA NGDC), 10′ grid by Fatiando a Terra, CC BY 4.0.” Evaluated from a degree-720 spherical-harmonic model, so relief is smoothed (Everest region about 5.9 km). To be replaced by NOAA ETOPO 2022 60″ (public domain) with `build_earth.py --elevation-etopo2022` once www.ncei.noaa.gov is reachable from the build environment. |
| Earth coastline distance, land and lakes | `earth-coast.bin` (int8, 0.5 km steps, 5′ nodes) | Natural Earth 1:10m physical vectors: land, minor islands, lakes, Antarctic ice shelves ([nvkelso/natural-earth-vector](https://github.com/nvkelso/natural-earth-vector), raw GeoJSON, 2026-10-30) | Public domain (Natural Earth terms of use) | Rasterized at 1.25′ and converted to a signed distance field by `scripts/data/coast_sdf.py`; east–west distances are approximate at high latitudes. |
| Earth water levels | `earth-water.bin` (int16 m, 10′ nodes) | Derived from the two layers above | As above | Ocean 0 m; each lake's level is estimated (5th percentile of the elevation on land within 5–30 km of its shore, at least +1 m), tagged `estimated`; checked against commonly cited levels of 18 large lakes (median error 7 m). |
| Earth land cover (biome fractions) | `earth-biome.bin` (uint8 × 5, 0.25° nodes) | ESA WorldCover 10 m 2021 v200 (Zanaga et al. 2022, doi:10.5281/zenodo.7254221), public AWS bucket `esa-worldcover`, coarsest COG overviews, 2026-10-30 | CC BY 4.0 | “© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium.” Aggregated by `scripts/data/worldcover_fractions.py` into tree / low vegetation / bare / snow-ice / moss-lichen shares. |
| Sol positions at EPOCH (2026-01-01 00:00 TDB, interim) | `src/data/sol.json` | JPL DE421 (Folkner, Williams & Boggs 2009) read with `jplephem` from the PyPI `de421` package (2008.1), cross-checked against IAU SOFA plan94/moon98 via `pyerfa` | Ephemeris: US Government work (JPL); `de421` packaging MIT; SOFA/ERFA BSD-3-Clause (algorithms only, nothing bundled) | To be replaced by JPL Horizons vectors (`scripts/data/horizons.mjs`) once ssd.jpl.nasa.gov is reachable. Europa and Titan directions are fictional until then. |
| Earth orientation at EPOCH | `src/data/sol.json` (`orientation`) | IAU 2006/2000A precession–nutation and Earth rotation angle (SOFA/ERFA `c2t06a`) | BSD-3-Clause algorithms; values are facts | Polar motion neglected; UT1 = TT − 69.2 s. |
| Physical constants (radii, masses, gravity, rotation, solar luminosity and temperature) | `src/data/sol.json` | Reference values of the IAU 2015 nominal solar values and the NASA/NSSDCA fact sheets | Facts; NASA material is public domain in the US | Entered without a live fetch (nasa.gov unreachable from the build environment): tagged `estimated`, `verified: false`, source `pending` until checked against a fetched source. |

The CC BY 4.0 attributions above must appear in the game's credits or data
sources view (the strings are also in `src/data/earth/earth.json`).
