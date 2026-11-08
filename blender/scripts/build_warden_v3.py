"""B-196 (LEAD 14:1x): the Warden sentinel as a v3 sheet (creatures/warden/sentinel), replacing its v2 model: Sentinel.cs
loads the key as a sheet (FxSheet.Get) and plays idle (patrol), walk (hunt) and attack (it rings its bell, D-087: it never
shoots), scaling the frame's width to 1.6 m. Faceless (D-101): a hovering brass-capped lantern machine - one barred lamp
(a lantern, not an eye: vertical cage bars over the glow), a bell hung under it, one tail vane behind and a short antenna in
front (nothing symmetric to read as a pair of eyes). B-131's camp materials and ink (palette tones only, no alpha glow).

  sentinel  104x112 (1.625 x 1.75 m at 64 px / m), pivot centre (it hovers), clips:
            idle 6 (loop)   a slow bob, the lamp pulses, the vane flutters, the bell sways a little
            walk 6 (loop)   the hunt: leaning into the chase, the lamp hot red, the vane fast, speed dashes behind
            attack 6 (once) the bell swings and rings: ring arcs spread from it, the lamp flashes

The export writes creatures/warden/sentinel_color.png + sentinel.json and removes sentinel.glb + its normal / mask /
emission maps in the same run (LEAD: never delete the v2 files alone - its 1024^2 map would import as one sprite).

  python -I build_warden_v3.py <review png>   lock-free preview: every frame at 2x, the clips at 1x over Mars and Mercury
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_props_common_v3 as PC  # noqa: E402  (gp_draw through fakegp outside Blender; the camp props' materials)
from meridian import fakegp, v3  # noqa: E402
import gp_raster as GR  # noqa: E402

G, P = PC.G, PC.P
O, I = PC.O, PC.I
PPU = PC.PPU
KEY = "creatures/warden/{}"
FW, FH = 104, 112
CLIPS = [("idle", 8, True), ("walk", 12, True), ("attack", 8, False)]      # the contract's clip caps: idle 8-12, walk 12-16
SWING = [0.0, 22.0, -18.0, 13.0, -9.0, 5.0, -2.0, 0.0]       # attack: the bell's swing (deg) per frame


def _rot(deg, cx=0.0, cz=0.0):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return lambda pts: [(cx + (x - cx) * c - (z - cz) * s, cz + (x - cx) * s + (z - cz) * c) for x, z in pts]


def sentinel(d, M, clip, k):
    n = dict((c, m) for c, m, _l in CLIPS)[clip]
    ph = 2 * math.pi * k / n
    bob = 0.03 * math.sin(ph) if clip != "attack" else 0.0
    tilt = -10.0 if clip == "walk" else 0.0
    T0 = _rot(tilt)
    T = lambda pts: [(x, z + bob) for x, z in T0(pts)]  # noqa: E731

    def S(pts, mat, w=I, cyc=True):
        G.stroke(d, T(pts), M[mat], w, cyclic=cyc)

    def seam(pts):
        G.seam(d, T(pts), M["ink"])

    if clip == "walk":                                                                  # speed dashes behind (not tilted)
        for i, z in enumerate((0.18, 0.0, -0.18)):
            x0 = -0.74 + 0.05 * ((k + i) % 2)
            G.stroke(d, [(x0, z + bob), (x0 + 0.16, z + bob)], M["ink"], I)
    flut = math.sin(ph * (2 if clip == "walk" else 1))
    vane = [(-0.28, 0.12), (-0.62, 0.2 + 0.05 * flut), (-0.66, 0.1 + 0.05 * flut), (-0.58, -0.06 + 0.04 * flut), (-0.28, -0.02)]
    S(vane, "teal", O)                                                                  # the tail vane, behind
    S([(-0.3, 0.06), (-0.6, 0.12 + 0.05 * flut), (-0.6, 0.06 + 0.04 * flut), (-0.3, 0.02)], "teal_sh", 0.0)
    seam([(-0.34, 0.07), (-0.58, 0.12 + 0.05 * flut)])
    # the bell under the lamp, hung from a yoke; it sways (idle / walk) or swings (attack)
    sw = SWING[k] if clip == "attack" else 4.0 * math.sin(ph + 0.6)
    B = _rot(sw, 0.0, -0.2)
    bell = B([(-0.08, -0.25), (0.08, -0.25), (0.12, -0.34), (0.15, -0.48), (0.22, -0.58), (0.22, -0.62),
              (-0.22, -0.62), (-0.22, -0.58), (-0.15, -0.48), (-0.12, -0.34)])
    S(B([(-0.02, -0.2), (0.02, -0.2), (0.02, -0.26), (-0.02, -0.26)]), "iron", I)
    S(B(G.lumpy_ellipse(0.0, -0.665, 0.035, 0.03, n=10, seed=609)), "iron", I)         # the clapper
    S(bell, "mustard_f", 0.0)
    S(B([(0.04, -0.25), (0.08, -0.25), (0.12, -0.34), (0.15, -0.48), (0.22, -0.58), (0.22, -0.62), (0.06, -0.62)]), "mustard_sh", 0.0)
    S(B([(-0.22, -0.58), (0.22, -0.58), (0.22, -0.62), (-0.22, -0.62)]), "mustard_dp", 0.0)
    S(bell, "ink", O)
    seam(B([(-0.13, -0.45), (0.13, -0.45)]))
    if clip == "attack" and 1 <= k <= 6:                                                # the ring: arcs spreading from the bell
        r = 0.16 + 0.05 * k
        for side in (-1, 1):
            arc = [(side * (r + 0.02) * math.cos(t), -0.45 + r * 0.9 * math.sin(t)) for t in [-0.7 + 1.4 * i / 8 for i in range(9)]]
            G.stroke(d, G.hose_outline(arc, 0.022), M["mustard"], I, cyclic=True)
    # the collar, the lamp chamber, the cap
    S(PC.box(-0.3, -0.21, 0.3, -0.12, seed=601), "iron", O)
    G.rivets(d, T([(-0.2, -0.165), (0.0, -0.165), (0.2, -0.165)]), M["ink"])
    lamp = PC.box(-0.24, -0.12, 0.24, 0.27, seed=602, wob=0.004)
    S(lamp, "teal_dp", 0.0)
    pulse = 0.5 + 0.5 * math.sin(ph)
    hot = clip == "walk" or (clip == "attack" and k in (1, 2))
    gr = 0.11 + 0.025 * (pulse if clip == "idle" else 1.0) + (0.04 if clip == "attack" and k in (1, 2) else 0.0)
    S(G.lumpy_ellipse(0.0, 0.07, gr, gr * 1.15, n=18, lump=0.05, seed=603), "glow_hot" if hot else "glow", 0.0)
    S(G.lumpy_ellipse(0.0, 0.08, gr * 0.5, gr * 0.62, n=12, lump=0.05, seed=604), "glow" if hot else "glow_core", 0.0)
    for x in (-0.17, -0.06, 0.05, 0.16):                                               # the lantern's cage bars
        S(PC.box(x - 0.018, -0.12, x + 0.018, 0.27, seed=int(x * 100) + 610, wob=0.001, n=2), "iron", I)
    S(PC.box(0.17, -0.12, 0.24, 0.27, seed=605, wob=0.002), "teal_sh", 0.0)
    S(lamp, "ink", O)
    S(PC.box(-0.38, 0.26, 0.38, 0.33, seed=606), "iron", O)                            # brim
    dome = [(-0.32, 0.33)] + G.bezier((-0.32, 0.33), (-0.3, 0.56), (0.3, 0.56), (0.32, 0.33), n=14)[1:]
    S(dome, "mustard_f", 0.0)
    S([(0.12, 0.33)] + G.bezier((0.12, 0.33), (0.18, 0.5), (0.28, 0.47), (0.32, 0.33), n=8)[1:], "mustard_sh", 0.0)
    S(dome, "ink", O)
    G.rivets(d, T([(-0.22, 0.38), (-0.08, 0.42), (0.1, 0.42)]), M["ink"])
    S(G.lumpy_ellipse(0.0, 0.58, 0.04, 0.035, n=10, seed=607), "red", I)              # the finial
    aa = 0.04 * math.sin(ph * 2)                                                        # the antenna, in front
    S(G.hose_outline([(0.26, 0.42), (0.36 + aa, 0.54), (0.44 + aa, 0.6)], 0.022), "iron", I)
    S(G.lumpy_ellipse(0.45 + aa, 0.61, 0.03, 0.03, n=10, seed=608), "red" if hot else "mustard", I)
    if clip != "walk":                                                                  # the hover field under it (drawn rings)
        for i, (z, w) in enumerate(((-0.72, 0.2), (-0.77, 0.13))):                      # (above the 2 px margin with the bob)
            ww = w * (1.0 + 0.15 * math.sin(ph + i))
            G.stroke(d, G.hose_outline([(-ww, z + bob), (0.0, z - 0.02 + bob), (ww, z + bob)], 0.012), M["off"], I, cyclic=True)


def render_frame(clip, k, seed=7):
    gp = fakegp.FakeGP()
    M = PC.mats(gp)
    d = fakegp.FakeDrawing()
    sentinel(d, M, clip, k)
    return GR.render_frame(fakegp.strokes_of(d, gp), FW, FH, PPU, (0.5, 0.5), ss=4, seed=seed)


PROPS = {"sentinel": (None, FW, FH, "idle", sum(n for _c, n, _l in CLIPS), False)}   # do_prop_sheet_set's API


def render_all():
    frames, widths = [], []
    for clip, n, _loop in CLIPS:
        for k in range(n):
            img, w = render_frame(clip, k)
            frames.append(img)
            widths += w
    return {"sentinel": frames}, {"sentinel": widths}


def sheet_meta(frames):
    import numpy as np
    g = v3.GUTTER
    n = len(frames)
    cols = PC.columns_within(FW, FH, n, cap=1024)
    rows = -(-n // cols)
    sheet = np.zeros((rows * FH + (rows - 1) * g, min(cols, n) * FW + (min(cols, n) - 1) * g, 4), np.uint8)
    for i, im in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * (FH + g):r * (FH + g) + FH, c * (FW + g):c * (FW + g) + FW] = im
    anims, s = [], 0
    for clip, m, loop in CLIPS:
        anims.append({"name": clip, "start": s, "length": m, "loop": loop, **({"loop_from": 0} if loop else {})})
        s += m
    meta = {"key": KEY.format("sentinel"), "style": "v3", "frame_width": FW, "frame_height": FH, "columns": cols, "gutter": g,
            "frames": n, "fps": v3.FPS, "pivot": [0.5, 0.5], "facing": "right", "ppu": PPU, "animations": anims, "squash_root": False,
            "hovers": True,
            "note": "B-196: replaces the v2 model (B-043); Sentinel.cs scales the frame width to 1.6 m; idle = patrol, walk = hunt, "
                    "attack = it rings its bell (once); faceless (a barred lantern, a bell)"}
    problems = list(v3.validate_sheet(meta, sheet.shape))
    m = v3.EDGE_MARGIN
    for i, im in enumerate(frames):
        a = im[..., 3]
        if a[:m].any() or a[-m:].any() or a[:, :m].any() or a[:, -m:].any():
            problems.append(f"frame {i} touches the {m} px frame edge")
    hit, off = v3.palette_hits(sheet, "earth")
    if hit < 0.98:
        problems.append(f"palette {hit * 100:.1f}% (off {' '.join(off[:3])})")
    return sheet, meta, problems


V2_SUFFIXES = (".glb", "_normal.png", "_mask.png", "_emission.png")


def export(art, imgs=None, names=None):
    import json
    from meridian import pngio
    if imgs is None:
        imgs, _w = render_all()
    sheet, meta, problems = sheet_meta(imgs["sentinel"])
    if problems:
        raise ValueError("B-196 export checks: " + "; ".join(problems))
    d = os.path.join(art, "creatures", "warden")
    n = pngio.write_png(os.path.join(d, "sentinel_color.png"), sheet)
    with open(os.path.join(d, "sentinel.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    removed = [os.path.join(d, "sentinel" + s) for s in V2_SUFFIXES if os.path.isfile(os.path.join(d, "sentinel" + s))]
    for p in removed:
        os.remove(p)
    return [(meta["key"], sheet.shape[1], sheet.shape[0], n)], {}, removed


def main(out, imgs=None, widths=None, stamp_paths=()):
    """Every frame at 2x on the paper, then the three clips at 1x over the Mars and Mercury skies (the Wardens' planets),
    the surveyor for scale (the sentinel drawn at Sentinel.Size = 1.6 m wide), the checks."""
    import json
    import time
    import numpy as np
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    if imgs is None:
        imgs, widths = render_all()
    frames = imgs["sentinel"]
    ART = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Assets", "_Game", "Art")
    W = max(n for _c, n, _l in CLIPS) * (FW * 2 + 8) + 16                             # the longest clip's 2x row
    rows = []

    def lab(t, h=22):
        r = np.empty((h, W, 3), np.float32)
        r[:] = review.PAPER
        review._label(r, t[:int(W / 6)], 4, 6, scale=1)
        return r
    rows.append(lab("B-196: creatures/warden/sentinel as a v3 sheet (faceless: a barred lantern, a bell; it hovers), replacing the v2 model", 26))
    s = 0
    for clip, n, loop in CLIPS:                                                         # 2x, one row per clip
        r = np.empty((FH * 2 + 30, W, 3), np.float32)
        r[:] = review.PAPER
        review._label(r, f"{clip} {n} ({'loop' if loop else 'once'}) at 2x", 8, 4, scale=1)
        x = 8
        for k in range(n):
            big = np.repeat(np.repeat(frames[s + k], 2, 0), 2, 1)
            r[22:22 + FH * 2, x:x + FW * 2] = np.array(v3.hex_rgb(v3.PALETTES["mars"]["sky"]), np.float32) / 255.0
            review._over(r, big, x, 22)
            x += FW * 2 + 8
        rows.append(r)
        s += n
    try:
        sm = json.load(open(os.path.join(ART, "characters", "surveyor", "side.json"), encoding="utf-8"))
        sv = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png"))[:sm["frame_height"], :sm["frame_width"]]
    except (OSError, KeyError, ValueError):
        sv = None
    for planet in ("mars", "mercury"):                                                 # 1x over the Wardens' planets' skies
        r = np.empty((260, W, 3), np.float32)
        r[:] = np.array(v3.hex_rgb(v3.PALETTES[planet]["sky"]), np.float32) / 255.0
        review._label(r, f"{planet}: idle 0 / walk 0 / every attack frame at 1x (frame width = Sentinel.Size 1.6 m), the surveyor for scale", 8, 4, scale=1)
        x = 40
        ni, nw, na = (n for _c, n, _l in CLIPS)
        for f in [frames[0], frames[ni]] + frames[ni + nw:ni + nw + na]:
            review._over(r, f, x, 60)
            x += FW + 16
        if sv is not None:
            review._over(r, sv, x + 20, 260 - sv.shape[0] - 4)
        rows.append(r)
    lines = []
    ws = (widths or {}).get("sentinel", [])
    o = [w for w in ws if w[0] >= v3.OUTER_SPLIT]
    n_ = [w for w in ws if w[0] < v3.OUTER_SPLIT]
    rng = lambda q: f"{min(w[1] for w in q):.1f}-{max(w[2] for w in q):.1f}" if q else "-"  # noqa: E731
    _sheet, meta, problems = sheet_meta(frames)
    lines.append(f"sentinel: {FW}x{FH} x {len(frames)} ({', '.join(f'{c} {n}' for c, n, _l in CLIPS)}), sheet {_sheet.shape[1]}x{_sheet.shape[0]}, "
                 f"ink {rng(o)} / {rng(n_)} px, palette {v3.palette_hits(_sheet, 'earth')[0] * 100:.1f}%; problems: {'; '.join(problems) or 'none'}")
    for p in stamp_paths:
        lines.append("exported " + review.stamp_text(p))
    foot = np.empty((30 + 16 * len(lines), W, 3), np.float32)
    foot[:] = review.PAPER
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + ("exported" if stamp_paths else "design preview (lock-free, fakegp + numpy)"),
                2, img.shape[0] - 16, (1.0, 1.0, 0.85))
    np.clip(img, 0.0, 1.0, out=img)
    u8 = np.empty(img.shape[:2] + (4,), np.uint8)
    u8[..., :3] = np.rint(img * 255.0)
    u8[..., 3] = 255
    pngio.write_png(out, u8)
    print("written", out, u8.shape[1], "x", u8.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":
    main(sys.argv[1])
    fakegp.restore()
