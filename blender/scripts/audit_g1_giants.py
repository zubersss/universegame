"""B-194: the giants' G1 audit (B-182's pattern for B-177's islands, D-166): one stamped sheet per giant, read back from
Assets/_Game/Art/ at 1x with numpy only (no blender.exe, no export):

  assembled  per floe strip material: a 12 m floe (cap_left + 10 tiles + cap_right, the strip's bottom on the underside
             outline, its ground line 2 m above) on the sky, island_belly along the outline (its row 72), island_end_l / _r
             with their pivots on the floe's ends, an under_haze below the outline (a different deck per panel, faded in
             over 2.5 m as UNITY does)
  islands    island_belly tiled x2 (its 8 m seam), island_end_l, island_end_r: outline row / pivot / sort, ink, palette, edge
  hazes      under_haze_<deck> at 1x: periodic both ways (row 0 against the last, column 0 against the last); painted, so no
             palette or ink check
  strips     each floe_strip_<material>: its frames (8 tiles + the caps), ground line, palette, the tile seam (frame 7 -> 0)

The foot lists every key a json names that is not on disk (an end's "meets" strip cap, a deck's haze), and the outliers
(palette < 98 %, raster ink outside 1-4 px, an end touching the 2 px edge, a belly with ink on its top / bottom rows, a seam
whose p99 step is over twice the piece's own neighbouring-column p99 + 16).

  python -I audit_g1_giants.py <giant> [<giant> ...]   -> blender/preview/audit_g1_<giant>.png (stamped) + one line per giant
                                                           in coordination/reports/blender/audit_g1.md (replacing that giant's)
"""
import glob
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import audit_c2 as A  # noqa: E402
import audit_g1 as G1  # noqa: E402
from meridian import pngio, v3  # noqa: E402
import review  # noqa: E402

ART, PREVIEW = A.ART, A.PREVIEW
W = 2200
DECKS = ("deck1", "deck2", "deck3", "deep")
PAPER = np.array(review.PAPER, np.float32)


def rd(giant, name):
    d = os.path.join(ART, "terrain", giant)
    meta = json.load(open(os.path.join(d, name + ".json"), encoding="utf-8"))
    return meta, pngio.read_png_np(os.path.join(d, name + "_color.png"))


def seam(img, axis):
    """-> (p99 |last - first| across the wrap, p99 of the neighbouring steps) on the opaque pixels, along axis 1 (x) or 0 (y)."""
    f = img[..., :3].astype(np.int16)
    a = img[..., 3] > 0
    if axis == 1:
        wrap = np.abs(f[:, -1] - f[:, 0]).max(axis=-1)[a[:, -1] & a[:, 0]]
        step = np.abs(np.diff(f, axis=1)).max(axis=-1)[a[:, 1:] & a[:, :-1]]
    else:
        wrap = np.abs(f[-1] - f[0]).max(axis=-1)[a[-1] & a[0]]
        step = np.abs(np.diff(f, axis=0)).max(axis=-1)[a[1:] & a[:-1]]
    p = lambda v: float(np.percentile(v, 99)) if v.size else 0.0  # noqa: E731
    return p(wrap), p(step)


def seam_bad(w, s):
    return w > 2 * s + 16


def lab_row(text, width, h=22, scale=1):
    r = np.empty((h, width, 3), np.float32)
    r[:] = PAPER
    review._label(r, text[:int(width / 6)], 4, 6, scale=scale)
    return r


def panel(giant, sname, smeta, ssheet, deck, haze, belly, bmeta, end_l, lmeta, end_r, rmeta, sky):
    PW, PH = 1080, 520
    img = np.empty((PH, PW, 3), np.float32)
    img[:] = sky
    line = 300                                                                                # the floe's underside outline
    hz = haze[..., :3].astype(np.float32) / 255.0
    y0 = line - 40
    t = np.clip(np.arange(PH - y0, dtype=np.float32) / 160.0, 0.0, 1.0)[:, None, None]
    img[y0:] = np.tile(hz, (2, 3, 1))[:PH - y0, :PW] * t + img[y0:] * (1 - t)
    fr = [A.frame_of(ssheet, smeta, i) for i in range(smeta["frames"])]
    caps = smeta.get("caps", {"cap_left": 8, "cap_right": 9})
    ncol = 12
    fw, fh = smeta["frame_width"], smeta["frame_height"]
    x0 = (PW - fw * ncol) // 2
    cols = [fr[caps["cap_left"]]] + [fr[i % 8] for i in range(ncol - 2)] + [fr[caps["cap_right"]]]
    for i, c in enumerate(cols):
        review._over(img, c, x0 + fw * i, line - fh)                                         # the strip's bottom on the outline
    x1 = x0 + fw * ncol
    bt = np.tile(belly, (1, 3, 1))[:, :x1 - x0]
    review._over(img, bt, x0, line - bmeta["outline_row"])
    for e, m, xe in ((end_l, lmeta, x0), (end_r, rmeta, x1)):
        h, w = e.shape[:2]
        review._over(img, e, xe - int(round(m["pivot"][0] * w)), line - int(round((1 - m["pivot"][1]) * h)))
    gl = line - fh + int(round((1 - smeta["pivot"][1]) * fh))
    img[gl, x0 - 30:x0 - 6] = (0.85, 0.2, 0.2)                                                # ticks: the ground line, the outline
    img[line, x0 - 30:x0 - 6] = (0.2, 0.2, 0.85)
    return np.vstack([lab_row(f"{sname} (12 m floe) + island_belly / end_l / end_r over under_haze_{deck}; ticks: ground line red, outline blue", PW), img])


def audit(giant):
    t0 = time.time()
    sky = np.array(v3.hex_rgb(v3.PALETTES[giant]["sky"]), np.float32) / 255.0
    miss, outl, lines_ok = [], [], []
    pieces = {}
    for n in ("island_belly", "island_end_l", "island_end_r"):
        try:
            pieces[n] = rd(giant, n)
        except OSError:
            miss.append(f"{n} (no json / png)")
    hazes = {}
    for dk in DECKS:
        try:
            hazes[dk] = rd(giant, f"under_haze_{dk}")
        except OSError:
            miss.append(f"under_haze_{dk}")
    strips = []
    for js in sorted(glob.glob(os.path.join(ART, "terrain", giant, "floe_strip_*.json"))):
        name = os.path.basename(js)[:-5]
        strips.append((name,) + rd(giant, name))
    strips.sort(key=lambda s: (s[0] != "floe_strip_ice", s[0]))                               # the ice strip first
    if not strips:
        miss.append("no floe_strip_*")
    for n in ("island_end_l", "island_end_r"):
        if n in pieces:
            meets = str(pieces[n][0].get("meets", ""))
            cap = meets.split()[-1] if meets else ""
            if strips and cap and not all(cap in s[1].get("caps", {}) for s in strips):
                miss.append(f"{n} meets {meets}: not a cap of every strip")
    for n, (m, _img) in pieces.items():
        if m.get("contract") != "v3.3 11.10":
            outl.append(f"{n} contract {m.get('contract')}")
    rows = []
    # assembled
    if len(pieces) == 3 and strips and hazes:
        (bm, belly), (lm, el), (rm, er) = pieces["island_belly"], pieces["island_end_l"], pieces["island_end_r"]
        dks = [d for d in DECKS if d in hazes]
        pans = [panel(giant, s[0], s[1], s[2], dks[i % len(dks)], hazes[dks[i % len(dks)]][1], belly, bm, el, lm, er, rm, sky)
                for i, s in enumerate(strips)]
        rows.append(lab_row("assembled: each floe strip as an island at 1x (B-177 / D-166)", W, 26, 2))
        for i in range(0, len(pans), 2):
            pair = pans[i:i + 2]
            row = np.empty((pair[0].shape[0], W, 3), np.float32)
            row[:] = PAPER
            for j, p in enumerate(pair):
                row[:, 8 + j * (p.shape[1] + 24):8 + j * (p.shape[1] + 24) + p.shape[1]] = p
            rows.append(row)
    # islands
    if pieces:
        rows.append(lab_row("islands: island_belly tiled x2 (the 8 m seam at its middle), island_end_l, island_end_r, 1x", W, 26, 2))
        r = np.empty((40 + 256 + 40, W, 3), np.float32)
        r[:] = PAPER
        x = 8
        for n in ("island_belly", "island_end_l", "island_end_r"):
            if n not in pieces:
                continue
            m, img = pieces[n]
            hit, off = A.palette(img, giant)
            ink = A.logged_ink().get(f"terrain/{giant}/{n}") or A.raster_ink(img)
            show = np.tile(img, (1, 2, 1)) if n == "island_belly" else img
            h, w = show.shape[:2]
            r[30:30 + h, x:x + w] = sky
            review._over(r, show, x, 30)
            fields = [f"pivot {m['pivot'][0]:g},{m['pivot'][1]:.3g}"]
            if "outline_row" in m:
                fields.append(f"outline row {m['outline_row']}")
            if m.get("end"):
                fields.append(f"end {m['end']}, meets {m.get('meets')}")
            cap = f"{'; '.join(fields)}; ink {ink}; palette {hit * 100:.1f}%"
            if hit < 0.98:
                outl.append(f"{n} palette {hit * 100:.1f}% (off {' '.join(off[:3])})")
            if n == "island_belly":
                ws, ss = seam(img, 1)
                cap += f"; x seam p99 {ws:.0f} (steps {ss:.0f})"
                if seam_bad(ws, ss):
                    outl.append(f"island_belly x seam p99 {ws:.0f} vs steps {ss:.0f}")
                if img[:v3.EDGE_MARGIN, :, 3].any() or img[-v3.EDGE_MARGIN:, :, 3].any():
                    outl.append("island_belly ink on its top / bottom rows")
            else:
                if G1.edge_touched([img]):
                    outl.append(f"{n} touches the {v3.EDGE_MARGIN} px edge")
            mm = __import__("re").search(r"raster p25-p75 (\d+)-(\d+) px", cap)
            if mm and (int(mm.group(2)) > 4 or int(mm.group(1)) < 1):
                outl.append(f"{n} ink {mm.group(1)}-{mm.group(2)} px")
            review._label(r, n, x, 10, scale=1)
            review._label(r, cap[:int(max(w, 330) / 5)], x, 30 + h + 6, scale=1)
            x += max(w, 330) + 24
        rows.append(r)
    # hazes
    if hazes:
        rows.append(lab_row("hazes: under_haze_<deck> at 1x (painted; periodic both ways)", W, 26, 2))
        r = np.empty((30 + 512 + 30, W, 3), np.float32)
        r[:] = PAPER
        x = 8
        for dk, (m, img) in hazes.items():
            wx, sx = seam(img, 1)
            wy, sy = seam(img, 0)
            review._over(r, img, x, 26)
            review._label(r, f"under_haze_{dk} {img.shape[1]}x{img.shape[0]}", x, 8, scale=1)
            review._label(r, f"x seam {wx:.0f} (steps {sx:.0f}), y seam {wy:.0f} (steps {sy:.0f})", x, 26 + img.shape[0] + 6, scale=1)
            if seam_bad(wx, sx) or seam_bad(wy, sy):
                outl.append(f"under_haze_{dk} seam x {wx:.0f} / y {wy:.0f} vs steps {sx:.0f} / {sy:.0f}")
            x += img.shape[1] + 16
        rows.append(r)
    # strips
    if strips:
        rows.append(lab_row("floe strips: frames 0-7 tile, then cap_left / cap_right, 1x", W, 26, 2))
        for name, m, img in strips:
            fr = [A.frame_of(img, m, i) for i in range(m["frames"])]
            strip_img = A.hcat(fr, 6)
            hit, off = A.palette(img, giant)
            ink = A.logged_ink().get(f"terrain/{giant}/{name}") or A.raster_ink(img)
            ws, ss = seam(np.concatenate([fr[7], fr[0]], axis=1)[:, fr[7].shape[1] - 1:fr[7].shape[1] + 1], 1)
            _w2, steps = seam(np.concatenate(fr[:8], axis=1), 1)
            cap = (f"{name}: {m['frames']} frames {m['frame_width']}x{m['frame_height']}, ground line {m.get('ground_line_px')}, caps {m.get('caps')}, "
                   f"material {m.get('material')}; ink {ink}; palette {hit * 100:.1f}%; tile seam 7->0 p99 {ws:.0f} (steps {steps:.0f})")
            if hit < 0.98:
                outl.append(f"{name} palette {hit * 100:.1f}% (off {' '.join(off[:3])})")
            if seam_bad(ws, steps):
                outl.append(f"{name} tile seam 7->0 p99 {ws:.0f} vs steps {steps:.0f}")
            r = np.empty((strip_img.shape[0] + 40, W, 3), np.float32)
            r[:] = PAPER
            r[8:8 + strip_img.shape[0], 8:8 + strip_img.shape[1]] = sky
            review._over(r, strip_img, 8, 8)
            review._label(r, cap, 8, 8 + strip_img.shape[0] + 8, scale=1)
            rows.append(r)
            del fr
    n_keys = len(pieces) + len(hazes) + len(strips)
    head = lab_row(f"b-194 g1 audit: {giant}  ({n_keys} keys: island 3, haze {len(hazes)}, floe strips {len(strips)}; {len(miss)} missing, "
                   f"{len(outl)} outliers) read back from assets/_game/art at 1x", W, 28, 2)
    foot_lines = ["missing (" + str(len(miss)) + "): " + (", ".join(miss) if miss else "none"),
                  "outliers (" + str(len(outl)) + "): " + (", ".join(outl) if outl else "none")]
    foot = np.empty((30 + 16 * len(foot_lines) + 24, W, 3), np.float32)
    foot[:] = PAPER
    for i, ln in enumerate(foot_lines):
        review._label(foot, ln[:360], 6, 6 + 16 * i, scale=1)
    img = np.vstack([head] + rows + [foot])
    del rows
    review.draw(img, time.strftime("%m-%d %H:%M") + " audit (read back, numpy only)", 2, img.shape[0] - 16, (1.0, 1.0, 0.85))
    np.clip(img, 0.0, 1.0, out=img)
    u8 = np.empty(img.shape[:2] + (4,), np.uint8)
    u8[..., :3] = np.rint(img * 255.0)
    u8[..., 3] = 255
    out = os.path.join(PREVIEW, f"audit_g1_{giant}.png")
    pngio.write_png(out, u8)
    print(f"{giant}: {n_keys} keys, {len(miss)} missing, {len(outl)} outliers, {u8.shape[1]}x{u8.shape[0]}, {time.time() - t0:.1f}s")
    for o in outl:
        print("  outlier:", o)
    return (f"- {giant} ({time.strftime('%m-%d %H:%M')}): B-194, {n_keys} keys (island 3, haze {len(hazes)}, floe strips {len(strips)}: "
            f"{', '.join(s[0] for s in strips)}); missing: {', '.join(miss) if miss else 'none'}; outliers: {', '.join(outl) if outl else 'none'}; "
            f"sheet blender/preview/audit_g1_{giant}.png")


if __name__ == "__main__":
    G1.write_report([audit(g) for g in sys.argv[1:]])
