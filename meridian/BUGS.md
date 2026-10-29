# MERIDIAN — bug list (studio round)

Maintained by GAUGE. Every bug is assigned to its owning role with an `ISSUE` message; the owner
fixes it, GAUGE verifies the fix and closes it. Nobody fixes another role's feature bug unless the
Director assigns it.

**Severity:** 1 = crash / data loss · 2 = broken feature · 3 = visible defect · 4 = polish.
**Status:** open → assigned → fixed (awaiting verification) → verified / won't fix (with reason).

| ID | Sev | Owner | Summary | Repro | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| B-001 | 4 | ATLAS | `isBodyId()` in `src/world/bodies.ts` lists the three body ids literally instead of checking `BODY_IDS`, so a body added to `BODY_IDS` would fail save/import validation until this is updated too. | Read `isBodyId` (bottom of `src/world/bodies.ts`); add a body to `BodyId`/`BODY_IDS` only → `isBodyId('<new id>')` is false. | Code reading 2026-10-29 at `26538d0`; not a bug in the current game (three bodies). | fixed on `studio/atlas` (per Director); verify after integration |
| B-002 | 3 | Director | Terrain splits by camera while the focus entity keeps near-ground detail, so a photo camera placed at high flight or orbit over a landed ship exceeds the A4 Low budget (259–351 draw calls, 545k–744k triangles against limits of 200 / 450k). Ground poses stay inside budget (104–180 calls, 211k–385k tris). | LUMEN baseline photo set, `evidence/studio/lumen/baseline/perf-*.json`, original build. | open — these poses are not the profile route, so real high flight may not reproduce it; confirm on the per-preset profile route before changing LOD (C1.8). |
| B-003 | 3 | LUMEN | Orrin's ground renders near-black at the landing site. The brighter palette (a632d61) fixed the distant hills, which now read violet, but not the ground near the camera; the ship is lit normally in the same frame, so this is the terrain material or its near-camera lighting, not the sun. | Land on Orrin at any preset and look at the ground around the ship. | `evidence/studio/atlas/m2-orrin-landed-1280.png` (on `studio/atlas`); Director confirmed it visually, 2026-10-29. | open — confirmed still broken; inherited by LUMEN with the worlds role |
| B-004 | 4 | Director | `index.html` title text still reads "A survey of Ilex, Vesper and Cairn", which now omits Orrin and Saro. | Title screen. | ATLAS DONE note. | open |
| B-005 | 2 | LUMEN | On ATLAS's unmerged M2 terrain build, the on-foot walk from the Orrin landing site to its relay never arrived within 30 minutes, so that browser run failed and Saro was never reached. The path is flat (190 m, 0.4 m relief), so the cause is unknown: an obstacle from the new flora or fauna, or the walk autopilot itself. | Build `studio/atlas` @ 41efe23, land on Orrin, autopilot-walk to the relay. | ATLAS DONE note, 2026-10-29. Not reproduced by the Director. | open — **blocks merging `studio/atlas` 41efe23**; diagnose before that terrain reaches integration |
| B-006 | 4 | LUMEN | Orrin's biome edges look stair-stepped from orbit. | View Orrin from orbit. | ATLAS DONE note, 2026-10-29. | open |

