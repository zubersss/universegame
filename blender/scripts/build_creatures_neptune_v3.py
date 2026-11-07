"""B-161 (C2 Neptune design prep): Neptune creature design previews on the B-132 kit, in the Neptune palette (D-148). Faces
kept, friendly or neutral, no teeth (D-087 / D-101). None of them is in Art yet (v2 never exported creatures/neptune), so
every key is new (no replaces_v2). Three reuse proven drawings: the kit's fish() (the Windrider's sail is a tall dorsal,
the Shadow shoal a small fish), Saturn's helium jelly (the Pressure phantom, its bell a translucent wash); the Anchor worm is
new. The wind blows +x (D-148): UNITY mirrors for a -x wind.

  windrider         192x112  a sail-finned floater surfing the gusts: a wind-cyan body, a tall wisp-white sail with ink veins,
                             pie eyes; idle 8 (a hover, the sail canting), glide 12 at index 1, react 8 (the sail furls, a
                             dart), bump 8; pivot at the centre
  shadow_shoal      64x48    small dark fish that dart in storms (UNITY spawns 5-9): deep-indigo bodies, a wind-cyan belly
                             rim, big wisp-white eyes; idle 8, swim 12 at index 1, react 8 (scatter), bump 8; centre pivot
  pressure_phantom  96x112   a shy ghost-jelly of Deck 3: a wisp-white bell at partial alpha (straight, D-147) round a
                             storm-violet core, its pie eyes inside, trailing veils; idle 10 (a pulse), drift 12, react 8
                             (it shoots up, veils wrapping), bump 10; centre pivot
  anchor_worm       256x80   holds floes against the wind: a segmented abyss-sage body, a round head with pie eyes and two
                             feelers, a beacon-coral hook tail (rounded, never sharp); idle 10, crawl 12 at index 1,
                             anchored 10 (braced, hook set, shivering), react 8 (lets go, recoils), bump 10; a floe walker:
                             pivot on the ground line

The Umbral Leviathan (apex) is a Grand rig set (D-140, 8 bones): its own builder, later. Design previews only.

  python -I build_creatures_neptune_v3.py <preview dir> [names]      lock-free (meridian.fakegp; exact stroke ids)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_earth_v3 as K  # noqa: E402  (the kit; gp_draw real in Blender, fakegp outside)
import build_creatures_saturn_v3 as CS  # noqa: E402  (the helium jelly's drawing)
from meridian import v3  # noqa: E402

G = K.G
P = v3.PALETTES["neptune"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi


def SH(h):
    return v3.shadow_of(h, "neptune")


def DP(h):
    return v3.deep_of(h, "neptune")


FISH = {    # the kit's fish() materials: coat / far (fins, sail) / back tone / belly / spots
    "windrider": dict(coat=P["teal"], coat_sh=SH(P["teal"]), coat_dp=DP(P["teal"]), far=P["offwhite"], light=SH(P["offwhite"]),
                      light_sh=DP(P["offwhite"]), spot=P["offwhite"]),
    "shadow_shoal": dict(coat=SH(P["sky"]), coat_sh=DP(P["sky"]), coat_dp=P["brown"], far=DP(P["sky"]), light=P["teal"],
                         light_sh=SH(P["teal"]), spot=P["teal"]),
}
ALIAS = {   # the material names a reused drawing uses -> Neptune's slots
    "pressure_phantom": {"gold": "offwhite", "salmon": "mustard", "cream": "offwhite", "slate": "brown"},
    "anchor_worm": {"sage": "green", "coral": "red", "cyan": "teal", "indigo": "brown", "wisp": "offwhite"},
}
GHOST = 0.72                                   # the phantom's bell: a flat translucent wash (straight alpha)


def mats(gp, sp):
    def m(name, **kw):
        return G.mat(gp, f"{sp}_{name}", **kw)
    out = {"ink": m("ink", fill=None), "pupil": m("pupil", fill=G.INK, ink=False), "eye": m("eye_white", fill=P["offwhite"]),
           "mouth": m("mouth", fill=DP(P["red"])), "star": m("star", fill=P["offwhite"]),
           "puff": m("puff", fill=P["offwhite"]), "puff_sh": m("puff_mid", fill=SH(P["offwhite"]), ink=False),
           "claw": m("claw", fill=P["offwhite"], behind=True), "horn": m("horn", fill=P["offwhite"], behind=True)}
    if sp in FISH:
        C = FISH[sp]
        out.update({"coat": m("coat", fill=C["coat"]), "coat_i": m("coat_inner", fill=C["coat"]), "far": m("far", fill=C["far"]),
                    "sh": m("coat_mid", fill=C["coat_sh"], ink=False), "dp": m("coat_deep", fill=C["coat_dp"], ink=False),
                    "light": m("light", fill=C["light"]), "light_f": m("light_f", fill=C["light"], ink=False),
                    "light_sh": m("light_mid", fill=C["light_sh"], ink=False), "spot": m("spot", fill=C["spot"], ink=False)})
        return out
    for key, slot in ALIAS[sp].items():
        h = P[slot]
        alpha = GHOST if (sp == "pressure_phantom" and key == "gold") else 1.0
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False, fill_alpha=alpha)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False, fill_alpha=alpha)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
        out[key + "_b"] = m(key + "_behind", fill=h, behind=True)
    out["leg"], out["coat"] = m("leg", fill=SH(P["green"])), m("coat", fill=SH(P["green"]))
    out["leg_far"], out["far"] = m("leg_far", fill=DP(P["green"])), m("far", fill=DP(P["green"]))
    return out


# ---------------------------------------------------------------- windrider (surfs the gusts on its sail)
def draw_windrider(d, M, pose=None, seed=0):
    p = K.water_pose()
    p.update(dict(sail=1.0, cant=0.0))
    p.update(pose or {})
    D = G.Xf(d, K.water_xf(p, ox=0.12))
    prof = lambda s: 0.15 * (math.sin(math.pi * (0.10 + 0.82 * s))) ** 0.6 * (1 - 0.45 * s * s) + 0.014   # noqa: E731
    sail = 0.52 * p["sail"]
    at = K.fish(D, M, p, 1.42, prof, snout=1.7, seed=seed, tail_len=0.28, tail_low=0.85,
                dorsal=(0.14, 0.64, sail, -0.10 - 0.12 * p["cant"]), anal=(0.66, 0.80, 0.06, -0.03), pect=(0.26, 0.5, 0.16),
                spots=[(0.34, 0.55, 0.016), (0.46, 0.60, 0.014), (0.58, 0.50, 0.015)])
    if p["speed"] > 0:
        K.speed_lines(D, M, -0.95, (-0.04, 0.06), p["speed"])
    if p["stars"] is not None:
        q = at(0.10, 0.3)
        K.stars(D, M, q[0], q[1] + 0.2, 0.14, p["stars"])


def windrider_poses():
    out = K.pike_poses()[:36]                                    # idle 8, swim 12 (the glide), react 8, bump 8
    for i, q in enumerate(out):
        if i < 8:                                                # idle: the sail cants with the gusts
            q.update(cant=0.5 * math.sin(TAU * i / 8), amp=0.012)
        elif i < 20:                                             # glide: the sail full, leaning
            q.update(cant=0.6 + 0.2 * math.sin(TAU * (i - 8) / 6), amp=0.03)
        elif i < 28:                                             # react: the sail furls, a dart
            q.update(sail=[0.7, 0.45, 0.3, 0.3, 0.35, 0.5, 0.75, 0.95][i - 20])
        else:                                                    # bump: the knock-back without stretching the sail off the frame
            q.update(stretch=1.0 + 0.5 * (q.get("stretch", 1.0) - 1.0), tilt=0.5 * q.get("tilt", 0.0), sail=0.8)
    return out


# ---------------------------------------------------------------- shadow shoal (dark, fast; curious, never biting)
def draw_shadow_shoal(d, M, pose=None, seed=0):
    p = K.water_pose()
    p.update(pose or {})
    p["eye_pop"] = p["eye_pop"] * 1.35                           # big eyes: they read on the dark by their eyes
    D = G.Xf(d, K.water_xf(p, ox=0.03))
    prof = lambda s: 0.075 * (math.sin(math.pi * (0.10 + 0.82 * s))) ** 0.6 * (1 - 0.45 * s * s) + 0.008   # noqa: E731
    at = K.fish(D, M, p, 0.40, prof, snout=1.5, seed=seed, tail_len=0.10, tail_low=1.0, dorsal=(0.40, 0.62, 0.05, -0.02),
                anal=(0.62, 0.78, 0.035, -0.02), pect=(0.26, 0.5, 0.05), rays=False, gill=0.24)
    if p["speed"] > 0:
        K.speed_lines(D, M, -0.22, (-0.02, 0.03), p["speed"] * 0.25)
    if p["stars"] is not None:
        q = at(0.10, 0.3)
        K.stars(D, M, q[0], q[1] + 0.12, 0.07, p["stars"])


def shoal_poses():
    out = K.pike_poses()[:36]                                    # idle 8, swim 12, react 8 (scatter), bump 8
    for q in out:                                                # a 0.4 m fish: the pike's darts and knock-backs scaled to its size
        q["shift"] = 0.35 * q.get("shift", 0.0)
        q["stretch"] = 1.0 + 0.6 * (q.get("stretch", 1.0) - 1.0)
    return out


# ---------------------------------------------------------------- pressure phantom (a shy ghost-jelly of Deck 3)
def draw_pressure_phantom(d, M, pose=None, seed=0):
    CS.draw_helium_jelly(d, M, pose, seed)                       # the bell is the translucent gold_f (wisp white at GHOST alpha)


def phantom_poses():
    return CS.jelly_poses()


# ---------------------------------------------------------------- anchor worm (holds floes against the wind)
WORM_N = 9
WORM_R = [0.10, 0.12, 0.14, 0.15, 0.155, 0.155, 0.15, 0.15, 0.17]   # tail .. head


def draw_anchor_worm(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(hump=-1.0, wave=0.0, hook=0.0, brace=0.0, shiver=0.0))
    p.update(pose or {})
    B = K.Body(p, (0.0, 0.0))
    db = G.Xf(d, B)
    L = 2.3 * (1 - 0.12 * p["brace"])
    xs = [-L / 2 + L * i / (WORM_N - 1) for i in range(WORM_N)]
    segs = []
    for i, (x, r) in enumerate(zip(xs, WORM_R)):
        hz = 0.32 * math.exp(-((x - p["hump"]) / 0.32) ** 2) if p["hump"] > -1.0 else 0.0     # the crawl's travelling hump
        wz = 0.02 * (0.5 + 0.5 * math.sin(p["wave"] + 1.1 * i))                       # the ripple only lifts (the ground line)
        sx = p["shiver"] * (0.012 if i % 2 else -0.012)
        segs.append((x + sx, r + hz + wz, r))
    tx, tz, tr = segs[0]                                         # the hook tail (behind the body): rounded, beacon coral
    hc, hr_ = (tx - 0.2, tz + 0.12), 0.17                                      # a big curl up over the tail; set = its tip down on the floe
    a0, a1 = math.radians(-20), math.radians(200 + 70 * p["hook"])
    hook = [(hc[0] + hr_ * math.cos(a0 + (a1 - a0) * k / 12), max(0.03, hc[1] + hr_ * math.sin(a0 + (a1 - a0) * k / 12))) for k in range(13)]
    tip = hook[-1]
    G.stroke(db, G.hose_outline(hook, 0.07), M["coral_f"], 0.0, cyclic=True)
    G.stroke(db, G.lumpy_ellipse(tip[0], max(tip[1], 0.07), 0.07, 0.065, n=12, seed=seed + 9), M["coral"], O, cyclic=True)   # the rounded tip
    G.stroke(db, G.hose_outline(hook, 0.07), M["ink"], O, cyclic=True)
    for i, (x, z, r) in enumerate(segs):                         # segments tail to head (each overlaps the last)
        blob = [(bx, max(bz, 0.0)) for bx, bz in G.lumpy_ellipse(x, z, r * 1.3, r * 0.92, n=20, lump=0.05, seed=seed + 20 + i)]
        G.stroke(db, blob, M["sage_f"], 0.0, cyclic=True)
        G.stroke(db, [q for q in blob if q[1] < z - r * 0.35] + [(x, z - r * 0.35)], M["sage_sh"], 0.0, cyclic=True)   # the belly tone
        G.stroke(db, blob, M["ink"], O if i in (0, WORM_N - 1) else I, cyclic=True)
        if i < WORM_N - 1:
            G.seam(db, [(x + r * 0.3, z + r * 0.75), (x + r * 0.45, z + r * 0.2)], M["ink"])   # the ring seam
    hx, hz, hr = segs[-1]
    G.stroke(db, [(qx, max(qz, 0.0)) for qx, qz in G.lumpy_ellipse(hx, hz, hr * 1.3, hr * 0.92, n=20, seed=seed + 20 + WORM_N - 1)], M["ink"], O, cyclic=True)
    H = K.turn((hx, hz), p["head_rot"], p["head"], B)
    dh = G.Xf(d, H)
    for k in (0, 1):                                             # two feelers, bending back with the wind
        G.stroke(dh, G.bezier((hx + 0.03 + 0.06 * k, hz + hr * 0.9), (hx - 0.02 + 0.06 * k, hz + hr + 0.12), (hx - 0.10 + 0.06 * k, hz + hr + 0.16 - 0.02 * p["brace"]), n=6),
                 M["ink"], I)
        G.stroke(dh, G.lumpy_ellipse(hx - 0.10 + 0.06 * k, hz + hr + 0.16 - 0.02 * p["brace"], 0.02, 0.02, n=8, seed=seed + 40 + k), M["cyan"], I, cyclic=True)
    K.eyes(dh, M, hx + 0.03, hz + 0.04, 0.036, 0.046, 0.065, p, seed)
    if p["mouth"] > 0.05:
        G.stroke(dh, G.lumpy_ellipse(hx + 0.13, hz - 0.06, 0.018 + 0.01 * p["mouth"], 0.012 + 0.014 * p["mouth"], n=10, seed=seed + 4), M["mouth"], I, cyclic=True)
    else:
        G.seam(dh, G.bezier((hx + 0.07, hz - 0.05), (hx + 0.12, hz - 0.08), (hx + 0.16, hz - 0.04), n=5), M["ink"])
    if p["stars"] is not None:
        K.stars(dh, M, hx, hz + hr + 0.22, 0.12, p["stars"])


def worm_poses():
    out = []
    for i in range(10):                                          # idle: a ripple along the rings, a blink
        ph = TAU * i / 10
        out.append(dict(wave=ph, bob=0.0, blink={6: 0.6, 7: 1.0}.get(i, 0.0), look=(0.6, 0.0)))
    for i in range(12):                                          # crawl: a hump runs tail to head (UNITY moves it)
        out.append(dict(hump=-1.1 + 2.3 * i / 11, wave=TAU * i / 12, look=(0.9, 0.0)))
    for i in range(10):                                          # anchored: braced, the hook set, shivering in the gale
        out.append(dict(brace=1.0, hook=1.0, shiver=1.0 if i % 2 else -1.0, sz=0.96, head=(-0.02, 0.0), look=(0.8, -0.1),
                        blink={7: 1.0}.get(i, 0.0)))
    for i in range(8):                                           # react: lets go, recoils
        out.append(dict(hook=max(0.0, 1.0 - 0.4 * i), shift=-0.03 * min(i, 4), sz=[0.85, 0.82, 0.9, 1.04, 1.02, 0.99, 1.0, 1.0][i],
                        eye_pop=1.5 if i < 3 else 1.1, mouth=0.5 if i in (1, 2) else 0.0, look=(-0.6, 0.0) if i < 4 else (0.8, 0.0)))
    for q in K.bump_clip():                                      # bump: a 2.3 m body must not rock (its ends would dip under the line)
        q.pop("legs", None)
        q.update(rock=0.0, lean=0.5 * q.get("lean", 0.0), shift=0.4 * q.get("shift", 0.0), sz=1.0 + 0.5 * (q.get("sz", 1.0) - 1.0))
        out.append(q)
    return out


SPECIES = {
    "windrider": dict(draw=draw_windrider, poses=windrider_poses, mats=mats, frame=(192, 112), seed=91, pivot=(0.5, 0.5),
                      clips=[("idle", 8, True), ("glide", 12, True), ("react", 8, False), ("bump", 8, False)],
                      self_check={"ink": "the sail's veins, fin rays, the lateral line, gill and spots", "motion": "a hover with the sail canting; glides; react furls the sail",
                                  "original": "our own sail-finned floater: a fish that tacks like a sailboat"},
                      ours="a wind-cyan fish that surfs Neptune's gale on a tall wisp-white sail"),
    "shadow_shoal": dict(draw=draw_shadow_shoal, poses=shoal_poses, mats=mats, frame=(64, 48), seed=92, pivot=(0.5, 0.5),
                         clips=[("idle", 8, True), ("swim", 12, True), ("react", 8, False), ("bump", 8, False)],
                         self_check={"ink": "the gill line, the belly rim, the fins", "motion": "darts; react scatters (UNITY moves the shoal)",
                                     "original": "our own small storm fish read by their big eyes; curious, never biting (D-087)"},
                         ours="little indigo fish with big pale eyes that swirl round the surveyor's lamp in the storms"),
    "pressure_phantom": dict(draw=draw_pressure_phantom, poses=phantom_poses, mats=mats, frame=(96, 112), seed=93, pivot=(0.5, 0.5),
                             clips=[("idle", 10, True), ("drift", 12, True), ("react", 8, False), ("bump", 10, False)],
                             self_check={"ink": "the bell's seams, the frill, the veils", "motion": "a slow pulse; drifts with veils trailing; react shoots up",
                                         "original": "Saturn's helium jelly re-drawn as a translucent ghost: a cousin, not a copy of a real jellyfish"},
                             ours="a shy see-through ghost-jelly with a violet heart that hides behind its own veils"),
    "anchor_worm": dict(draw=draw_anchor_worm, poses=worm_poses, mats=mats, frame=(256, 80), seed=94,
                        clips=[("idle", 10, True), ("crawl", 12, True), ("anchored", 10, True), ("react", 8, False), ("bump", 10, False)],
                        self_check={"ink": "ring seams, the belly tone, the hook, the feelers", "motion": "a ripple; the crawl's travelling hump; anchored shivers in the gale",
                                    "original": "our own segmented worm that lassos floes with a rounded coral hook tail"},
                        ours="a sage ring-worm that hooks its tail into a floe and digs in against the gale"),
}
HABITAT = {"windrider": "deck1", "shadow_shoal": "storm", "pressure_phantom": "deck3", "anchor_worm": "deck2"}
SOURCES = os.path.join(os.path.dirname(HERE), "sources", "creatures")


def build(name, out=None):
    """The source .blend for one Neptune creature (inside Blender): one GP object, one drawing per frame, clip markers."""
    import bpy
    sp = SPECIES[name]
    out = out or os.path.join(SOURCES, f"neptune_{name}_v3.blend")
    scene = G.new_scene()
    coll = G.collection(name)
    ob, gp = G.gp_object(name, coll)
    M = sp["mats"](gp, name)
    layer = gp.layers.new("art")
    for f, pose in enumerate(sp["poses"]()):
        sp["draw"](G.drawing(layer, f + 1), M, pose, seed=5 * f)
    G.mark_clips(scene, [(c, n) for c, n, _l in sp["clips"]])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


def build_windrider(out=None):          # manifest build_fn: render.py passes the source path
    return build("windrider", out)


def build_shadow_shoal(out=None):
    return build("shadow_shoal", out)


def build_pressure_phantom(out=None):
    return build("pressure_phantom", out)


def build_anchor_worm(out=None):
    return build("anchor_worm", out)


def entry_for(name):
    sp = SPECIES[name]
    return {"key": f"creatures/neptune/{name}", "style": "v3", "source": f"sources/creatures/neptune_{name}_v3.blend",
            "build": "scripts/build_creatures_neptune_v3.py", "build_fn": f"build_{name}", "collection": name,
            "frame": list(sp["frame"]), "pivot": list(sp.get("pivot", (0.5, 0.0))), "facing": "right", "squash_root": True,
            "planet": "neptune", "seed": sp["seed"], "bg_scene": HABITAT[name], "beside": "characters/surveyor/side",
            "review_name": f"b161_neptune_{name}", "clips": [{"name": c, "frames": n, "loop": lp} for c, n, lp in sp["clips"]],
            "self_check": dict(sp["self_check"], style="the B-132 kit (Gus's construction); LEAD judges"), "ours": sp["ours"],
            "note": "B-161 design (new Neptune creatures; no v2 export to replace); floaters pivot at the body centre, the Anchor worm on the ground line"}


def preview(out_dir, name="windrider"):
    """The export's review layout from exact frames (as_object ids, ss 4) on the placeholder background (centre-pivot
    creatures: all four edges checked; the worm: sides + top and the ground line)."""
    import json
    import numpy as np
    from meridian import fakegp, pngio
    import gp_raster as GR
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    sp = SPECIES[name]
    fw, fh = sp["frame"]
    piv = sp.get("pivot", (0.5, 0.0))
    frames, widths, below = [], [], []
    for f, pose in enumerate(sp["poses"]()):
        gp = fakegp.FakeGP()
        M = mats(gp, name)
        d = fakegp.FakeDrawing()
        sp["draw"](d, M, pose, seed=5 * f)
        st = fakegp.strokes_of(d, gp, as_object=(name, "art"))
        if piv[1] == 0.0 and min(float((s_["xz"][:, 1] - s_["radius"] * 1.2).min()) for s_ in st) * 64 < -2.0:
            below.append(f)                                                            # feet-pivot creatures: the ground line
        img, w = GR.render_frame(st, fw, fh, 64, piv, ss=4, seed=sp["seed"] * 1000 + f + 1)
        frames.append(img)
        widths += w
    cols = v3.columns_for(fw, len(frames))
    rows = -(-len(frames) // cols)
    sheet = np.zeros((rows * fh + (rows - 1) * 4, min(cols, len(frames)) * fw + (min(cols, len(frames)) - 1) * 4, 4), np.uint8)
    for i, im in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * (fh + 4):r * (fh + 4) + fh, c * (fw + 4):c * (fw + 4) + fw] = im
    anims, s_ = [], 0
    for c, n, lp in sp["clips"]:
        anims.append({"name": c, "start": s_, "length": n, "loop": lp, **({"loop_from": 0} if lp else {})})
        s_ += n
    meta = {"key": f"creatures/neptune/{name}", "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": 4,
            "frames": len(frames), "fps": 12, "pivot": list(piv), "facing": "right", "ppu": 64, "animations": anims, "squash_root": True}
    problems = v3.validate_sheet(meta, sheet.shape)
    bottom = piv[1] != 0.0
    clipped = [i for i, im in enumerate(frames) if im[:2, :, 3].any() or (bottom and im[-2:, :, 3].any()) or im[:, :2, 3].any() or im[:, -2:, 3].any()]
    if clipped:
        problems.append(f"frames {clipped[:8]} touch the 2 px edge")
    if below:
        problems.append(f"frames {below[:8]} below the ground line")
    dd = os.path.join(out_dir, "b161_neptune")
    os.makedirs(dd, exist_ok=True)
    png = os.path.join(dd, f"{name}_color.png")
    nb = pngio.write_png(png, sheet)
    with open(os.path.join(dd, f"{name}.json"), "w", encoding="utf-8", newline="\n") as f_:
        json.dump(meta, f_, indent=2)
    outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
    stats = {"outer_px": (min(w[1] for w in outer), max(w[2] for w in outer)), "inner_px": (min(w[1] for w in inner), max(w[2] for w in inner)),
             "inner_n": len(inner), "palette": v3.palette_hits(sheet, "neptune"), "problems": problems,
             "sheet_wh": (sheet.shape[1], sheet.shape[0]), "png_kb": nb // 1024}
    out = os.path.join(out_dir, f"review_b161_neptune_{name}_preview.png")
    boxes = review.v3_sheet_review(entry_for(name), meta, frames, png, out, stats)
    print(name, f"sheet {sheet.shape[1]}x{sheet.shape[0]} {nb // 1024} KB, ink {stats['outer_px'][0]:.2f}-{stats['outer_px'][1]:.2f} / "
          f"{stats['inner_px'][0]:.2f}-{stats['inner_px'][1]:.2f}, palette {stats['palette'][0] * 100:.1f}% {stats['palette'][1][:3]}, "
          f"problems {problems or '-'}, boxes not x: {','.join(k for k, (mk, _n) in boxes.items() if mk != 'x') or '-'}")


if __name__ == "__main__":
    for _n in (sys.argv[2:] or list(SPECIES)):
        preview(sys.argv[1], _n)
