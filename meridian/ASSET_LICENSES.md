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
