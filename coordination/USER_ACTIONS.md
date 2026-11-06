# What I need from you

Owner: LEAD (only the Lead edits this). Do the open items below, then tell the Lead session
`done: USER-0X`. Each item has exact steps. Everything here fits in one sitting (about
90 minutes, mostly downloads).

## Open

### USER-18 — Free memory before the workers' first heavy job (3 min)
At 23:3x on 2026-11-05 the laptop had 0.37 GB free; the gate is 1.5 GB, so neither worker can compile, test or export yet. The four Claude sessions use about 1.2 GB (normal). The rest is apps we don't need:
1. Close Chrome.
2. Close the Xbox app and Phone Link (taskbar ^ arrow → right-click each → Exit; or Task Manager → right-click → End task).
3. If "Antimalware Service Executable" is still above 300 MB in Task Manager, wait for the Defender scan to finish (a few minutes) rather than killing it.
4. Tell the Lead "done: USER-18". Nothing else is needed; the workers resume on their own once memory is above the gate.

### USER-19 - Windows Update is holding the memory the workers need (check in 30 min)
At 00:2x on 2026-11-06 "Windows Modules Installer Worker" (TiWorker) was using 1.36 GB while installing an update, which keeps free RAM below the 1.5 GB gate. It ends on its own, usually within half an hour; the workers poll and start as soon as it does.
1. If it is still above 1 GB in Task Manager after 30 minutes, open Settings > Windows Update and let the install finish there (do not pause it mid-install).
2. If Windows asks to restart, tell the Lead first ("restart pending"); I will have the workers finish their current jobs and then you restart and paste the three resume messages (as in USER-17).
3. Nothing else: no need to report "done" unless step 2 happens.

### USER-08 — Optional: let the team run PowerShell commands without prompts (2 min)
On Windows, Claude Code runs commands through PowerShell as well as Bash, and the
`Bash(...)` allow rules in `.claude/settings.json` don't cover PowerShell. The Lead added
matching PowerShell *deny* rules, but isn't allowed to grant itself new *allow* rules.
If you get too many "allow this command?" prompts, tell the Lead "approve PowerShell
allow rules" and accept the edit when Claude Code asks you. Otherwise skip this.

## Done
- 2026-11-05 23:3x · USER-17 (the three windows were restarted; LEAD found two peer sessions at resume). USER-14 and USER-15 were folded into it. Memory is still short → USER-18.
- 2026-11-02 00:5x · USER-16 and USER-12 (M3/M2 playtests) withdrawn: the owner chose the 3D rehaul (D-062) and "switch now". The next playtest is R1 (Earth in 3D).
- 2026-11-01 20:0x · USER-13 (the owner restarted all three windows; the LEAD loop is running again).
- 2026-10-30 · USER-01 (Git 2.56 and Git LFS 3.8 already installed; the Lead ran
  `git lfs install --local`), USER-02 (repo already at `C:\dev\universegame`),
  USER-05 (Claude Code 2.1.314 already running), USER-06 (89 GB free, 7.6 GB RAM) —
  verified by the Lead.
- 2026-10-30 · USER-03 (Unity 6000.6.5f1 + Hub 3.22.3) and USER-04 (Blender 5.2.2 LTS) —
  found on disk by the Lead. The IL2CPP module isn't needed (D-014).
- 2026-10-30 · USER-07 (UNITY and BLENDER sessions started; first commits 10:23).
- 2026-10-31 · USER-09 (M1 playtest of Build/MERIDIAN_0.1.1): done; the owner reported no problems and asked to close M1.
- 2026-10-31 13:0x · USER-10 (the owner typed "rerun the check" in the UNITY window; the standing-approval sentence was not included, so it became USER-11).
- 2026-10-31 14:0x · USER-11 (the owner gave UNITY the standing low-memory restart approval in its window).

## Status
READY FOR WORKERS · 2026-10-30 · Start the two worker sessions now (USER-07).
