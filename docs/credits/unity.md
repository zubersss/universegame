# Credits — UNITY (code, audio, UI)

Owner: UNITY. Every license-bearing file the UNITY role adds to the game is listed here with its
source and license (Bible §12 M6 builds the in-game credits from `docs/credits/`).

## Audio

All M1 placeholder sounds are original, generated procedurally by
`Assets/_Game/Code/Editor/AudioSynth.cs` (menu MERIDIAN → Synthesize Placeholder Audio) from
fixed seeds. No third-party recordings or samples are used. They are dedicated to the public
domain under **CC0 1.0** (https://creativecommons.org/publicdomain/zero/1.0/).

| File | Use | Source | License |
|------|-----|--------|---------|
| `Assets/_Game/Audio/sfx/jump.wav` | player jump | AudioSynth.cs, seed 1 (rising chirp + air) | CC0 1.0 (original) |
| `Assets/_Game/Audio/sfx/land.wav` | player landing | AudioSynth.cs, seed 2 (low thump) | CC0 1.0 (original) |
| `Assets/_Game/Audio/sfx/dig.wav` | Beam removes a tile | AudioSynth.cs, seed 3 (gritty noise) | CC0 1.0 (original) |
| `Assets/_Game/Audio/sfx/place.wav` | Builder places a tile | AudioSynth.cs, seed 4 (click + thunk) | CC0 1.0 (original) |
| `Assets/_Game/Audio/sfx/thrust.wav` | ship thrust loop | AudioSynth.cs, seed 5 (filtered rumble, 2 s loop) | CC0 1.0 (original) |
| `Assets/_Game/Audio/sfx/ui_click.wav` | UI click | AudioSynth.cs (2.2 kHz tick) | CC0 1.0 (original) |
| `Assets/_Game/Audio/ambient/ambient_wind.wav` | ambient loop | AudioSynth.cs, seed 6 (gusting wind, 20 s loop) | CC0 1.0 (original) |
| (no file: built at run time) | sonic boom placeholder (U-150, D-158) | `Code/Runtime/Audio/SfxSynth.cs` Boom(), seed 158 (two N-wave cracks 0.11 s apart, a 45 Hz thump, a low rumble; 1.4 s) | CC0 1.0 (original) |
| (no file: built at run time) | shovel scoop placeholder (U-193, D-182) | `Code/Runtime/Audio/SfxSynth.cs` Shovel(), seed 193 (a low-passed soil scrape, a 90 Hz thud as the clod comes loose, a crumble of grit; 0.28 s) | CC0 1.0 (original) |
| (no file: built at run time) | clod-fall placeholder (U-195, D-183; until D-186's sample) | `Code/Runtime/Audio/SfxSynth.cs` ClodFall(), seed 195 (silent 0.16 s for the clods' flight, then five soft low-passed thuds over 70-106 Hz bodies; 0.5 s) | CC0 1.0 (original) |
| (no file: built at run time) | pack tick placeholder (U-195, D-183; until D-186's sample) | `Code/Runtime/Audio/SfxSynth.cs` PackTick() (a 1.9 kHz tone with its octave, 70 ms, no noise source) | CC0 1.0 (original) |

## Fonts

| File | Use | Source | License |
|------|-----|--------|---------|
| `Assets/_Game/UI/Fonts/JetBrainsMono-Regular.ttf` | all HUD and menu text, monospace numerals (Bible §9) | JetBrains Mono, https://github.com/JetBrains/JetBrainsMono (master, fonts/ttf, fetched 2026-10-30), © 2020 The JetBrains Mono Project Authors | SIL Open Font License 1.1 (OFL); license text shipped beside it as `JetBrainsMono-OFL.txt` |
| `Assets/_Game/UI/Fonts/JetBrainsMono-Bold.ttf` | titles, buttons, warnings | same source | SIL Open Font License 1.1 (OFL) |
| `Assets/_Game/Fonts/Limelight/Limelight-Regular.ttf` | titles and intertitles (Bible §9 v4, D-090; U-104) | Limelight by Eben Sorkin (Sorkin Type), Google Fonts, https://github.com/google/fonts/tree/main/ofl/limelight | SIL Open Font License 1.1 (OFL.txt beside the file) |
| `Assets/_Game/Fonts/PatrickHand/PatrickHand-Regular.ttf` | HUD and body text, the Escape Line sign lettering (D-090; U-104) | Patrick Hand by Patrick Wagesreiter, Google Fonts, https://github.com/google/fonts/tree/main/ofl/patrickhand | SIL Open Font License 1.1 (OFL.txt beside the file) |
| `Assets/TextMesh Pro/Fonts/LiberationSans.ttf` (+ `LiberationSans SDF`) | TextMeshPro's default face, imported with the TMP essential resources so the Limelight / Patrick Hand SDF assets can be built; not used for game text | Liberation Fonts, Red Hat / Ascender, via Unity's TextMeshPro package (TMP essential resources) | SIL Open Font License 1.1 (`Assets/TextMesh Pro/Fonts/LiberationSans - OFL.txt`) |
| `Assets/TextMesh Pro/` (settings, shaders, sprite assets, style sheet) | TextMeshPro essential resources (TMP Settings, Distance Field shaders, default sprite asset) | Unity Technologies, com.unity.ugui 2.6.0 "Import TMP Essential Resources" | Unity Companion License (package content) |
| Unity built-in `LegacyRuntime.ttf` | fallback only, if the UI theme asset is missing | ships with the Unity Editor | Unity Editor license |

## Code and packages

Unity packages (URP, Input System, Addressables, Test Framework, Cinemachine, uGUI/TextMeshPro,
2D Tilemap Extras) are used under the Unity Companion License via `Packages/manifest.json`; no
third-party code is vendored into `Assets/`.

U-097 (2026-11-06): `com.unity.2d.animation` pinned to 16.0.1, the version bundled with Unity 6000.6.5f1
(no registry fetch), Unity Companion License; it carries the sprite-bone tooling for the contract §11.3 rig
sets. The runtime rigs (Code/Runtime/Flora) drive bone Transforms + part sprites and need no package API.
