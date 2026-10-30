# MERIDIAN — Review Log

Owner: LEAD. One entry per review cycle. Format:

```
## Cycle <n> · <date time>
Checked: <files/logs/previews opened>
Moved: <task → status (commit)>
Decided: <D-### or none>
Signals: <loop/stall signals and responses, or none>
User: <USER_ACTIONS changes, or none>
```

## Cycle 0 · (M0 start)
Checked: —
Moved: —
Decided: D-001…D-008, D-010 adopted from the architect draft.
Signals: none
User: USER-01…06 posted.

## Cycle 1 · 2026-10-30
Checked: MERIDIAN_SETUP.md (all 18 files extracted, line counts match); `git lfs track`; `git check-ignore` on logs/, Build/, blender/preview/, coordination/locks/*.lock, Library/; `.claude/settings.json` vs code.claude.com/docs/en/permissions; installed tools on the laptop.
Moved: L-001 → Done (4c10618); L-002 → Done (21d0584); L-003 → Done (4396dfa); L-004 → Done.
Decided: D-009 filled; D-012 (play/meridian/ and the old GPT automation stay on main, user choice).
Signals: none (workers not started).
User: USER-01, 02, 05, 06 verified done; USER-03 (Unity), USER-04 (Blender) open; USER-08 (optional PowerShell allow rules) posted.
L-004 note: settings.json parses; `Bash(x:*)` and `acceptEdits` valid per current docs; all 40 deny rules kept; 42 `PowerShell(...)` deny equivalents added because Bash rules don't cover the PowerShell tool on Windows.
