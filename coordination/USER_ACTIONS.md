# What I need from you

Owner: LEAD (only the Lead edits this). Do the open items below, then tell the Lead session
`done: USER-0X`. Each item has exact steps. Everything here fits in one sitting (about
90 minutes, mostly downloads).

## Open

### USER-28 — Close ChatGPT and Edge so the team can run again (1 min)
At 14:3x free memory is 0.65 GB; the team's gate is 1.5 GB. ChatGPT (three processes, about 400 MB) and Edge
opened at 14:19–14:20 while the three Claude windows restarted. Until memory is back nothing heavy can start:
UNITY's check of Build 0.4.4 (Mercury) and BLENDER's Uranus renders both wait. Close ChatGPT and Edge
(right-click their taskbar icons → Close window), then tell the Lead "done: USER-28". Both workers resume on
their own once memory clears; nothing else to do.

### USER-27 — Play the Earth and Mars build 0.4.3 and look at its page (15 min)
Open https://claude.ai/artifact/3FkYSjxX9bwjf34tapwDZU (the C2 Earth and Mars page: the stills, the numbers,
what changed since the flight, what comes next). Build 0.4.3 has both planets drawn (12:00; D-144).
Then play: double-click `C:devNiversegameBuildMERIDIAN_0.4.3MERIDIAN.exe`. The first launch now takes
about a second before you stand on the ground. On Earth walk left from the camp into the forest and right to
the coast; the Hadal Maw waits in the deep water past the beach. Board with F, fly to Mars as before (W or
Space to thrust, A / D to tilt; come down under 6 m/s), land, and walk until the canyon walls rise; stay a
while and a dust storm will find you. Fifteen minutes is enough. Tell the Lead "C2 reads" or what bothered
you, planet by planet. This replaces USER-26 (the C1 playtest): 0.4.3 contains everything 0.4.1 had.



### USER-08 — Optional: let the team run PowerShell commands without prompts (2 min)
On Windows, Claude Code runs commands through PowerShell as well as Bash, and the
`Bash(...)` allow rules in `.claude/settings.json` don't cover PowerShell. The Lead added
matching PowerShell *deny* rules, but isn't allowed to grant itself new *allow* rules.
If you get too many "allow this command?" prompts, tell the Lead "approve PowerShell
allow rules" and accept the edit when Claude Code asks you. Otherwise skip this.

## Done
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
