"""B-145 (C2 Mercury design prep; D-126): Mercury props as v3.1 prop sheets (colour + json only), the build_props_common_v3
/ build_props_mars_v3 API (PROPS, KEY, render_all, sheet_meta, export, main) so render.py's prop rows can export them.

  ice_burrow  112x40, 1 static frame: the Shadewyrm's den, a mound of faceted cold-teal ice blocks with frost on the
              top facets and slate shadows, whose top line is build_creatures_mercury_v3.DEN_TOP (the wyrm's peek rises
              behind it). UNITY draws it IN FRONT of creatures/mercury/shadewyrm on the same pivot (D-126).

B-167 (D-150), the Mercury props re-inked from the B-145 language (each replaces its v2 model under the same key; sized to
UNITY's PoiCatalog placement; frame counts as the v2 jsons: static except the door; faces on none):
  flare_shelter      272x160  a squat cold-steel dome under gold heat-shield scales, a vestibule where the door stands
                              (+2.6 m), a vent, one lamp (3.88 x 2.13 m)
  shelter_door       128x192  open 6: the B-131 door's design with a gold heat-shield frame (1.75 x 2.69 m)
  meridian_beacon    136x224  the Mars beacon's design in the Mercury palette (2.0 x 3.3 m)
  solarite_cluster   128x120  gold prisms from ember rock; its two states are UNITY's tint (1.81 x 1.63 m)
  warden_vault_gate  272x256  a round steel vault gate with the gold Sowing hub in a slate arch, the Warden bell (3.94 x 3.56 m)
  equipment_locker   80x144   a steel locker under a gold heat-shield cap (1.0 x 1.98 m)

  python -I build_props_mercury_v3.py <review png>          lock-free den review: the burrow at 3x, the wyrm behind it
  python -I build_props_mercury_v3.py <review png> --b167   lock-free B-167 review: the six props at 1x beside the surveyor
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_mercury_v3 as CM  # noqa: E402  (gp_draw through fakegp outside Blender)
from meridian import fakegp, v3  # noqa: E402
import gp_raster as GR  # noqa: E402

G = CM.G
P = v3.PALETTES["mercury"]
O, I = G.OUTER, G.INNER
PPU = 64
GROUND_PX = 10
KEY = "props/mercury/{}"
SHEET_CAP = 512
TAU = 2 * math.pi


def SH(h):
    return v3.shadow_of(h, "mercury")


def DP(h):
    return v3.deep_of(h, "mercury")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, f"mercury_prop_{name}", **kw)
    return {"ice": m("ice", fill=P["teal"], ink=False), "ice_sh": m("ice_mid", fill=SH(P["teal"]), ink=False),
            "ice_dp": m("ice_deep", fill=DP(P["teal"]), ink=False), "frost": m("frost", fill=P["offwhite"], ink=False),
            "slate": m("slate", fill=P["brown"], ink=False), "pebble": m("pebble", fill=SH(P["offwhite"])), "ink": m("ink", fill=None)}


def ice_burrow(d, M, k=0):
    """The den: three faceted ice blocks under the shared top line, the base sunk 0.06 m (no ink along it)."""
    top = CM.DEN_TOP
    base = -0.06
    G.stroke(d, top + [(top[-1][0], base), (top[0][0], base)], M["ice"], 0.0, cyclic=True)
    for (x0, z0), (x1, z1) in zip(top, top[1:]):                                          # frost on the upward-facing facets
        if z1 > 0.08 and z0 > 0.08:
            G.stroke(d, [(x0, z0), (x1, z1), (x1, z1 - 0.045), (x0, z0 - 0.045)], M["frost"], 0.0, cyclic=True)
    G.stroke(d, [(0.30, 0.2), (0.54, 0.12), (0.62, 0.0), (0.62, base), (0.30, base)], M["ice_sh"], 0.0, cyclic=True)   # the shaded side
    G.stroke(d, [(0.44, 0.0), (0.62, 0.0), (0.62, base), (0.44, base)], M["ice_dp"], 0.0, cyclic=True)
    for x0, z0, x1, z1 in ((-0.30, 0.24, -0.22, 0.0), (0.02, 0.31, 0.08, 0.02), (0.36, 0.18, 0.30, 0.0)):   # block seams
        G.seam(d, [(x0, z0 - 0.04), ((x0 + x1) / 2 + 0.01, (z0 + z1) / 2), (x1, z1 + 0.01)], M["ink"])
    G.seam(d, [(-0.45, 0.08), (-0.38, 0.12)], M["ink"])                                  # a crack
    G.specks(d, [(-0.12, 0.12), (0.18, 0.10), (0.46, 0.06)], M["ink"])
    G.stroke(d, top, M["ink"], O)
    for cx, rx, rz, sd in ((-0.70, 0.045, 0.03, 3), (0.70, 0.04, 0.025, 4)):           # two ice chips at the foot
        G.stroke(d, G.lumpy_ellipse(cx, rz * 0.6, rx, rz, n=10, lump=0.08, seed=sd), M["pebble"], I, cyclic=True)


PROPS = {"ice_burrow": (ice_burrow, 112, 40, None, 1, False)}
DEN_FOR = {"ice_burrow": "creatures/mercury/shadewyrm"}


# ---------------------------------------------------------------- B-167 (D-150): the Mercury props re-inked from the B-145 language
# Sizes from UNITY's placement (PoiCatalog: the shelter 3.88 x 2.13 m, its door 1.75 x 2.69 m beside it at +2.6 m, the vault
# gate 3.94 x 3.56 m, the beacon 2.06 x 3.13 m, the Solarite cluster 1.81 x 1.63 m); frame counts as the v2 jsons (static, the
# door's open clip); the pivot on the ground line (the v2 origin "base"). Faces on none. The Solarite's two states are UNITY's
# tint of one sprite (glowing white / crusted, SolariteCrystals.cs), so the crystals are drawn at full brightness.
import build_props_common_v3 as PC  # noqa: E402  (the B-131 door's drawing and box())
import build_props_mars_v3 as PM  # noqa: E402  (the Mars beacon's drawing and lamp())


def mats_b167(gp):
    """mats() plus the Mars / common prop material names mapped onto the Mercury palette (so their drawings take Mercury's
    colours): off / red / mustard / teal / olive / salmon / umber, wood = the gold heat shield, iron / hole = the slate."""
    def m(name, **kw):
        return G.mat(gp, f"mercury_prop_{name}", **kw)
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
    M["glass"] = m("glass", fill=P["sky"])
    M["halo"] = m("halo", fill=P["offwhite"], ink=False, fill_alpha=0.30)
    M["halo2"] = m("halo2", fill=P["mustard"], ink=False, fill_alpha=0.25)
    M["puff"], M["puff_sh"] = m("puff", fill=P["offwhite"]), m("puff_mid", fill=SH(P["offwhite"]), ink=False)
    return M


def flare_shelter(d, M, k=0):
    """A squat steel dome bunker under gold heat-shield scales, a vestibule on its right where shelter_door stands, a vent,
    one lamp. 3.88 x 2.13 m."""
    box = PC.box
    G.stroke(d, box(-1.94, 0.0, 1.94, 0.32, seed=101), M["umber"], O, cyclic=True)                       # the footing ring
    G.stroke(d, box(-1.94, 0.0, 1.94, 0.1, seed=101, wob=0.002), M["umber_dp"], 0.0, cyclic=True)
    G.rivets(d, [(-1.7 + 0.42 * j, 0.21) for j in range(9)], M["ink"])
    G.stroke(d, box(1.25, 0.3, 1.94, 1.36, seed=102), M["teal_sh"], O, cyclic=True)                       # the vestibule
    G.stroke(d, [(1.45, 0.32), (1.94, 0.32), (1.94, 1.1), (1.45, 1.1)], M["hole"], 0.0, cyclic=True)    # its passage to the door
    G.stroke(d, box(1.2, 1.32, 1.98, 1.44, seed=103), M["mustard"], I, cyclic=True)                      # its gold lintel
    dome = [(1.8 * math.cos(a), 0.32 + 1.55 * math.sin(a)) for a in [math.pi * j / 40 for j in range(41)]]
    G.stroke(d, dome, M["teal_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in dome if q[0] > 0.7] + [(0.7, 0.32)], M["teal_sh"], 0.0, cyclic=True)
    for row, (z, n) in enumerate(((1.62, 5), (1.24, 7), (0.86, 8))):                                      # gold heat-shield scales
        half = 1.8 * math.sqrt(max(0.0, 1 - ((z - 0.32) / 1.55) ** 2)) - 0.12
        for j in range(n):
            x = -half + (2 * half) * (j + 0.5) / n
            w = half / n * 0.95
            tile = [(x - w, z + 0.17), (x + w, z + 0.17), (x + w * 0.92, z - 0.02)] + \
                [(x + w * 0.92 * math.cos(a), z - 0.02 - 0.13 * math.sin(a)) for a in [math.pi * i / 6 for i in range(1, 6)]] + [(x - w * 0.92, z - 0.02)]
            G.stroke(d, tile, M["mustard_f"] if x < 0.7 else M["mustard_sh"], 0.0, cyclic=True)
            G.stroke(d, tile, M["ink"], I, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(-0.9, 0.62, 0.28, 0.1, n=16, seed=104), M["glass"], I, cyclic=True)        # a slot viewport
    G.stroke(d, dome, M["ink"], O, cyclic=True)
    G.stroke(d, G.hose_outline([(0.55, 1.78), (0.58, 1.98)], 0.07), M["umber"], I, cyclic=True)            # the vent
    G.stroke(d, box(0.42, 1.98, 0.74, 2.08, seed=105), M["umber"], I, cyclic=True)
    PM.lamp(d, M, 1.62, 1.56, lit=True, r=0.055)                                                           # its one lamp, over the door side


def mercury_shelter_door(d, M, k=0):
    """The B-131 door's design with a gold heat-shield frame (common's posts and lintel in the Mercury gold), scaled to the
    1.75 x 2.69 m opening; open 6 like the common door."""
    PC.shelter_door(G.Xf(d, lambda pts: [(x * 1.45, z * 1.075) for x, z in pts]), M, k)


def mercury_beacon(d, M, k=0):
    """The Mars beacon's design in the Mercury palette (B-145): 2.0 x 3.3 m; static (the v2 frame count)."""
    PM.meridian_beacon(d, M, 0)


SOLARITE = ((-0.48, 26, 0.92, 0.15), (0.46, -30, 0.86, 0.14), (-0.17, 7, 1.42, 0.21), (0.17, -11, 1.18, 0.19), (0.0, -1, 0.72, 0.13))


def solarite_cluster(d, M, k=0):
    """Gold Solarite prisms bursting from a crust of ember rock; UNITY tints it crusted between flares. 1.81 x 1.63 m."""
    base = [(x, max(z, 0.0)) for x, z in G.lumpy_ellipse(0.0, 0.08, 0.86, 0.24, n=28, lump=0.1, seed=111)]
    G.stroke(d, base, M["red_dp"], 0.0, cyclic=True)
    G.stroke(d, [q for q in base if q[0] > 0.3] + [(0.3, 0.05)], M["umber_f"], 0.0, cyclic=True)
    for j, (x, deg, L, w) in enumerate(SOLARITE):
        a = math.radians(deg)
        ux, uz = math.sin(a), math.cos(a)
        nx, nz = uz, -ux

        def p(s, t):
            return (x + ux * s + nx * t, 0.14 + uz * s + nz * t)
        prism = [p(0, -w), p(0, w), p(L * 0.82, w), p(L, 0.0), p(L * 0.82, -w)]
        G.stroke(d, prism, M["mustard_f"], 0.0, cyclic=True)
        G.stroke(d, [p(0, w * 0.15), p(0, w), p(L * 0.82, w), p(L, 0.0), p(L * 0.82, w * 0.15)], M["mustard_sh"], 0.0, cyclic=True)
        G.stroke(d, [p(L * 0.1, -w * 0.6), p(L * 0.1, -w * 0.35), p(L * 0.75, -w * 0.35), p(L * 0.75, -w * 0.6)], M["off_f"], 0.0, cyclic=True)
        G.seam(d, [p(0, w * 0.15), p(L * 0.82, w * 0.15), p(L, 0.0)], M["ink"])
        G.stroke(d, prism, M["ink"], O if j < 4 else I, cyclic=True)
    tx, tz = (lambda s, t: (SOLARITE[2][0] + math.sin(math.radians(SOLARITE[2][1])) * s, 0.14 + math.cos(math.radians(SOLARITE[2][1])) * s))(SOLARITE[2][2], 0)
    for ang in (0.0, math.pi / 2):                                                                        # a glint on the tallest tip
        G.stroke(d, [(tx - 0.07 * math.cos(ang), tz + 0.02 - 0.07 * math.sin(ang)), (tx + 0.07 * math.cos(ang), tz + 0.02 + 0.07 * math.sin(ang))], M["off"], I)
    G.specks(d, [(-0.6, 0.1), (0.35, 0.12), (0.7, 0.06)], M["ink"])
    G.stroke(d, base, M["ink"], O, cyclic=True)


def warden_vault_gate(d, M, k=0):
    """The Warden-guarded Sowing vault: a round steel gate with a vault wheel and the gold Sowing hub, set in an arch of
    slate blocks, the Warden bell hanging from the keystone (the Wardens ring a bell, never shoot). 3.94 x 3.56 m."""
    box = PC.box
    cz, R0, R1 = 1.55, 1.5, 1.95
    for sx in (-1, 1):                                                                                    # the jambs
        G.stroke(d, box(sx * R0 if sx < 0 else R0, 0.0, sx * R1 if sx < 0 else R1, cz, seed=120 + sx), M["umber"], O, cyclic=True)
        for z in (0.5, 1.0):
            G.seam(d, [(sx * R0, z), (sx * R1, z + 0.02)], M["ink"])
    arch = [(R1 * math.cos(a), cz + R1 * math.sin(a)) for a in [math.pi * j / 30 for j in range(31)]] + \
        [(R0 * math.cos(a), cz + R0 * math.sin(a)) for a in [math.pi * j / 30 for j in range(30, -1, -1)]]
    G.stroke(d, arch, M["umber"], 0.0, cyclic=True)
    G.stroke(d, [q for q in arch if q[0] > 0.9] + [(0.9, cz)], M["umber_dp"], 0.0, cyclic=True)
    for j in range(1, 7):                                                                                 # the voussoir seams
        a = math.pi * j / 7
        G.seam(d, [(R0 * math.cos(a), cz + R0 * math.sin(a)), (R1 * math.cos(a), cz + R1 * math.sin(a))], M["ink"])
    G.stroke(d, arch, M["ink"], O, cyclic=True)
    gate = G.lumpy_ellipse(0.0, cz, R0 - 0.04, R0 - 0.04, n=48, lump=0.005, seed=121)
    G.stroke(d, gate, M["teal_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in gate if q[0] > 0.55] + [(0.55, cz)], M["teal_sh"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.0, cz, 1.12, 1.12, n=40, seed=122), M["ink"], I, cyclic=True)              # the inner ring
    for j in range(6):                                                                                    # the vault wheel's spokes
        a = math.pi * j / 3 + 0.3
        G.stroke(d, G.hose_outline([(0.3 * math.cos(a), cz + 0.3 * math.sin(a)), (1.0 * math.cos(a), cz + 1.0 * math.sin(a))], 0.05),
                 M["umber_f"], 0.0, cyclic=True)
        G.seam(d, [(0.3 * math.cos(a), cz + 0.3 * math.sin(a)), (1.0 * math.cos(a), cz + 1.0 * math.sin(a))], M["ink"])
    G.rivets(d, [(1.3 * math.cos(a), cz + 1.3 * math.sin(a)) for a in [TAU * j / 12 for j in range(12)]], M["ink"])
    hub = G.lumpy_ellipse(0.0, cz, 0.32, 0.32, n=24, seed=123)
    G.stroke(d, hub, M["mustard_f"], 0.0, cyclic=True)
    G.stroke(d, G.bezier((0.0, cz - 0.2), (0.16, cz), (0.0, cz + 0.22), n=8) + G.bezier((0.0, cz + 0.22), (-0.16, cz), (0.0, cz - 0.2), n=8)[1:],
             M["olive"], I, cyclic=True)                                                                  # the Sowing seed emblem
    G.seam(d, [(0.0, cz - 0.18), (0.0, cz + 0.18)], M["ink"])
    G.stroke(d, hub, M["ink"], O, cyclic=True)
    G.stroke(d, gate, M["ink"], O, cyclic=True)
    G.stroke(d, box(-0.2, cz + R1 - 0.05, 0.2, cz + R1 + 0.12, seed=124), M["umber"], I, cyclic=True)    # the keystone bracket
    bell = G.bezier((-0.05, 3.5), (-0.14, 3.46), (-0.15, 3.3), (-0.22, 3.2), n=8) + [(0.0, 3.17)] + \
        G.bezier((0.22, 3.2), (0.15, 3.3), (0.14, 3.46), (0.05, 3.5), n=8)
    G.stroke(d, bell, M["mustard"], O, cyclic=True)                                                       # the Warden bell
    G.stroke(d, [q for q in bell if q[0] > 0.03] + [(0.03, 3.25)], M["mustard_sh"], 0.0, cyclic=True)
    G.seam(d, [(-0.18, 3.25), (0.18, 3.25)], M["ink"])
    PM.lamp(d, M, 0.0, 3.12, lit=False, r=0.04)                                                           # its clapper lamp, dark at rest


def equipment_locker(d, M, k=0):
    """A standing steel locker under a gold heat-shield cap: two doors with vents and handles, a stencil band. 1.0 x 1.98 m."""
    box = PC.box
    body = box(-0.46, 0.06, 0.46, 1.86, seed=131)
    G.stroke(d, body, M["teal_f"], 0.0, cyclic=True)
    G.stroke(d, box(0.26, 0.06, 0.46, 1.86, seed=131, wob=0.002), M["teal_sh"], 0.0, cyclic=True)
    G.stroke(d, box(-0.46, 1.1, 0.46, 1.24, seed=132, wob=0.002), M["red_f"], 0.0, cyclic=True)             # the stencil band
    for x in (-0.3, -0.12, 0.08, 0.26):
        G.seam(d, [(x, 1.14), (x + 0.08, 1.2)], M["ink"])
    G.seam(d, [(0.0, 0.1), (0.0, 1.82)], M["ink"])                                                          # the doors' split
    for sx in (-1, 1):
        for j in range(3):                                                                                # vents
            z = 1.62 - 0.08 * j
            G.seam(d, [(sx * 0.08, z), (sx * 0.36, z)], M["ink"])
        G.stroke(d, box(sx * 0.06 - 0.025, 0.8, sx * 0.06 + 0.025, 0.98, seed=133 + sx), M["off"], I, cyclic=True)   # handles
    G.rivets(d, [(-0.4, 0.14), (0.4, 0.14), (-0.4, 1.78), (0.4, 1.78)], M["ink"])
    G.hatch(d, -0.25, 0.45, M["ink"], n=3, length=0.1, spacing=0.035, angle_deg=65, seed=134)
    G.stroke(d, body, M["ink"], O, cyclic=True)
    G.stroke(d, box(-0.5, 1.86, 0.5, 1.98, seed=135), M["mustard"], O, cyclic=True)                       # the gold heat-shield cap
    for sx in (-1, 1):
        G.stroke(d, box(sx * 0.42 - 0.05, 0.0, sx * 0.42 + 0.05, 0.07, seed=136 + sx), M["umber"], I, cyclic=True)   # feet


B167 = {"flare_shelter": (flare_shelter, 272, 160, None, 1, False), "shelter_door": (mercury_shelter_door, 128, 192, "open", 6, False),
        "meridian_beacon": (mercury_beacon, 136, 224, None, 1, False), "solarite_cluster": (solarite_cluster, 128, 120, None, 1, False),
        "warden_vault_gate": (warden_vault_gate, 272, 256, None, 1, False), "equipment_locker": (equipment_locker, 80, 144, None, 1, False)}
PROPS.update(B167)
LOOPS = {"open": False}
INTERACTABLE = ("flare_shelter", "shelter_door", "meridian_beacon", "solarite_cluster", "warden_vault_gate", "equipment_locker")
SELF = {"flare_shelter": "static (v2: no clip); its door is shelter_door beside it at +2.6 m",
        "shelter_door": "open 6: the leaf swings in about its left hinge, the status lamp turns green at 4",
        "meridian_beacon": "static (v2: no clip); the Mars beacon's pulse 4 is ready if a card asks for it",
        "solarite_cluster": "static; the two states are UNITY's tint (glowing white / crusted)",
        "warden_vault_gate": "static (v2: no clip); the bell can take the Mars pylon's hum 4 later",
        "equipment_locker": "static (v2: no clip)"}


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
            "note": f"frame 0 = at rest (closed); {clip} plays once; the pivot sits on the ground line"}
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


def b167_review(out, imgs=None, widths=None, stamp_paths=()):
    """B-167's stamped review: the six props at 1x on the Mercury regolith strip beside the surveyor (the shelter with its
    door at +2.6 m as UNITY places them), the door's open clip at 1x, and the measured boxes per prop."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_c2_mercury_ground as MG
    import build_c2_mercury_plants as MPL
    import preview_c2_earth_rigs as PR
    names = list(B167)
    if imgs is None:
        imgs, widths = {}, {}
        for name in names:
            imgs[name], widths[name] = [], []
            for kk in range(PROPS[name][4]):
                im, w = render_prop(name, kk)
                imgs[name].append(im)
                widths[name] += w
    W, H = 1700, 470
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, "b-167 mercury props re-inked (d-150; the b-145 language, the mercury palette, no faces): flare shelter + its door, the beacon, "
                        "solarite, the warden vault gate, the locker", 6, 8)
    scene, _g = MPL.mercury_strip(W, H)
    base = H - 60
    S, _w = MG.sheets()
    rnd = np.random.default_rng(5)
    for c in range(W // 64 + 1):
        im = S["regolith"][int(rnd.integers(0, 8))]
        y0 = base - (MG.GS.FH - int(round(MG.GS.SURF * 64)))
        review._over(scene, im[:max(0, min(MG.GS.FH, H - y0))][:, :max(0, min(64, W - c * 64))], c * 64, y0)

    def stand(name, xc, f=0):
        im = imgs[name][f]
        review._over(scene, im, int(xc - im.shape[1] * 0.5), base - im.shape[0] + GROUND_PX)
    x = 180
    stand("flare_shelter", x)
    stand("shelter_door", x + 2.6 * 64)                                                    # PoiCatalog: the door at +2.6 m
    x += 2.6 * 64 + 200
    stand("meridian_beacon", x)
    x += 230
    stand("warden_vault_gate", x)
    x += 250
    stand("solarite_cluster", x)
    x += 120
    stand("equipment_locker", x)
    x += 90
    try:
        fr, piv = PR.surveyor_frame()
        review._over(scene, fr, int(x), base - fr.shape[0] + int(round(piv[1] * fr.shape[0])))
    except Exception:  # noqa: BLE001
        pass
    review._label(scene, "1x on the mercury regolith strip beside the surveyor (2 m): the shelter + its door (+2.6 m), the beacon, the vault gate, solarite, the locker", 6, 6)
    fw, fh = PROPS["shelter_door"][1], PROPS["shelter_door"][2]
    r = np.tile(review.PAPER, (fh + 30, W, 1)).astype(np.float32)
    for j, im in enumerate(imgs["shelter_door"]):
        review._over(r, im, 8 + j * (fw + 10), 26)
    review._label(r, "shelter_door open 6 at 1x (the leaf swings in about its left hinge; the lamp turns green at 4)", 6, 4)
    notes = []
    for name in names:
        sheet, meta, problems = sheet_meta(name, imgs[name])
        hits, _o = v3.palette_hits(sheet, "mercury", tints=[("offwhite", 0.30), ("mustard", 0.25)])
        ws = widths[name]
        outer = [w for w in ws if w[0] >= v3.OUTER_SPLIT]
        inner = [w for w in ws if w[0] < v3.OUTER_SPLIT]
        notes.append(f"{name} {meta['frame_width']}x{meta['frame_height']} x{meta['frames']}: ink {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} / "
                     f"{min(w[1] for w in inner):.1f}-{max(w[2] for w in inner):.1f} px, palette {hits * 100:.1f}%, json {'valid' if not problems else problems}, "
                     f"faces none, motion: {SELF[name]}")
    foot = np.tile(review.PAPER, (20 + 18 * len(notes), W, 1)).astype(np.float32)
    for i, t in enumerate(notes):
        review._label(foot, t, 6, 6 + 18 * i, scale=1)
    img = np.vstack([head, scene, r, foot])
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + (" export" if stamp_paths else " preview (not exported)"), 2, img.shape[0] - 16)
    review.write(out, img)
    print("written", out)
    for t in notes:
        print(" ", t)
    return []


def pivot_of(name):
    _fn, fw, fh, _c, _n, _t = PROPS[name]
    return (0.5, GROUND_PX / fh)


def render_prop(name, k=0, seed=7):
    fn, fw, fh, _c, _n, _t = PROPS[name]
    gp = fakegp.FakeGP()
    M = mats_b167(gp)                                   # mats() + the Mars / common names (B-167); the burrow's keys unchanged
    d = fakegp.FakeDrawing()
    fn(d, M, k)
    return GR.render_frame(fakegp.strokes_of(d, gp), fw, fh, PPU, pivot_of(name), ss=4, seed=seed)


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
    _fn, fw, fh, clip, n, _t = PROPS[name]
    if n > 1:                                           # B-167: a clip sheet (the door's open 6), the Mars props' layout
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
    if a[:m].any() or a[-m:].any() or a[:, :m].any() or a[:, -m:].any():
        problems.append(f"touches the {m} px frame edge")
    return sheet, meta, problems


def v2_leftovers(art, names=None):
    d = os.path.join(art, "props", "mercury")
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
        raise ValueError("Mercury prop export checks: " + "; ".join(problems))
    d = os.path.join(art, "props", "mercury")
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
    """The wyrm's idle + react frames (exact ids) with the burrow composited IN FRONT, as UNITY will draw them."""
    import numpy as np
    sp = CM.SPECIES["shadewyrm"]
    fw, fh = sp["frame"]
    mound, _w = render_prop("ice_burrow")
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
            M = sp["mats"](gp, "shadewyrm")
            d = fakegp.FakeDrawing()
            sp["draw"](d, M, poses[f], seed=5 * f)
            img, _w = GR.render_frame(fakegp.strokes_of(d, gp, as_object=("shadewyrm", "art")), fw, fh, 64, (0.5, 0.0), ss=4,
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
    """The den review: the burrow at 3x (ink, palette, json), then the wyrm's idle + react behind it at 2x."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    if imgs is None:
        imgs, widths = render_all()
    sheet, meta, problems = sheet_meta("ice_burrow", imgs["ice_burrow"])
    hits, _off = v3.palette_hits(sheet, "mercury")
    ws = widths["ice_burrow"]
    outer = [w for w in ws if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in ws if w[0] < v3.OUTER_SPLIT]
    W = 1700
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, f"review props/mercury/ice_burrow (b-145, d-126)  112x40  pivot {meta['pivot']}  ink {min(w[1] for w in outer):.2f}-"
                        f"{max(w[2] for w in outer):.2f} / {min(w[1] for w in inner):.2f}-{max(w[2] for w in inner):.2f} px  "
                        f"mercury palette {hits * 100:.1f}%  json {'valid' if not problems else '; '.join(problems)}", 6, 8)
    big = sheet.repeat(3, 0).repeat(3, 1)
    r1 = np.tile(review.PAPER, (big.shape[0] + 16, W, 1)).astype(np.float32)
    review._over(r1, big, 8, 8)
    review._label(r1, "3x: drawn in front of creatures/mercury/shadewyrm on the same pivot", big.shape[1] + 24, 10)
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
        review._label(r, f"den {clip} at 2x: the wyrm behind its burrow ({len(fr)} frames)", 6, 6)
        rows.append(r)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + (" export" if stamp_paths else " preview"), 2, img.shape[0] - 16)
    review.write(out, img)
    return problems


if __name__ == "__main__":
    if "--b167" in sys.argv:
        b167_review(sys.argv[1])
    else:
        print("problems", main(sys.argv[1]) or "-")
