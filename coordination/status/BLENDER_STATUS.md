# BLENDER STATUS
Updated: 2026-11-07 15:03 · Session: 8 (resumed 14:3x after the ~14:17 machine restart; C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
B-158 Uranus decks (queue rank 2) + B-161 Neptune source (lock-free). Deck2 x4 ACCEPTED (LEAD 14:5x). 14:56:51-15:00:55 DECK3 SLOT (lock free, 2.98 GB, no other want): udeck3 x4 in 244 s, peak 672 MB; review_b158_uranus_udeck3_{sun_left,sun_right,night,survey}_preview.png 14:57-15:00; --uranus-check deck3 PASS (alpha md5 SAME in all four lights); denser methane-cyan banks, hail streaks on layer2, the sun + haze swap sides, night the dark slate with hail and stars. Released 15:01:00; want_unity on file, so UNITY goes next; I re-file for deep x4 only once its lock appears (D-039). Left on B-158: deep x4, then deck1 again (before export); B-158 Done on those.
B-161 lock-free beside UNITY's lock: the five flora as drawing functions (a1924873): kitebloom, gripweed, pipereed, stormlantern, rimecomb; drawn upright (D-148); smoke render 47 MB: every idle / react frame inside the 2 px edge, palette 100 %, ink 2.01-3.00 / 1.01-1.49 px (gripweed's tendrils and the lantern stem thickened after a look: thin hoses read as ink scribbles). Next: build_c2_neptune_floes.py (ice: the windward cap rounded, the lee cap ragged; superionic), then in a free gap the stamped plants + floes previews (the Uranus plants preview measured 301 MB: not beside another role's lock) and B-151's dry run (unmeasured: a free gap only); then the Venus rows.
14:4x D-148 (LEAD): the Neptune palette in meridian.v3.PALETTES["neptune"] + the ui/palettes/neptune manifest row (decf9ad0); the report's proposals are rulings (flora + wind sock upright; the storm rim on its own layer with a `pulse` block; the Meridian's segments ~7.5 m).
14:09:59-14:10:35 B-165 reopened + re-exported (RGBA gutters, e0f476c7); UNITY measures the dip in its probe lock (U-131); Done on a flat reading.

## Last completed
- 14:56:51-15:01:00 SLOT (bundled python, lock held): B-158 udeck3 x4 studies, --uranus-check deck3 PASS (244 s, peak 672 MB).
- 14:5x B-161 Neptune flora source (a1924873; lock-free, 47 MB smoke render).
- 14:46:29-14:50:37 SLOT (bundled python, lock held): B-158 udeck2 x4 studies, --uranus-check deck2 PASS (231 s, peak 672 MB; ACCEPTED).
- 14:4x B-161 D-148 palette into v3 + the manifest row (decf9ad0).
- 14:36-14:45 B-161 palette + design report (e4ef46b2, 05a4e3a4; ACCEPTED as D-148).
- 14:09:59-14:10:35 SLOT (wrapper, gate 1500): B-165 reopened - the nine strips with RGBA gutters, frame rects identical (log OK x4, peak 525 MB).

## Ready for review
- B-158 deck3 x4: review_b158_uranus_udeck3_{sun_left,sun_right,night,survey}_preview.png (14:57-15:00) + the --uranus-check deck3 PASS lines.

## Handoffs (unrouted only)
-> UNITY (B-150, cca20f60): drop the .meta of the removed Mercury v2 files (glassback / cinderling / flarewing / shadewyrm .glb, _normal, _mask, _emission); props/mercury/ice_burrow is den_for creatures/mercury/shadewyrm (D-126: drawn in front).
-> UNITY (B-148, 70c40e1e): flora/mercury/rigset biomes are day / twilight / night / polar (shadebloom night + polar).

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

## For USER_ACTIONS
none (USER-28, closing ChatGPT + Edge for RAM, is LEAD's).

## HeavyJobLock
none held (deck3 slot released 15:01:00); no want on file: UNITY's want goes next, and I re-file for deep x4 only after UNITY takes the lock (D-039).
