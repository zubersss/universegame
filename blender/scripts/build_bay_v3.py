"""B-223 (B-201 0.6.0 #11 / #17): the Earth waystation's docking bay in v3 ink, and the catalogue's Camp icon.

DockingBay.cs already stacks backgrounds/waystation/layer0..2 as three full-screen 1920x1080 RawImages (no parallax: the bay is a
screen) with the market panel on the right (x 916-1880, y 48-1032). The v2 keys hold B-0xx's 3D renders (grey cloudy panels, a
photographic starfield): these redraw them under the same keys, so the bay changes with no code change. Drawn at 1920x1080 (the
screen, PPU 64: the docked Pilgrim at its side-view size) so the RawImage shows them unstretched; no json (the v2 files had none;
3-segment keys import as plain textures).

  backgrounds/waystation/layer0   the view out: the painted starfield (backgrounds/space/starfield layer0 + its nebula layer1),
                                  Earth's near disc low in the porthole, Luna above it. Opaque
  backgrounds/waystation/layer1   the bay: a riveted cream wall under a brown ceiling truss and a steel gantry rail, a teal
                                  wainscot with the stencilled HALCYON FREIGHT, blue-grey deck plates; the big brass porthole on the
                                  left, open (alpha 0) onto layer0, a faint glass glare; the Pilgrim (its rig's side plant) docked on
                                  a hazard-striped cradle with two umbilicals to the wall; a crate on the gantry hook; crates behind
                                  the market panel; a BAY 2 plate
  backgrounds/waystation/layer2   the near frame: a brass railing along the bottom, a hanging lamp top-left. Transparent elsewhere
  icons/catalogue/camp            128x128 @ PPU 128 (B-199's item-icon style; the catalogue shows it at 64): the spawn camp as the
                                  game builds it - the landing pad with a crate stack, a lamp post with a red pennant, a grass strip

  python -I build_bay_v3.py <review png>     the lock-free 1080p preview (the market panel outlined), the three layers at 1/4,
                                             the camp icon at 128 / 64 beside its catalogue neighbours
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import pngio, v3  # noqa: E402
import build_ui_v3 as U  # noqa: E402  (installs fakegp; the UI canvas in px, y down, PPU 64)
import build_title_v3 as TT  # noqa: E402  (png / pilgrim / prop_frame from B-221)

G = U.G
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi
ART = TT.ART
W, H = 1920, 1080
CEIL, WAIN, FLOOR = 112, 800, 940                          # the truss's foot, the wainscot's top, the deck's top (px from the top)
PORT = (250, 440, 190, 232)                                # the porthole: centre x, y, the glass opening's radius, the ring's outer
SHIP_X, PAD_TOP = 660, 900                                 # the Pilgrim's centre line, the cradle's deck (its ground point)
MARKET = (916, 48, 1880, 1032)                             # DockingBay's market frame on screen (x0, y0, x1, y1)
KEYS = ["backgrounds/waystation/layer0", "backgrounds/waystation/layer1", "backgrounds/waystation/layer2", "icons/catalogue/camp"]
PAL = TT.PAL
INK = np.array(v3.hex_rgb(v3.INK), np.float32) / 255.0


# ---------------------------------------------------------------- helpers
def R(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def C(cx, cy, r, n=24, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(TAU * i / n), cy + ry * math.sin(TAU * i / n)) for i in range(n)]


def hose(pts, w):
    return G.hose_outline(pts, w)


def line(d, M, pts, r=None):
    G.stroke(d, pts, M["ink"], I if r is None else r)


def draw(w, h, fn, seed=3):
    """fn(d, M) in the canvas's px (y down) -> RGBA uint8 straight alpha."""
    c = U.Canvas(w, h)
    fn(c.dm, c.M)
    return c.render(seed)[0]


def sprite(x0, y0, x1, y1, fn, seed=3):
    """fn(d, M, t) in SCREEN px (t(pts) maps them into the sprite) -> (premultiplied float RGBA, x0, y0)."""
    def g(d, M):
        fn(d, M, lambda pts: [(x - x0, y - y0) for x, y in pts])
    return pre(draw(x1 - x0, y1 - y0, g, seed)), x0, y0


def pre(img):
    """uint8 (or 0..1 float) straight RGBA -> premultiplied float."""
    f = img.astype(np.float32)
    if img.dtype == np.uint8:
        f /= 255.0
    f[..., :3] *= f[..., 3:4]
    return f


def over(dst, src, x, y):
    """Premultiplied src over premultiplied dst at (x, y), clipped."""
    h, w = src.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    dst[y0:y1, x0:x1] = s + dst[y0:y1, x0:x1] * (1 - s[..., 3:4])


def tile(dst, img, y):
    p = pre(img)
    for x in range(0, W, img.shape[1]):
        over(dst, p, x, y)


def to_u8(p, seed, grain=0.035):
    """Premultiplied float -> straight uint8 with the backdrops' paper grain."""
    a = p[..., 3:4]
    rgb = np.where(a > 1e-5, p[..., :3] / np.maximum(a, 1e-5), 0.0)
    u8 = np.clip(np.rint(np.dstack([rgb, a]) * 255), 0, 255).astype(np.uint8)
    return U.paper_grain(u8, seed, grain) if grain else u8


def text_sprite(text, size, fill, seed, tracking=0.12):
    """Limelight lettering, a drawn-ink edge (as the CRUSH band's), premultiplied."""
    tm = U.text_mask(U.LIMELIGHT, text, size, tracking=tracking, wobble=0.5, seed=seed)
    tm = np.pad(tm, 4)
    grow = tm.copy()
    for dy, dx in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        grow = np.maximum(grow, np.roll(np.roll(tm, dy, 0), dx, 1))
    out = np.zeros(tm.shape + (4,), np.float32)
    out[..., :3] = INK * grow[..., None]
    out[..., 3] = grow
    a = tm[..., None]
    out[..., :3] = fill * a + out[..., :3] * (1 - a)
    out[..., 3:4] = a + out[..., 3:4] * (1 - a)
    return out


def fit(img, px):
    """Integer box-downscale a straight float RGBA image until its larger side is <= px (premultiplied mean)."""
    k = 1
    while max(img.shape[:2]) / k > px:
        k += 1
    if k == 1:
        return img
    h, w = img.shape[0] // k * k, img.shape[1] // k * k
    p = pre(img[:h, :w])
    m = p.reshape(h // k, k, w // k, k, 4).mean(axis=(1, 3))
    a = m[..., 3:4]
    m[..., :3] = np.where(a > 1e-5, m[..., :3] / np.maximum(a, 1e-5), 0.0)
    return m


def sheet_frame(rel, i=0):
    """Frame i of an Art sheet by its json (straight float RGBA)."""
    base = os.path.join(ART, *rel.split("/"))
    img = TT.png(*(rel + "_color.png").split("/"))
    if not os.path.isfile(base + ".json"):
        return img
    m = json.load(open(base + ".json", encoding="utf-8"))
    fw, fh = m.get("frame_width"), m.get("frame_height")
    if not fw or not fh or (fw >= img.shape[1] and fh >= img.shape[0]):
        return img
    cols, g = m.get("columns", max(1, img.shape[1] // fw)), m.get("gutter", 0)
    r, c = divmod(i, cols)
    return img[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw]


# ---------------------------------------------------------------- the tiled modules (each 240 px wide, drawn past its sides so
# ---------------------------------------------------------------- no ink falls on the tile seams)
def m_truss(d, M):
    G.stroke(d, R(-10, -10, 250, 122), M["brown_dp"], 0.0, cyclic=True)                       # the dark ceiling
    for x in (0, 120, 240):                                                                    # braces between the girders
        for a, b in (((x, 26), (x + 60, 86)), ((x + 60, 86), (x + 120, 26)), ((x - 60, 86), (x, 26))):
            G.stroke(d, hose([a, b], 11), M["brown"], I, cyclic=True)
    for y0, y1 in ((4, 26), (86, 108)):                                                        # the girders
        G.stroke(d, R(-10, y0, 250, y1), M["brown"], O, cyclic=True)
        G.stroke(d, R(-10, y1 - 6, 250, y1), M["brown_sh"], 0.0, cyclic=True)
        line(d, M, [(-10, y1), (250, y1)], O)
    for x in (0, 60, 120, 180, 240):                                                           # bolts at the joints
        for y in (16, 97):
            G.stroke(d, C(x, y, 5, 12), M["mustard"], I, cyclic=True)


def m_rail(d, M):
    G.stroke(d, R(-10, 2, 250, 22), M["sky"], O, cyclic=True)                                  # the gantry's steel I-beam
    G.stroke(d, R(-10, 14, 250, 22), M["sky_sh"], 0.0, cyclic=True)
    line(d, M, [(-10, 22), (250, 22)], O)
    for x in (30, 150):
        G.stroke(d, C(x, 8, 3, 10), M["sky_dp"], 0.0, cyclic=True)


def m_wall(d, M):
    G.stroke(d, R(-10, -10, 250, 354), M["offwhite_dp"], 0.0, cyclic=True)                    # the seams between plates
    for y0, y1 in ((0, 172), (172, 344)):
        G.stroke(d, R(3, y0 + 3, 237, y1 - 3), M["offwhite"], O, cyclic=True)                 # a riveted cream plate
        G.stroke(d, [(3, y0 + 3), (3, y1 - 3), (237, y1 - 3), (226, y1 - 14), (14, y1 - 14), (14, y0 + 14)], M["offwhite_sh"], 0.0, cyclic=True)
        G.stroke(d, R(3, y0 + 3, 237, y1 - 3), M["ink"], O, cyclic=True)                      # (the shade lower-left: light upper-right)
        for x in range(20, 240, 40):
            for y in (y0 + 10, y1 - 10):
                G.stroke(d, C(x, y, 3, 10), M["brown"], I, cyclic=True)


def m_wainscot(d, M):
    G.stroke(d, R(-10, 14, 250, 150), M["teal_sh"], 0.0, cyclic=True)                         # the teal wainscot
    G.stroke(d, R(-10, 14, 250, 40), M["teal_f"], 0.0, cyclic=True)
    for x in (60, 180):
        line(d, M, [(x, 14), (x, 140)], O)
    for cx in (0, 120, 240):                                                                   # vents
        for y in (74, 90, 106):
            G.stroke(d, R(cx - 28, y - 4, cx + 28, y + 4), M["teal_dp"], 0.0, cyclic=True)
            G.stroke(d, R(cx - 28, y - 4, cx + 28, y + 4), M["ink"], I, cyclic=True)
    G.stroke(d, R(-10, 0, 250, 14), M["mustard"], O, cyclic=True)                              # the brass kick rail


def m_floor(d, M):
    G.stroke(d, R(-10, 0, 250, 150), M["sky_dp"], 0.0, cyclic=True)                           # the deck's front face
    for x in (30, 90, 150, 210):
        line(d, M, [(x, 40), (x, 140)], I)
    G.stroke(d, R(-10, 0, 250, 36), M["sky_sh"], 0.0, cyclic=True)                            # the deck plates' top
    G.stroke(d, R(-10, 0, 250, 7), M["sky_f"], 0.0, cyclic=True)
    for x in (0, 120, 240):
        line(d, M, [(x, 0), (x, 36)], I)
    for row, y in enumerate((14, 26)):                                                         # tread
        for x in range(6 + 12 * row, 240, 24):
            G.stroke(d, [(x - 4, y), (x, y - 2.5), (x + 4, y), (x, y + 2.5)], M["sky_dp"], 0.0, cyclic=True)
    line(d, M, [(-10, 0), (250, 0)], O)
    line(d, M, [(-10, 36), (250, 36)], O)


def m_railing(d, M):
    G.stroke(d, hose([(60, 14), (60, 130)], 12), M["mustard"], O, cyclic=True)                # a post
    G.stroke(d, R(50, 100, 70, 110), M["mustard_sh"], 0.0, cyclic=True)
    for y, w in ((14, 14), (64, 10)):                                                          # the top rail, the mid rail
        G.stroke(d, hose([(-20, y), (260, y)], w), M["mustard"], O, cyclic=True)
        G.stroke(d, hose([(-20, y + w * 0.25), (260, y + w * 0.25)], w * 0.4), M["mustard_sh"], 0.0, cyclic=True)


# ---------------------------------------------------------------- the pieces
def porthole(d, M, t):
    cx, cy, ri, ro = PORT
    G.stroke(d, t(C(cx, cy, ro, 72)), M["mustard"], O, cyclic=True)                           # the brass ring
    a0, a1 = math.radians(70), math.radians(200)                                               # its shade, lower-left
    G.stroke(d, t([(cx + ro * math.cos(a0 + (a1 - a0) * k / 20), cy + ro * math.sin(a0 + (a1 - a0) * k / 20)) for k in range(21)]
                  + [(cx + (ri + 8) * math.cos(a1 - (a1 - a0) * k / 20), cy + (ri + 8) * math.sin(a1 - (a1 - a0) * k / 20)) for k in range(21)]),
             M["mustard_sh"], 0.0, cyclic=True)
    G.stroke(d, t(C(cx, cy, ro, 72)), M["ink"], O, cyclic=True)
    G.stroke(d, t(C(cx, cy, ri + 8, 64)), M["sky"], I, cyclic=True)                           # the steel bezel (the glass is cut later)
    for k in range(12):                                                                        # bolts
        a = TAU * k / 12 + 0.13
        G.stroke(d, t(C(cx + 0.5 * (ro + ri + 8) * math.cos(a), cy + 0.5 * (ro + ri + 8) * math.sin(a), 6, 12)), M["brown"], I, cyclic=True)


def glare(d, M, t):
    cx, cy, ri, _ro = PORT
    for dx, w in ((-60, 34), (10, 14)):                                                        # two glass streaks, upper-right to lower-left
        G.stroke(d, t([(cx + dx + 120, cy - 200), (cx + dx + 120 + w, cy - 200), (cx + dx - 80 + w, cy + 200), (cx + dx - 80, cy + 200)]),
                 M["offwhite_f"], 0.0, cyclic=True)


def cradle(d, M, t):
    x0, x1 = SHIP_X - 220, SHIP_X + 220
    G.stroke(d, t(R(x0 + 10, PAD_TOP + 12, x1 - 10, FLOOR + 2)), M["mustard_f"], 0.0, cyclic=True)   # the hazard band
    x = x0 + 10 + 26
    while x + 12 <= x1 - 10:
        G.stroke(d, t([(x, PAD_TOP + 12), (x + 12, PAD_TOP + 12), (x + 12 - 26, FLOOR + 2), (x - 26, FLOOR + 2)]), M["brown_dp"], 0.0, cyclic=True)
        x += 28
    G.stroke(d, t(R(x0 + 10, PAD_TOP + 12, x1 - 10, FLOOR + 2)), M["ink"], O, cyclic=True)
    G.stroke(d, t(R(x0, PAD_TOP, x1, PAD_TOP + 12)), M["mustard"], O, cyclic=True)             # the deck plate
    for xx in range(x0 + 20, x1 - 10, 50):
        G.stroke(d, t(C(xx, PAD_TOP + 6, 2.5, 8)), M["brown"], I * 0.8, cyclic=True)


def umbilicals(d, M, t):
    for pts, w, tone, wall in ((((446, 660), (480, 700), (520, 724), (552, 714), (572, 700)), 16, "teal", (416, 640, 446, 680)),
                               (((752, 640), (782, 676), (822, 688), (862, 664), (884, 622)), 14, "brown", (872, 590, 896, 624))):
        G.stroke(d, t(R(*wall)), M["mustard"], O, cyclic=True)                                 # the wall socket
        G.stroke(d, t(hose(list(pts), w)), M[tone], O, cyclic=True)                            # the hose
        for (x, y) in (pts[0], pts[-1]):                                                       # brass couplings at both ends
            G.stroke(d, t(C(x, y, w * 0.72, 14)), M["mustard"], I, cyclic=True)


def gantry(d, M, t):
    G.stroke(d, t(C(855, 128, 7, 12)), M["sky"], I, cyclic=True)                               # the trolley's wheels on the rail
    G.stroke(d, t(C(895, 128, 7, 12)), M["sky"], I, cyclic=True)
    G.stroke(d, t(R(842, 132, 908, 160)), M["mustard"], O, cyclic=True)                        # the trolley
    G.stroke(d, t(R(842, 150, 908, 160)), M["mustard_sh"], 0.0, cyclic=True)
    for y in range(166, 292, 12):                                                              # the chain
        G.stroke(d, t(C(875, y, 4, 10, ry=7)), M["ink"], I, cyclic=True)
    G.stroke(d, t(hose([(875, 290), (875, 306), (869, 318), (858, 316)], 8)), M["sky"], I, cyclic=True)   # the hook
    for x in (840, 910):                                                                       # the sling
        G.stroke(d, t(hose([(872, 304), (x, 334)], 4)), M["brown"], I * 0.7, cyclic=True)


def rack(d, M, t):
    x0, x1 = 980, 1160
    for x in (x0, x1):                                                                         # a steel shelf behind the panel
        G.stroke(d, t(hose([(x, FLOOR - 250), (x, FLOOR)], 10)), M["sky"], I, cyclic=True)
    for y in (FLOOR - 250, FLOOR - 124):
        G.stroke(d, t(R(x0 - 8, y, x1 + 8, y + 10)), M["sky"], I, cyclic=True)


def lamp(d, M, t):
    G.stroke(d, t(hose([(130, -10), (130, 82)], 4)), M["brown"], I * 0.6, cyclic=True)         # the cord
    G.stroke(d, t(C(130, 118, 11, 14)), M["offwhite"], I, cyclic=True)                         # the bulb
    G.stroke(d, t([(112, 80), (148, 80), (172, 114), (88, 114)]), M["mustard"], O, cyclic=True)   # the shade
    G.stroke(d, t([(130, 80), (148, 80), (172, 114), (140, 114)]), M["mustard_sh"], 0.0, cyclic=True)
    G.stroke(d, t([(112, 80), (148, 80), (172, 114), (88, 114)]), M["ink"], O, cyclic=True)


# ---------------------------------------------------------------- the layers
def screen(img):
    """A 2048x1024 tileable layer cut to the screen: the top W columns, its first rows repeated under it to reach H."""
    img = img[:, :W]
    if img.shape[0] < H:
        img = np.vstack([img, img[:H - img.shape[0]]])
    return img[:H]


def layer0():
    p = pre(screen(TT.png("backgrounds", "space", "starfield", "layer0_color.png")))
    if os.path.isfile(os.path.join(ART, "backgrounds", "space", "starfield", "layer1_color.png")):
        over(p, pre(screen(TT.png("backgrounds", "space", "starfield", "layer1_color.png"))), 0, 0)   # the nebula
    cx, cy, ri, _ro = PORT
    earth = TT.png("planets", "earth", "disc_near_color.png")                                 # Earth low in the porthole
    over(p, pre(earth), cx + 80 - earth.shape[1] // 2, cy + 230 - earth.shape[0] // 2)
    luna = fit(sheet_frame("planets/earth/luna"), 64)
    over(p, pre(luna), cx - 95 - luna.shape[1] // 2, cy - 105 - luna.shape[0] // 2)
    p[..., 3] = 1.0
    return p


def layer1():
    p = np.zeros((H, W, 4), np.float32)
    tile(p, draw(240, 344, m_wall, 11), CEIL)
    tile(p, draw(240, 344, m_wall, 12), CEIL + 344)
    tile(p, draw(240, 112, m_truss, 13), 0)
    tile(p, draw(240, 24, m_rail, 14), CEIL)
    tile(p, draw(240, 140, m_wainscot, 15), WAIN)
    tile(p, draw(240, 140, m_floor, 16), FLOOR)
    cx, cy, ri, ro = PORT
    over(p, *sprite(cx - ro - 4, cy - ro - 4, cx + ro + 4, cy + ro + 4, porthole, 17))
    yy, xx = np.mgrid[0:H, 0:W]
    glass = (xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2 < ri * ri                              # the porthole open onto layer0
    p[glass] = 0.0
    gl, gx, gy = sprite(cx - ri, cy - ri, cx + ri, cy + ri, glare, 18)
    sub = glass[gy:gy + gl.shape[0], gx:gx + gl.shape[1]]
    gl *= (0.22 * sub)[..., None]
    over(p, gl, gx, gy)
    del yy, xx, glass
    over(p, text_sprite("HALCYON FREIGHT", 36, PAL["offwhite"], 31), 34, WAIN + 18)          # the stencil on the wainscot (above the vents)
    plate, px_, py_ = sprite(30, 700, 200, 766, lambda d, M, t: G.stroke(d, t(R(34, 704, 196, 762)), M["offwhite"], O, cyclic=True), 19)
    over(p, plate, px_, py_)
    bay = text_sprite("BAY 2", 40, PAL["red"], 37)
    over(p, bay, 115 - bay.shape[1] // 2, 733 - bay.shape[0] // 2)
    over(p, *sprite(960, FLOOR - 260, 1180, FLOOR, rack, 20))
    crate = pre(TT.prop_frame("storage_crate"))
    ch, cw = crate.shape[:2]
    for x, y in ((990, FLOOR - ch), (1072, FLOOR - ch), (1030, FLOOR - 124 - ch), (1300, FLOOR - ch), (1380, FLOOR - ch), (1340, FLOOR - 2 * ch + 4)):
        over(p, crate, x, y)
    over(p, *sprite(830, CEIL + 4, 930, 340, gantry, 21))
    over(p, crate, 875 - cw // 2, 334)
    over(p, *sprite(SHIP_X - 230, PAD_TOP - 4, SHIP_X + 230, FLOOR + 6, cradle, 22))
    rocket, (rgx, rgy) = TT.pilgrim()                                                          # the Pilgrim, docked (premultiplied)
    over(p, rocket, SHIP_X - rgx, PAD_TOP - 6 - rgy)                                          # (B-221's offset: the feet on the deck)
    over(p, *sprite(400, 580, 910, 740, umbilicals, 23))
    return p


def layer2():
    p = np.zeros((H, W, 4), np.float32)
    tile(p, draw(240, 120, m_railing, 24), H - 104)
    over(p, *sprite(70, 0, 190, 140, lamp, 25))
    return p


def layers():
    return [to_u8(layer0(), 41), to_u8(layer1(), 42), to_u8(layer2(), 43)]


# ---------------------------------------------------------------- the camp icon (icons, metres: 1 m = 128 px, centre origin)
def camp_icon(d, M):
    import build_icons_items_v3 as IT
    G.stroke(d, hose([(-0.40, -0.36), (0.40, -0.36)], 0.06), M["brown_sh_i"], O, cyclic=True)        # the ground
    G.stroke(d, hose([(-0.42, -0.31), (0.42, -0.31)], 0.06), M["green_i"], O, cyclic=True)           # the grass on it
    for x in (-0.33, 0.03):                                                                            # the pad's legs
        G.stroke(d, hose([(x, -0.27), (x, -0.31)], 0.035), M["brown_i"], I, cyclic=True)
    G.stroke(d, [(-0.39, -0.27), (0.09, -0.27), (0.09, -0.20), (-0.39, -0.20)], M["mustard_i"], O, cyclic=True)   # the landing pad
    for x0, z0, w, h in ((-0.36, -0.20, 0.21, 0.17), (-0.13, -0.20, 0.20, 0.17), (-0.26, -0.03, 0.21, 0.17)):  # the crate stack
        box = [(x0, z0), (x0 + w, z0), (x0 + w, z0 + h), (x0, z0 + h)]
        G.stroke(d, box, M["brown_i"], O, cyclic=True)
        G.stroke(d, [(x0 + 0.04, z0 + h * 0.38), (x0 + w - 0.04, z0 + h * 0.38), (x0 + w - 0.04, z0 + h * 0.62), (x0 + 0.04, z0 + h * 0.62)],
                 M["red_i"], I, cyclic=True)
        for cxx in (x0 + 0.025, x0 + w - 0.025):
            for czz in (z0 + 0.025, z0 + h - 0.025):
                G.stroke(d, IT.lump(cxx, czz, 0.014, 0.014, int((cxx + czz) * 1000) % 97, n=6, jit=0.0), M["mustard_i"], I * 0.6, cyclic=True)
    # the lamp post: a straight post with a box lantern on top. The 18:17 preview at 3x: the hooked arm, the mustard shade and
    # the round white bulb beside it read as a bird's neck, beak and eye (D-101) - no hook, no round bulb
    G.stroke(d, hose([(0.27, -0.31), (0.27, 0.25)], 0.05), M["teal_sh_i"], O, cyclic=True)
    G.stroke(d, [(0.27, 0.17), (0.11, 0.12), (0.27, 0.07)], M["red_i"], I, cyclic=True)              # the pennant
    G.stroke(d, [(0.215, 0.24), (0.325, 0.24), (0.335, 0.355), (0.205, 0.355)], M["mustard_i"], O, cyclic=True)   # the lantern's pane
    G.stroke(d, [(0.19, 0.355), (0.35, 0.355), (0.315, 0.40), (0.225, 0.40)], M["brown_i"], O, cyclic=True)   # its cap (one pane,
    #                                                                                                 no glazing bar: two lit panes
    #                                                                                                 under a dark cap were a pair of eyes)
    G.stroke(d, hose([(0.24, -0.31), (0.30, -0.31)], 0.05), M["brown_i"], I, cyclic=True)             # its foot


def camp():
    import build_rig_tools_v3 as RT
    import build_icons_items_v3 as IT
    return RT.render(camp_icon, IT.SIZE, IT.SIZE, IT.PPU, (0.5, 0.5))[0]


# ---------------------------------------------------------------- export / preview
def export(art):
    out = []
    img = camp()
    m = v3.EDGE_MARGIN
    if img[:m, :, 3].any() or img[-m:, :, 3].any() or img[:, :m, 3].any() or img[:, -m:, 3].any():
        raise ValueError("B-223 checks: icons/catalogue/camp touches the 2 px edge")
    hit = v3.palette_hits(img, "earth")[0]
    if hit < 0.995:
        raise ValueError(f"B-223 checks: icons/catalogue/camp palette {hit * 100:.1f}%")
    for n, u8 in enumerate(layers()):
        p = os.path.join(art, "backgrounds", "waystation", f"layer{n}_color.png")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        out.append((f"backgrounds/waystation/layer{n}", W, H, pngio.write_png(p, u8)))
    base = os.path.join(art, "icons", "catalogue", "camp")
    os.makedirs(os.path.dirname(base), exist_ok=True)
    nb = pngio.write_png(base + "_color.png", img)
    with open(base + ".json", "w", encoding="utf-8", newline="\n") as f:
        json.dump({"key": "icons/catalogue/camp", "style": "v3", "width": 128, "height": 128, "palette": "earth", "ppu": 128, "pivot": [0.5, 0.5],
                   "note": "B-223: the catalogue's Camp (the spawn camp: the landing pad, a crate stack, a lamp post with a pennant)"}, f, indent=2)
        f.write("\n")
    out.append(("icons/catalogue/camp", 128, 128, nb))
    return out


def keys():
    return list(KEYS)


def preview(out, footnote=None):
    import time
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    from build_tool_icons_v3 import shrink
    L = layers()
    comp = np.zeros((H, W, 3), np.float32)
    for u8 in L:                                                                               # stacked as DockingBay draws them
        f = u8.astype(np.float32) / 255.0
        comp = f[..., :3] * f[..., 3:4] + comp * (1 - f[..., 3:4])
    x0, y0, x1, y1 = MARKET                                                                    # the market panel's frame, outlined
    col = np.array([0.85, 0.2, 0.2], np.float32)
    comp[y0:y0 + 3, x0:x1] = col
    comp[y1 - 3:y1, x0:x1] = col
    comp[y0:y1, x0:x0 + 3] = col
    comp[y0:y1, x1 - 3:x1] = col
    review._label(comp, "the market panel (DockingBay) covers this", x0 + 12, y0 + 12, scale=2)
    paper = np.array(review.PAPER, np.float32)
    strip = np.tile(paper, (330, W, 1)).astype(np.float32)
    review._label(strip, "the three layers at 1/4 (layer0 the view out, layer1 the bay with the porthole open, layer2 the near railing and lamp) | icons/catalogue/camp at 128 / 64 beside its catalogue neighbours", 6, 4, scale=1)
    for n, u8 in enumerate(L):
        q = u8.astype(np.float32)[:H // 4 * 4, :W // 4 * 4].reshape(H // 4, 4, W // 4, 4, 4).mean(axis=(1, 3)) / 255.0
        cell = np.tile(paper, (H // 4, W // 4, 1)).astype(np.float32)
        chk = ((np.arange(H // 4)[:, None] // 12 + np.arange(W // 4)[None, :] // 12) % 2)[..., None] * 0.08
        cell = cell - chk                                                                      # a checker shows the transparency
        cell = q[..., :3] * q[..., 3:4] + cell * (1 - q[..., 3:4])
        strip[24:24 + H // 4, 10 + n * (W // 4 + 10):10 + n * (W // 4 + 10) + W // 4] = cell
    icon = camp()
    neigh = [("catalogue/camp", icon)]
    for k in ("iron/base", "copper/base"):
        pth = os.path.join(ART, "icons", *k.split("/")) + "_color.png"
        if os.path.isfile(pth):
            neigh.append((k, pngio.read_png_np(pth)))
    x = 10 + 3 * (W // 4 + 10) + 10
    import build_rig_tools_v3 as RT
    RT._ov(strip, icon, x, 30)
    review._label(strip, "camp 128", x, 164, scale=1)
    x += 140
    for name, im in neigh:
        RT._ov(strip, shrink(im, 64), x, 30)
        review._label(strip, name.split("/")[0], x, 100, scale=1)
        x += 80
    img = np.vstack([np.clip(comp, 0, 1), strip])
    hit = v3.palette_hits(icon, "earth")[0] * 100
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or f"B-223 design preview (lock-free, fakegp + numpy); camp palette {hit:.1f}%"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0], f"camp palette {hit:.1f}%")


if __name__ == "__main__":                       # python -I build_bay_v3.py <review png>
    preview(sys.argv[1])
