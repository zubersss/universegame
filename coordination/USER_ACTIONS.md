# What I need from you

Owner: LEAD (only the Lead edits this). Do the open items below, then tell the Lead session
`done: USER-0X`. Each item has exact steps. Everything here fits in one sitting (about
90 minutes, mostly downloads).

## Open

### USER-09 — Playtest M1 (15–30 min)
1. Open File Explorer and go to `C:\dev\universegame\Build\MERIDIAN_0.1.1`.
2. Double-click `MERIDIAN.exe`. If Windows shows "Windows protected your PC", click
   "More info" → "Run anyway" (it's our own build, not signed).
3. Click NEW. Controls and what to try are in `coordination/reviews/M1_REPORT.md`.
   The short version: A/D walk, Space jump, left click dig, F boards the ship, W thrust.
   In space, turn with A/D toward Mars (straight to the right of Earth). On Mars, use W
   gently to land slowly.
4. Press Esc → Main Menu to quit. Then tell the Lead session in plain words what felt
   wrong, confusing, slow, or ugly, for example "done: USER-09, landing felt too floaty".
The team keeps working while you play, so the game may stutter now and then if a
heavy job is running at the same time. Mention it if it bothers you.

### USER-08 — Optional: let the team run PowerShell commands without prompts (2 min)
On Windows, Claude Code runs commands through PowerShell as well as Bash, and the
`Bash(...)` allow rules in `.claude/settings.json` don't cover PowerShell. The Lead added
matching PowerShell *deny* rules, but isn't allowed to grant itself new *allow* rules.
If you get too many "allow this command?" prompts, tell the Lead "approve PowerShell
allow rules" and accept the edit when Claude Code asks you. Otherwise skip this.

## Done
- 2026-10-30 · USER-01 (Git 2.56 and Git LFS 3.8 already installed; the Lead ran
  `git lfs install --local`), USER-02 (repo already at `C:\dev\universegame`),
  USER-05 (Claude Code 2.1.314 already running), USER-06 (89 GB free, 7.6 GB RAM) —
  verified by the Lead.
- 2026-10-30 · USER-03 (Unity 6000.6.5f1 + Hub 3.22.3) and USER-04 (Blender 5.2.2 LTS) —
  found on disk by the Lead. The IL2CPP module isn't needed (D-014).
- 2026-10-30 · USER-07 (UNITY and BLENDER sessions started; first commits 10:23).

## Status
READY FOR WORKERS · 2026-10-30 · Start the two worker sessions now (USER-07).
