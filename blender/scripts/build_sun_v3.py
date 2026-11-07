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


if __name__ == "__main__":
    if len(sys.argv) > 2:                # a smaller design scale for low-memory runs (default 240)
        R_DESIGN = int(sys.argv[2])
    preview(sys.argv[1])
