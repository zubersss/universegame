# LEAD STATUS
Updated: 2026-11-10 13:1x · Session: 13 (zuber-36; windows restarted 00:50; Fable 5.2: LEAD high, UNITY and BLENDER extra high) · Review cycle: 308 · Cadence: every 2 hours (session cron f87d9baf, `43 */2 * * *`; it dies with this session: a NEW LEAD re-creates it)
Session addresses (ListAgents 00:52; they change at a restart): this session zuber-36 · UNITY zuber-57 · BLENDER zuber-e2.

## Where things stand (resume here)
1. BUILD 0.6.3 IS WITH THE OWNER (USER-45; page https://claude.ai/artifact/TdyF9gzKsFWzXebcu5KUSm, version 2 with the save note; source scratchpad p063/). The dig as one motion (D-196, a, b). No playtest answer yet. Unanswered from before: do the holes look right, the shovel as a start, the Beam's price.
2. ART v6 IS ACCEPTED (D-199, D-200, D-202; docs/STYLE_V6.md; owner: "I like it so far but find a painter's hand or you do it ... continue doing the rest"). THE C5 SLICE = the Earth camp at the forest edge with the v6 surveyor, behind a flag.
   - B-250 slice 1 of the surveyor's frames is EXPORTED (2c151225: characters/surveyor_v6/side, side_air, side_dig; drawn frames, ppu 128, 288 × 320 box; walk = a lope at 4.0 m/s, run = a sprint at 6.5, stroll 1.63, each with ground_speed; slide_min / slide_max, a stow table). In Review until UNITY's import and captures IN MOTION (nobody has seen it move).
   - B-251, the painter's-hand PILOT, is running (BLENDER's lock 13:12; a sheet on disk 13:09, not yet handed over): my two AI-painted files (docs/art_sources/v6_painted/strokes_01.png, plant_01.png; made through the owner's Canva: see memory canva-full-size-export-route; credited in docs/credits/lead.md; prompts name a medium and period only). JUDGE on its sheet: do painted strokes beat the code's dab; does the plate sit in the frame's light. If yes: generate a library on BLENDER's list (I can make more within minutes), then card the stage layers (tiling, alpha).
   - B-252 (slice 2: the v6 fist first, far-reach and low dig drawings, the rest of the clips) after B-251.
   - U-213 (UNITY): the slice in the game: the v6 sheets (own atlas and label, never the common atlas), the v6 stage, THE CAMERA (96 px per metre on foot at the surface, easing to 64 underground; coded and captured on today's art first).
3. MEASUREMENT AND SAFETY FAULTS FOUND TODAY, all UNITY's own finds: D-197 (walls stay RGBA32), D-201 (the dead allocation counter; every settled GC row now under 1 KB, U-211's table), D-203 / D-203a (tests and smokes wrote the owner's save slot: guarded; the built player takes -meridianSaveRoot; NO smoke or player probe on a player without it; the next build's probe has no control row), the autosave hitch (37–62 ms in the first frame after a transition: being moved before the iris now).

## UNITY's order
U-211 (b) the autosave before the iris (now) → U-212 (the smoke with the owner on, a contact frame and a Beam shot; reticle under the surveyor, pip only in a swing, the red state over an animal, block-ground brackets, the stowed blade in bump frames, G5, the Maw in the shallows) → U-213 (camera first) → BUILD 0.6.4 when those are in → U-214 (panels, autosave off the main thread) → U-215 → U-197 (collapse) → U-198 (audio) → U-210 → U-208. Open under U-211: the AI's first-time frame, LastAiAllocBytes on the live counter, the cell-open frame.
## BLENDER's order
B-251 pilot → (my judgement, a library) → B-252 → the stage layers card → Earth's kinds in the frame. B-249 (the pip) and B-243, B-250 in Review on UNITY.

## The owner
Open: USER-45 (play 0.6.3; choose NEW), USER-42 (memory margin, not blocking), USER-40 (quit Ollama). Said today: no downloads, use the Canva connector; does not mind earlier saved games lost. REMIND at the next natural break: restart the three windows (up since 00:50).

## Loop / stall watch
None at 13:1x. Rules kept: read `date` FIRST, then write a time label; read the code or the stills a complaint points at before carding; judge only what its author has handed over; a figure from another hour is no baseline; an allocation row needs a control; nothing of the team's touches the owner's AppData; never enlarge pixels on an owner page; an edits-only Artifact publish sends no files; check an assumption about the game in the code before telling a worker (the pack does not slow the walk). The board file is rewritten by my card script: re-read a line before an Edit.

## HeavyJobLock
none of mine
