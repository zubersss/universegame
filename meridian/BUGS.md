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
| B-003 | 3 | ATLAS | Orrin's ground renders near-black until its palette is tuned with LUMEN. | Land on Orrin at any preset. | ATLAS DONE note, 2026-10-29; partly addressed by a632d61 (brighter palette/sediment), not yet re-photographed. | assigned |
| B-004 | 4 | Director | `index.html` title text still reads "A survey of Ilex, Vesper and Cairn", which now omits Orrin and Saro. | Title screen. | ATLAS DONE note. | open |

