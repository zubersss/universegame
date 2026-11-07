"""B-147 (C2 Venus design prep; D-126, D-134): Venus props as v3.1 prop sheets (colour + json only), the build_props_common_v3
/ build_props_mercury_v3 API (PROPS, KEY, render_all, sheet_meta, export, main) so render.py's prop rows can export them.
One prop so far:

  vent_mouth  96x40, 1 static frame: the Vent eel's den, a squat black-basalt vent cone with glassy sheen dabs, a
              sulphur crust on its lee side and a vent-orange glow inside the lip, whose top line is
              build_creatures_venus_v3.VENT_TOP (the eel's peek rises behind it). Nothing is drawn above the top line, so the
              eel is never covered. UNITY draws it IN FRONT of creatures/venus/vent_eel on the same pivot (D-126).

  python -I build_props_venus_v3.py <review png>   lock-free den review: the vent at 3x, the eel's idle + react behind it
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_venus_v3 as CM  # noqa: E402  (gp_draw through fakegp outside Blender)
from meridian import fakegp, v3  # noqa: E402
import gp_raster as GR  # noqa: E402

G = CM.G
P = v3.PALETTES["venus"]
O, I = G.OUTER, G.INNER
PPU = 64
GROUND_PX = 10
KEY = "props/venus/{}"
SHEET_CAP = 512


def SH(h):
    return v3.shadow_of(h, "venus")


def DP(h):
    return v3.deep_of(h, "venus")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, f"venus_prop_{name}", **kw)
    return {"basalt": m("basalt", fill=P["brown"], ink=False), "basalt_sh": m("basalt_mid", fill=DP(P["brown"]), ink=False),
            "sheen": m("sheen", fill=SH(P["offwhite"]), ink=False), "sulphur": m("sulphur", fill=P["mustard"], ink=False),
            "glow": m("glow", fill=P["red"], ink=False), "glow_hot": m("glow_hot", fill=P["mustard"], ink=False),
            "pebble": m("pebble", fill=SH(P["brown"])), "ink": m("ink", fill=None)}


def vent_mouth(d, M, k=0):
    """The den: a basalt cone under the shared top line, the base sunk 0.06 m (no ink along it), the glow inside the lip."""
    top = CM.VENT_TOP
    base = -0.06
    G.stroke(d, top + [(top[-1][0], base), (top[0][0], base)], M["basalt"], 0.0, cyclic=True)
    G.stroke(d, [(0.26, 0.24), (0.42, 0.10), (0.56, 0.0), (0.56, base), (0.20, base), (0.18, 0.12)], M["basalt_sh"], 0.0, cyclic=True)   # the lee side
    G.stroke(d, [(0.30, 0.20), (0.40, 0.11), (0.46, 0.05), (0.36, 0.04), (0.30, 0.10)], M["sulphur"], 0.0, cyclic=True)   # the sulphur crust
    G.stroke(d, [(-0.13, 0.285), (0.13, 0.285), (0.10, 0.235), (-0.10, 0.235)], M["glow"], 0.0, cyclic=True)               # the glow in the lip
    G.stroke(d, [(-0.07, 0.28), (0.07, 0.28), (0.05, 0.255), (-0.05, 0.255)], M["glow_hot"], 0.0, cyclic=True)
    G.seam(d, [(-0.13, 0.235), (0.13, 0.235)], M["ink"])                                  # the lip's lower edge
    for x0, z0, x1, z1 in ((-0.36, 0.17, -0.28, 0.02), (-0.04, 0.22, 0.02, 0.03), (0.22, 0.20, 0.16, 0.02)):   # cooling cracks
        G.seam(d, [(x0, z0), ((x0 + x1) / 2 - 0.01, (z0 + z1) / 2), (x1, z1 + 0.01)], M["ink"])
    for cx, cz, rx, rz in ((-0.30, 0.13, 0.05, 0.012), (-0.12, 0.20, 0.04, 0.01)):        # glassy sheen dabs (the light side)
        G.stroke(d, G.lumpy_ellipse(cx, cz, rx, rz, n=10, lump=0.05, seed=int(abs(cx) * 100) + 50), M["sheen"], 0.0, cyclic=True)
    G.specks(d, [(-0.20, 0.08), (0.08, 0.12), (0.34, 0.06)], M["ink"])
    G.stroke(d, top, M["ink"], O)
    for cx, rx, rz, sd in ((-0.64, 0.04, 0.026, 3), (0.65, 0.035, 0.022, 4)):            # two cinders at the foot
        G.stroke(d, G.lumpy_ellipse(cx, rz * 0.6, rx, rz, n=10, lump=0.08, seed=sd), M["pebble"], I, cyclic=True)


PROPS = {"vent_mouth": (vent_mouth, 96, 40, None, 1, False)}
DEN_FOR = {"vent_mouth": "creatures/venus/vent_eel"}


# ---------------------------------------------------------------- B-168 (D-151): the Venus station props re-inked from the B-147 language
# Frames sized so UNITY's PoiPlacer keeps the station layout: it scales each sprite to the catalog width (frame width = the
# declared width at 64 px/m, so the scale stays 1) and stands a solid deck on `topRow` rows below the frame top (the json's
# top_row: 37 at 64 px/m for the 2.14 m deck surface; v2's 62 was at 128 px/m). Static as the v2 jsons, the door with
# an open 6 like Mercury's. The deck module is four B-153 plank frames (the strip UNITY lays along the deck) on a keel,
# with a continuous railing: modules and railings tile in x (seams steadied, the right column = the left one).
import build_props_common_v3 as PC  # noqa: E402  (the B-131 door's drawing, box(), steady_edges())
import build_props_mars_v3 as PM  # noqa: E402  (columns_within, lamp())
import build_c2_venus_ground as VG  # noqa: E402  (the B-153 deck planks)

DECK_TOP = (336 - 62) / 128.0          # PoiCatalog.DeckTop: the deck surface above a deck module's base (2.14 m)
TAU = 6.283185307179586


def mats_b168(gp):
    """mats() + the Mars / common prop material names mapped onto the Venus palette (wood = the brass frame, glass = sea
    glass) + the B-153 strip materials under M["vg"] (kept apart: mats()'s "pebble" differs from the strip's)."""
    def m(name, **kw):
        return G.mat(gp, f"venus_prop_{name}", **kw)
    M = mats(gp)
    for key, slot in (("off", "offwhite"), ("red", "red"), ("mustard", "mustard"), ("teal", "teal"), ("olive", "green"),
                      ("salmon", "sky"), ("umber", "brown"), ("wood", "mustard"), ("steel", "teal"), ("green", "green")):
        hx = P[slot]
        M[key] = m(key, fill=hx)
        M[key + "_f"] = m(key + "_f", fill=hx, ink=False)
        M[key + "_sh"] = m(key + "_mid", fill=SH(hx), ink=False)
        M[key + "_dp"] = m(key + "_deep", fill=DP(hx), ink=False)
        M[key + "_b"] = m(key + "_behind", fill=hx, behind=True)
    M["iron"], M["iron_f"] = m("iron", fill=P["brown"]), m("iron_f", fill=P["brown"], ink=False)
    M["iron_sh"], M["hole"] = m("iron_mid", fill=DP(P["sky"]), ink=False), m("hole", fill=P["brown"], ink=False)
    M["glass"] = m("glass", fill=P["teal"])
    M["halo"] = m("halo", fill=P["offwhite"], ink=False, fill_alpha=0.30)
    M["halo2"] = m("halo2", fill=P["mustard"], ink=False, fill_alpha=0.25)
    M["puff"], M["puff_sh"] = m("puff", fill=P["offwhite"]), m("puff_mid", fill=SH(P["offwhite"]), ink=False)
    M["vg"] = VG.mats(gp)
    return M


def rail(d, M, x0, x1, z, h=0.05):
    """A brass rail from x0 to x1 at height z: a flat band, inked along its top and bottom only (no end caps: it tiles)."""
    G.stroke(d, [(x0, z - h / 2), (x1, z - h / 2), (x1, z + h / 2), (x0, z + h / 2)], M["mustard_f"], 0.0, cyclic=True)
    G.stroke(d, [(x0, z + h / 2), (x1, z + h / 2)], M["ink"], I)
    G.stroke(d, [(x0, z - h / 2), (x1, z - h / 2)], M["ink"], I)


def railing_posts(d, M, xs, z0, z1, r=None):
    for x in xs:
        G.stroke(d, PC.box(x - 0.03, z0, x + 0.03, z1, seed=int(x * 10) + 500), M["mustard"], r or I, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(x, z1 + 0.02, 0.04, 0.03, n=10, seed=int(x * 10) + 501), M["teal"], I, cyclic=True)


def aerostat_deck(d, M, k=0):
    """One 4 m deck module: a keel, four B-153 plank frames raised so their deck line is DECK_TOP, a two-rail railing."""
    VM = M["vg"]
    G.stroke(d, [(-2.0, 0.0), (2.0, 0.0), (2.0, 0.16), (-2.0, 0.16)], M["red_dp"], 0.0, cyclic=True)        # the keel
    G.stroke(d, [(-2.0, 0.02), (2.0, 0.02)], M["ink"], O)
    for j, kk in enumerate((1, 2, 3, 5)):                                                 # k % 4 == 0 would add a strip post
        x0 = -1.5 + j
        VG.planks_frame(G.Xf(d, lambda pts, x0=x0: [(x + x0, z + DECK_TOP - VG.SURF) for x, z in pts]), VM, kk)
    railing_posts(d, M, (-1.5, -0.5, 0.5, 1.5), DECK_TOP, DECK_TOP + 0.43)
    rail(d, M, -2.0, 2.0, DECK_TOP + 0.24)
    rail(d, M, -2.0, 2.0, DECK_TOP + 0.43)


def railing(d, M, k=0):
    """A standalone 2 m railing section (tiles in x): brass posts with sea-glass knobs, two rails, a foot plate."""
    G.stroke(d, [(-1.0, 0.0), (1.0, 0.0), (1.0, 0.05), (-1.0, 0.05)], M["umber_f"], 0.0, cyclic=True)
    G.stroke(d, [(-1.0, 0.05), (1.0, 0.05)], M["ink"], I)
    railing_posts(d, M, (-0.5, 0.5), 0.05, 0.5, r=O)                                     # the posts carry the silhouette weight
    rail(d, M, -1.0, 1.0, 0.28)
    rail(d, M, -1.0, 1.0, 0.5)


def portholes(d, M, xs, z, r, seed):
    for j, x in enumerate(xs):
        G.stroke(d, G.lumpy_ellipse(x, z, r * 1.25, r * 1.25, n=18, seed=seed + j), M["mustard"], I, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(x, z, r, r, n=16, seed=seed + 10 + j), M["glass"], I, cyclic=True)
        G.stroke(d, [(x - r * 0.5, z + r * 0.2), (x - r * 0.15, z + r * 0.55)], M["off"], I)


def station_hull_a(d, M, k=0):
    """A pressure module lying on the deck: a cream capsule with brass hoops, sea-glass portholes, an antenna. 3.81 x 3.19 m."""
    hull = G.bezier((-1.6, 0.1), (-1.95, 0.1), (-1.95, 2.75), (-1.5, 2.75), n=10) + G.bezier((1.5, 2.75), (1.95, 2.75), (1.95, 0.1), (1.6, 0.1), n=10)
    G.stroke(d, hull, M["off_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in hull if q[1] < 0.9] + [(1.7, 0.9), (-1.7, 0.9)], M["off_sh"], 0.0, cyclic=True)
    for x in (-1.15, 0.0, 1.15):                                                          # brass hoops
        G.stroke(d, [(x - 0.08, 0.12), (x + 0.08, 0.12), (x + 0.08, 2.73), (x - 0.08, 2.73)], M["mustard_f"], 0.0, cyclic=True)
        G.seam(d, [(x - 0.08, 0.14), (x - 0.08, 2.71)], M["ink"])
        G.seam(d, [(x + 0.08, 0.14), (x + 0.08, 2.71)], M["ink"])
    portholes(d, M, (-0.58, 0.58), 1.75, 0.2, 610)
    G.rivets(d, [(x, 2.55) for x in (-1.5, -0.6, 0.6, 1.5)] + [(x, 0.3) for x in (-1.5, -0.6, 0.6, 1.5)], M["ink"])
    G.stroke(d, PC.box(-0.5, 0.0, 0.5, 0.14, seed=611), M["umber"], I, cyclic=True)        # the cradle
    G.stroke(d, hull, M["ink"], O, cyclic=True)
    G.stroke(d, G.hose_outline([(0.9, 2.75), (0.95, 3.05)], 0.025), M["umber"], I, cyclic=True)   # the antenna
    G.stroke(d, G.lumpy_ellipse(0.95, 3.08, 0.05, 0.05, n=10, seed=612), M["red"], I, cyclic=True)


def station_hull_b(d, M, k=0):
    """The habitat module: a cream drum under a brass dome, a vent stack breathing a vent-orange glow, a sea-glass window
    band, a hatch on its side. 3.81 x 3.19 m."""
    drum = PC.box(-1.85, 0.08, 1.85, 1.95, seed=620)
    G.stroke(d, drum, M["off_f"], 0.0, cyclic=True)
    G.stroke(d, PC.box(0.9, 0.08, 1.85, 1.95, seed=620, wob=0.002), M["off_sh"], 0.0, cyclic=True)
    dome = [(1.7 * math.cos(a), 1.95 + 0.85 * math.sin(a)) for a in [math.pi * j / 30 for j in range(31)]]
    G.stroke(d, dome, M["mustard_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in dome if q[0] > 0.6] + [(0.6, 1.95)], M["mustard_sh"], 0.0, cyclic=True)
    for a in (0.5, 1.1, 1.7, 2.3):                                                        # dome ribs
        G.seam(d, [(1.7 * math.cos(a), 1.95 + 0.85 * math.sin(a)), (0.5 * math.cos(a), 1.95 + 0.6 * math.sin(a))], M["ink"])
    G.stroke(d, dome, M["ink"], O, cyclic=True)
    G.stroke(d, PC.box(-1.6, 1.25, 0.7, 1.6, seed=621), M["glass"], I, cyclic=True)          # the window band
    for x in (-1.0, -0.4, 0.2):
        G.seam(d, [(x, 1.27), (x, 1.58)], M["ink"])
    G.stroke(d, PC.box(1.05, 0.12, 1.6, 1.05, seed=622), M["red_f"], I, cyclic=True)        # the side hatch
    G.stroke(d, G.lumpy_ellipse(1.32, 0.72, 0.12, 0.12, n=14, seed=623), M["glass"], I, cyclic=True)
    G.rivets(d, [(x, 0.25) for x in (-1.6, -0.8, 0.0, 0.8)], M["ink"])
    G.stroke(d, drum, M["ink"], O, cyclic=True)
    G.stroke(d, PC.box(-1.15, 2.4, -0.8, 3.0, seed=624), M["umber"], O, cyclic=True)        # the vent stack
    G.stroke(d, G.lumpy_ellipse(-0.97, 3.08, 0.2, 0.08, n=14, seed=625), M["halo2"], 0.0, cyclic=True)   # its glow (a tone)
    G.stroke(d, PC.box(-1.12, 2.92, -0.83, 3.0, seed=626, wob=0.002), M["red_f"], 0.0, cyclic=True)


def meridian_station_door(d, M, k=0):
    """The B-131 door's design for the station airlock: brass frame, an open 6 like Mercury's; scaled to 2.19 x 3.5 m."""
    PC.shelter_door(G.Xf(d, lambda pts: [(x * 1.6, z * 1.36) for x, z in pts]), M, k)


def buoyancy_cell(d, M, k=0):
    """A squat gas cell strapped to the deck: a cream envelope with brass straps, a valve on top. 1.5 x 1.31 m."""
    cell = G.lumpy_ellipse(0.0, 0.6, 0.66, 0.52, n=36, lump=0.015, seed=640)
    cell = [(x, max(z, 0.1)) for x, z in cell]
    G.stroke(d, cell, M["off_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in cell if q[0] > 0.25] + [(0.25, 0.62)], M["off_sh"], 0.0, cyclic=True)
    for x in (-0.35, 0.35):                                                               # straps
        G.stroke(d, [(x - 0.05, 0.1), (x + 0.05, 0.1), (x + 0.05 - 0.02 * (x < 0), 1.07), (x - 0.05 - 0.02 * (x < 0), 1.07)], M["mustard_f"], 0.0, cyclic=True)
        G.seam(d, [(x - 0.05, 0.12), (x - 0.05, 1.04)], M["ink"])
    G.hatch(d, -0.25, 0.4, M["ink"], n=3, length=0.08, spacing=0.03, angle_deg=70, seed=641)
    G.stroke(d, cell, M["ink"], O, cyclic=True)
    G.stroke(d, PC.box(-0.58, 0.0, 0.58, 0.12, seed=642), M["umber"], I, cyclic=True)       # the cradle
    G.stroke(d, PC.box(-0.07, 1.1, 0.07, 1.18, seed=643), M["mustard"], I, cyclic=True)     # the valve
    G.stroke(d, PC.box(-0.12, 1.17, 0.12, 1.21, seed=644), M["red"], I, cyclic=True)


def aerostat_balloon(d, M, k=0):
    """The station's lifting balloon: an apricot envelope with brass gores and a net, a load ring, tethers hanging. 3 x 4 m."""
    env = G.lumpy_ellipse(0.0, 2.55, 1.4, 1.38, n=48, lump=0.01, seed=650)
    G.stroke(d, env, M["salmon_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in env if q[0] > 0.5] + [(0.5, 2.55)], M["salmon_sh"], 0.0, cyclic=True)
    for x in (-0.95, -0.35, 0.35, 0.95):                                                  # the gores
        G.seam(d, G.bezier((x * 0.3, 3.93), (x * 1.15, 3.0), (x * 1.1, 2.0), (x * 0.35, 1.2), n=12), M["ink"])
    G.stroke(d, G.lumpy_ellipse(0.0, 3.85, 0.3, 0.1, n=14, seed=651), M["mustard"], I, cyclic=True)   # the crown cap
    G.stroke(d, env, M["ink"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.0, 1.05, 0.5, 0.08, n=18, seed=652), M["mustard"], I, cyclic=True)  # the load ring
    for x in (-0.45, -0.15, 0.15, 0.45):
        G.stroke(d, [(x * 1.6, 1.3), (x, 1.07)], M["ink"], I)                              # the net lines to the ring
    for x in (-0.4, 0.4):
        G.stroke(d, G.bowed_line((x, 1.0), (x * 1.2, 0.06), bow=0.03, n=10), M["ink"], I)  # tethers down toward the deck


def vent_harvester(d, M, k=0):
    """A vent harvester over a surface vent: a brass tripod, a hood that drinks the vent gas, a cream tank and a pipe; the
    vent glows below (a tone). 2.81 x 3.13 m."""
    G.stroke(d, G.lumpy_ellipse(0.0, 0.05, 0.55, 0.12, n=20, seed=660), M["halo2"], 0.0, cyclic=True)   # the vent's glow
    G.stroke(d, G.lumpy_ellipse(0.0, 0.04, 0.32, 0.06, n=16, seed=661), M["red_f"], 0.0, cyclic=True)
    for sx in (-1, 1):                                                                    # the tripod legs
        G.stroke(d, G.hose_outline([(sx * 1.25, 0.02), (sx * 0.2, 2.75)], 0.05), M["mustard"], O, cyclic=True)
    G.stroke(d, G.hose_outline([(0.1, 0.02), (0.05, 2.75)], 0.04), M["mustard_dp"], I, cyclic=True)
    hood = [(-0.5, 0.55), (0.5, 0.55), (0.18, 1.1), (-0.18, 1.1)]                         # the hood over the vent
    G.stroke(d, hood, M["umber_f"], 0.0, cyclic=True)
    G.stroke(d, hood, M["ink"], O, cyclic=True)
    G.stroke(d, G.hose_outline([(0.0, 1.1), (0.0, 1.8)], 0.07), M["teal"], I, cyclic=True)   # the riser
    tank = PC.box(-0.42, 1.8, 0.42, 2.55, seed=662)
    G.stroke(d, tank, M["off_f"], 0.0, cyclic=True)
    G.stroke(d, PC.box(0.12, 1.8, 0.42, 2.55, seed=662, wob=0.002), M["off_sh"], 0.0, cyclic=True)
    for z in (1.95, 2.4):
        G.seam(d, [(-0.42, z), (0.42, z)], M["ink"])
    G.stroke(d, tank, M["ink"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.0, 2.17, 0.12, 0.12, n=14, seed=663), M["glass"], I, cyclic=True)   # a gauge
    G.stroke(d, G.hose_outline(G.bezier((0.42, 2.2), (1.0, 2.2), (1.15, 1.2), (1.2, 0.3), n=10), 0.05), M["teal_sh"], I, cyclic=True)   # the outlet pipe
    G.stroke(d, PC.box(-0.3, 2.75, 0.3, 2.88, seed=664), M["mustard"], O, cyclic=True)        # the crown
    PM.lamp(d, M, 0.0, 2.95, lit=True, r=0.035)


B168 = {"aerostat_deck": (aerostat_deck, 256, 184, None, 1, True), "railing": (railing, 128, 48, None, 1, True),
        "station_hull_a": (station_hull_a, 244, 216, None, 1, False), "station_hull_b": (station_hull_b, 244, 216, None, 1, False),
        "meridian_station_door": (meridian_station_door, 140, 236, "open", 6, False),
        "buoyancy_cell": (buoyancy_cell, 96, 96, None, 1, False), "aerostat_balloon": (aerostat_balloon, 192, 268, None, 1, False),
        "vent_harvester": (vent_harvester, 180, 216, None, 1, False)}
PROPS.update(B168)
LOOPS = {"open": False}
INTERACTABLE = ("meridian_station_door", "vent_harvester")
SELF = {"aerostat_deck": "static (v2: no clip); a 4 m module that tiles in x, the deck surface 2.14 m up (top_row in the json)",
        "railing": "static; a 2 m section that tiles in x",
        "station_hull_a": "static (v2: no clip)", "station_hull_b": "static (v2: no clip); the vent's glow is a tone",
        "meridian_station_door": "open 6: the leaf swings in about its left hinge, the lamp turns green at 4",
        "buoyancy_cell": "static (v2: no clip)", "aerostat_balloon": "static (v2: no clip); UNITY may bob it",
        "vent_harvester": "static (v2: no clip); its lamp lit"}



def b168_review(out, imgs=None, widths=None, stamp_paths=()):
    """B-168's stamped review: the Meridian station assembled as PoiCatalog places it (five deck modules, the two hulls and
    the door on the deck, two buoyancy cells, two balloons 4.5 m up, the B-153 deck planks at the deck line) beside the
    surveyor at 1x, the vent harvester and a railing run beside it, the door's open clip, the per-prop lines."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import preview_c2_earth_rigs as PR
    names = list(B168)
    if imgs is None:
        imgs, widths = {}, {}
        for name in names:
            imgs[name], widths[name] = [], []
            for kk in range(PROPS[name][4]):
                im, w = render_prop(name, kk)
                imgs[name].append(im)
                widths[name] += w
    W, H = 1900, 820
    base = H - 40                                                                          # the station's float line (its keel)
    sky = np.empty((H, W, 3), np.float32)
    t = (np.arange(H) / H)[:, None, None]
    sky[:] = (np.array(v3.hex_rgb(P["sky"]), np.float32) / 255) * (1 - 0.5 * t) + (np.array(v3.hex_rgb(P["offwhite"]), np.float32) / 255) * 0.5 * t
    x0 = 60                                                                                # the station's left end (POI x)

    def stand(name, dx, dy=0.0, f=0):
        im = imgs[name][f]
        review._over(sky, im, int(x0 + dx * PPU - im.shape[1] * 0.5), int(base - dy * PPU - im.shape[0] + GROUND_PX))
    for dx in (2, 6, 10, 14, 18):
        stand("aerostat_deck", dx)
    S, _w = VG.sheets(("planks",))                                                        # the deck planks as GroundStrip lays them
    gl = int(base - DECK_TOP * PPU)
    for c in range(20):
        im = S["planks"][c % 8]
        review._over(sky, im, x0 + c * 64, gl - (VG.FH - int(round(VG.SURF * 64))))
    for name, dx in (("station_hull_a", 5), ("meridian_station_door", 10), ("station_hull_b", 15), ("buoyancy_cell", 1.2), ("buoyancy_cell", 18.8)):
        stand(name, dx, DECK_TOP)
    for dx in (6, 14):
        stand("aerostat_balloon", dx, DECK_TOP + 4.5)
    try:
        fr, piv = PR.surveyor_frame()
        review._over(sky, fr, int(x0 + 12.4 * PPU), int(base - DECK_TOP * PPU - fr.shape[0] + int(round(piv[1] * fr.shape[0]))))
    except Exception:  # noqa: BLE001
        pass
    xr = x0 + 21 * PPU                                                                     # beside it: the harvester and a railing run
    review._over(sky, imgs["vent_harvester"][0], xr, base - imgs["vent_harvester"][0].shape[0] + GROUND_PX)
    for j in range(2):
        review._over(sky, imgs["railing"][0], xr + 200 + j * 128, base - imgs["railing"][0].shape[0] + GROUND_PX)
    review._label(sky, "1x: the meridian station as poicatalog places it (5 deck modules, the hulls, the door, 2 cells, 2 balloons 4.5 m up, "
                       "the b-153 planks at the deck line) beside the surveyor; the vent harvester and a railing run", 6, 6)
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, "b-168 venus station props re-inked (d-151; the b-147 language, the venus palette, no faces), sized to the station layout", 6, 8)
    fw, fh = PROPS["meridian_station_door"][1], PROPS["meridian_station_door"][2]
    r = np.tile(review.PAPER, (fh + 30, W, 1)).astype(np.float32)
    for j, im in enumerate(imgs["meridian_station_door"]):
        review._over(r, im, 8 + j * (fw + 10), 26)
    review._label(r, "meridian_station_door open 6 at 1x (the leaf swings in about its left hinge; the lamp turns green at 4)", 6, 4)
    notes = []
    for name in names:
        sheet, meta, problems = sheet_meta(name, imgs[name])
        hits, _o = v3.palette_hits(sheet, "venus", tints=[("offwhite", 0.30), ("mustard", 0.25)])
        ws = widths[name]
        outer = [w for w in ws if w[0] >= v3.OUTER_SPLIT]
        inner = [w for w in ws if w[0] < v3.OUTER_SPLIT]
        extra = f", top_row {meta['top_row']}" if "top_row" in meta else ""
        notes.append(f"{name} {meta['frame_width']}x{meta['frame_height']} x{meta['frames']}: ink {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} / "
                     f"{min(w[1] for w in inner):.1f}-{max(w[2] for w in inner):.1f} px, palette {hits * 100:.1f}%, json {'valid' if not problems else problems}{extra}, "
                     f"faces none, motion: {SELF[name]}")
    foot = np.tile(review.PAPER, (20 + 18 * len(notes), W, 1)).astype(np.float32)
    for i, t_ in enumerate(notes):
        review._label(foot, t_, 6, 6 + 18 * i, scale=1)
    img = np.vstack([head, sky, r, foot])
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + (" export" if stamp_paths else " preview (not exported)"), 2, img.shape[0] - 16)
    review.write(out, img)
    print("written", out)
    for t_ in notes:
        print(" ", t_)
    return []


def top_row(name):
    """Rows from the frame top to the standing surface (PoiPlacer's topRow at 64 px/m) for a solid deck module."""
    _fn, fw, fh, _c, _n, _t = PROPS[name]
    return int(round(fh - GROUND_PX - DECK_TOP * PPU)) if name == "aerostat_deck" else 0


def clip_sheet_meta(name, frames):
    """A multi-frame prop sheet (build_props_mars_v3.sheet_meta's layout: the fewest-pixel columns within 512^2)."""
    import numpy as np
    _fn, fw, fh, clip, n, _t = PROPS[name]
    g = v3.GUTTER
    cols = PM.columns_within(fw, fh, n, cap=SHEET_CAP)
    rows = -(-n // cols)
    sheet = np.zeros((rows * fh + (rows - 1) * g, min(cols, n) * fw + (min(cols, n) - 1) * g, 4), np.uint8)
    for i, im in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw] = im
    px, py = pivot_of(name)
    anims = [{"name": clip, "start": 0, "length": n, "loop": LOOPS[clip], **({"loop_from": 0} if LOOPS[clip] else {})}]
    meta = {"key": KEY.format(name), "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": g,
            "frames": n, "fps": v3.FPS, "pivot": [round(px, 6), round(py, 6)], "facing": "right", "ppu": PPU,
            "animations": anims, "squash_root": False, "ground_line_px": GROUND_PX,
            "note": f"frame 0 = at rest (closed); {clip} plays once; the pivot sits on its base line"}
    if name in INTERACTABLE:
        meta["interactable"] = True
    problems = list(v3.validate_sheet(meta, sheet.shape))
    if sheet.shape[0] > SHEET_CAP or sheet.shape[1] > SHEET_CAP:
        problems.append(f"sheet {sheet.shape[1]}x{sheet.shape[0]} over {SHEET_CAP}^2")
    m = v3.EDGE_MARGIN
    for i, im in enumerate(frames):
        a = im[..., 3]
        if a[:m].any() or a[-m:].any() or a[:, :m].any() or a[:, -m:].any():
            problems.append(f"frame {i} touches the {m} px frame edge")
    return sheet, meta, problems


def pivot_of(name):
    _fn, fw, fh, _c, _n, _t = PROPS[name]
    return (0.5, GROUND_PX / fh)


def render_prop(name, k=0, seed=7):
    fn, fw, fh, _c, _n, tiles = PROPS[name]
    gp = fakegp.FakeGP()
    M = mats_b168(gp)                                   # mats() + the B-168 names (the vent's keys and pixels unchanged)
    d = fakegp.FakeDrawing()
    fn(d, M, k)
    st = fakegp.strokes_of(d, gp)
    if tiles:                                           # B-168: the deck / railing tile in x (build_props_common_v3's way)
        half = fw / 2 / PPU
        PC.steady_edges(st, -half, half, seed)
    img, w = GR.render_frame(st, fw, fh, PPU, pivot_of(name), ss=4, seed=seed)
    if tiles:
        img[:, -1] = img[:, 0]
    return img, w


def render_all():
    imgs, widths = {}, {}
    for name, (_fn, _fw, _fh, _c, n, _t) in PROPS.items():
        imgs[name], widths[name] = [], []
        for k in range(n):
            img, w = render_prop(name, k)
            imgs[name].append(img)
            widths[name] += w
    return imgs, widths


def sheet_meta(name, frames):
    _fn, fw, fh, clip, n, tiles = PROPS[name]
    if n > 1:                                           # B-168: a clip sheet (the door's open 6)
        return clip_sheet_meta(name, frames)
    sheet = frames[0].copy()
    px, py = pivot_of(name)
    meta = {"key": KEY.format(name), "style": "v3", "frame_width": fw, "frame_height": fh, "columns": 1, "gutter": v3.GUTTER,
            "frames": 1, "fps": v3.FPS, "pivot": [round(px, 6), round(py, 6)], "facing": "right", "ppu": PPU, "animations": [],
            "squash_root": False, "ground_line_px": GROUND_PX,
            "note": "one static frame (no clip); the pivot sits on the ground line"}
    if name in DEN_FOR:
        meta["den_for"] = DEN_FOR[name]
        meta["note"] += f"; D-126: drawn in front of {DEN_FOR[name]} on the same pivot"
    problems = [p for p in v3.validate_sheet(meta, sheet.shape) if "sum of clip lengths" not in p]
    m = v3.EDGE_MARGIN
    a = sheet[..., 3]
    if a[:m].any() or a[-m:].any() or (not tiles and (a[:, :m].any() or a[:, -m:].any())):
        problems.append(f"touches the {m} px frame edge")
    if tiles:                                           # B-168: a tiling module joins itself (the right column = the left)
        meta["tiles_x"] = True
        meta["note"] += "; tiles in x: modules sit side by side, seam-free"
        j = float(abs(sheet[:, -1].astype(int) - sheet[:, 0].astype(int)).max())
        if j > 1.0:
            problems.append(f"tile seam {j:.0f}/255")
    if top_row(name):                                   # B-168: the solid deck's standing surface for PoiPlacer
        meta["top_row"] = top_row(name)
        meta["stand_line"] = round(DECK_TOP, 4)
        meta["note"] += f"; the deck surface {DECK_TOP:.3f} m above the pivot = top_row {top_row(name)} rows below the frame top (PoiCatalog topRow at 64 px/m)"
    return sheet, meta, problems


def v2_leftovers(art, names=None):
    d = os.path.join(art, "props", "venus")
    return [os.path.join(d, n + s) for n in (names or PROPS) for s in (".glb", "_normal.png", "_mask.png", "_emission.png")
            if os.path.isfile(os.path.join(d, n + s))]


def export(art, imgs=None, names=None):
    import json
    from meridian import pngio
    names = list(names or PROPS)
    if imgs is None:
        imgs, _w = render_all()
    built, problems = [], []
    for name in names:
        sheet, meta, p = sheet_meta(name, imgs[name])
        problems += [f"{name}: {x}" for x in p]
        built.append((name, sheet, meta))
    if problems:
        raise ValueError("Venus prop export checks: " + "; ".join(problems))
    d = os.path.join(art, "props", "venus")
    os.makedirs(d, exist_ok=True)
    out = []
    for name, sheet, meta in built:
        n = pngio.write_png(os.path.join(d, name + "_color.png"), sheet)
        with open(os.path.join(d, name + ".json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((meta["key"], sheet.shape[1], sheet.shape[0], n))
    removed = v2_leftovers(art, names)
    for p in removed:
        os.remove(p)
    return out, {}, removed


def den_frames():
    """The eel's idle + react frames (exact ids) with the vent composited IN FRONT, as UNITY will draw them."""
    import numpy as np
    sp = CM.SPECIES["vent_eel"]
    fw, fh = sp["frame"]
    mound, _w = render_prop("vent_mouth")
    mh, mw = mound.shape[:2]
    poses = sp["poses"]()
    starts, s_ = {}, 0
    for c, n, _l in sp["clips"]:
        starts[c] = (s_, n)
        s_ += n
    out = []
    for clip in ("idle", "react"):
        a0, n = starts[clip]
        for f in range(a0, a0 + n):
            gp = fakegp.FakeGP()
            M = sp["mats"](gp, "vent_eel")
            d = fakegp.FakeDrawing()
            sp["draw"](d, M, poses[f], seed=5 * f)
            img, _w = GR.render_frame(fakegp.strokes_of(d, gp, as_object=("vent_eel", "art")), fw, fh, 64, (0.5, 0.0), ss=4,
                                      seed=sp["seed"] * 1000 + f + 1)
            H = fh + GROUND_PX
            c = np.zeros((H, fw, 4), np.float32)
            c[:fh] = img.astype(np.float32) / 255
            x0, y0 = fw // 2 - mw // 2, H - mh
            mf = mound.astype(np.float32) / 255
            reg = c[y0:y0 + mh, x0:x0 + mw]
            al = mf[..., 3:]
            reg[..., :3] = mf[..., :3] * al + reg[..., :3] * (1 - al)
            reg[..., 3:] = al + reg[..., 3:] * (1 - al)
            out.append((clip, c))
    return out


def main(out, imgs=None, widths=None, stamp_paths=()):
    """The den review: the vent at 3x (ink, palette, json), then the eel's idle + react behind it at 2x."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    if imgs is None:
        imgs, widths = render_all()
    sheet, meta, problems = sheet_meta("vent_mouth", imgs["vent_mouth"])
    hits, _off = v3.palette_hits(sheet, "venus")
    ws = widths["vent_mouth"]
    outer = [w for w in ws if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in ws if w[0] < v3.OUTER_SPLIT]
    W = 1700
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, f"review props/venus/vent_mouth (b-147, d-126)  96x40  pivot {meta['pivot']}  ink {min(w[1] for w in outer):.2f}-"
                        f"{max(w[2] for w in outer):.2f} / {min(w[1] for w in inner):.2f}-{max(w[2] for w in inner):.2f} px  "
                        f"venus palette {hits * 100:.1f}%  json {'valid' if not problems else '; '.join(problems)}", 6, 8)
    big = sheet.repeat(3, 0).repeat(3, 1)
    r1 = np.tile(review.PAPER, (big.shape[0] + 16, W, 1)).astype(np.float32)
    review._over(r1, big, 8, 8)
    review._label(r1, "3x: drawn in front of creatures/venus/vent_eel on the same pivot", big.shape[1] + 24, 10)
    rows = [head, r1]
    den = den_frames()
    for clip in ("idle", "react"):
        fr = [c for cl, c in den if cl == clip]
        h, w = fr[0].shape[:2]
        per = (W - 8) // (2 * w + 6)
        nr = -(-len(fr) // per)
        r = np.tile(review.PAPER, (nr * (2 * h + 6) + 26, W, 1)).astype(np.float32)
        for j, c in enumerate(fr):
            rr, cc = divmod(j, per)
            review._over(r, (np.clip(c, 0, 1) * 255).astype(np.uint8).repeat(2, 0).repeat(2, 1), 8 + cc * (2 * w + 6), 26 + rr * (2 * h + 6))
        review._label(r, f"den {clip} at 2x: the eel behind its vent ({len(fr)} frames)", 6, 6)
        rows.append(r)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + (" export" if stamp_paths else " preview"), 2, img.shape[0] - 16)
    review.write(out, img)
    return problems


if __name__ == "__main__":
    if "--b168" in sys.argv:
        b168_review(sys.argv[1])
    else:
        print("problems", main(sys.argv[1]) or "-")
