# BLENDER STATUS
Updated: 2026-11-07 22:3x · Session: 8 (resumed 14:3x after the ~14:17 machine restart; C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
PAUSED by the owner (LEAD relayed 21:1x; acted on 22:3x): the RAM / locks monitor stopped, want_blender.lock removed, no renders, no dry runs, no polling until the owner or LEAD says continue.
RESUME POINT, in order: (1) creatures/jupiter/vortex_whale under D-156: `blender/scripts/oneoff/whale_d156.ps1` (one-off gate 1300 MB, a 900 MB Blender working-set cap; the 20:51 attempt never reached 1300 free, so the exception is unspent; D-153 scale in code a9bae628, the parts pack 46 % of one sheet; its stamped review at 0.25x beside the surveyor). Then release: UNITY's D-156 compile + EditMode (1250 / 1000) runs next. (2) B-170: the lock-free card preview (`python -I build_ui_v3.py --cards <png>`, ~60 MB, for LEAD's look), then the export slot (ui/c2/titlecards_set; source fc08fbff). (3) B-163 slot 1: backgrounds/saturn/deck1,deck2,deck3,deep,hexagon (straight; U-129 loads these names). (4) B-163 slot 2: terrain/saturn/floe_strip_set, flora/saturn/rigset, props/saturn/props_set, ui/palettes/saturn. (5) B-164: creatures/saturn/helium_jelly, hex_drake, floe_moth, ringmite, polar_hydra. In free gaps only (nobody waiting): `oneoff/grand_pack.py` before the Hydra / Diamondback / Leviathan slots (a misfit goes to LEAD with a scale first), `oneoff/uranus_rows.py`, then `oneoff/neptune_rows.py` (LEAD 19:4x).
Uncommitted on purpose: blender/sources/creatures/jupiter_vortex_whale_rigset.blend (the stale 1x build from 18:25; the D-156 export rebuilds it).

## Last completed
- files (pause): B-170 source fc08fbff, the D-141 palette guards fa039f3b, the resume helpers 391c7cf7 (blender/scripts/oneoff/).
- 18:22:10-18:27:02 SLOT (wrapper): B-160 stormglider / lightning_eel / belt_wasp / ballast_tortoise (db4d5a53; 658 MB); the whale failed to pack -> D-153.
- 18:20:58-18:21:37 SLOT (wrapper): B-159 slot 2, floes / flora / props / palette (2b00434b; 393 MB).
- 18:14:01-18:20:21 SLOT (wrapper): B-159 slot 1, Jupiter deck1-3 / deep / spot straight + the B-156 aerostat kit (ad3d2e98; 836 MB).
- files: the Saturn v3 rows (81e90b17), the B-166 URANUS-CHECK hook (25a6477e).
- 17:24:43-17:28:29 SLOT: B-161 Neptune ndeck1-3 on the look pass (220 s, 590 MB).
- 17:23:23-17:24:07 SLOT (wrapper): B-168 the eight Venus station props (a5d30f30; VERIFIED).
- 16:55:43-16:56:06 SLOT (wrapper): B-167 the six Mercury props (243804c3; ice_burrow byte-identical; 24 v2 files removed).
- 16:18:39-16:19:42 SLOT (wrapper): B-154 the four Venus creatures + props/venus/vent_mouth (87e1ae22; 460 MB) + the missed Mars / Mercury v3 sources committed.
- 16:14:35-16:15:02 SLOT (wrapper): B-153 (VERIFIED by LEAD).
- 16:11:42-16:12:58 SLOT (wrapper): B-152 (VERIFIED by LEAD).
- 16:07:42-16:11:26 SLOT: the B-161 stamped reviews (all nine ACCEPTED).

## Ready for review
none (the whale lands with its slot).

## Handoffs (unrouted only)
none.

## Blockers
none.

## Proposals (undecided only)
none (B-161's three ruled in D-148).

## Rules I keep (from slips this session)
- A review grows with its rows: beside another role's lock, re-measure or cut it to the measured size (13:50: the 3-row before / after hit 207 MB vs 144 MB measured for 2 rows).
- While another role holds the lock, run only jobs already measured <= 150 MB; a new job (or a new whole preview) is first measured in a free gap, never estimated from its parts.
- A lock check is its own call; Blender starts only in a later call after reading a clear result (D-073). The same for RAM: read it in its own call, then decide.
- A want is filed only when the queue says I am next after the running job; never while the other role's multi-lock job is between locks.
- Light work while another role's heavy job runs: <= ~150 MB; lock-free otherwise <= ~300 MB (D-109); under 0.3 GB free, code only. Measure a new path on one part / a few frames first.
- Measure every new export path's frames against the 2 px edge and the ground line before the export.
- Short jobs run in the foreground; no background waiters (the harness reaps them under memory pressure): check the locks folder each turn.
- All three sessions share one working tree: a push can race another role's; fetch + merge (never rebase) and push again.
- A stroke's line is drawn in its material's ink_hex: a coloured line needs its own line material (fill=None, ink_hex=colour); a fill-only material on an open stroke draws nothing.
- While a want is on file, poll the locks each turn; never end a turn waiting for a ping (16:20-16:55: the lock sat free 33 min).
- RAM is read in its own call BEFORE a lock-free run, never in the same call (15:5x: a 92 MB Leviathan smoke started at 0.24 GB free beside UNITY's build, under the 0.3 GB code-only line).
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs, not even a capped dry run (LEAD 18:1x; D-037: my idle time is what frees the memory); lock-free work is then files only (rows, sources, reports).

## For USER_ACTIONS
none (USER-28, closing ChatGPT + Edge for RAM, is LEAD's).

## HeavyJobLock
none held, no want on file (paused; removed 22:3x).
