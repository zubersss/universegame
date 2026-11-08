# One-off helpers (BLENDER, 2026-11-07; kept across the owner's 21:1x pause)

Run from a free gap only (no other role holding the lock or waiting), RAM read in its own call first.

- `whale_d156.ps1`: D-156 (LEAD 20:4x), creatures/jupiter/vortex_whale only. tools/blender_render.ps1's lock / want / stamp / log
  formats with a one-off start gate of 1300 MB (waits up to 7 min) and a kill at 900 MB of Blender's working set (+ D-045's
  300 MB floor). One reap or one cap kill ends the exception (then wait for USER-31). The measured peak becomes the Grand-rig gate.
  `powershell -NoProfile -ExecutionPolicy Bypass -File blender/scripts/oneoff/whale_d156.ps1`
- `uranus_rows.py`: B-166, writes the Uranus v3 manifest rows (refuses to run twice). Approved by LEAD 19:4x.
- `neptune_rows.py`: B-169, the Neptune v3 manifest rows; run after uranus_rows.py. Approved by LEAD 19:4x.
- `grand_pack.py`: the Grand rigs' parts at 1x (stroke bounds) through v3.shelf_pack (whale, Hydra, Diamondback, Leviathan),
  before their slots; a rig that does not fit goes to LEAD with a D-153-style scale before its slot.

The Python ones run with Blender's bundled python: `"<blender>/5.2/python/bin/python.exe" -I blender/scripts/oneoff/<file>`.
