"""B-158 (C2 Uranus design prep): Uranus creature design previews on the B-132 kit, in the Uranus palette (D-142). Faces
kept, friendly or neutral, no teeth (D-087 / D-101). Two reuse proven drawings under Uranus' colours (mats() answers to the
Jupiter / Venus material names: the stormglider's manta becomes the Methane ray, the pressure crab the Hailcrab, its
sulphur crust now diamonds); two are new.

  frostwisp    64x80    luminous: an ice-white wisp with an ember heart (a tone), pie eyes; idle 10 (a hover, the heart
                        flickers), drift 12 at index 1, react 8 (darts away), bump 10; pivot at the centre
  methane_ray  176x96   glides between floes: a methane-cyan back, an ice-white belly, a whip tail (the stormglider's
                        drawing); idle 10, glide 12 at index 1, react 8 (a roll away), bump 10; pivot at the centre
  hailcrab     128x80   its shell catches diamonds: a night-slate shell with ice-white diamonds and rim, methane-cyan claws
                        that wave (never pinch, D-087), eye stalks (the pressure crab's drawing); idle 10, walk 12, react 8
                        (into its shell), bump 10; a floe walker: pivot on the ground line
  tiltbird     128x96   migrates with the season: an ice-white bird flying tilted with the planet, methane-cyan wings, a
                        frost-mint crest, a small rounded beak; idle 10, fly 12 at index 1, react 8, bump 10; pivot at the centre

The Diamondback Colossus (apex) is a Grand rig set (D-140): build_diamondback_v3.py. Design previews only.

  python -I build_creatures_uranus_v3.py <preview dir> [names]      lock-free (meridian.fakegp; exact stroke ids)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_earth_v3 as K  # noqa: E402  (the kit; gp_draw real in Blender, fakegp outside)
import build_creatures_jupiter_v3 as CJ  # noqa: E402  (the stormglider's drawing)
import build_creatures_venus_v3 as CV  # noqa: E402  (the pressure crab's drawing)
from meridian import v3  # noqa: E402

G = K.G
P = v3.PALETTES["uranus"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi
ALIAS = {   # the material names each drawing uses -> Uranus' slots
    "methane_ray": {"rust": "teal", "cream": "offwhite", "umber": "brown"},
    "hailcrab": {"basalt": "brown", "sulphur": "offwhite", "cream": "offwhite", "vent": "teal"},
    "frostwisp": {"ice": "offwhite", "ember": "red", "fog": "sky", "cyan": "teal"},
    "tiltbird": {"ice": "offwhite", "cyan": "teal", "mint": "green", "slate": "brown", "fog": "sky"},
}


def SH(h):
    return v3.shadow_of(h, "uranus")


def DP(h):
    return v3.deep_of(h, "uranus")


def mats(gp, sp):
    def m(name, **kw):
        return G.mat(gp, f"{sp}_{name}", **kw)
    out = {"ink": m("ink", fill=None), "pupil": m("pupil", fill=G.INK, ink=False), "eye": m("eye_white", fill=P["offwhite"]),
           "mouth": m("mouth", fill=DP(P["teal"])), "star": m("star", fill=P["mustard"]),
           "puff": m("puff", fill=P["offwhite"]), "puff_sh": m("puff_mid", fill=SH(P["offwhite"]), ink=False)}
    for key, slot in ALIAS[sp].items():
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
        out[key + "_b"] = m(key + "_behind", fill=h, behind=True)
    legs = "brown" if sp == "hailcrab" else "sky"
    out["leg"], out["coat"] = m("leg", fill=SH(P[legs])), m("coat", fill=SH(P[legs]))
    out["leg_far"], out["far"] = m("leg_far", fill=DP(P[legs])), m("far", fill=DP(P[legs]))
    out["claw"] = m("claw", fill=P["offwhite"], behind=True)
    return out


# ---------------------------------------------------------------- frostwisp (leads you to warmth or danger)
def draw_frostwisp(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(flicker=0.0, trail=0.0))
    p.update(pose or {})
    B = K.Body(p, (0.0, 0.0))
    db = G.Xf(d, B)
    tail = [(-0.05 - 0.32 * t, 0.06 * math.sin(p["flicker"] + 5 * t) * t - 0.12 * t * (1 + p["trail"])) for t in [k / 10 for k in range(11)]]
    for j, w in enumerate((0.09, 0.06, 0.035)):                                           # the wisp's trailing tail, tapering
        seg = tail[3 * j:3 * j + 5]
        if len(seg) > 1:
            G.stroke(db, G.hose_outline(seg, w), M["ice_sh"] if j else M["ice_f"], 0.0, cyclic=True)
    body = G.lumpy_ellipse(0.0, 0.0, 0.16, 0.15, n=26, lump=0.06, seed=seed + 1)
    G.stroke(db, body, M["ice_f"], 0.0, cyclic=True)
    k = 0.75 + 0.25 * math.sin(p["flicker"] * 2)
    G.stroke(db, G.lumpy_ellipse(-0.01, -0.03, 0.08 * k, 0.07 * k, n=16, lump=0.1, seed=seed + 2), M["ember_sh"], 0.0, cyclic=True)   # the heart (a tone)
    G.stroke(db, G.lumpy_ellipse(-0.01, -0.03, 0.035 * k, 0.03 * k, n=12, seed=seed + 3), M["ember_f"], 0.0, cyclic=True)
    G.stroke(db, body, M["ink"], O, cyclic=True)
    H = K.turn((0.02, 0.02), p["head_rot"], p["head"], B)
    dh = G.Xf(d, H)
    K.eyes(dh, M, 0.05, 0.06, 0.026, 0.034, 0.05, p, seed)
    if p["mouth"] > 0.05:
        G.stroke(dh, G.lumpy_ellipse(0.09, -0.02, 0.014 + 0.008 * p["mouth"], 0.01 + 0.01 * p["mouth"], n=10, seed=seed + 4), M["mouth"], I, cyclic=True)
    if p["stars"] is not None:
        K.stars(dh, M, 0.0, 0.22, 0.1, p["stars"])


def wisp_poses():
    out = []
    for i in range(10):
        ph = TAU * i / 10
        out.append(dict(flicker=ph * 2, bob=0.03 * math.sin(ph), blink={6: 0.6, 7: 1.0}.get(i, 0.0), look=(0.6, 0.1)))
    for i in range(12):
        ph = TAU * i / 6
        out.append(dict(flicker=ph * 2, bob=0.02 * math.sin(ph), trail=0.6, rock=-0.15, look=(0.9, 0.0)))
    for i in range(8):                                                                     # react: darts away (UNITY moves it)
        out.append(dict(flicker=3 * i, trail=1.0 - 0.1 * i, rock=0.25 if i < 4 else 0.05, shift=-0.01 * min(i, 4), eye_pop=1.5 if i < 3 else 1.1,
                        mouth=0.5 if i in (1, 2) else 0.0))
    out += [dict(q, shift=0.0, sz=1 + 0.5 * (q.get("sz", 1.0) - 1), head=(0.0, 0.3 * q.get("head", (0.0, 0.0))[1])) for q in K.bump_clip()]   # the tail fits
    return out


# ---------------------------------------------------------------- tiltbird (migrates with the season, flies tilted)
TILT = 0.38                                                                                 # it leans with the planet


def draw_tiltbird(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(flap=0.0))
    p.update(pose or {})
    p["rock"] = p["rock"] + TILT
    B = K.Body(p, (0.0, 0.0))
    db = G.Xf(d, B)
    f = math.sin(p["flap"])

    def wing(up, near):
        tip = (-0.18, up * (0.34 + 0.16 * f))
        shape = [(0.12, up * 0.03), (0.0, up * (0.22 + 0.1 * f)), tip, (-0.26, up * (0.18 + 0.08 * f)), (-0.2, up * 0.03)]
        G.stroke(db, shape, M["cyan_f" if near else "cyan_sh"], 0.0, cyclic=True)
        G.seam(db, [(0.06, up * 0.06), (-0.12, up * (0.24 + 0.1 * f))], M["ink"])
        G.stroke(db, shape, M["ink"], O if near else I, cyclic=True)
    wing(1, False)
    tail = [(-0.22, 0.0), (-0.38, 0.06), (-0.36, -0.04)]
    G.stroke(db, tail, M["cyan_sh"], I, cyclic=True)
    body = G.lumpy_ellipse(0.0, 0.0, 0.24, 0.11, n=26, lump=0.02, seed=seed + 1)
    G.stroke(db, body, M["ice_f"], 0.0, cyclic=True)
    G.stroke(db, [q for q in body if q[1] < -0.03] + [(0.0, -0.03)], M["fog_sh"], 0.0, cyclic=True)
    G.stroke(db, body, M["ink"], O, cyclic=True)
    H = K.turn((0.2, 0.03), p["head_rot"], p["head"], B)
    dh = G.Xf(d, H)
    hx, hz = 0.28, 0.07
    for j in range(3):                                                                     # the frost-mint crest
        a = math.radians(110 + 20 * j)
        G.stroke(dh, [(hx - 0.02, hz + 0.06), (hx - 0.02 + 0.1 * math.cos(a), hz + 0.06 + 0.1 * math.sin(a)), (hx + 0.01, hz + 0.07)], M["mint"], I, cyclic=True)
    head = G.lumpy_ellipse(hx, hz, 0.085, 0.075, n=20, seed=seed + 2)
    G.stroke(dh, head, M["ice_f"], 0.0, cyclic=True)
    G.stroke(dh, head, M["ink"], O, cyclic=True)
    G.stroke(dh, [(hx + 0.07, hz - 0.005), (hx + 0.14, hz - 0.02), (hx + 0.07, hz - 0.04)], M["mint"], I, cyclic=True)   # a small rounded beak
    K.eyes(dh, M, hx + 0.01, hz + 0.015, 0.02, 0.026, 0.038, p, seed)
    wing(-1, True)
    if p["stars"] is not None:
        K.stars(dh, M, hx, hz + 0.2, 0.1, p["stars"])


def tiltbird_poses():
    out = []
    for i in range(10):
        ph = TAU * i / 5
        out.append(dict(flap=ph, bob=0.02 * math.sin(ph + 1), blink={7: 1.0}.get(i, 0.0), look=(0.6, 0.0)))
    for i in range(12):
        ph = TAU * i / 6
        out.append(dict(flap=ph, bob=0.03 * math.sin(ph + 1), rock=-0.06, look=(0.9, 0.0)))
    for i in range(8):                                                                     # react: a startled flutter, more tilted
        out.append(dict(flap=TAU * i / 2, rock=0.25 * (1 if i % 2 else 0.5), eye_pop=1.5 if i < 3 else 1.1, mouth=0.4 if i in (1, 2) else 0.0))
    out += [dict(q, shift=0.4 * q.get("shift", 0.0), sz=1 + 0.5 * (q.get("sz", 1.0) - 1)) for q in K.bump_clip()]
    return out


SPECIES = {
    "frostwisp": dict(draw=draw_frostwisp, poses=wisp_poses, mats=mats, frame=(64, 80), seed=81, pivot=(0.5, 0.5),
                      clips=[("idle", 10, True), ("drift", 12, True), ("react", 8, False), ("bump", 10, False)],
                      self_check={"ink": "the body's lumpy edge, the tail's taper", "motion": "a hover, the ember heart flickers; react darts away",
                                  "original": "our own ice wisp with a warm heart; it leads, never attacks"},
                      ours="a little ice-white wisp with a glowing ember heart that drifts ahead of you toward warmth"),
    "methane_ray": dict(draw=CJ.draw_stormglider, poses=CJ.glider_poses, mats=mats, frame=(176, 96), seed=82, pivot=(0.5, 0.5),
                        clips=[("idle", 10, True), ("glide", 12, True), ("react", 8, False), ("bump", 10, False)],
                        self_check={"ink": "wing stripes, body specks, the belly line, the whip tail", "motion": "glides between floes; react rolls away",
                                    "original": "the stormglider's manta in Uranus' methane cyan: a cousin, not a copy of a real ray"},
                        ours="a methane-cyan manta gliding silently between the ice floes"),
    "hailcrab": dict(draw=CV.draw_pressure_crab, poses=CV.crab_poses, mats=mats, frame=(128, 80), seed=83,
                     clips=[("idle", 10, True), ("walk", 12, True), ("react", 8, False), ("bump", 10, False)],
                     self_check={"ink": "shell ridges, the diamonds' edges, the lit rim, claw seams", "motion": "claws wave, a shuffle; react: into its shell",
                                 "original": "our own hail crab with diamonds caught on its shell; claws wave, never pinch (D-087)"},
                     ours="a slate-shelled crab whose back glitters with the diamonds it catches from the hail"),
    "tiltbird": dict(draw=draw_tiltbird, poses=tiltbird_poses, mats=mats, frame=(128, 96), seed=84, pivot=(0.5, 0.5),
                     clips=[("idle", 10, True), ("fly", 12, True), ("react", 8, False), ("bump", 10, False)],
                     self_check={"ink": "wing seams, the crest, the beak", "motion": "flies tilted with the planet; react: a startled flutter",
                                 "original": "our own tilted bird with a frost-mint crest; it migrates with the season"},
                     ours="an ice-white bird that always flies leaning sideways, as Uranus itself does"),
}
HABITAT = {"frostwisp": "deck1_night", "methane_ray": "deck1_sun_left", "hailcrab": "deck2_sun_left", "tiltbird": "deck1_sun_right"}
SOURCES = os.path.join(os.path.dirname(HERE), "sources", "creatures")


def build(name, out=None):
    """The source .blend for one Uranus creature (inside Blender): one GP object, one drawing per frame, clip markers."""
    import bpy
    sp = SPECIES[name]
    out = out or os.path.join(SOURCES, f"uranus_{name}_v3.blend")
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


def build_frostwisp(out=None):          # manifest build_fn: render.py passes the source path
    return build("frostwisp", out)


def build_methane_ray(out=None):
    return build("methane_ray", out)


def build_hailcrab(out=None):
    return build("hailcrab", out)


def build_tiltbird(out=None):
    return build("tiltbird", out)


def entry_for(name):
    sp = SPECIES[name]
    return {"key": f"creatures/uranus/{name}", "style": "v3", "source": f"sources/creatures/uranus_{name}_v3.blend",
            "build": "scripts/build_creatures_uranus_v3.py", "build_fn": f"build_{name}", "collection": name,
            "frame": list(sp["frame"]), "pivot": list(sp.get("pivot", (0.5, 0.0))), "facing": "right", "squash_root": True,
            "planet": "uranus", "seed": sp["seed"], "bg_scene": HABITAT[name], "beside": "characters/surveyor/side",
            "review_name": f"b158_uranus_{name}", "clips": [{"name": c, "frames": n, "loop": lp} for c, n, lp in sp["clips"]],
            "self_check": dict(sp["self_check"], style="the B-132 kit (Gus's construction); LEAD judges"), "ours": sp["ours"],
            "replaces_v2": True, "note": "B-158 design (Uranus creature re-ink); floaters pivot at the body centre, the Hailcrab on the ground line"}




def preview(out_dir, name="frostwisp"):
    """The export's review layout from exact frames (as_object ids, ss 4) on a placeholder background (centre-pivot
    creatures: all four edges checked)."""
    if True:
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
        meta = {"key": f"creatures/uranus/{name}", "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": 4,
                "frames": len(frames), "fps": 12, "pivot": list(piv), "facing": "right", "ppu": 64, "animations": anims, "squash_root": True}
        problems = v3.validate_sheet(meta, sheet.shape)
        bottom = piv[1] != 0.0                                                             # centre pivots: all four edges; walkers: sides + top
        clipped = [i for i, im in enumerate(frames) if im[:2, :, 3].any() or (bottom and im[-2:, :, 3].any()) or im[:, :2, 3].any() or im[:, -2:, 3].any()]
        if clipped:
            problems.append(f"frames {clipped[:8]} touch the 2 px edge")
        if below:
            problems.append(f"frames {below[:8]} below the ground line")
        dd = os.path.join(out_dir, "b158_uranus")
        os.makedirs(dd, exist_ok=True)
        png = os.path.join(dd, f"{name}_color.png")
        nb = pngio.write_png(png, sheet)
        with open(os.path.join(dd, f"{name}.json"), "w", encoding="utf-8", newline="\n") as f_:
            json.dump(meta, f_, indent=2)
        outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
        inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
        stats = {"outer_px": (min(w[1] for w in outer), max(w[2] for w in outer)), "inner_px": (min(w[1] for w in inner), max(w[2] for w in inner)),
                 "inner_n": len(inner), "palette": v3.palette_hits(sheet, "uranus"), "problems": problems,
                 "sheet_wh": (sheet.shape[1], sheet.shape[0]), "png_kb": nb // 1024}
        out = os.path.join(out_dir, f"review_b158_uranus_{name}_preview.png")
        boxes = review.v3_sheet_review(entry_for(name), meta, frames, png, out, stats)
        print(name, f"sheet {sheet.shape[1]}x{sheet.shape[0]} {nb // 1024} KB, ink {stats['outer_px'][0]:.2f}-{stats['outer_px'][1]:.2f} / "
              f"{stats['inner_px'][0]:.2f}-{stats['inner_px'][1]:.2f}, palette {stats['palette'][0] * 100:.1f}% {stats['palette'][1][:3]}, "
              f"problems {problems or '-'}, boxes not x: {','.join(k for k, (mk, _n) in boxes.items() if mk != 'x') or '-'}")



if __name__ == "__main__":
    for _n in (sys.argv[2:] or list(SPECIES)):
        preview(sys.argv[1], _n)
