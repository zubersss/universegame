# What I need from you

Owner: LEAD (only the Lead edits this). Do the open items below, then tell the Lead session
`done: USER-0X`. Each item has exact steps. Everything here fits in one sitting (about
90 minutes, mostly downloads).

## Open

### USER-22 — Close two apps so the team can render and compile (1 min)
At 11:4x on 2026-11-06 the laptop had only 0.13 GB free memory; the workers need 1.5 GB before any compile, test or render. ChatGPT (about 340 MB) and the Copilot app (about 220 MB) are open again.
1. Close ChatGPT and the Copilot app (taskbar ^ arrow → right-click each → Exit/Quit; or Task Manager → right-click → End task).
2. Keep Chrome, Edge and WSL closed while the team works.
3. Nothing to report. The workers start their heavy jobs on their own once memory is above the gate.

### USER-08 — Optional: let the team run PowerShell commands without prompts (2 min)
On Windows, Claude Code runs commands through PowerShell as well as Bash, and the
`Bash(...)` allow rules in `.claude/settings.json` don't cover PowerShell. The Lead added
matching PowerShell *deny* rules, but isn't allowed to grant itself new *allow* rules.
If you get too many "allow this command?" prompts, tell the Lead "approve PowerShell
allow rules" and accept the edit when Claude Code asks you. Otherwise skip this.

## Done
- 2026-11-06 11:4x · USER-18 and USER-19 retired by LEAD: the Windows Update worker is gone and the gate opened several times since; the current memory ask is USER-22.
- 2026-11-06 10:16 · USER-20 (the owner closed ChatGPT, Edge and WSL; free RAM reached the gate and BLENDER's export started at 10:16).
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
