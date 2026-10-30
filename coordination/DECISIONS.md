# MERIDIAN — Decisions Log

Owner: LEAD. A decision stays settled until the "Reopen if" evidence appears. Format:
`D-### · date · decision · reason · reopen if`.

- D-001 · 2026-10-30 · The Unity project lives at the repo root (`Assets/`, `Packages/`, `ProjectSettings/`); Blender sources in `blender/`. · Shortest paths, one `.gitignore`, Unity never imports `.blend` files. · Reopen if a second Unity project is ever needed.
- D-002 · 2026-10-30 · All creatures, characters, and FX use pre-rendered frame sheets from Blender; Unity 2D skeletal animation only by a logged exception. · One pipeline, predictable memory per asset, no manual rigging step for an autonomous team. · Reopen if a creature's frame budget exceeds 2048² at 256 px with the standard set.
- D-003 · 2026-10-30 · Scale: 1 unit = 1 m = 1 tile = 128 px source (PPU 128); default camera size 9. · Realistic texel density at 1080p with zoom headroom. · Reopen if the texture budget in Bible §11.1 is exceeded by terrain atlases.
- D-004 · 2026-10-30 · Gas and ice giants use the cloud-column world type (Bible §7.5): floes, Decks, Crush Line, Float cells, Aerostats. · Fun, grounded in real atmosphere layers, reuses the chunk system. · Reopen if M4 playtest finds vertical traversal unfun after two tuning passes.
- D-005 · 2026-10-30 · UNITY owns audio sourcing (CC0/royalty-free) and `docs/credits/unity.md`. · Neither worker specializes in audio; UNITY integrates it anyway. · Reopen never.
- D-006 · 2026-10-30 · HeavyJobLock (CLAUDE.md rule 6) serializes heavy jobs; LEAD is the scheduler and the only deleter of others' stale locks. · 8 GB can't hold the Editor and a Blender render. · Reopen if RAM is upgraded (raise Bible §11.2 only).
- D-007 · 2026-10-30 · Art reaches code only through Addressable addresses equal to asset keys; `ArtImporter` retires placeholders automatically. · No manual import steps, no waiting on art. · Reopen if Addressables load time breaks the 4 s planet-load budget.
- D-008 · 2026-10-30 · Top-down distances and radii are compressed with a 0.6 power law relative to Earth (Bible §3); positions static until M5. · Fits one map, keeps order and feel. · Reopen if a Gravity Well overlaps a neighbor's orbit after drift is added.
- D-009 · (LEAD fills in M0) · Old MERIDIAN build archived on `archive/meridian-v1` and tag `meridian-v1-final`; contents: ____. · The Unity version replaces it; history is never deleted. · Reopen never.
- D-010 · 2026-10-30 · Water is a terrain tile set in M1–M2; a fluid simulation is a candidate for M3 if the Earth ocean needs it. · Simplest thing that lets M1 ship. · Reopen at M3 planning.
- D-011 · (LEAD fills in M0) · Company name for the save path and build: "Zubers" unless the user states another. · Needed by U-013. · Reopen if the user asks.
