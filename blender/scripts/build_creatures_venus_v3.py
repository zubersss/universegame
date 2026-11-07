"""B-147 (C2 Venus design prep): Venus creature design previews on the B-132 kit (build_creatures_earth_v3: posed body, pie
eyes, dizzy stars), in the Venus palette (D-134). Faces kept, friendly or neutral, no teeth (D-087 / D-101).

  sulfur_drifter  112x128, a gasbag filter feeder on the deck winds: a sulphur-yellow balloon with a cream filter frill
                  and swaying tendrils below, pie eyes, a small round mouth, two olive paddle fins. Pivot at the body
                  centre (creatures off the ground, B-135's rule); clips idle 10 (a bob), drift 12 at index 1 (the travel
                  clip, like the swimmers' swim / the Flarewing's fly), react 8 (puffs up), bump 10, flee 12.

Design previews only; Venus exports wait for their cards (B-147 is prep).

  python -I build_creatures_venus_v3.py <preview dir> [names]      lock-free (meridian.fakegp; exact stroke ids)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_earth_v3 as K  # noqa: E402  (the kit; gp_draw real in Blender, fakegp outside)
from meridian import v3  # noqa: E402

G = K.G
P = v3.PALETTES["venus"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi


def SH(h):
    return v3.shadow_of(h, "venus")


def DP(h):
    return v3.deep_of(h, "venus")


def mats(gp, sp):
    def m(name, **kw):
        return G.mat(gp, f"{sp}_{name}", **kw)
    out = {"ink": m("ink", fill=None), "pupil": m("pupil", fill=G.INK, ink=False), "eye": m("eye_white", fill=P["offwhite"]),
           "mouth": m("mouth", fill=DP(P["red"])), "star": m("star", fill=P["mustard"]),
           "puff": m("puff", fill=P["offwhite"]), "puff_sh": m("puff_mid", fill=SH(P["offwhite"]), ink=False)}
    for key, slot in (("sulphur", "mustard"), ("vent", "red"), ("cream", "offwhite"), ("glass", "teal"), ("olive", "green"),
                      ("haze", "sky"), ("basalt", "brown")):
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
        out[key + "_b"] = m(key + "_behind", fill=h, behind=True)
    return out


# ---------------------------------------------------------------- sulfur drifter
def draw_sulfur_drifter(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(inflate=0.0, paddle=0.0, trail=0.0, streak=None))
    p.update(pose or {})
    B = K.Body(p, (0.0, 0.0))
    db = G.Xf(d, B)
    k = 1.0 + 0.25 * p["inflate"]
    rx, rz, cz = 0.42 * k, 0.34 * k, 0.12
    for j in range(5):                                                                    # tendrils (behind the frill), trailing back
        x0 = -0.24 + 0.12 * j
        sw = 0.05 * math.sin(p["paddle"] * 1.3 + j) - 0.18 * p["trail"]
        tend = G.bezier((x0, cz - rz * 0.7), (x0 + sw * 0.5, cz - rz - 0.12), (x0 + sw, cz - rz - 0.30 + 0.02 * j % 3), n=8)
        G.stroke(db, G.hose_outline(tend, 0.025), M["cream_b"], I, cyclic=True)
    for side, sx in ((0, -1), (1, 1)):                                                     # paddle fins
        a = math.radians(-20 + 30 * math.sin(p["paddle"] + side * math.pi))
        root = (sx * rx * 0.9, cz - 0.02)
        fin = [root, (root[0] + sx * 0.16 * math.cos(a), root[1] + 0.16 * math.sin(a) + 0.04), (root[0] + sx * 0.18 * math.cos(a), root[1] + 0.18 * math.sin(a) - 0.05)]
        G.stroke(db, fin, M["olive"], I, cyclic=True)
    frill = [(x, z) for x, z in G.lumpy_ellipse(0.0, cz - rz * 0.62, rx * 0.86, 0.09, n=24, lump=0.12, seed=seed + 3)]
    G.stroke(db, frill, M["cream"], I, cyclic=True)                                       # the filter frill
    ball = G.lumpy_ellipse(0.0, cz, rx, rz, n=40, lump=0.025, seed=seed + 1)
    G.stroke(db, ball, M["sulphur_f"], 0.0, cyclic=True)
    G.stroke(db, [q for q in ball if q[1] < cz - 0.35 * rz] + [(0.0, cz - 0.35 * rz)], M["sulphur_sh"], 0.0, cyclic=True)
    for j in range(3):                                                                    # gasbag panel seams + sulphur specks
        x = -0.2 + 0.2 * j
        G.seam(db, G.bezier((x * 0.6, cz + rz * 0.92), (x * 1.1, cz + rz * 0.3), (x * 0.9, cz - rz * 0.3), n=6), M["ink"])
    G.specks(db, [(-0.25, cz + 0.12), (0.2, cz + 0.2), (0.08, cz - 0.05)], M["ink"])
    G.stroke(db, ball, M["ink"], O, cyclic=True)
    H = K.turn((0.0, cz - 0.05), p["head_rot"], p["head"], B)
    dh = G.Xf(d, H)
    ex, ez = 0.14 * k, cz - 0.04
    K.eyes(dh, M, ex, ez, 0.045, 0.06, 0.09, p, seed)
    if p["mouth"] > 0.05:
        G.stroke(dh, G.lumpy_ellipse(ex + 0.06, ez - 0.13, 0.02 + 0.012 * p["mouth"], 0.014 + 0.016 * p["mouth"], n=10, seed=seed + 4), M["mouth"], I, cyclic=True)
    else:
        G.stroke(dh, G.lumpy_ellipse(ex + 0.06, ez - 0.12, 0.022, 0.016, n=10, seed=seed + 4), M["sulphur_dp"], I, cyclic=True)   # the feeding funnel
    if p["streak"] is not None:                                                           # flee: wind streaks behind
        for j in range(3):
            y = cz - 0.2 + 0.18 * j
            x = -rx - 0.08 - 0.25 * ((p["streak"] + 0.3 * j) % 1.0)
            G.stroke(db, [(x, y), (x - 0.18, y + 0.01)], M["ink"], I)
    if p["stars"] is not None:
        K.stars(dh, M, 0.0, cz + rz + 0.12, 0.2, p["stars"])


def drifter_poses():
    out = []
    for i in range(10):                                                                   # idle: a bob, the frill and tendrils sway
        ph = TAU * i / 10
        out.append(dict(bob=0.035 * math.sin(ph), sz=1 + 0.03 * math.cos(ph), paddle=ph, rock=0.03 * math.sin(ph - 1.0),
                        blink={6: 0.6, 7: 1.0}.get(i, 0.0), look=(0.6, -0.2)))
    for i in range(12):                                                                   # drift: leaning into the wind, fins paddle
        ph = TAU * i / 6
        out.append(dict(bob=0.02 * math.sin(ph), rock=-0.10, paddle=ph * 1.5, trail=0.8, lean=0.04, look=(0.9, 0.0)))
    out += [dict(inflate=0.2, eye_pop=1.3, look=(0.7, 0.0)), dict(inflate=0.6, eye_pop=1.6, mouth=0.6),           # react: puffs up
            dict(inflate=1.0, eye_pop=1.5, mouth=0.7, sz=1.04), dict(inflate=0.95, eye_pop=1.4, mouth=0.5),
            dict(inflate=0.7, eye_pop=1.2, paddle=1.0), dict(inflate=0.4, paddle=2.0, look=(0.9, 0.2)), dict(inflate=0.2, paddle=3.0), dict(inflate=0.0)]
    out += [dict(q, shift=0.5 * q.get("shift", 0.0)) for q in K.bump_clip()]
    for i in range(12):                                                                   # flee: a little deflated, zipping off
        ph = TAU * i / 4
        out.append(dict(inflate=-0.12, rock=-0.18, lean=0.06, paddle=ph * 2, trail=1.0, streak=(i % 4) / 4.0, eye_pop=1.2, look=(0.9, 0.0)))
    return out


SPECIES = {
    "sulfur_drifter": dict(draw=draw_sulfur_drifter, poses=drifter_poses, mats=mats, frame=(112, 128), seed=51, pivot=(0.5, 0.5),
                           clips=[("idle", 10, True), ("drift", 12, True), ("react", 8, False), ("bump", 10, False), ("flee", 12, True)],
                           self_check={"ink": "gasbag panel seams, sulphur specks, the frill's lumpy edge, tendril hoses, fin edges",
                                       "motion": "bobs and breathes, the tendrils sway and trail in the drift, fins paddle; react puffs up",
                                       "original": "our own sulphur gasbag: a balloon with a cream filter frill and tendrils; gentle, no teeth"},
                           ours="a sulphur-yellow gasbag that drifts on the deck winds, combing the haze with its frill, and puffs up when startled"),
}


def entry_for(name):
    sp = SPECIES[name]
    return {"key": f"creatures/venus/{name}", "style": "v3", "source": f"sources/creatures/venus_{name}_v3.blend",
            "build": "scripts/build_creatures_venus_v3.py", "build_fn": f"build_{name}", "collection": name,
            "frame": list(sp["frame"]), "pivot": list(sp.get("pivot", (0.5, 0.0))), "facing": "right", "squash_root": True,
            "planet": "venus", "seed": sp["seed"], "bg_scene": "-", "beside": "characters/surveyor/side",
            "review_name": f"b147_venus_{name}", "clips": [{"name": c, "frames": n, "loop": lp} for c, n, lp in sp["clips"]],
            "self_check": dict(sp["self_check"], style="the B-132 kit (Gus's construction); LEAD judges"), "ours": sp["ours"],
            "replaces_v2": True, "note": "B-147 design (Venus creature re-ink)"}


def preview(out_dir, name="sulfur_drifter"):
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
        meta = {"key": f"creatures/venus/{name}", "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": 4,
                "frames": len(frames), "fps": 12, "pivot": list(piv), "facing": "right", "ppu": 64, "animations": anims, "squash_root": True}
        problems = v3.validate_sheet(meta, sheet.shape)
        clipped = [i for i, im in enumerate(frames) if im[:2, :, 3].any() or im[-2:, :, 3].any() or im[:, :2, 3].any() or im[:, -2:, 3].any()]
        if clipped:
            problems.append(f"frames {clipped[:8]} touch the 2 px edge")
        dd = os.path.join(out_dir, "b147_venus")
        os.makedirs(dd, exist_ok=True)
        png = os.path.join(dd, f"{name}_color.png")
        nb = pngio.write_png(png, sheet)
        with open(os.path.join(dd, f"{name}.json"), "w", encoding="utf-8", newline="\n") as f_:
            json.dump(meta, f_, indent=2)
        outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
        inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
        stats = {"outer_px": (min(w[1] for w in outer), max(w[2] for w in outer)), "inner_px": (min(w[1] for w in inner), max(w[2] for w in inner)),
                 "inner_n": len(inner), "palette": v3.palette_hits(sheet, "venus"), "problems": problems,
                 "sheet_wh": (sheet.shape[1], sheet.shape[0]), "png_kb": nb // 1024}
        out = os.path.join(out_dir, f"review_b147_venus_{name}_preview.png")
        boxes = review.v3_sheet_review(entry_for(name), meta, frames, png, out, stats)
        print(name, f"sheet {sheet.shape[1]}x{sheet.shape[0]} {nb // 1024} KB, ink {stats['outer_px'][0]:.2f}-{stats['outer_px'][1]:.2f} / "
              f"{stats['inner_px'][0]:.2f}-{stats['inner_px'][1]:.2f}, palette {stats['palette'][0] * 100:.1f}% {stats['palette'][1][:3]}, "
              f"problems {problems or '-'}, boxes not x: {','.join(k for k, (mk, _n) in boxes.items() if mk != 'x') or '-'}")


if __name__ == "__main__":
    for _n in (sys.argv[2:] or list(SPECIES)):
        preview(sys.argv[1], _n)
