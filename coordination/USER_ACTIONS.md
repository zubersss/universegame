# What I need from you

Owner: LEAD (only the Lead edits this). Do the open items below, then tell the Lead session
`done: USER-0X`. Each item has exact steps. Everything here fits in one sitting (about
90 minutes, mostly downloads).

## Open

### USER-42 — Free about half a gigabyte of memory (2 min) — not blocking right now, but the margin is thin
Thank you for restarting the three windows (00:50). Update 01:01: once the new windows settled, free memory rose to 1.9 GB and the team's builds and tests can start again. The laptop itself was not restarted (it has been on since yesterday 11:44) and builds need 1.5 GB free, so one busy app can stop them again. Either of these gives a safe margin:
- **Quick:** close the **Copilot** app (it holds 0.4 GB), the **Xbox** app (0.3 GB) and the **Settings** window (0.2 GB). For Copilot and Xbox, look in the system tray by the clock (click the ^ arrow), right-click the icon and choose Quit or Close.
- **Thorough:** close the three Claude windows (the Lead's last), restart the laptop, open the three windows again and paste the usual resume message into each.
Then tell the Lead session "done: USER-42". Nothing is lost either way: everything is in the project files.

### USER-41 — Play Build 0.6.2: ten minutes of digging (10 min)
Two of your 0.6.0 asks are in: digging that throws clods and dust, and holes that look like holes. The page with pictures: https://claude.ai/artifact/Xfb4R17qVr5K8DkFp4aLpT
1. Double-click `C:\dev\universegame\Build\MERIDIAN_0.6.2\MERIDIAN.exe` and choose **NEW**.
2. Dig at the camp with the left mouse button held: watch the clods and the find flying to the PACK gauge.
3. Dig a shaft straight down about ten metres and look at it: does it read as a hole?
4. Keep going past 10 m into Subsoil: the clods, dust and back wall change with the layer.
5. Fly out (Space), sell (G), buy The Beam (K, 250 Scrip) and dig again.
Then tell the Lead session: does digging feel better, is it enough or do you want more (bigger clods, more shake, more sound), and do the holes look right? This build includes everything in 0.6.1b, so USER-38's shovel questions can be answered here too (is the shovel a good start, does the Beam feel like a reward, is 250 Scrip right).
Known already: ground does not collapse yet and the sounds are still synthesized (both next); the docking bay's cradle is empty; a small pale box hangs near you on arrival at any planet but Earth (fixed for the next build).

### USER-40 — Free the laptop's memory: quit Ollama (1 min) — the team is blocked on this
At 18:52 the laptop has 0.12 GB of memory free and no build or render can start (they need 1.5 GB). The biggest holder is the **Ollama** app: 4.2 GB, running since 11:47 this morning. It is not part of the game team.
1. Look in the system tray (the small icons by the clock, bottom right; click the ^ arrow if it is hidden) for the Ollama llama icon.
2. Right-click it and choose **Quit Ollama**.
3. If you are not using them, also close the **Xbox** app and any Chrome windows you don't need.
4. Tell the Lead session "done: USER-40".
If you are using Ollama for something of your own, say so instead and the team will wait or work around it. You can start it again whenever the team is idle.
Update 18:59: the memory came back on its own at about 18:57 (Ollama let go of its 4.2 GB; it is still running, at 0.06 GB) and the team is working again. The ask stands, less urgently: while Ollama runs, it can take those 4 GB back at any moment and stop a build halfway; quitting it for the evening avoids that.

### USER-39 — Look over the new surveyor design (5 min, no game needed)
The first design for the new-look surveyor you asked for after 0.6.0 is on this page: https://claude.ai/artifact/Ts7md2pqMrMby3hnTGZdiq
It is drawings only; nothing in the game changes until you answer. Open the page, look at the pictures, then tell the Lead session:
1. Is this the look? Yes, close but change something, or no.
2. Is the figure the right weight beside the camp's crate and smelter?
3. Do you like the face side-on?
4. Do the crouch, the jump and the dig read the way you pictured them?
A "yes" starts the surveyor being built as a moving rig in the game (about a day to a test scene you can play). A "change this" is about half a day a round.

### USER-38 — (folded into USER-41 at 21:5x: play 0.6.2 instead; it includes 0.6.1b) Play Build 0.6.1b: ten minutes with the shovel (10 min)
Your shovel ask is in. The page with pictures: https://claude.ai/artifact/JQ1uqincAcQRRt1yFqrT5w
Use the fixed build 0.6.1b (16:0x), not 0.6.1.
1. Double-click `C:\dev\universegame\Build\MERIDIAN_0.6.1b\MERIDIAN.exe` and choose **NEW** (a game continued from 0.6.0 keeps the Beam if you had bought Beam Power I, so only a new game shows the shovel).
2. Look at the new title screen.
3. Hold the left mouse button on ground within about two metres: the shovel digs one scoop at a time.
4. Fill the pack, climb above the dashed Surface Line, press G and SELL ALL.
5. Press K, open the Dig branch and buy **The Beam** (250 Scrip). The tool slot under the top bar changes from SHOVEL to BEAM MK1. Dig again.
Then tell the Lead session: is the shovel a good start or too slow, does the Beam feel like a reward, does the price feel right, and anything else you notice. Known already: the shovel stroke is plain for now (the shovel moves, the body stands still; 0.6.2 gives it weight), a hint card covers the tool slot's name while it shows, and at the rocket's foot the surveyor is drawn behind the landing leg. (The first 0.6.1 showed a pickaxe during each stroke and an empty bar at the top of the screen; 0.6.1b removes both.)

### USER-08 — Optional: let the team run PowerShell commands without prompts (2 min)
On Windows, Claude Code runs commands through PowerShell as well as Bash, and the
`Bash(...)` allow rules in `.claude/settings.json` don't cover PowerShell. The Lead added
matching PowerShell *deny* rules, but isn't allowed to grant itself new *allow* rules.
If you get too many "allow this command?" prompts, tell the Lead "approve PowerShell
allow rules" and accept the edit when Claude Code asks you. Otherwise skip this.

## Done
- 2026-11-09 13:5x · USER-36 done: the owner played 0.6.0: "I like the digging so far"; make digging more satisfying and rewarding (a dirt animation), the dug part should look like a hole rather than an opaque part, dirt should collapse when dug all the way under; then the big one: keep the cartoon but much higher quality, a modern hand-drawn or painted look rather than 1930s animation, never digital or 3D-cartoony; better art and more moving parts for the animals and characters, especially the surveyor, with crouching and jumps with knees that bend; and much better audio → D-183 / D-184 / D-185 / D-186; U-195..U-199, B-230..B-232; milestone C5 (the v5 style test) before any redraw.
- 2026-11-09 12:5x · USER-37 done: the ChatGPT app is closed (it held 1.27 GB); free RAM 1.99 GB at 12:51 and UNITY's U-193 check started. You can reopen it when the team is idle.
- 2026-11-09 10:2x · USER-35 resolved: free RAM rose to 2.5–2.9 GB around 09:59 (apps closed or gone idle) and UNITY's 0.6.0 checks ran at the flat gate; nothing left to do. Edge can be reopened.
- 2026-11-08 19:3x · USER-34 done: the owner checked 0.5.1: "the walking seems fixed"; and asked for a minimap in space → D-178, U-184, B-209.
- 2026-11-08 16:2x · USER-33 done: the owner played 0.5.0 and likes it so far; the walking animation glitches when walking downhill (→ U-172, first); and they really like the digging: make MERIDIAN a progression digging game (better tools unlocked to dig deeper and faster, money from collected materials, rarer deeper, no hard gate, a boundary line underground marking topside where upgrading happens, better ways up and bigger packs, a Skill Tree with branches people choose themselves, planets as a difficulty ladder with rarer materials) → D-174, Bible 5.2 §8.1, milestone D1 (L-013, U-174..U-177, B-203..B-205); Build 0.5.1 (U-173) brings the walk fix first.
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
