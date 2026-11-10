# What I need from you

Owner: LEAD (only the Lead edits this). Do the open items below, then tell the Lead session
`done: USER-0X`. Each item has exact steps. Everything here fits in one sitting (about
90 minutes, mostly downloads).

## Open

### USER-47 — Your Canva image credits ran out, and the more detailed look needs them (2 min)
You asked for a look that is a lot more detailed and as close to the film as we can get. The honest finding from today's test: plants and brush work painted by the AI in your Canva are far better drawn than anything our own code paints, so the detailed backgrounds have to be built mostly from AI-painted pieces. Four sheets were made today (three sheets of brush marks, one sheet of nine jungle plants). Then Canva refused the next two with "You have exceeded your credit quota".
- If you do nothing: the surveyor gets its detail anyway (that is drawn by our code), and the backgrounds get as detailed as four sheets allow. They will fall short of what you asked for.
- To get the backgrounds close: in Canva, look at your plan's AI image credits (Account settings, then Billing and plans). Tell the Lead "credits are back" when there are some. About twenty more sheets are wanted (ferns, grasses, palms, vines, tree trunks, logs, rocks, ground litter, misty far jungle).
- Or say "use something else" if you would rather the Lead not spend Canva credits; the Lead will say what else is possible.

### USER-45 — Play Build 0.6.3: ten minutes of the rebuilt digging (10 min)
You said digging felt disconnected from your clicks and from the surveyor. It has been rebuilt. The page with frame-by-frame pictures: https://claude.ai/artifact/TdyF9gzKsFWzXebcu5KUSm
1. Double-click `C:\dev\universegame\Build\MERIDIAN_0.6.3\MERIDIAN.exe` and choose **NEW** (not Continue: see the note at the end).
2. Click once, quickly, on the ground beside you: a whole swing plays and lands. Then click fast, then hold.
3. Move the mouse without pressing: four brackets show where the next dig will land (mustard at the edge of your reach, red when there is nothing to dig).
4. Dig straight down, into a wall beside you, and above your head in a tunnel.
5. Go deeper: hard ground takes several hits, each leaving a crack.
6. Sell (G), buy The Beam (K, 250 Scrip) and dig with it.
Then tell the Lead session: does a click feel connected to the dig now; do the surveyor and shovel look like they are doing the digging; are several hits on hard ground satisfying or tedious; and from last time: do the holes look right, is the shovel a good start, is 250 Scrip right for the Beam?
Known already: the surveyor is still the round-headed one (the new look is on its own page, USER-44); the marker's small cross is being redrawn; upward digging in a low tunnel pushes the blade into the ceiling; Mars and Space may hitch slightly (a memory fault found today, fixed next); no collapse yet and the sounds are still synthesized.
A NOTE ON YOUR SAVED GAME (found 12:00, our fault): the team's automatic test runs have been saving into your real save slot. Continue would load a test's game on Mars, and any progress you saved in an earlier build was overwritten by those runs. It is fixed from the next build. Nothing in your save folder has been touched by hand and nothing will be: if a NEW game ever shows something left over from that test state, tell the Lead and you decide whether the slot is cleared.



### USER-42 — Free about half a gigabyte of memory (2 min) — not blocking right now, but the margin is thin
Thank you for restarting the three windows (00:50). Update 01:01: once the new windows settled, free memory rose to 1.9 GB and the team's builds and tests can start again. The laptop itself was not restarted (it has been on since yesterday 11:44) and builds need 1.5 GB free, so one busy app can stop them again. Either of these gives a safe margin:
- **Quick:** close the **Copilot** app (it holds 0.4 GB), the **Xbox** app (0.3 GB) and the **Settings** window (0.2 GB). For Copilot and Xbox, look in the system tray by the clock (click the ^ arrow), right-click the icon and choose Quit or Close.
- **Thorough:** close the three Claude windows (the Lead's last), restart the laptop, open the three windows again and paste the usual resume message into each.
Then tell the Lead session "done: USER-42". Nothing is lost either way: everything is in the project files.

### USER-40 — Free the laptop's memory: quit Ollama (1 min) — the team is blocked on this
At 18:52 the laptop has 0.12 GB of memory free and no build or render can start (they need 1.5 GB). The biggest holder is the **Ollama** app: 4.2 GB, running since 11:47 this morning. It is not part of the game team.
1. Look in the system tray (the small icons by the clock, bottom right; click the ^ arrow if it is hidden) for the Ollama llama icon.
2. Right-click it and choose **Quit Ollama**.
3. If you are not using them, also close the **Xbox** app and any Chrome windows you don't need.
4. Tell the Lead session "done: USER-40".
If you are using Ollama for something of your own, say so instead and the team will wait or work around it. You can start it again whenever the team is idle.
Update 18:59: the memory came back on its own at about 18:57 (Ollama let go of its 4.2 GB; it is still running, at 0.06 GB) and the team is working again. The ask stands, less urgently: while Ollama runs, it can take those 4 GB back at any moment and stop a build halfway; quitting it for the evening avoids that.

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
- 2026-11-10 12:0x · USER-46 withdrawn: the owner pointed out Canva is connected ("I have canvas as a connector tho"); the Lead exported both files itself through a holding design in the owner's Canva (2048 × 2048 PNG, in docs/art_sources/v6_painted/). No downloads are asked of the owner. The same message: "I dont care for any unsaved gameplay so far just when its done": the overwritten saves (D-203) are no loss to the owner; the fix stands.
- 2026-11-10 11:3x · USER-44 answered: "I like it so far but find a painters hand or you do it ai is so capable nowadays and continue doing the rest" → D-202: art v6 accepted as shown and rolling out (a playable slice first: the Earth camp with the v6 surveyor); the painter's hand from AI-painted strokes and plates (pilot made, USER-46 for the full-size files); the camera ruled by the Lead (close on the surface, easing back underground), since the owner did not choose.
- 2026-11-10 07:4x · USER-43 answered within minutes of the page (https://claude.ai/artifact/DfszsRAPjF6hwbjr5i36GX): "ive seen the first look and i like the colors but the details i dont like look at the reference photos again i want that level of detail or at least as close as possible this still looks like a 1930s cartoon big cricle head and eyes make it look like the reference photos the same style as the jungle and same level to details from the proportions to everything pretty much try to make the movie but in game and moving form just the style tho none of the story or anything else" → D-200, STYLE_V6 §4a: the surveyor redesigned to natural proportions and built drawing, figures as drawn frames, scenery at the film's level of detail, the colours kept; specimens to the Lead first, then a second look-over page. Not answered: the scanned-brush question (asked again if the specimens fall short).
- 2026-11-10 06:1x · USER-39 answered: the owner on the new surveyor design: "Polish up the surveyor a bit more then that I want fine lines that dont render into pixels" → D-198 (the v5 line is fine and drawn large enough never to show pixels), B-231 round 3; a new look-over page follows when round 3's plates pass the Lead. Read as: the design's direction stands, the finish and the line change. Not answered: the figure's weight beside the camp props, the face side-on, the poses (asked again on the new page).
- 2026-11-10 01:1x · USER-41 done: the owner played 0.6.2: "The digging is wacky it feels disconnected from clicks and the avatar smoothen that out to the max like a pro make the animations and the connections incredible" → D-196 (the dig as one motion), U-209, B-246; Build 0.6.3 is for it. Not yet answered from USER-41 / USER-38: do the holes look right, is the shovel a good start, does the Beam feel like a reward, is 250 Scrip right (asked again with 0.6.3).
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
