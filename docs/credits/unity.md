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

## Fonts

| File | Use | Source | License |
|------|-----|--------|---------|
| `Assets/_Game/UI/Fonts/JetBrainsMono-Regular.ttf` | all HUD and menu text, monospace numerals (Bible §9) | JetBrains Mono, https://github.com/JetBrains/JetBrainsMono (master, fonts/ttf, fetched 2026-10-30), © 2020 The JetBrains Mono Project Authors | SIL Open Font License 1.1 (OFL); license text shipped beside it as `JetBrainsMono-OFL.txt` |
| `Assets/_Game/UI/Fonts/JetBrainsMono-Bold.ttf` | titles, buttons, warnings | same source | SIL Open Font License 1.1 (OFL) |
| Unity built-in `LegacyRuntime.ttf` | fallback only, if the UI theme asset is missing | ships with the Unity Editor | Unity Editor license |

## Code and packages

Unity packages (URP, Input System, Addressables, Test Framework, Cinemachine, uGUI/TextMeshPro,
2D Tilemap Extras) are used under the Unity Companion License via `Packages/manifest.json`; no
third-party code is vendored into `Assets/`.
