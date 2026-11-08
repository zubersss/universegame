# What I need from you

Owner: LEAD (only the Lead edits this). Do the open items below, then tell the Lead session
`done: USER-0X`. Each item has exact steps. Everything here fits in one sitting (about
90 minutes, mostly downloads).

## Open

### USER-33 — The 0.5.0 look and feel check: Earth on smooth ground (15 min)
Open https://claude.ai/artifact/CHnmoFrDg2jzUuM42BVi83 (the stills, the numbers, what changed), then double-click
`C:\dev\universegame\Build\MERIDIAN_0.5.0\MERIDIAN.exe`.
1. Walk the camp and the hills: A / D to walk, Space to jump, Shift to run.
2. Press 1 (the Beam), aim at the ground with the mouse and left-click to dig a round scoop; keep clicking for a tunnel.
3. Press 4 (the Builder) and hold the left button while you sweep the mouse to pile a mound from the dirt you dug.
4. With the Beam, left-click an ore rock three times to mine it.
5. Press 3 (the Survey scanner) and left-click to scan; dig down to a red X.
6. Walk far left or right to the desert, the taiga, the tundra and the coast.
Tell the Lead "0.5.0 looks right" or what still feels off: the ground, the digging, the mounds, the backgrounds, or the
mining speed (too fast, too slow, right). If you skipped the 0.4.8 flight check (USER-32), add how the rocket climb feels
(F to board, W to climb). Only Earth has the new ground so far.

### USER-08 — Optional: let the team run PowerShell commands without prompts (2 min)
On Windows, Claude Code runs commands through PowerShell as well as Bash, and the
`Bash(...)` allow rules in `.claude/settings.json` don't cover PowerShell. The Lead added
matching PowerShell *deny* rules, but isn't allowed to grant itself new *allow* rules.
If you get too many "allow this command?" prompts, tell the Lead "approve PowerShell
allow rules" and accept the edit when Claude Code asks you. Otherwise skip this.

## Done
- 2026-11-08 12:3x · USER-32 (the 0.4.8 feel check, unanswered since 04:3x) folded into USER-33: the 0.5.0 check asks for the rocket climb too.
- 2026-11-08 01:3x · USER-30 done: the owner played 0.4.7 and likes it so far; leaving the atmosphere felt laggy and stuttery, the view too zoomed in, and the ship should fly smoother, with weight, a felt difference between accelerating and top speed, and a sound barrier break → D-158, U-148 / U-149 / U-150, B-171; the fix ships in 0.4.8 (the next playtest item comes with it).
- 2026-11-08 01:0x · USER-31 done: Chrome and Edge are closed, free RAM 2.0 GB; the team resumed on the owner’s "continue work".
- 2026-11-07 17:5x · USER-27 folded into USER-30 (Build 0.4.7 has Earth, Mars, Mercury, Venus and the paper menus).
- 2026-11-07 16:0x · USER-29 retired by LEAD: the build finished at 15:56 without a memory stop and free RAM is back at 2.2 GB with Edge and Chrome still open; nothing to do.
- 2026-11-07 15:0x · USER-28 retired by LEAD: free memory cleared the gate on its own at 14:46 (1.76 GB) and held through UNITY's probe and BLENDER's Uranus slot with ChatGPT and Edge still open; nothing to do.
- 2026-11-07 12:0x · USER-26 folded into USER-27 (Build 0.4.3 has both planets; the C2 page replaces the C1 ask).
- 2026-11-07 05:4x · USER-24 folded into USER-26 (the round 2 art is in the C1 build and on its page).
- 2026-11-07 01:04 · USER-25 done: free RAM reached 1.98 GB (ChatGPT, Copilot and Chrome gone); UNITY's U-103 + U-109 check started at 01:06.
- 2026-11-06 19:3x · USER-23 done: the owner kept the look and asked for four changes (thinner detailed ink, faces only on people and animals, an upright Pilgrim, fully manual fuel-free flight) → D-100..D-104, Bible 4.1, contract v3.1, cards U-107, B-123..B-127. A second look-over follows when the re-inked set lands (C1).
- 2026-11-06 19:0x · USER-22 retired by LEAD: free memory has stayed above the gate since 15:00 (2.6 GB at 19:00) without the owner's action.
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
