# MERIDIAN — bug list (studio round)

Maintained by GAUGE. Every bug is assigned to its owning role with an `ISSUE` message; the owner
fixes it, GAUGE verifies the fix and closes it. Nobody fixes another role's feature bug unless the
Director assigns it.

**Severity:** 1 = crash / data loss · 2 = broken feature · 3 = visible defect · 4 = polish.
**Status:** open → assigned → fixed (awaiting verification) → verified / won't fix (with reason).

| ID | Sev | Owner | Summary | Repro | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| B-001 | 4 | ATLAS | `isBodyId()` in `src/world/bodies.ts` lists the three body ids literally instead of checking `BODY_IDS`, so a body added to `BODY_IDS` would fail save/import validation until this is updated too. | Read `isBodyId` (bottom of `src/world/bodies.ts`); add a body to `BodyId`/`BODY_IDS` only → `isBodyId('<new id>')` is false. | Code reading 2026-10-29 at `26538d0`; not a bug in the current game (three bodies). | assigned |
