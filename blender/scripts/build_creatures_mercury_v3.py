"""B-145 (C2 Mercury design prep): Mercury creature design previews on the B-132 kit (build_creatures_earth_v3: posed body,
pie eyes, dizzy stars), in the Mercury palette (D-130). Faces kept, friendly or neutral, no teeth (D-087 / D-101).

  flarewing  124x124, a flyer that feeds on flares ("aggressive" becomes excited, D-087): a violet moth-bat with ember
             belly, membrane wings on drawn ribs, gold flare-catching vanes at the wing tips and a forked gold-tipped
             tail. Pivot at the body centre (the B-135 swimmers' rule for creatures that leave the ground); clips idle 10
             (a hover), fly 12 (index 1: the travel clip, like the swimmers' swim), react 8 (a loop-de-loop), bump 10,
             flare_dance 12 (during a flare: fast flaps, the vanes glow, sparks spiral).

Design previews only; Mercury exports wait for their cards (B-145 is prep).

  python -I build_creatures_mercury_v3.py <preview dir> [names]      lock-free (meridian.fakegp; exact stroke ids)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_earth_v3 as K  # noqa: E402  (the kit; gp_draw real in Blender, fakegp outside)
from meridian import v3  # noqa: E402

G = K.G
P = v3.PALETTES["mercury"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi


def SH(h):
    return v3.shadow_of(h, "mercury")


def DP(h):
    return v3.deep_of(h, "mercury")


def mats(gp, sp):
    def m(name, **kw):
        return G.mat(gp, f"{sp}_{name}", **kw)
    out = {"ink": m("ink", fill=None), "pupil": m("pupil", fill=G.INK, ink=False), "eye": m("eye_white", fill=P["offwhite"]),
           "mouth": m("mouth", fill=DP(P["red"])), "star": m("star", fill=P["mustard"]),
           "puff": m("puff", fill=P["offwhite"]), "puff_sh": m("puff_mid", fill=SH(P["offwhite"]), ink=False),
           "glow": m("glow", fill=P["mustard"], ink=False, fill_alpha=0.30)}
    for key, slot in (("violet", "sky"), ("ember", "red"), ("gold", "mustard"), ("ice", "teal"), ("white", "offwhite"),
                      ("sage", "green"), ("slate", "brown")):
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
        out[key + "_b"] = m(key + "_behind", fill=h, behind=True)
    return out


# ---------------------------------------------------------------- flarewing
def wing(d, M, root, theta, L, far, vane, seed):
    """A membrane wing from `root` toward angle theta (radians from +x): a bowed leading edge, a scalloped trailing
    edge between three ribs, the mid tone at the root, a gold vane at the tip (it glows during a flare)."""
    c, s = math.cos(theta), math.sin(theta)
    n = (-s, c) if c < 0 else (s, -c)                                # the trailing side: away from the body's front

    def at(t, w):
        return (root[0] + c * t * L + n[0] * w + 0.03 * math.sin(math.pi * t) * -n[0],
                root[1] + s * t * L + n[1] * w + 0.03 * math.sin(math.pi * t) * -n[1])
    tip = at(1.0, 0.0)
    trail = []
    for t, w in ((0.90, 0.12), (0.70, 0.19), (0.52, 0.17), (0.32, 0.21), (0.12, 0.17), (0.0, 0.08)):   # a soft scallop
        trail.append(at(t, w))
    lead = [at(t, 0.0) for t in (0.0, 0.25, 0.5, 0.75)]
    shape = lead + [tip] + trail
    G.stroke(d, shape, M["violet_sh"] if far else M["violet_f"], 0.0, cyclic=True)
    G.stroke(d, lead[:2] + [at(0.3, 0.17), at(0.12, 0.18), at(0.0, 0.08)], M["violet_dp"] if far else M["violet_sh"], 0.0, cyclic=True)
    for t, w in ((0.70, 0.18), (0.32, 0.20)):                                           # two ribs
        G.seam(d, [at(0.05, 0.01), at(t * 0.8, w * 0.5), at(t, w - 0.015)], M["ink"])
    G.stroke(d, shape, M["ink"], O, cyclic=True)
    vt = (tip[0] + c * 0.05, tip[1] + s * 0.05)
    if vane > 0.05:
        G.stroke(d, G.lumpy_ellipse(vt[0], vt[1], 0.07 + 0.04 * vane, 0.07 + 0.04 * vane, n=14, lump=0.04, seed=seed + 9), M["glow"], 0.0, cyclic=True)
    vpts = [(vt[0] + 0.07 * math.cos(theta + a), vt[1] + 0.07 * math.sin(theta + a)) for a in (-0.7, -0.25, 0.2, 0.7)]
    G.stroke(d, [tip] + vpts, M["gold" if not far else "gold_sh"], I, cyclic=True)        # the flare-catching vane


def draw_flarewing(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(flap=0.0, vane=0.0, sparks=None, tail2=0.0))
    p.update(pose or {})
    B = K.Body(p, (0.0, 0.0))
    db = G.Xf(d, B)
    theta = math.radians(147.5 + 52.5 * math.sin(p["flap"]))                              # 95 deg (up) .. 200 deg (down, back)
    wing(db, M, (0.02, 0.06), theta + 0.25, 0.58, True, p["vane"], seed)                  # the far wing, a step behind
    for k in (0, 1):                                                                      # the forked tail, gold tips
        a = math.pi + 0.25 * (k - 0.5) + p["tail"] + 0.15 * math.sin(p["tail2"] + k)
        base = (-0.20, 0.0)
        tip = (base[0] + 0.36 * math.cos(a), base[1] + 0.36 * math.sin(a))
        G.stroke(db, G.hose_outline(G.bezier(base, ((base[0] + tip[0]) / 2, base[1] + 0.05 * (k - 0.5)), tip, n=6), 0.03), M["violet_b"], I, cyclic=True)
        G.stroke(db, G.lumpy_ellipse(tip[0], tip[1], 0.035, 0.025, n=10, seed=seed + 20 + k, rot=a), M["gold"], I, cyclic=True)
    body = G.lumpy_ellipse(-0.02, 0.0, 0.22, 0.10, n=30, lump=0.03, seed=seed + 1)
    G.stroke(db, body, M["violet_f"], 0.0, cyclic=True)
    G.stroke(db, [q for q in body if q[1] < -0.02] + [(0.18, -0.02), (-0.2, -0.02)], M["ember_f"], 0.0, cyclic=True)   # ember belly
    for k in range(3):
        G.seam(db, [(-0.12 + 0.08 * k, -0.075), (-0.10 + 0.08 * k, -0.035)], M["ink"])   # belly bands
    G.specks(db, [(-0.08, 0.05), (0.04, 0.06)], M["ink"])
    G.stroke(db, body, M["ink"], O, cyclic=True)
    H = K.turn((0.16, 0.02), p["head_rot"], p["head"], B)
    hx, hz = 0.25, 0.04
    dh = G.Xf(G.Xf(d, H), K.scale_about((hx, hz), 1.3))                                   # the head 1.3x (era proportions)
    for k in (0, 1):                                                                      # two little gold feelers
        a = math.radians(70 - 35 * k) + p["ears"] * 0.6
        G.stroke(dh, G.hose_outline(G.bezier((hx - 0.02 + 0.03 * k, hz + 0.07), (hx + 0.0 + 0.03 * k, hz + 0.13), (hx + 0.1 * math.cos(a) + 0.03 * k, hz + 0.07 + 0.12 * math.sin(a)), n=5), 0.014), M["gold_b"], I, cyclic=True)
    G.stroke(dh, G.lumpy_ellipse(hx, hz, 0.095, 0.085, n=24, lump=0.03, seed=seed + 2), M["violet"], O, cyclic=True)
    G.stroke(dh, G.lumpy_ellipse(hx + 0.075, hz - 0.02, 0.03, 0.025, n=10, seed=seed + 3), M["ember"], I, cyclic=True)   # a round snout
    if p["mouth"] > 0.05:
        G.stroke(dh, G.lumpy_ellipse(hx + 0.05, hz - 0.055, 0.012 + 0.008 * p["mouth"], 0.008 + 0.01 * p["mouth"], n=10, seed=seed + 4), M["mouth"], I, cyclic=True)
    else:
        G.seam(dh, G.bezier((hx + 0.07, hz - 0.05), (hx + 0.04, hz - 0.06), (hx + 0.01, hz - 0.05), n=4), M["ink"])
    K.eyes(dh, M, hx - 0.01, hz + 0.02, 0.022, 0.03, 0.042, p, seed)
    wing(db, M, (-0.02, 0.05), theta, 0.62, False, p["vane"], seed + 5)                   # the near wing, in front
    if p["sparks"] is not None:                                                           # flare sparks spiral round it
        G.specks(db, [(0.45 * math.cos(p["sparks"] + k * 2.1), 0.35 * math.sin(p["sparks"] + k * 2.1)) for k in range(3)], M["ink"])
        for k in range(2):
            a = p["sparks"] + 1.0 + k * math.pi
            G.stroke(db, K.star(0.4 * math.cos(a), 0.3 * math.sin(a), 0.035, rot=a), M["gold"], I, cyclic=True)
    if p["stars"] is not None:
        K.stars(dh, M, hx, hz + 0.2, 0.14, p["stars"])


def flarewing_poses():
    out = []
    for i in range(10):                                                                   # idle: a hover, two slow flaps
        ph = TAU * i / 5
        out.append(dict(flap=ph, bob=0.03 * math.sin(ph + math.pi / 2), rock=0.05 * math.sin(ph), tail=0.1 * math.sin(ph - 1.0),
                        tail2=ph, ears=0.2 * math.sin(ph), blink={7: 0.6, 8: 1.0}.get(i, 0.0), look=(0.7, -0.1)))
    for i in range(12):                                                                   # fly: forward, nose a touch down
        ph = TAU * i / 6
        out.append(dict(flap=ph, bob=0.025 * math.sin(ph + math.pi / 2), rock=-0.10 + 0.04 * math.sin(ph), tail=-0.12, tail2=ph,
                        ears=-0.3, look=(0.9, 0.0)))
    for i in range(8):                                                                    # react: a loop-de-loop
        out.append(dict(flap=TAU * i / 4, rock=TAU * i / 8, eye_pop=1.3 if i < 3 else 1.1, mouth=0.4 if 1 <= i <= 4 else 0.0,
                        tail=0.2, tail2=i, ears=-0.4))
    out += [dict(q, flap=0.0, shift=0.5 * q.get("shift", 0.0), ears=q.get("ears", 0.0)) for q in K.bump_clip()]   # wings held up-back, half the knock
    for i in range(12):                                                                   # flare_dance: fast flaps, glowing vanes
        ph = TAU * i / 4
        out.append(dict(flap=ph, bob=0.04 * math.sin(TAU * i / 6), rock=0.12 * math.sin(TAU * i / 12), vane=0.6 + 0.4 * math.sin(TAU * i / 3),
                        sparks=TAU * i / 12, tail=0.15 * math.sin(ph), tail2=ph, eye_pop=1.2, mouth=0.5, ears=0.4 * math.sin(ph), look=(0.6, 0.3)))
    return out


SPECIES = {
    "flarewing": dict(draw=draw_flarewing, poses=flarewing_poses, mats=mats, frame=(124, 124), seed=41, pivot=(0.5, 0.5), flyer=True,
                      clips=[("idle", 10, True), ("fly", 12, True), ("react", 8, False), ("bump", 10, False), ("flare_dance", 12, True)],
                      self_check={"ink": "wing ribs, belly bands, specks, vane edges, feeler hoses",
                                  "motion": "flaps on the beat, the far wing a step behind, the forked tail streams, feelers drag; react loops; flare_dance glows",
                                  "original": "our own flare-feeder: a violet moth-bat with an ember belly and gold vanes; excited, never aggressive (D-087), no teeth"},
                      ours="a violet moth-bat that hovers on gold-vaned wings and loops for joy when a flare lights its vanes"),
}


def entry_for(name):
    sp = SPECIES[name]
    return {"key": f"creatures/mercury/{name}", "style": "v3", "source": f"sources/creatures/mercury_{name}_v3.blend",
            "build": "scripts/build_creatures_mercury_v3.py", "build_fn": f"build_{name}", "collection": name,
            "frame": list(sp["frame"]), "pivot": list(sp.get("pivot", (0.5, 0.0))), "facing": "right", "squash_root": True,
            "planet": "mercury", "seed": sp["seed"], "bg_scene": "-", "beside": "characters/surveyor/side",
            "review_name": f"b145_mercury_{name}", "clips": [{"name": c, "frames": n, "loop": lp} for c, n, lp in sp["clips"]],
            "self_check": dict(sp["self_check"], style="the B-132 kit (Gus's construction); LEAD judges"), "ours": sp["ours"],
            "replaces_v2": True, "note": "B-145 design (Mercury creature re-ink); a flyer's travel clip sits at index 1 like the swimmers' swim"}


def preview(out_dir, name="flarewing"):
    """The export's review layout from exact frames (as_object ids, ss 4), a Mercury placeholder background."""
    import json
    import numpy as np
    from meridian import fakegp, pngio
    import gp_raster as GR
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    sp = SPECIES[name]
    fw, fh = sp["frame"]
    piv = sp.get("pivot", (0.5, 0.0))
    frames, widths = [], []
    for f, pose in enumerate(sp["poses"]()):
        gp = fakegp.FakeGP()
        M = mats(gp, name)
        d = fakegp.FakeDrawing()
        sp["draw"](d, M, pose, seed=5 * f)
        img, w = GR.render_frame(fakegp.strokes_of(d, gp, as_object=(name, "art")), fw, fh, 64, piv, ss=4, seed=sp["seed"] * 1000 + f + 1)
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
    meta = {"key": f"creatures/mercury/{name}", "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": 4,
            "frames": len(frames), "fps": 12, "pivot": list(piv), "facing": "right", "ppu": 64, "animations": anims, "squash_root": True}
    problems = v3.validate_sheet(meta, sheet.shape)
    clipped = [i for i, im in enumerate(frames) if im[:2, :, 3].any() or im[-2:, :, 3].any() or im[:, :2, 3].any() or im[:, -2:, 3].any()]
    if clipped:
        problems.append(f"frames {clipped[:8]} touch the 2 px edge")
    dd = os.path.join(out_dir, "b145_mercury")
    os.makedirs(dd, exist_ok=True)
    png = os.path.join(dd, f"{name}_color.png")
    nb = pngio.write_png(png, sheet)
    with open(os.path.join(dd, f"{name}.json"), "w", encoding="utf-8", newline="\n") as f_:
        json.dump(meta, f_, indent=2)
    outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
    stats = {"outer_px": (min(w[1] for w in outer), max(w[2] for w in outer)), "inner_px": (min(w[1] for w in inner), max(w[2] for w in inner)),
             "inner_n": len(inner), "palette": v3.palette_hits(sheet, "mercury", tints=[("mustard", 0.30)]), "problems": problems,
             "sheet_wh": (sheet.shape[1], sheet.shape[0]), "png_kb": nb // 1024}
    out = os.path.join(out_dir, f"review_b145_mercury_{name}_preview.png")
    boxes = review.v3_sheet_review(entry_for(name), meta, frames, png, out, stats)
    print(name, f"sheet {sheet.shape[1]}x{sheet.shape[0]} {nb // 1024} KB, ink {stats['outer_px'][0]:.2f}-{stats['outer_px'][1]:.2f} / "
          f"{stats['inner_px'][0]:.2f}-{stats['inner_px'][1]:.2f}, palette {stats['palette'][0] * 100:.1f}% {stats['palette'][1][:3]}, "
          f"problems {problems or '-'}, boxes not x: {','.join(k for k, (mk, _n) in boxes.items() if mk != 'x') or '-'}")


if __name__ == "__main__":
    for _n in (sys.argv[2:] or list(SPECIES)):
        preview(sys.argv[1], _n)
