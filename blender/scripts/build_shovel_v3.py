"""B-226 (D-182, THE OWNER: the first digging tool is a shovel; the Beam an early unlock): the shovel, its flick, its icon. v3 ink.

  props/rig/shovel        192x64 @ PPU 128 (1.5 x 0.5 m), pivot at the D-grip (the hand): a sturdy field shovel - a brass D-grip,
                          a teal-painted haft (~0.85 m) with a brass ferrule, a steel round-point blade (~0.37 m) on a teal socket, its
                          step shoulders and a dirt smear; json grip [0, 0], blade_tip and the dig point (muzzle) in metres from the grip
  fx/shovel_flick/base    6 frames 128x128 @ PPU 64 (2 m), pivot [0.5, 0.25] (the dig point, as dig_puff), clip 'flick' (once): a short
                          lift of crumbs off the blade, up and back (-x when facing right); B-238: its big clod is gone (B-232's
                          clods are the debris). Cream + ink: UNITY tints it by the dug cell's tier tone, as the dust
  icons/tools/shovel      128x128 @ PPU 128: the shovel on a diagonal, for the HUD tool slot and the tree (B-199's item-icon style)

  python -I build_shovel_v3.py <review png>     the lock-free sheet: the shovel in the surveyor's hand at three scoop angles beside
                                                Beam Mk1, the flick on Earth and Mars ground, the icon beside its neighbours
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_rig_tools_v3 as RT  # noqa: E402  (installs fakegp; the tool render + the icon materials)
import build_icons_items_v3 as IT  # noqa: E402
from meridian import v3  # noqa: E402

G = RT.G
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi
ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))
SW, SH_, SPPU = 192, 64, 128
SPIV = (0.10 / 1.5, 0.5)                                    # the grip 0.10 m in from the frame's left
GRIP, TIP, DIG = (0.0, 0.0), (1.33, 0.0), (1.24, 0.0)       # metres from the grip, the shovel along +x


def hose(pts, w):
    return G.hose_outline(pts, w)


def shovel(scale=1.0, ox=0.0, oz=0.0, rot=0.0, bold=1.0):
    """The shovel along +x from its grip (scale / offset / rotation / bold for the icon). rev (11:15 sheet): a thicker haft, a
    heavier D-grip and a broader blade - the first one read as a thin stick with a small dark head."""
    ca, sa = math.cos(rot), math.sin(rot)

    def T(pts):
        return [(ox + scale * (x * ca - z * sa), oz + scale * (x * sa + z * ca)) for x, z in pts]

    def fn(d, M):
        dg = [(-0.035, -0.085), (-0.035, 0.085)] + [(0.045 + 0.085 * math.cos(a), 0.085 * math.sin(a)) for a in np.linspace(math.pi / 2, -math.pi / 2, 9)]
        G.stroke(d, T(hose(dg + [dg[0]], 0.03 * bold)), M["mustard_i"], I, cyclic=True)     # the brass D-grip (the hand on its bar)
        G.stroke(d, T(hose([(0.13, 0.0), (0.88, 0.0)], 0.052 * bold)), M["teal_i"], I, cyclic=True)   # the teal haft
        G.stroke(d, T([(0.2, 0.012 * bold), (0.8, 0.012 * bold)]), M["teal_sh"], I * 0.8)     # its shade line
        G.stroke(d, T([(0.83, -0.035 * bold), (0.90, -0.035 * bold), (0.90, 0.035 * bold), (0.83, 0.035 * bold)]), M["mustard_i"], I, cyclic=True)   # ferrule
        G.stroke(d, T([(0.90, -0.04), (0.97, -0.055), (0.97, 0.055), (0.90, 0.04)]), M["teal_sh_i"], I, cyclic=True)    # the socket
        blade = [(0.97, -0.13), (1.04, -0.145), (1.14, -0.14), (1.25, -0.10), (1.33, 0.0), (1.25, 0.10), (1.14, 0.14), (1.04, 0.145),
                 (0.97, 0.13)]
        G.stroke(d, T(blade), M["sky_sh_i"], O, cyclic=True)                                 # the steel round-point blade
        G.stroke(d, T([(0.97, 0.13), (1.04, 0.145), (1.14, 0.14), (1.22, 0.11), (1.04, 0.10)]), M["sky"], 0.0, cyclic=True)   # a lit edge
        G.stroke(d, T(blade), M["ink"], O, cyclic=True)
        G.seam(d, T([(0.98, 0.0), (1.27, 0.0)]), M["ink"])                                  # the centre rib
        G.stroke(d, T([(0.97, -0.13), (1.03, -0.13)]), M["ink"], I)                          # the step shoulders
        G.stroke(d, T([(0.97, 0.13), (1.03, 0.13)]), M["ink"], I)
        G.stroke(d, T(IT.lump(1.19, -0.05, 0.065, 0.04, 261, n=9, jit=0.15)), M["brown_sh_i"], I * 0.6, cyclic=True)   # a dirt smear
    return fn


def shovel_icon(d, M):
    """icons/tools/shovel with its own proportion (rev, LEAD 11:2x: the scaled prop stayed a thin stick at 48 / 40 px beside the
    chunky icons): a short haft, the blade ~45 % of the icon's height, heavy ink; on the diagonal, the D-grip top-left."""
    a = math.radians(-50)
    k = 0.92                                                                                 # rev: inside the 2 px margin (the grip
    ux, uz = k * math.cos(a), k * math.sin(a)                                                # touched the top-left edge at 1.0)
    sx, sz = -0.225, 0.271                                                                   # the D-grip's centre: the bbox centred

    def T(pts):
        return [(sx + x * ux - z * uz, sz + x * uz + z * ux) for x, z in pts]
    dg = [(-0.05, -0.10), (-0.05, 0.10)] + [(0.04 + 0.10 * math.cos(t), 0.10 * math.sin(t)) for t in np.linspace(math.pi / 2, -math.pi / 2, 9)]
    G.stroke(d, T(hose(dg + [dg[0]], 0.05)), M["mustard_i"], O, cyclic=True)                # a heavy brass D-grip
    G.stroke(d, T(hose([(0.15, 0.0), (0.42, 0.0)], 0.085)), M["teal_i"], O, cyclic=True)    # a short, thick teal haft
    G.stroke(d, T([(0.40, -0.06), (0.47, -0.06), (0.47, 0.06), (0.40, 0.06)]), M["mustard_i"], O, cyclic=True)   # the ferrule
    blade = [(0.47, -0.17), (0.56, -0.19), (0.70, -0.18), (0.84, -0.12), (0.93, 0.0), (0.84, 0.12), (0.70, 0.18), (0.56, 0.19), (0.47, 0.17)]
    G.stroke(d, T(blade), M["sky_sh_i"], O, cyclic=True)                                     # the blade: ~0.46 m on its long side
    G.stroke(d, T([(0.48, 0.16), (0.56, 0.18), (0.70, 0.17), (0.80, 0.12), (0.56, 0.11)]), M["sky"], 0.0, cyclic=True)
    G.stroke(d, T(blade), M["ink"], O * 1.25, cyclic=True)
    G.seam(d, T([(0.49, 0.0), (0.86, 0.0)]), M["ink"])
    G.stroke(d, T(IT.lump(0.74, -0.07, 0.07, 0.045, 262, n=9, jit=0.15)), M["brown_sh_i"], I, cyclic=True)        # dirt on the blade


# ---------------------------------------------------------------- the flick (cream + ink: UNITY tints it per ground)
def flick_frame(k, seed=1500):
    import build_ui_v3 as U
    import build_skilltree_v3 as ST
    c = U.Canvas(128, 128)
    d, M = c.dm, ST.extra(c)
    px, py = 64, 96                                                                          # the dig point (pivot 0.5, 0.25)
    rng = np.random.default_rng(seed)
    # B-238 (D-183, LEAD 16:5x; B-226's flick reopened on the owner's playtest): the big clod and the "ground lifting" oval
    # are gone - B-232's clods are the debris now, and the oval read as a brown plate (B-228 F1b). What stays is a short lift
    # of seven crumbs off the blade, up and back (-x), ~0.15 m high and ~0.3 m far, settling by frame 5; every frame holds
    # crumbs (the first was empty but for the oval)
    t = (k + 1) / 6.0
    for j in range(7):
        a = math.radians(rng.uniform(110, 172))
        s = rng.uniform(10, 22)
        x, y = px + s * t * math.cos(a) * 1.1, py - s * t * math.sin(a) * 1.6 + 26 * t * t
        rr = (3.0 - 1.4 * t) * (0.7 + 0.3 * (j % 3))
        G.stroke(d, G.lumpy_ellipse(x, y, rr, rr * 0.85, n=8, lump=0.15, seed=seed + 20 + j), M["offwhite"], I * 0.8, cyclic=True)
    return ST.done(c, seed + k)[0]


# ---------------------------------------------------------------- kit / export
def kit():
    import build_fx_rare_v3 as FR
    tool = RT.render(shovel(), SW, SH_, SPPU, SPIV)[0]
    frames = [flick_frame(k) for k in range(6)]
    sheet, cols = FR.sheet_of(frames)
    icon = RT.render(shovel_icon, IT.SIZE, IT.SIZE, IT.PPU, (0.5, 0.5))[0]                  # rev 2: its own proportion (LEAD 11:2x)
    return [("props/rig/shovel", tool, {"ppu": SPPU, "pivot": [round(SPIV[0], 4), 0.5], "grip": list(GRIP), "blade_tip": list(TIP),
                                         "muzzle": list(DIG), "note": "B-226: the first digging tool, a field shovel (teal and brass, a D-grip); "
                                                                       "pivot = the grip in the hand; muzzle = the dig point on the blade"}, None),
            ("fx/shovel_flick/base", sheet, {"ppu": 64, "frame_width": 128, "frame_height": 128, "columns": cols, "gutter": v3.GUTTER, "frames": 6,
                                             "fps": 12, "pivot": [0.5, 0.25], "facing": "right",
                                             "animations": [{"name": "flick", "start": 0, "length": 6, "loop": False}],
                                             "note": "B-226 / B-238: a short lift of crumbs off the blade, up and back (the big clod is gone: "
                                                     "fx/dig_clods are the debris); cream + ink: tint by the dug cell's tier tone (as the dust); "
                                                     "mirror x when facing left"}, frames),
            ("icons/tools/shovel", icon, {"ppu": IT.PPU, "pivot": [0.5, 0.5], "note": "B-226: the shovel's icon (the HUD tool slot, the tree)"}, None)]


def export(art):
    from meridian import pngio
    built, problems = [], []
    m = v3.EDGE_MARGIN
    for key, img, extra, frames in kit():
        meta = {"key": key, "style": "v3", "width": img.shape[1], "height": img.shape[0], "palette": "earth", **extra}
        hit = v3.palette_hits(img, "earth")[0]
        if hit < 0.995:
            problems.append(f"{key}: palette {hit * 100:.1f}%")
        if img.shape[1] % 4 or img.shape[0] % 4:
            problems.append(f"{key}: {img.shape[1]}x{img.shape[0]} not a multiple of 4")
        for i, f in enumerate(frames or [img]):
            if f[:m, :, 3].any() or f[-m:, :, 3].any() or f[:, :m, 3].any() or f[:, -m:, 3].any():
                problems.append(f"{key} frame {i}: touches the {m} px edge")
        built.append((key, img, meta))
    if problems:
        raise ValueError("B-226 checks: " + "; ".join(problems))
    out = []
    for key, img, meta in built:
        base = os.path.join(art, *key.split("/"))
        os.makedirs(os.path.dirname(base), exist_ok=True)
        n = pngio.write_png(base + "_color.png", img)
        with open(base + ".json", "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((key, img.shape[1], img.shape[0], n))
    return out


def keys():
    return ["props/rig/shovel", "fx/shovel_flick/base", "icons/tools/shovel"]


# ---------------------------------------------------------------- the review sheet
def preview(out, footnote=None):
    import time
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    K = {k: (img, frames) for k, img, _e, frames in kit()}
    side = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png"))
    surv = side[:192, :192]
    pal = {k: np.array(v3.hex_rgb(h), np.float32) / 255.0 for k, h in v3.PALETTES["earth"].items()}
    paper = np.array(review.PAPER, np.float32)
    W = 1560
    rows = []
    head = np.tile(paper, (28, W, 1)).astype(np.float32)
    review._label(head, "B-226 the shovel (the first digging tool): in the hand at three scoop angles beside Beam Mk1; the flick on Earth and Mars ground; the icon", 6, 8)
    rows.append(head)
    HAND = (0.12, 0.95)
    r = np.empty((240, W, 3), np.float32)
    r[:] = pal["sky"]
    r[214:] = pal["green"]
    r[218:] = pal["brown"]
    review._label(r, "1x on the surveyor (the hand at RigToolView.Hand): shovel -55 (into the ground), -20, +30 (lifting) | Beam Mk1 -10", 6, 4, scale=1)
    beam = RT.render(RT.beam_tool(1), RT.TW, RT.TH, RT.TPPU, RT.TPIV)[0]
    for k, (name, aim) in enumerate((("shovel", -55), ("shovel", -20), ("shovel", 30), ("beam_mk1", -10))):
        x0 = 20 + k * 360
        RT._ov(r, surv, x0, 24)
        fx, fz = x0 + 96, 24 + 192
        t = RT._half(K["props/rig/shovel"][0]) if name == "shovel" else RT._half(beam)
        piv = (SW * SPIV[0] / 2, SH_ * 0.5 / 2) if name == "shovel" else (RT.TW * RT.TPIV[0] / 2, RT.TH * RT.TPIV[1] / 2)
        timg, tpiv = RT._rot(t, aim, piv)
        hx, hy = fx + HAND[0] * 64, fz - HAND[1] * 64
        RT._ov(r, timg, int(hx - tpiv[0]), int(hy - tpiv[1]))
        review._label(r, f"{name} {aim:+d}", x0 + 4, 222, scale=1)
    rows.append(r)
    frames = K["fx/shovel_flick/base"][1]
    for planet, tint_key in (("earth", "brown"), ("mars", "red")):                            # the flick, tinted per ground
        rr = np.empty((128 * 2 + 40, W, 3), np.float32)
        rr[:] = paper
        tint = np.array(v3.hex_rgb(v3.PALETTES[planet][tint_key]), np.float32) / 255.0
        tint = 0.5 + 0.5 * tint
        review._label(rr, f"fx/shovel_flick on {planet} (tinted by multiply), 1x frames 0-5 then 2x 1-3", 6, 4, scale=1)
        for i, f in enumerate(frames):
            cell = np.empty((128, 128, 3), np.float32)
            cell[:] = pal["sky"]
            cell[96:] = np.array(v3.hex_rgb(v3.PALETTES[planet]["brown"]), np.float32) / 255.0
            ff = f.astype(np.float32).copy()
            ff[..., :3] *= tint
            RT._ov(cell, ff.astype(np.uint8), 0, 0)
            rr[22:150, 10 + i * 136:138 + i * 136] = cell
        x = 10 + 6 * 136 + 20
        for i in (1, 2, 3):
            f2 = np.repeat(np.repeat(frames[i], 2, 0), 2, 1).astype(np.float32)
            f2[..., :3] *= tint
            cell = np.empty((256, 256, 3), np.float32)
            cell[:] = pal["sky"]
            RT._ov(cell, f2.astype(np.uint8), 0, 0)
            if x + 256 <= W:
                rr[22:278, x:x + 256] = cell
            x += 264
        rows.append(rr)
    ic = np.tile(paper, (190, W, 1)).astype(np.float32)                                       # the icon beside its neighbours
    review._label(ic, "icons/tools/shovel beside icons/nodes/dig_power_1 (the Beam) and two item icons, at 128 / 48 (HUD slot) / 40 (the tree)", 6, 4, scale=1)
    neigh = [("tools/shovel", K["icons/tools/shovel"][0])]
    for k in ("nodes/dig_power_1", "iron/base", "copper/base"):
        p = os.path.join(ART, "icons", *k.split("/")) + "_color.png"
        if os.path.isfile(p):
            neigh.append((k, pngio.read_png_np(p)))
    x = 10
    for name, im in neigh:
        RT._ov(ic, im, x, 24)
        for j, s in enumerate((48, 40)):
            idx = (np.arange(s) * im.shape[0] / s).astype(int)
            RT._ov(ic, im[idx][:, idx], x + 136 + j * 56, 24)
        review._label(ic, name, x, 160, scale=1)
        x += 260
    rows.append(ic)
    lines = []
    m_ = v3.EDGE_MARGIN
    for key, (img, frs) in K.items():
        hit = v3.palette_hits(img, "earth")[0] * 100
        bad = [i for i, f in enumerate(frs or [img]) if f[:m_, :, 3].any() or f[-m_:, :, 3].any() or f[:, :m_, 3].any() or f[:, -m_:, 3].any()]
        lines.append(f"{key}: {img.shape[1]}x{img.shape[0]}, palette {hit:.1f}%" + (f"; EDGE {bad}" if bad else ""))
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "B-226 design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_shovel_v3.py <review png>
    preview(sys.argv[1])
    RT.fakegp.restore()
