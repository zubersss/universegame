"""B-209 (D-178): the space minimap's and the system map's art, paper and ink like the HUD (no glow), Earth palette for the paper
and marks, each planet's own palette for its disc.

  ui/map/minimap_frame    256x256  the porthole: a brass rim with rivets, an aged-paper degree band, a compass N at the top;
                                   the centre (r < 100 px) transparent for UNITY's marks
  ui/map/minimap_chart    208x208  an optional aged-paper disc for under the marks (faint range rings, a faint cross)
  ui/map/sun              40x40    the Sun mark;   ui/map/station 24x24 a Waystation;   ui/map/ship 32x32 the ship's heading
                                   arrow (points up = rotation 0);   ui/map/rim_arrow 24x24 (points up: rotate to the bearing);
                                   ui/map/landed 20x20 the landed tick
  ui/map/well_dash        32x8     a dash tile (tile_x) for the Gravity Wells' dashed rings;   ui/map/orbit_dot 16x4 the orbits'
  ui/map/name_tag         64x24    slice 8 8 8 8: the HUD's paper tag, lettered at runtime
  ui/map/planet_<name>    32x32    the eight planets' map discs from planets/<p>/disc frame 0 (area-resampled, snapped to the
                                   planet's palette); Saturn 48x32 with its ring; ui/map/planet_luna 20x20
  ui/map/system_panel     256x256  slice 80: the system map's paper chart (B-208's flat paper; tile ui/panels/grain over it)
  ui/map/title_cartouche  384x80   the inked "THE SOLAR SYSTEM" cartouche (a scroll), baked lettering

  python -I build_map_v3.py <review png>     the mock-up: the minimap at 1x over a space frame, the system map at 1080p
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_ui_v3 as U  # noqa: E402
import build_skilltree_v3 as ST  # noqa: E402
from meridian import v3  # noqa: E402

G, O, I = U.G, U.O, U.I
TAU = 2 * math.pi
circ, arc, extra, done, ov = ST.circ, ST.arc, ST.extra, ST.done, ST.ov
ART = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Assets", "_Game", "Art")
PLANETS = ("mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune")
NAMES = {"mercury": "Mercury", "venus": "Venus", "earth": "Earth", "mars": "Mars", "jupiter": "Jupiter", "saturn": "Saturn",
         "uranus": "Uranus", "neptune": "Neptune", "luna": "Moon"}
INK = np.array(v3.hex_rgb(v3.INK), np.float32) / 255.0


def letter(img_u8, text, cx, cy, size, font, col=None):
    """Ink lettering composited into an RGBA uint8 sprite (centred at cx, cy px)."""
    m = U.text_mask(font, text, size, wobble=0.2, seed=3)
    h, w = m.shape
    x, y = int(round(cx - w / 2)), int(round(cy - h / 2))
    c = np.array(v3.hex_rgb(col or v3.INK), np.float32)
    sub = img_u8[y:y + h, x:x + w].astype(np.float32)
    a = m[..., None]
    sub[..., :3] = c * a + sub[..., :3] * (1 - a)
    sub[..., 3:4] = np.maximum(sub[..., 3:4], a * 255)
    img_u8[y:y + h, x:x + w] = np.rint(sub).astype(np.uint8)
    return img_u8


# ---------------------------------------------------------------- the minimap frame + chart
def minimap_frame(seed=300):
    S = 256
    c = U.Canvas(S, S)
    d, M = c.dm, extra(c)
    cx = cy = S / 2
    ring = circ(cx, cy, 124, 120) + list(reversed(circ(cx, cy, 100, 100)))
    G.stroke(d, circ(cx, cy, 124, 120), M["mustard"], O, cyclic=True)                       # the brass rim
    G.stroke(d, circ(cx, cy, 113, 110), M["offwhite_sh"], 0.0, cyclic=True)                   # the aged degree band
    G.stroke(d, circ(cx, cy, 113, 110), M["ink"], I, cyclic=True)
    for k in range(36):
        a = TAU * k / 36
        r0 = 104 if k % 9 == 0 else 108
        G.stroke(d, [(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + 113 * math.cos(a), cy + 113 * math.sin(a))], M["ink"], I * 0.7)
    for k in range(8):                                                                        # rivets on the brass
        a = TAU * k / 8 + TAU / 16
        G.stroke(d, circ(cx + 118.5 * math.cos(a), cy + 118.5 * math.sin(a), 2.6, 10), M["mustard_sh"], I * 0.7, cyclic=True)
    G.stroke(d, ST.sector(cx, cy, 116, 122, math.radians(200), math.radians(250), 10), M["offwhite_f"], 0.0, cyclic=True)   # sheen
    G.stroke(d, U.wavy_rect(cx - 15, 1 + 5, cx + 15, 29, 0.3, seed), M["offwhite"], I, cyclic=True)   # the N plate
    G.stroke(d, [(cx - 6, 99), (cx + 6, 99), (cx, 90)], M["red"], I, cyclic=True)              # the north pointer, inside
    G.stroke(d, circ(cx, cy, 100, 100), M["ink"], I, cyclic=True)
    img, _w = done(c, seed)
    img = img.copy()
    yy, xx = np.mgrid[0:S, 0:S]
    img[((xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2) < 99.0 ** 2] = 0                      # the clear centre
    return letter(img, "N", cx, 17, 22, U.LIMELIGHT)


def minimap_chart(seed=310):
    S = 208
    c = U.Canvas(S, S)
    d, M = c.dm, extra(c)
    cx = cy = S / 2
    G.stroke(d, circ(cx, cy, 102, 100), M["offwhite_f"], 0.0, cyclic=True)
    for r in (34, 68):
        G.stroke(d, circ(cx, cy, r, 80), M["ln_offwhite"], 0.0, cyclic=True)
        G.stroke(d, G.hose_outline(circ(cx, cy, r, 80) + [circ(cx, cy, r, 80)[0]], 1.2), M["offwhite_sh"], 0.0, cyclic=True)
    for a in (0.0, math.pi / 2):
        G.stroke(d, G.hose_outline([(cx - 100 * math.cos(a), cy - 100 * math.sin(a)), (cx + 100 * math.cos(a), cy + 100 * math.sin(a))], 1.2),
                 M["offwhite_sh"], 0.0, cyclic=True)
    return done(c, seed, 0.0)


# ---------------------------------------------------------------- the marks
def sun_mark(seed=320):
    S = 40
    c = U.Canvas(S, S)
    d, M = c.dm, extra(c)
    cx = cy = S / 2
    for k in range(8):                                                                        # (inside the 2 px margin)
        a = TAU * k / 8
        G.stroke(d, [(cx + 11 * math.cos(a - 0.22), cy + 11 * math.sin(a - 0.22)), (cx + 16 * math.cos(a), cy + 16 * math.sin(a)),
                     (cx + 11 * math.cos(a + 0.22), cy + 11 * math.sin(a + 0.22))], M["mustard"], I, cyclic=True)
    G.stroke(d, circ(cx, cy, 10, 30), M["mustard"], O, cyclic=True)
    G.stroke(d, ST.sector(cx, cy, 6, 8.5, math.radians(200), math.radians(260), 6), M["offwhite_f"], 0.0, cyclic=True)
    return done(c, seed)


def station_mark(seed=330):
    S = 24
    c = U.Canvas(S, S)
    d, M = c.dm, extra(c)
    cx = cy = S / 2
    G.stroke(d, [(cx - 0.8, 5), (cx + 0.8, 5), (cx + 0.8, cy), (cx - 0.8, cy)], M["ink"], I * 0.7, cyclic=True)    # the mast
    for s in (-1, 1):                                                                         # two panels
        G.stroke(d, [(cx + s * 4.5, cy - 3), (cx + s * 8.5, cy - 3), (cx + s * 8.5, cy + 3), (cx + s * 4.5, cy + 3)], M["teal"], I, cyclic=True)
    G.stroke(d, [(cx - 4, cy - 4), (cx + 4, cy - 4), (cx + 4, cy + 4), (cx - 4, cy + 4)], M["sky_sh"], I, cyclic=True)
    G.stroke(d, [(cx - 2, cy + 4), (cx + 2, cy + 4), (cx + 2, cy + 7.5), (cx - 2, cy + 7.5)], M["mustard"], I * 0.8, cyclic=True)
    return done(c, seed)


def ship_arrow(seed=340):
    S = 32
    c = U.Canvas(S, S)
    d, M = c.dm, extra(c)
    cx = cy = S / 2
    G.stroke(d, [(cx, 6), (cx + 9, 26), (cx, 21), (cx - 9, 26)], M["red"], O, cyclic=True)
    G.stroke(d, [(cx, 11), (cx + 3.2, 19), (cx - 3.2, 19)], M["offwhite"], 0.0, cyclic=True)
    return done(c, seed)


def rim_arrow(seed=350):
    S = 24
    c = U.Canvas(S, S)
    d, M = c.dm, extra(c)
    G.stroke(d, [(12, 5.5), (19.5, 19), (12, 15.5), (4.5, 19)], M["mustard"], O, cyclic=True)
    return done(c, seed)


def landed_tick(seed=360):
    S = 20
    c = U.Canvas(S, S)
    d, M = c.dm, extra(c)
    G.stroke(d, G.hose_outline([(5.5, 10), (8.5, 13.5), (14.5, 6)], 3.2), M["green"], I, cyclic=True)
    return done(c, seed)


def well_dash(seed=370):
    c = U.Canvas(32, 8)
    d, M = c.dm, extra(c)
    for x0 in (-26, 6):
        G.stroke(d, G.hose_outline([(x0, 4), (x0 + 16, 4)], 2.6), M["brown_sh"], 0.0, cyclic=True)
    return done(c, seed)


def orbit_dot(seed=380):
    c = U.Canvas(16, 8)
    d, M = c.dm, extra(c)
    G.stroke(d, circ(8, 4, 1.4, 8), M["sky_sh"], 0.0, cyclic=True)
    return done(c, seed)


def name_tag(seed=390):
    W, H = 64, 24
    c = U.Canvas(W, H)
    d, M = c.dm, extra(c)
    body = U.wavy_rect(4, 4, W - 4, H - 4, 0.3, seed)                                       # (inside the 2 px margin)
    G.stroke(d, body, M["offwhite_f"], 0.0, cyclic=True)
    G.stroke(d, [(4, H - 9), (W - 4, H - 9), (W - 4, H - 4), (4, H - 4)], M["offwhite_sh"], 0.0, cyclic=True)
    G.stroke(d, body, M["ink"], I * 1.3, cyclic=True)
    return done(c, seed)


# ---------------------------------------------------------------- the planets' map discs
def _area(img, tw, th):
    """Area resample (premultiplied) of an RGBA uint8 image to tw x th."""
    f = img.astype(np.float32) / 255.0
    f[..., :3] *= f[..., 3:4]
    h, w = f.shape[:2]

    def W(n, t):
        m = np.zeros((t, n), np.float32)
        s = n / t
        for i in range(t):
            a, b = i * s, (i + 1) * s
            for j in range(int(a), min(n, int(math.ceil(b)))):
                m[i, j] = max(0.0, min(b, j + 1) - max(a, j))
            m[i] /= m[i].sum()
        return m
    Wy, Wx = W(h, th), W(w, tw)
    out = np.einsum("ij,jkc,lk->ilc", Wy, f, Wx)
    a = out[..., 3:4]
    out[..., :3] = np.where(a > 1e-4, out[..., :3] / np.maximum(a, 1e-4), 0.0)
    return out


def _snap(f, planet):
    """Snap each pixel's colour to the nearest of the planet's palette tones (+ ink); alpha kept."""
    pal = np.array([v3.hex_rgb(h) for h in v3.palette_with_shadows(planet).values()] + [v3.hex_rgb(v3.INK)], np.float32) / 255.0
    rgb = f[..., :3]
    dist = ((rgb[..., None, :] - pal[None, None, :, :]) ** 2).sum(-1)
    out = np.zeros(f.shape[:2] + (4,), np.uint8)
    out[..., :3] = np.rint(pal[dist.argmin(-1)] * 255)
    out[..., 3] = np.rint(np.clip(f[..., 3], 0, 1) * 255)
    out[out[..., 3] < 24] = 0
    return out


def planet_disc(planet, size=32):
    from meridian import pngio
    import json
    if planet == "luna":
        base, pal = os.path.join(ART, "planets", "earth", "luna"), "earth"
    else:
        base, pal = os.path.join(ART, "planets", planet, "disc"), planet
    meta = json.load(open(base + ".json", encoding="utf-8"))
    sheet = pngio.read_png_np(base + "_color.png")
    fw, fh = meta["frame_width"], meta["frame_height"]
    fr = sheet[:fh, :fw]
    r = meta.get("radius_px", fw / 2 - 4)
    crop = int(math.ceil(r + 2))
    cx, cy = fw // 2, fh // 2
    fr = fr[max(cy - crop, 0):cy + crop, max(cx - crop, 0):cx + crop]
    inner = size - 4                                                                          # the 2 px margin
    disc = _snap(_area(fr, inner, inner), pal)
    W = size + (24 if planet == "saturn" else 0)                                             # Saturn 56 wide: its ring clear of the edge
    out = np.zeros((size, W, 4), np.uint8)
    ox = (W - inner) // 2
    out[2:2 + inner, ox:ox + inner] = disc
    if planet == "saturn":                                                                    # its ring, drawn at map size
        c = U.Canvas(W, size, planet="saturn")                                               # the ring in Saturn's palette
        d, M = c.dm, extra(c)
        ring = [(W / 2 + 22 * math.cos(t), size / 2 + 6 * math.sin(t)) for t in [TAU * i / 40 for i in range(40)]]
        G.stroke(d, G.hose_outline(ring + ring[:1], 3.0), M["mustard_sh"], I * 0.7, cyclic=True)
        ring_img, _w = done(c, 5)
        back = ring_img.copy()
        back[size // 2:] = 0                                                                  # the far half behind the disc
        front = ring_img.copy()
        front[:size // 2] = 0
        res = np.zeros_like(out, dtype=np.float32)
        for layer in (back, out, front):
            a = layer[..., 3:4].astype(np.float32) / 255.0
            res[..., :3] = layer[..., :3] * a + res[..., :3] * (1 - a)
            res[..., 3:4] = np.maximum(res[..., 3:4], layer[..., 3:4])
        out = np.rint(res).astype(np.uint8)
    return out


# ---------------------------------------------------------------- the system map's panel + cartouche
def system_panel(seed=400):
    S, sl = 256, 80
    c = U.Canvas(S, S)
    d, M = c.dm, extra(c)
    outer = U.wavy_rect(6, 6, S - 6, S - 6, 1.0, seed)
    G.stroke(d, outer, M["offwhite_dp"], 0.0, cyclic=True)
    G.stroke(d, U.wavy_rect(12, 12, S - 12, S - 12, 0.8, seed + 1), M["offwhite"], 0.0, cyclic=True)
    for inset, w, mat in ((22, I * 1.3, "ln_brown"), (28, I * 0.8, "ln_mustard_sh")):
        G.stroke(d, U.wavy_rect(inset, inset, S - inset, S - inset, 0.3, seed + inset), M[mat], w, cyclic=True)
    cx, cy = 52, S - 52                                                                       # a small compass rose, bottom-left
    for k in (1, 3, 5, 7, 0, 2, 4, 6):
        a = -TAU / 4 + TAU * k / 8
        L, w = (20, 4.5) if k % 2 == 0 else (12, 3)
        tip = (cx + L * math.cos(a), cy + L * math.sin(a))
        lf = (cx + w * math.cos(a - TAU / 4), cy + w * math.sin(a - TAU / 4))
        rt = (cx + w * math.cos(a + TAU / 4), cy + w * math.sin(a + TAU / 4))
        G.stroke(d, [(cx, cy), lf, tip], M["mustard_sh" if k else "red_sh"], 0.0, cyclic=True)
        G.stroke(d, [(cx, cy), tip, rt], M["mustard_f" if k else "red_f"], 0.0, cyclic=True)
        G.stroke(d, [(cx, cy), lf, tip, rt], M["ink"], I * 0.8, cyclic=True)
    for k in range(3):                                                                        # a star-chart flourish, top-right
        a0 = math.radians(95 + 25 * k)
        G.stroke(d, arc(S - 36, 36, 18 + 8 * k, a0, a0 + 0.9, 10), M["ln_brown"], I * 0.8)
    G.stroke(d, outer, M["ink"], O, cyclic=True)
    img, w = done(c, seed)
    return img, w, [sl] * 4


def title_cartouche(seed=410):
    W, H = 384, 80
    c = U.Canvas(W, H)
    d, M = c.dm, extra(c)
    G.stroke(d, U.wavy_rect(30, 12, W - 30, H - 12, 0.6, seed), M["offwhite"], O, cyclic=True)
    G.stroke(d, U.wavy_rect(30, H - 22, W - 30, H - 12, 0.4, seed + 1), M["offwhite_sh"], 0.0, cyclic=True)
    for side in (0, 1):                                                                       # the rolled ends
        x0, x1 = (8, 34) if side == 0 else (W - 34, W - 8)
        roll = U.wavy_rect(x0, 6, x1, H - 6, 0.3, seed + 2 + side)
        G.stroke(d, roll, M["mustard"], O, cyclic=True)
        G.stroke(d, U.wavy_rect(x0 + (x1 - x0) * 0.6, 8, x1 - 2, H - 8, 0.2, seed + 4 + side), M["mustard_sh"], 0.0, cyclic=True)
        G.stroke(d, roll, M["ink"], O, cyclic=True)
    G.stroke(d, U.wavy_rect(40, 18, W - 40, H - 18, 0.3, seed + 6), M["ln_brown"], I * 0.8, cyclic=True)
    img, _w = done(c, seed)
    return letter(img.copy(), "THE SOLAR SYSTEM", W / 2, H / 2 - 1, 30, U.LIMELIGHT)


# ---------------------------------------------------------------- the export (on LEAD's OK)
def kit():
    out = [("minimap_frame", minimap_frame(), {"clear_radius_px": 99, "note": "the porthole: the centre (r < 99 px) is clear for UNITY's marks; N up"}),
           ("minimap_chart", minimap_chart()[0], {"note": "optional paper disc under the marks (208 px, centred under the frame)"}),
           ("sun", sun_mark()[0], {}), ("station", station_mark()[0], {"note": "a Waystation"}),
           ("ship", ship_arrow()[0], {"note": "points up at rotation 0: rotate to the ship's heading"}),
           ("rim_arrow", rim_arrow()[0], {"note": "points up (outward) at rotation 0: rotate to the bearing; the distance on a name_tag beside it"}),
           ("landed", landed_tick()[0], {"note": "on the tag's top-right corner of a planet you have landed on"}),
           ("well_dash", well_dash()[0], {"tile_x": True, "repeat_px": 32, "note": "tiled along a Gravity Well's circle (a LineRenderer / UI line)"}),
           ("orbit_dot", orbit_dot()[0], {"tile_x": True, "repeat_px": 16, "note": "tiled along an orbit, faint"}),
           ("name_tag", name_tag()[0], {"slice": [8, 8, 8, 8], "lettering": "runtime", "note": "the HUD's paper tag; Patrick Hand, ink"})]
    for p in list(PLANETS) + ["luna"]:
        out.append((f"planet_{p}", planet_disc(p, 20 if p == "luna" else 32), {"planet": p, "palette": "earth" if p == "luna" else p,
                                                                             "note": "the map disc (from its disc frame 0, snapped to its palette)"}))
    pan, _w, sl = system_panel()
    out.append(("system_panel", pan, {"slice": list(sl), "grain": U.GRAIN_KEY, "note": "the system map's paper (B-208 flat paper: tile the grain over it)"}))
    out.append(("title_cartouche", title_cartouche(), {"lettering": "baked", "note": "top-centre of the system map"}))
    return out


def export(art):
    import json
    from meridian import pngio
    built, problems = [], []
    for name, img, extra_meta in kit():
        h, w = img.shape[:2]
        pal = extra_meta.get("palette", "earth")
        meta = {"key": f"ui/map/{name}", "style": "v3", "ppu": U.PPU, "pivot": [0.5, 0.5], "width": w, "height": h, "palette": pal, **extra_meta}
        hit = v3.palette_hits(img, pal)[0]
        m = v3.EDGE_MARGIN
        tile = name in ("well_dash", "orbit_dot")
        if w % 4 or h % 4:
            problems.append(f"{name}: {w}x{h} not a multiple of 4")
        if hit < 0.995:
            problems.append(f"{name}: palette {hit * 100:.1f}%")
        if name != "system_panel" and (img[:m, :, 3].any() or img[-m:, :, 3].any() or (not tile and (img[:, :m, 3].any() or img[:, -m:, 3].any()))):
            problems.append(f"{name}: touches the {m} px edge")
        built.append((meta["key"], img, meta))
    if problems:
        raise ValueError("B-209 map kit checks: " + "; ".join(problems))
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
    return [f"ui/map/{n}" for n in ["minimap_frame", "minimap_chart", "sun", "station", "ship", "rim_arrow", "landed", "well_dash", "orbit_dot",
                                    "name_tag"] + [f"planet_{p}" for p in list(PLANETS) + ["luna"]] + ["system_panel", "title_cartouche"]]


# ---------------------------------------------------------------- the mock-up
def preview(out, footnote=None):
    import time
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    frame_, chart = minimap_frame(), minimap_chart()[0]
    sun, st, ship, rim, tick = sun_mark()[0], station_mark()[0], ship_arrow()[0], rim_arrow()[0], landed_tick()[0]
    dash, dot, tag = well_dash()[0], orbit_dot()[0], name_tag()[0]
    discs = {p: planet_disc(p) for p in PLANETS}
    discs["luna"] = planet_disc("luna", 20)
    pan, _w, sl = system_panel()
    cart = title_cartouche()

    def stamp(dst, spr, cx, cy, alpha=1.0):
        ov(dst, spr, int(round(cx - spr.shape[1] / 2)), int(round(cy - spr.shape[0] / 2)), alpha)

    def rot(spr, deg):
        h, w = spr.shape[:2]
        R = int(math.ceil(math.hypot(w, h) / 2)) + 1
        outi = np.zeros((2 * R, 2 * R, 4), np.uint8)
        yy, xx = np.mgrid[0:2 * R, 0:2 * R]
        a = math.radians(deg)
        u = (xx - R) * math.cos(a) + (yy - R) * math.sin(a) + w / 2
        v = -(xx - R) * math.sin(a) + (yy - R) * math.cos(a) + h / 2
        ok = (u >= 0) & (u < w) & (v >= 0) & (v < h)
        outi[ok] = spr[v[ok].astype(int), u[ok].astype(int)]
        return outi

    def tagged(dst, text, cx, cy, ticked=False, size=16, h=24):
        m = U.text_mask(U.PATRICK, text, size, wobble=0.2, seed=4)
        tw = max(40, m.shape[1] + 16)
        t = U.nine_slice(tag, [8, 8, 8, 8], tw, h)
        x, y = int(cx - tw / 2), int(cy)
        ov(dst, t, x, y)
        sub = dst[y + 2:y + 2 + m.shape[0], x + 8:x + 8 + m.shape[1]]
        sub[:] = INK * m[:sub.shape[0], :sub.shape[1], None] + sub * (1 - m[:sub.shape[0], :sub.shape[1], None])
        if ticked:
            ov(dst, tick, x + tw - 8, y - 8)

    def dashed_circle(dst, cx, cy, r):                                                        # rev 19:3x: tangent dashes (rot turns
        n = max(6, int(TAU * r / 32))                                                         # the sprite's +x clockwise on screen)
        for k in range(n):
            a = TAU * k / n
            stamp(dst, rot(dash, math.degrees(a) + 90), cx + r * math.cos(a), cy + r * math.sin(a))

    def dotted_arc(dst, cx, cy, r, a0, a1, step=12, big=False):
        d_ = dot[2:6, 6:10] if not big else np.repeat(np.repeat(dot[2:6, 6:10], 2, 0), 2, 1)
        n = int(abs(a1 - a0) * r / step)
        for k in range(n + 1):
            a = a0 + (a1 - a0) * k / max(n, 1)
            stamp(dst, d_, cx + r * math.cos(a), cy + r * math.sin(a))

    # 1) the minimap at 1x over a space frame (1280x720)
    W1, H1 = 1280, 720
    sp = np.empty((H1, W1, 3), np.float32)
    lay = os.path.join(ART, "backgrounds", "space", "layer0_color.png")
    if os.path.isfile(lay):
        bgi = pngio.read_png_np(lay)
        t = np.tile(bgi, (H1 // bgi.shape[0] + 1, W1 // bgi.shape[1] + 1, 1))[:H1, :W1]
        sp[:] = t[..., :3].astype(np.float32) / 255.0
    else:
        sp[:] = np.array(v3.hex_rgb(v3.PALETTES["neptune"]["brown"]), np.float32) / 255.0
    mx, my = W1 - 24 - 128, 24 + 128                                                          # the minimap, top-right
    stamp(sp, chart, mx, my)
    dotted_arc(sp, mx - 260, my + 40, 236, -0.55, 0.45)                                       # Earth's orbit, the Sun off the left
    dotted_arc(sp, mx - 260, my + 40, 330, -0.38, 0.32)                                       # Mars's orbit
    ex, ey = mx - 10, my - 40
    dashed_circle(sp, ex, ey, 26)                                                             # Earth's Gravity Well
    stamp(sp, discs["earth"], ex, ey)
    stamp(sp, discs["luna"], ex + 22, ey - 20)
    stamp(sp, st, mx - 40, my + 22)
    stamp(sp, discs["mars"], mx + 56, my - 6)
    stamp(sp, rot(ship, 40), mx, my)                                                          # the ship, heading NE
    for bearing in (265, 160):                                                                # rim arrows: the Sun, Venus (from north,
        a = math.radians(bearing - 90)                                                        # clockwise; the arrow points outward)
        stamp(sp, rot(rim, bearing), mx + 91 * math.cos(a), my + 91 * math.sin(a))
    stamp(sp, frame_, mx, my)
    for text, x_, y_, tk in (("Earth", ex, ey + 16, True), ("Moon", ex + 44, ey - 44, False), ("Mars", mx + 56, my + 12, False),
                             ("Waystation", mx - 36, my + 34, False), ("Sun", mx - 62, my + 2, False), ("Venus 41 Mm", mx + 12, my + 56, False)):
        tagged(sp, text, x_, y_, ticked=tk, size=13, h=20)                                    # the minimap's tags: smaller, inside
    # 2) the system map at 1080p
    W2, H2 = 1920, 1080
    sm = np.empty((H2, W2, 3), np.float32)
    sm[:] = np.array([0.18, 0.2, 0.26], np.float32)
    g = U.grain_tile().astype(np.float32) / 255.0
    big = U.nine_slice(pan, sl, W2 - 80, H2 - 80)
    ov(sm, big, 40, 40)
    tt = np.tile(g, ((H2 - 80) // 128 + 1, (W2 - 80) // 128 + 1, 1))[:H2 - 80, :W2 - 80]       # the B-208 grain over it
    a = tt[..., 3:4] * (big[..., 3:4] > 0)
    sm[40:H2 - 40, 40:W2 - 40] = sm[40:H2 - 40, 40:W2 - 40] * (1 - a) + g[0, 0, :3] * a
    stamp(sm, cart, W2 / 2, 110)
    sx, sy = 150, H2 / 2 + 60                                                                 # the Sun at the left
    stamp(sm, np.repeat(np.repeat(sun, 2, 0), 2, 1), sx, sy)
    tagged(sm, "Sun", sx, sy + 44)
    radii = [150, 260, 380, 500, 720, 960, 1250, 1560]
    angs = [-0.85, 0.75, -0.62, 0.55, -0.45, 0.30, -0.3, 0.2]                                # rev 19:3x: spread round their orbits
    for p, r in zip(PLANETS, radii):                                                          # (they bunched in one band)
        lim = min(1.0, math.asin(min(1.0, 430.0 / r)))
        dotted_arc(sm, sx, sy, r, -lim, lim, step=14, big=True)
    for k, (p, r, ang) in enumerate(zip(PLANETS, radii, angs)):
        px_, py_ = sx + r * math.cos(ang), sy + r * math.sin(ang)
        dashed_circle(sm, px_, py_, 30 if p not in ("jupiter", "saturn") else 40)
        stamp(sm, discs[p], px_, py_)
        tagged(sm, NAMES[p], px_, py_ + 26, ticked=p in ("earth", "mars"))
        if p == "earth":
            stamp(sm, discs["luna"], px_ + 22, py_ - 20)
            stamp(sm, rot(ship, 60), px_ + 52, py_ - 44)
            stamp(sm, st, px_ - 30, py_ - 30)
        if p == "mars":
            stamp(sm, st, px_ + 30, py_ - 28)
    head = np.empty((26, W2, 3), np.float32)
    head[:] = review.PAPER
    review._label(head, "B-209 the space minimap at 1x over a space frame (top-right), and the system map at 1080p (paper and ink, no glow)", 6, 6)
    r1 = np.empty((H1, W2, 3), np.float32)
    r1[:] = review.PAPER
    r1[:, :W1] = sp
    sprites = [("minimap_frame", frame_), ("minimap_chart", chart), ("sun", sun), ("station", st), ("ship", ship), ("rim_arrow", rim),
               ("landed", tick), ("well_dash", dash), ("orbit_dot", dot), ("name_tag", tag), ("title_cartouche", cart)] + \
              [(f"planet_{p}", discs[p]) for p in list(PLANETS) + ["luna"]] + [("system_panel", pan)]
    x, y = W1 + 20, 10
    for name, s in sprites:
        if name in ("minimap_frame", "minimap_chart", "title_cartouche", "system_panel"):
            continue
        s2 = np.repeat(np.repeat(s, 2, 0), 2, 1)
        if x + s2.shape[1] > W2 - 10:
            x, y = W1 + 20, y + 110
        ov(r1, s2, x, y + 14)
        review._label(r1, name, x, y, scale=1)
        x += s2.shape[1] + 14
    lines = []
    for name, s in sprites:
        hit = v3.palette_hits(s, name[7:] if name.startswith("planet_") and name != "planet_luna" else "earth")[0] * 100
        m = v3.EDGE_MARGIN
        tile = name in ("well_dash", "orbit_dot")
        edge = name != "system_panel" and (s[:m, :, 3].any() or s[-m:, :, 3].any() or (not tile and (s[:, :m, 3].any() or s[:, -m:, 3].any())))
        lines.append(f"ui/map/{name}: {s.shape[1]}x{s.shape[0]}, palette {hit:.1f}%" + ("; EDGE" if edge else ""))
    foot = np.empty((24 + 16 * ((len(lines) + 2) // 3), W2, 3), np.float32)
    foot[:] = review.PAPER
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6 + (i % 3) * 640, 6 + 16 * (i // 3), scale=1)
    img = np.vstack([head, r1, sm, foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_map_v3.py <review png>
    preview(sys.argv[1])
