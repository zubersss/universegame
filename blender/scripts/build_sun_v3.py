"""Painted Sun disc design (C2 candidate, LEAD cycle 250 while-waiting #4; preview only, never exported here: the Sun
stays a lit spheroid through C1 per the U-103 ruling). numpy only, on build_discs_v3's Disc / finish (watercolour
fill, paper grain, lumpy ink outline at 2.0-3.0 px, interior marks 1.0-1.5 px).

Look (Bible §9.3 planets: character from colour and motion, NO face, D-101): an off-white-to-mustard core in three
lumpy cel rings warming to soft red at the limb, mottled granulation, two drifting sunspot groups (brown umbra,
mustard-deep penumbra), a ring of 1930s flame tongues round the rim (red outer, mustard inner, inked outline),
a soft translucent corona, two prominence loops. Idle 12 frames at 12 fps: the tongues ripple round the rim,
the corona breathes (+-3 %), the spots drift, a prominence rises and falls.

Scale: the space view's Sun is 300 u = 900 px radius at SPACE_PPU 3 (1800 px across before the flames), so a
12-frame sheet cannot fit 2048. Proposal for the export (LEAD decides): a rig like Saturn's rings (disc_rig.json):
  body  sun/disc_color.png  static, painted at 0.5x (R 450 px, 1024^2 incl. a rim margin) and drawn 2x by Unity,
  flames sun/flames_color.png  one ring part (1024^2 at 0.5x) that Unity rotates slowly and pulses (+-3 %),
  corona sun/corona_color.png  a soft wash (512^2, scaled 4x), breathing,
  2 prominence parts on sockets at the limb.
This preview draws everything at a design scale of R = 240 px (the frame strip), and one frame next to the
Earth disc at the space scale ratio.

  python -I build_sun_v3.py <preview dir>
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_discs_v3 as D  # noqa: E402
from meridian import v3  # noqa: E402

PAL = D.PAL
R_DESIGN = 240
FRAMES = 12
TAU = 2 * math.pi


def tongues(theta, phase, n=14, amp=0.16, base=1.07):
    """Flame contour radius (in R) round the rim: n tongues, alternating long and short, rippling with phase."""
    k = np.arange(n)
    r = np.full_like(theta, base)
    for i in k:
        c = TAU * i / n + 0.12 * math.sin(phase + 1.7 * i)
        L = amp * (1.0 if i % 2 == 0 else 0.62) * (1 + 0.18 * math.sin(phase * 2 + 2.3 * i))
        dth = np.angle(np.exp(1j * (theta - c)))
        r = np.maximum(r, base + L * np.clip(1 - np.abs(dth) / (TAU / n * 0.75), 0, 1) ** 1.6
                       * (1 + 0.25 * np.sign(dth) * np.sin(phase + i)))
    return r


def paint_sun(f):
    ph = TAU * f / FRAMES
    d = D.Disc("sun", R_DESIGN, pad=int(R_DESIGN * 0.62), seed=20251)
    n = d.size * D.SS
    rng = np.random.default_rng(777)
    # the core: three lumpy concentric cel rings, off-white -> mustard -> soft red at the limb
    ang = np.arctan2(d.v, d.u)
    wob = 0.025 * np.sin(5 * ang + 0.6 * ph) + 0.015 * np.sin(9 * ang - ph)
    core = D.mix(PAL["offwhite"], PAL["mustard"], 0.35)
    mid = PAL["mustard"]
    limb = D.mix(PAL["mustard"], PAL["red"], 0.55)
    rgb = np.empty(d.u.shape + (3,), np.float32)
    rgb[:] = limb
    rgb[d.r < 0.86 + wob] = mid
    rgb[d.r < 0.52 + wob] = core
    # granulation: mottled mid-tone cells (the mustard's shadow tone) in the mid ring
    gran = D.noise2(rng, n, 6 * D.SS)
    cells = (gran > 1.05) & (d.r > 0.5) & (d.r < 0.84)
    rgb[cells] = D.shade(PAL["mustard"])
    # sunspots drift with the rotation: umbra brown, penumbra mustard deep
    su = D.sphere_u(d, 0.012 * f)
    pen = D.blobs(d, [(0.20, 0.30, 0.085), (0.24, 0.27, 0.05), (0.64, -0.22, 0.065)], su)
    umb = D.blobs(d, [(0.20, 0.30, 0.042), (0.24, 0.27, 0.022), (0.64, -0.22, 0.03)], su)
    rgb[pen & d.inside] = D.mix(PAL["mustard"], PAL["brown"], 0.55)
    rgb[umb & d.inside] = PAL["brown"]
    # flames (behind the body: alpha 0 inside the rim), the corona wash further out, two prominence loops
    c = n / 2
    k = R_DESIGN * D.SS
    outer = tongues(ang, ph)
    inner = 1.0 + 0.55 * (outer - 1.0)
    fl = np.zeros(d.u.shape + (4,), np.float32)
    corona_r = 1.42 * (1 + 0.03 * math.sin(ph))
    halo = np.clip((corona_r - d.r) / 0.12, 0, 1) * (d.r > d.rim)
    fl[..., :3] = D.mix(PAL["offwhite"], PAL["mustard"], 0.3)
    fl[..., 3] = 0.22 * halo
    o_m = (d.r <= outer) & (d.r > d.rim)
    i_m = (d.r <= inner) & (d.r > d.rim)
    fl[o_m, :3] = D.mix(PAL["red"], PAL["mustard"], 0.25)
    fl[o_m, 3] = 1.0
    fl[i_m, :3] = PAL["mustard"]
    for lon_c, h0, w0 in ((0.55 * math.pi + 0.25 * math.sin(ph), 0.22 + 0.06 * math.sin(ph), 0.10), (1.55 * math.pi, 0.15, 0.07)):
        dth = np.angle(np.exp(1j * (ang - lon_c)))
        arc_r = 1.0 + h0 * np.sqrt(np.clip(1 - (dth / w0) ** 2, 0, 1))
        loop = (np.abs(d.r - arc_r) < 0.022) & (np.abs(dth) < w0) & (d.r > d.rim)
        fl[loop, :3] = PAL["red"]
        fl[loop, 3] = 1.0
    # ink: the flame contour, spot rims and convection swirls (interior)
    t = np.linspace(-math.pi, math.pi, 420, endpoint=False)
    ro = tongues(t, ph)
    flame_ink = (np.c_[c + np.cos(t) * ro * k, c - np.sin(t) * ro * k], D.OUT_PX)
    swirls = []
    for i in range(7):
        a0 = TAU * i / 7 + 0.3 + 0.05 * f
        rr = 0.62 + 0.12 * (i % 3) / 2
        s = np.linspace(0, 0.55, 12)
        pts = np.c_[c + np.cos(a0 + s) * (rr + 0.05 * s) * k, c - np.sin(a0 + s) * (rr + 0.05 * s) * k]
        swirls.append((pts, D.IN_PX))
    hatch = []
    for i in range(5):                                        # a few limb hatch strokes (the drawn texture marks)
        a0 = TAU * (i + 0.5) / 5 - 0.4
        p0, p1 = 0.88, 0.95
        hatch.append((np.c_[c + np.cos([a0, a0 + 0.04]) * np.array([p0, p1]) * k, c - np.sin([a0, a0 + 0.04]) * np.array([p0, p1]) * k], D.IN_PX))
    flames = fl.copy()
    flames[d.inside, 3] = 0.0                                 # behind the body
    return D.finish(d, rgb, extra_ink=[flame_ink] + swirls + hatch, extra_rgba=[flames])


def preview(out_dir):
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    from meridian import pngio
    frames = [paint_sun(f) for f in range(FRAMES)]
    fh, fw = frames[0].shape[:2]
    W = 16 + 4 * (fw // 2 + 8)
    rows = []
    head = np.tile(review.PAPER, (30, max(W, 1500), 1)).astype(np.float32)
    review._label(head, "painted sun disc design (c2 candidate, preview only; no face, d-101): 12-frame idle at 12 fps, "
                        f"design scale r {R_DESIGN} px (the game's sun is r 900 px: rig proposal in the script header)", 6, 8)
    rows.append(head)
    # frame 0 at the design scale on the starfield, beside the Earth disc at the true size ratio
    star = os.path.join(review.ART, "backgrounds", "space", "starfield", "layer0_color.png")
    bg = np.zeros((fh + 40, max(W, 1500), 3), np.float32)
    if os.path.isfile(star):
        sf = review._read(star)
        bg[:] = np.tile(sf[..., :3], (-(-bg.shape[0] // sf.shape[0]), -(-bg.shape[1] // sf.shape[1]), 1))[:bg.shape[0], :bg.shape[1]]
    review._over(bg, frames[0], 20, 20)
    try:
        em = pngio.read_png_np(os.path.join(review.ART, "planets", "earth", "disc_color.png"))
        import json
        mj = json.load(open(os.path.join(review.ART, "planets", "earth", "disc.json"), encoding="utf-8"))
        ef = em[:mj.get("frame_height", em.shape[0]), :mj.get("frame_width", em.shape[1])]
        s = R_DESIGN / 900.0                                   # the same shrink as the Sun: true ratio
        idx = (np.arange(int(ef.shape[0] * s)) / s).astype(int), (np.arange(int(ef.shape[1] * s)) / s).astype(int)
        small = ef[idx[0]][:, idx[1]] if len(idx[0]) and len(idx[1]) else ef[:1, :1]
        review._over(bg, small, fw + 60, fh // 2)
        review._label(bg, "earth disc at the same shrink (true size ratio)", fw + 40, fh // 2 - 24, scale=1)
    except Exception:  # noqa: BLE001
        pass
    review._label(bg, "frame 0 on the b-120 starfield", 6, 4)
    rows.append(bg)
    # the 12-frame idle at half size, 4 per row
    for r0 in range(0, FRAMES, 4):
        r = np.tile(review.PAPER, (fh // 2 + 30, max(W, 1500), 1)).astype(np.float32)
        r[:] = (0.13, 0.12, 0.16)
        for j, im in enumerate(frames[r0:r0 + 4]):
            review._over(r, im[::2, ::2], 8 + j * (fw // 2 + 8), 22)
            review._label(r, str(r0 + j), 10 + j * (fw // 2 + 8), 4)
        rows.append(r)
    ws = D.WIDTHS
    outer = [w for w in ws if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in ws if w[0] < v3.OUTER_SPLIT]
    foot = np.tile(review.PAPER, (60, max(W, 1500), 1)).astype(np.float32)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior "
                        f"{min(w[1] for w in inner):.1f}-{max(w[2] for w in inner):.1f} px; frame {fw}x{fh} at the design scale; "
                        "colours: palette + mid / deep tones, corona a translucent off-white wash", 6, 8)
    review._label(foot, "proposal: export as a rig (static body 0.5x + flame ring part + corona wash + 2 prominence sockets), "
                        "unity rotates / pulses the parts (12 hz stepped)", 6, 30)
    rows.append(foot)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " preview (not exported)", 2, img.shape[0] - 16)
    out = os.path.join(out_dir, "review_sun_disc_design_preview.png")
    review.write(out, img)
    print("written", out, f"frame {fw}x{fh}")




# ---------------------------------------------------------------- B-137 (D-123): the Sun as a rig set of parts on one sheet
# The body alone at the game's r 900 px is 1800 px across, so parts are drawn at EXPORT_SCALE (0.5x, Unity draws them 2x)
# with ink at half width (2.5 px on screen after the 2x). The flame ring is ONE tongue part that Unity instances
# RING["count"] times round the rim (alternating sizes, a slow spin, a pulse): the whole ring as one image at 0.5x would
# be ~1220 px and could not share a <= 2048^2 sheet with the 928 px body. The 12-frame spot drift does not fit either,
# so the body is static (the card's "else static").

GAME_R = 900                         # px: SpaceLayout.SunRadius 300 u x SPACE_PPU 3
EXPORT_SCALE = 0.5
RING = {"count": 14, "alt_scale": [1.0, 0.62], "base_r": 0.97, "spin_deg_per_s": 2.0, "pulse": 0.08, "beat_bpm": 110, "stepped_hz": 12}
PROMINENCES = [{"part": "prominence_a", "angle_deg": 100.0}, {"part": "prominence_b", "angle_deg": 280.0}]
CORONA_PX = 512
CORONA_R = 1.42                      # corona radius in sun radii
ORDER = {"corona": 0, "tongue": 1, "prominence_a": 2, "prominence_b": 2, "body": 3}


def body_part(R):
    """The static body at radius R px (no flames, no corona): cel rings, granulation, two spot groups, ink."""
    d = D.Disc("sun", R, pad=max(6, int(R * 0.03)), seed=20251)
    n = d.size * D.SS
    rng = np.random.default_rng(777)
    ang = np.arctan2(d.v, d.u)
    wob = 0.025 * np.sin(5 * ang) + 0.015 * np.sin(9 * ang)
    rgb = np.empty(d.u.shape + (3,), np.float32)
    rgb[:] = D.mix(PAL["mustard"], PAL["red"], 0.55)
    rgb[d.r < 0.86 + wob] = PAL["mustard"]
    rgb[d.r < 0.52 + wob] = D.mix(PAL["offwhite"], PAL["mustard"], 0.35)
    del wob
    gran = D.noise2(rng, n, 6 * D.SS * R / R_DESIGN)
    rgb[(gran > 1.05) & (d.r > 0.5) & (d.r < 0.84)] = D.shade(PAL["mustard"])
    del gran
    su = D.sphere_u(d, 0.0)
    pen = D.blobs(d, [(0.20, 0.30, 0.085), (0.24, 0.27, 0.05), (0.64, -0.22, 0.065)], su)
    rgb[pen & d.inside] = D.mix(PAL["mustard"], PAL["brown"], 0.55)
    del pen
    umb = D.blobs(d, [(0.20, 0.30, 0.042), (0.24, 0.27, 0.022), (0.64, -0.22, 0.03)], su)
    rgb[umb & d.inside] = PAL["brown"]
    del umb, su, ang
    c, k = n / 2, R * D.SS
    marks = []
    for i in range(7):
        a0 = TAU * i / 7 + 0.3
        rr = 0.62 + 0.12 * (i % 3) / 2
        s = np.linspace(0, 0.55, 12)
        marks.append((np.c_[c + np.cos(a0 + s) * (rr + 0.05 * s) * k, c - np.sin(a0 + s) * (rr + 0.05 * s) * k], D.IN_PX))
    for i in range(5):
        a0 = TAU * (i + 0.5) / 5 - 0.4
        marks.append((np.c_[c + np.cos([a0, a0 + 0.04]) * np.array([0.88, 0.95]) * k,
                            c - np.sin([a0, a0 + 0.04]) * np.array([0.88, 0.95]) * k], D.IN_PX))
    return D.finish(d, rgb, extra_ink=marks)


def _poly_part(R, polys, size, pivot_px, ss=2):
    """Rasterise [(points in R units with the origin at pivot_px and y up, rgb, alpha)] + ink on the first outline."""
    W_, H_ = size
    n_w, n_h = W_ * ss, H_ * ss
    acc = np.zeros((n_h, n_w, 4), np.float32)
    yy, xx = np.mgrid[0:n_h, 0:n_w] + 0.5
    for pts, col, alpha in polys:
        px = np.array([pivot_px[0] * ss + x * R * ss for x, _y in pts])
        py = np.array([pivot_px[1] * ss - y * R * ss for _x, y in pts])
        inside = np.zeros((n_h, n_w), bool)
        j = len(px) - 1
        for i in range(len(px)):                                  # even-odd fill
            cond = ((py[i] > yy) != (py[j] > yy)) & (xx < (px[j] - px[i]) * (yy - py[i]) / (py[j] - py[i] + 1e-9) + px[i])
            inside ^= cond
            j = i
        a = inside.astype(np.float32)[..., None] * alpha
        acc[..., :3] = col * a + acc[..., :3] * (1 - a)
        acc[..., 3:] = a + acc[..., 3:] * (1 - a)
    pts = polys[0][0]
    sx = np.array([pivot_px[0] * ss + x * R * ss for x, _y in pts])
    sy = np.array([pivot_px[1] * ss - y * R * ss for _x, y in pts])
    xz = np.c_[sx, -sy] / (ss * 64.0)
    r = D.GR.jittered_radius(xz, np.full(len(sx), D.OUT_PX / 2 / 64.0), 4242 + len(sx), 64.0) * 64.0 * ss
    D.WIDTHS.append((D.OUT_PX, float(r.min()) * 2 / ss, float(r.max()) * 2 / ss))
    m = D.GR._ink_mask(sx, sy, r, True, n_h, n_w).astype(np.float32)[..., None]
    acc[..., :3] = PAL["ink"] * m + acc[..., :3] * (1 - m)
    acc[..., 3:] = m + acc[..., 3:] * (1 - m)
    small = acc.reshape(H_, ss, W_, ss, 4).mean(axis=(1, 3))
    al = small[..., 3:4]
    rgbo = np.where(al > 1e-6, small[..., :3] / np.maximum(al, 1e-6), 0)
    return np.clip(np.rint(np.dstack([rgbo, al]) * 255), 0, 255).astype(np.uint8)


def _bez(p0, p1, p2, n=12):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
            for t in np.linspace(0, 1, n)]


def _size(w, h):
    return w + (-w) % 4, h + (-h) % 4


def tongue_part(R):
    """One flame tongue (red, mustard inside, an off-white core), base on the rim, pointing out (+y); its pivot is
    the base centre, which Unity puts on the rim at RING['base_r']."""
    L, w = 0.22, 0.20                                           # length above the rim, half-width at the base: neighbours overlap into one ring

    def shape(k, ww):
        tip = (0.012 * k, L * k)
        return _bez((-ww, -0.05), (-ww * 1.1, 0.45 * L * k), tip) + _bez(tip, (ww * 1.1, 0.45 * L * k), (ww, -0.05))[1:]
    W_, H_ = _size(int(2 * (w + 0.03) * R) + 8, int((L + 0.09) * R) + 8)
    piv = (W_ / 2, H_ - 4 - 0.05 * R)
    img = _poly_part(R, [(shape(1.0, w), D.mix(PAL["red"], PAL["mustard"], 0.25), 1.0), (shape(0.66, w * 0.62), PAL["mustard"], 1.0),
                         (shape(0.34, w * 0.3), PAL["offwhite"], 1.0)], (W_, H_), piv)
    return img, (0.5, 1 - piv[1] / H_)


def prominence_part(R, h, w):
    """A red loop arching off the limb: base centre on the rim (the pivot), height h, half-span w (R units)."""
    t = 0.045
    outer = [(w * math.cos(a), h * math.sin(a)) for a in np.linspace(0, math.pi, 24)]
    inner = [((w - t) * math.cos(a), max(0.0, h - t) * math.sin(a)) for a in np.linspace(math.pi, 0, 24)]
    W_, H_ = _size(int(2 * (w + 0.03) * R) + 8, int((h + 0.05) * R) + 8)
    piv = (W_ / 2, H_ - 4)
    img = _poly_part(R, [(outer + inner, PAL["red"], 1.0)], (W_, H_), piv)
    return img, (0.5, 4 / H_)


def corona_part(size=CORONA_PX):
    """The corona: a soft translucent off-white / mustard wash with a wavy rim, no ink; Unity scales it to CORONA_R."""
    yy, xx = (np.mgrid[0:size, 0:size] + 0.5 - size / 2) / (size / 2)
    r = np.hypot(xx, yy)
    a = np.arctan2(yy, xx)
    edge = 0.92 + 0.03 * np.sin(7 * a) + 0.02 * np.sin(11 * a + 1.0)        # max 0.97: the wash fades out inside its image
    alpha = 0.24 * np.clip((edge - r) / 0.18, 0, 1)
    rgb = np.broadcast_to(D.mix(PAL["offwhite"], PAL["mustard"], 0.3), (size, size, 3))
    return np.clip(np.rint(np.dstack([rgb, alpha]) * 255), 0, 255).astype(np.uint8), (0.5, 0.5)


def parts(scale=EXPORT_SCALE):
    """{name: (RGBA uint8, pivot [x, y] from the bottom-left)} at `scale` x the game's size; ink drawn at `scale` so it is
    2.5 / 1.25 px on screen once Unity draws the part at 1 / scale... (the export uses EXPORT_SCALE and draw_scale 2)."""
    R = GAME_R * scale
    keep = (D.OUT_PX, D.IN_PX)
    D.OUT_PX, D.IN_PX = 2.5 * scale, 1.25 * scale
    try:
        out = {"body": (body_part(R), (0.5, 0.5)), "tongue": tongue_part(R),
               "prominence_a": prominence_part(R, 0.24, 0.10), "prominence_b": prominence_part(R, 0.16, 0.07),
               "corona": corona_part()}
    finally:
        D.OUT_PX, D.IN_PX = keep
    return out


def pack(ps, gutter=4, cap=2048):
    """Shelf-pack the parts (tallest first) into one sheet <= cap; json rects [x, y, w, h] with a bottom-left origin."""
    order = sorted(ps, key=lambda k: -ps[k][0].shape[0])
    x = y = shelf = 0
    rects = {}
    for k in order:
        h, w = ps[k][0].shape[:2]
        if x + w > cap:
            x, y, shelf = 0, y + shelf + gutter, 0
        rects[k] = (x, y, w, h)
        x += w + gutter
        shelf = max(shelf, h)
    W_, H_ = _size(max(r[0] + r[2] for r in rects.values()), max(r[1] + r[3] for r in rects.values()))
    sheet = np.zeros((H_, W_, 4), np.uint8)
    for k, (rx, ry, w, h) in rects.items():
        sheet[ry:ry + h, rx:rx + w] = ps[k][0]                     # rows from the top here; the json uses bottom-left
    meta = {"key": "planets/sun/disc_rig", "style": "v3", "space_ppu": 3.0, "sheet": "planets/sun/parts", "rect_origin": "bottom_left",
            "export_scale": EXPORT_SCALE, "draw_scale": 1 / EXPORT_SCALE,
            "parts": [{"name": k, "rect": [rects[k][0], H_ - rects[k][1] - rects[k][3], rects[k][2], rects[k][3]],
                       "pivot": [round(v, 4) for v in ps[k][1]], "order": ORDER[k]} for k in ps],
            "corona": {"part": "corona", "radius_r": CORONA_R, "breathe": 0.03},
            "ring": dict(RING, part="tongue"), "prominences": PROMINENCES,
            "note": "B-137 (D-123): Unity draws every part at draw_scale, instances the tongue round the rim (spin + pulse, "
                    "stepped at 12 Hz), puts each prominence on the rim at its angle and breathes the corona"}
    return sheet, meta


def assemble(ps, scale):
    """The Sun as Unity would draw it (numpy, for the review): corona, tongues round the rim, prominences, body."""
    import review
    R = GAME_R * scale
    S_ = int(2 * CORONA_R * R) + 16
    can = np.zeros((S_, S_, 4), np.float32)
    c = S_ / 2

    def over(img, x, y):
        f = img.astype(np.float32) / 255
        h, w = f.shape[:2]
        x0, y0 = int(round(x)), int(round(y))
        xs, ys, xe, ye = max(0, x0), max(0, y0), min(S_, x0 + w), min(S_, y0 + h)
        if xe <= xs or ye <= ys:
            return
        f = f[ys - y0:ye - y0, xs - x0:xe - x0]
        a = f[..., 3:4]
        can[ys:ye, xs:xe, :3] = f[..., :3] * a + can[ys:ye, xs:xe, :3] * (1 - a)
        can[ys:ye, xs:xe, 3:] = a + can[ys:ye, xs:xe, 3:] * (1 - a)

    def resize(img, s):
        iy = (np.arange(max(1, int(img.shape[0] * s))) / s).astype(int).clip(0, img.shape[0] - 1)
        ix = (np.arange(max(1, int(img.shape[1] * s))) / s).astype(int).clip(0, img.shape[1] - 1)
        return img[iy][:, ix]
    cor = ps["corona"][0]
    k = 2 * CORONA_R * R
    over(resize(cor, k / cor.shape[0]), c - k / 2, c - k / 2)
    tg, tp = ps["tongue"]
    for i in range(RING["count"]):
        deg = 360.0 * i / RING["count"]
        t = resize(tg, RING["alt_scale"][i % 2])
        a = math.radians(deg)
        rot = review.rotate_about(t, deg, (tp[0] * t.shape[1], t.shape[0] * (1 - tp[1])))
        bx, by = c + RING["base_r"] * R * math.sin(a), c - RING["base_r"] * R * math.cos(a)
        over(rot, bx - rot.shape[1] / 2, by - rot.shape[0] / 2)
    for pr in PROMINENCES:
        img, pv = ps[pr["part"]]
        a = math.radians(pr["angle_deg"])
        rot = review.rotate_about(img, pr["angle_deg"], (pv[0] * img.shape[1], img.shape[0] * (1 - pv[1])))
        over(rot, c + R * math.sin(a) - rot.shape[1] / 2, c - R * math.cos(a) - rot.shape[0] / 2)
    body = ps["body"][0]
    over(body, c - body.shape[1] / 2, c - body.shape[0] / 2)
    al = can[..., 3:4]
    can[..., :3] = np.where(al > 1e-6, can[..., :3] / np.maximum(al, 1e-6), 0)   # premultiplied -> straight for review._over
    return np.clip(np.rint(can * 255), 0, 255).astype(np.uint8)


def parts_preview(out_dir, scale=0.18):
    """Lock-free B-137 parts preview at a reduced scale (the export runs at EXPORT_SCALE in a slot): the assembled Sun
    on the B-120 starfield beside the Earth disc at the same scale, each part on a checker, the sheet size at export."""
    import json
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    from meridian import pngio
    D.WIDTHS.clear()
    ps = parts(scale)
    sheet, meta = pack(ps)
    sun = assemble(ps, scale)
    m = v3.EDGE_MARGIN
    edge = {k: [e for e, v in (("top", im[:m, :, 3].max()), ("bottom", im[-m:, :, 3].max()), ("left", im[:, :m, 3].max()),
                               ("right", im[:, -m:, 3].max())) if v > 0] for k, (im, _p) in ps.items() if k != "corona"}
    at_export = {k: (int(ps[k][0].shape[1] / scale * EXPORT_SCALE), int(ps[k][0].shape[0] / scale * EXPORT_SCALE)) for k in ps if k != "corona"}
    at_export["corona"] = (CORONA_PX, CORONA_PX)
    W = max(1600, sun.shape[1] + 420)
    rows = []
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, f"b-137 sun rig parts (d-123), preview at {scale}x the game's size (export {EXPORT_SCALE}x, drawn 2x): body, one flame "
                        f"tongue instanced x{RING['count']}, corona 512^2 wash, two prominences; no face", 6, 8)
    rows.append(head)
    bg = np.zeros((sun.shape[0] + 40, W, 3), np.float32)
    star = os.path.join(review.ART, "backgrounds", "space", "starfield", "layer0_color.png")
    if os.path.isfile(star):
        sf = review._read(star)
        bg[:] = np.tile(sf[..., :3], (-(-bg.shape[0] // sf.shape[0]), -(-bg.shape[1] // sf.shape[1]), 1))[:bg.shape[0], :bg.shape[1]]
    review._over(bg, sun, 20, 20)
    try:
        mj = json.load(open(os.path.join(review.ART, "planets", "earth", "disc.json"), encoding="utf-8"))
        em = pngio.read_png_np(os.path.join(review.ART, "planets", "earth", "disc_color.png"))[:mj["frame_height"], :mj["frame_width"]]
        k = max(2, int(em.shape[0] * scale))
        idx = (np.arange(k) * em.shape[0] / k).astype(int)
        review._over(bg, em[idx][:, idx], sun.shape[1] + 80, sun.shape[0] // 2)
        review._label(bg, "earth disc, same scale", sun.shape[1] + 50, sun.shape[0] // 2 - 22, scale=1)
    except Exception:  # noqa: BLE001
        pass
    review._label(bg, "assembled as unity draws it (corona, 14 tongues alternating 1.0 / 0.62, two prominences, body) on the b-120 starfield", 6, 4)
    rows.append(bg)
    ph = max(im.shape[0] for im, _p in ps.values()) + 40
    pr = np.tile(review.PAPER, (ph, W, 1)).astype(np.float32)
    x = 8
    for kname, (im, _pv) in ps.items():
        if x + im.shape[1] > W:
            break
        chk = ((((np.arange(im.shape[0])[:, None] // 8) + (np.arange(im.shape[1])[None, :] // 8)) % 2) * 0.15 + 0.7)[..., None]
        pr[24:24 + im.shape[0], x:x + im.shape[1]] = chk
        review._over(pr, im, x, 24)
        review._label(pr, f"{kname} {at_export[kname][0]}x{at_export[kname][1]} at export", x, 4, scale=1)
        x += im.shape[1] + 24
    rows.append(pr)
    ow = [w_ for w_ in D.WIDTHS if w_[0] >= 2.0 * scale]
    foot = np.tile(review.PAPER, (70, W, 1)).astype(np.float32)
    dummy = {k: (np.zeros((h, w, 4), np.uint8), (0.5, 0.5)) for k, (w, h) in at_export.items()}
    est = pack(dummy)[0].shape[1::-1]                          # the real export packing (the corona stays 512)
    review._label(foot, f"packed sheet at {EXPORT_SCALE}x ~ {est[0]}x{est[1]} (<= 2048^2; corona stays 512); parts touching their 2 px edge: "
                        + (", ".join(f"{k}: {v}" for k, v in edge.items() if v) or "none"), 6, 8)
    review._label(foot, "ring = one tongue part instanced 14x (one ring image at 0.5x would be ~1220 px and could not share the sheet with "
                        "the 928 px body); the body is static (no room for 12 frames)", 6, 28)
    if ow:
        review._label(foot, f"outline ink at this preview scale {min(w_[1] for w_ in ow):.2f}-{max(w_[2] for w_ in ow):.2f} px "
                            f"(2.0-3.0 on screen at the game's size)", 6, 48)
    rows.append(foot)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " preview (not exported)", 2, img.shape[0] - 16)
    out = os.path.join(out_dir, "review_b137_sun_parts_preview.png")
    review.write(out, img)
    print("written", out, "| sheet at export ~", est, "| parts at export", at_export, "| edges", {k: v for k, v in edge.items() if v} or "clear")




def _upscale(img, k):
    iy = (np.arange(int(img.shape[0] * k)) / k).astype(int).clip(0, img.shape[0] - 1)
    ix = (np.arange(int(img.shape[1] * k)) / k).astype(int).clip(0, img.shape[1] - 1)
    return img[iy][:, ix]


def export(art, review_out):
    """B-137 export (D-123): planets/sun/disc_rig_color.png (the parts on one sheet at EXPORT_SCALE) + disc_rig.json, and
    the stamped review at the game's size (parts drawn at draw_scale as Unity does) on the B-120 starfield beside the
    Earth disc at the true ratio. Raises before writing if a part touches its 2 px edge or the sheet is over 2048."""
    import json
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    from meridian import pngio
    D.WIDTHS.clear()
    ps = parts(EXPORT_SCALE)
    sheet, meta = pack(ps)
    meta["sheet"] = "planets/sun/disc_rig"                      # disc_rig_color.png beside disc_rig.json (the rig-set pairing)
    m = v3.EDGE_MARGIN
    problems = [f"{k} touches its {m} px edge" for k, (im, _p) in ps.items()
                if im[:m, :, 3].any() or im[-m:, :, 3].any() or im[:, :m, 3].any() or im[:, -m:, 3].any()]
    if sheet.shape[0] > v3.MAX_SHEET or sheet.shape[1] > v3.MAX_SHEET:
        problems.append(f"sheet {sheet.shape[1]}x{sheet.shape[0]} over {v3.MAX_SHEET}")
    if problems:
        raise ValueError("B-137: " + "; ".join(problems))
    d = os.path.join(art, "planets", "sun")
    os.makedirs(d, exist_ok=True)
    png = os.path.join(d, "disc_rig_color.png")
    nbytes = pngio.write_png(png, sheet)
    with open(os.path.join(d, "disc_rig.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    ow = [w for w in D.WIDTHS if w[0] >= 1.0]
    iw = [w for w in D.WIDTHS if w[0] < 1.0]
    ink = ((min(w[1] for w in ow) * 2, max(w[2] for w in ow) * 2) if ow else (0, 0),
           (min(w[1] for w in iw) * 2, max(w[2] for w in iw) * 2) if iw else (0, 0))     # on screen (drawn 2x)
    # the review at the game's size: every part drawn 2x (nearest, Unity filters), assembled as Unity does
    big = {k: (_upscale(im, meta["draw_scale"]) if k != "corona" else im, pv) for k, (im, pv) in ps.items()}
    sun = assemble(big, 1.0)
    del big
    W = sun.shape[1] + 420
    bg = np.zeros((sun.shape[0] + 60, W, 3), np.float32)
    star = os.path.join(review.ART, "backgrounds", "space", "starfield", "layer0_color.png")
    if os.path.isfile(star):
        sf = review._read(star)
        bg[:] = np.tile(sf[..., :3], (-(-bg.shape[0] // sf.shape[0]), -(-bg.shape[1] // sf.shape[1]), 1))[:bg.shape[0], :bg.shape[1]]
    review._over(bg, sun, 20, 40)
    del sun
    try:
        mj = json.load(open(os.path.join(review.ART, "planets", "earth", "disc.json"), encoding="utf-8"))
        em = pngio.read_png_np(os.path.join(review.ART, "planets", "earth", "disc_color.png"))[:mj["frame_height"], :mj["frame_width"]]
        review._over(bg, em, W - 300, bg.shape[0] // 2)
        review._label(bg, "earth disc at its game size (true ratio)", W - 400, bg.shape[0] // 2 - 30)
    except Exception:  # noqa: BLE001
        pass
    review._label(bg, f"planets/sun/disc_rig at the game's size (r {GAME_R} px at space_ppu 3): corona, {RING['count']} tongues, two "
                      f"prominences, body; parts exported {EXPORT_SCALE}x, drawn {meta['draw_scale']:g}x", 6, 6)
    review._label(bg, f"sheet {sheet.shape[1]}x{sheet.shape[0]} {nbytes // 1024} kb; parts " +
                  ", ".join(f"{k} {im.shape[1]}x{im.shape[0]}" for k, (im, _p) in ps.items()) +
                  f"; ink on screen outer {ink[0][0]:.1f}-{ink[0][1]:.1f} / interior {ink[1][0]:.1f}-{ink[1][1]:.1f} px; no face (d-101)", 6, 26)
    review.stamp(bg, png, review.stale_keys())
    review.write(review_out, bg)
    return {"sheet": sheet.shape[1::-1], "bytes": nbytes, "parts": {k: im.shape[1::-1] for k, (im, _p) in ps.items()}, "ink": ink}


if __name__ == "__main__":
    if "--parts" in sys.argv:            # B-137: python -I build_sun_v3.py <dir> --parts [scale]
        rest = [a for a in sys.argv[2:] if a != "--parts"]
        parts_preview(sys.argv[1], float(rest[0]) if rest else 0.18)
    else:
        if len(sys.argv) > 2:            # a smaller design scale for low-memory runs (default 240)
            R_DESIGN = int(sys.argv[2])
        preview(sys.argv[1])
