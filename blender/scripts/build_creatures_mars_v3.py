"""B-139 part 5 (C2 Mars design prep, LEAD cycle 255): Mars creature design previews on the B-132 creature kit
(build_creatures_earth_v3: posed body, hose legs, pie eyes, dizzy stars), in the Mars palette (D-125). List order 1:

  dustskater  128x80  a small scavenger of the rust plains (~0.8 m): a domed butterscotch shell with rust plate bands,
              a dust-white underside, a short snout, two pie eyes, two knobbed antenna stalks that drag, four splayed
              hose legs on flat dust-white skate pads. Clips idle 10, walk 12 (a skating glide: pads slide, the body
              barely bobs), react 8 (eye-pop and a skid), bump 10, flee 12 (a low dash with dust puffs behind)

Faces kept, friendly or neutral, no teeth (D-087 / D-101). Design preview only: Mars exports wait for Mars cards.

  python -I build_creatures_mars_v3.py <preview dir>      lock-free (meridian.fakegp; exact stroke ids)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_earth_v3 as K  # noqa: E402  (the kit; gp_draw real in Blender, fakegp outside)
from meridian import v3  # noqa: E402

G = K.G
P = v3.PALETTES["mars"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi


def SH(h):
    return v3.shadow_of(h, "mars")


def DP(h):
    return v3.deep_of(h, "mars")


def mats(gp, sp="dustskater"):
    def m(name, **kw):
        return G.mat(gp, f"{sp}_{name}", **kw)
    return {
        "shell": m("shell", fill=P["mustard"]), "shell_f": m("shell_f", fill=P["mustard"], ink=False),
        "shell_sh": m("shell_mid", fill=SH(P["mustard"]), ink=False), "shell_dp": m("shell_deep", fill=DP(P["mustard"]), ink=False),
        "band": m("band", fill=P["red"], ink=False), "band_sh": m("band_mid", fill=SH(P["red"]), ink=False),
        "under": m("under", fill=P["offwhite"], ink=False), "under_sh": m("under_mid", fill=SH(P["offwhite"]), ink=False),
        "head": m("head", fill=P["mustard"]), "snout": m("snout", fill=P["offwhite"]),
        "leg": m("leg", fill=SH(P["red"]), behind=True), "leg_far": m("leg_far", fill=DP(P["red"]), behind=True),
        "pad": m("pad", fill=P["offwhite"]), "pad_far": m("pad_far", fill=SH(P["offwhite"])),
        "knob": m("knob", fill=P["red"]), "nose": m("nose", fill=P["brown"]),
        "ink": m("ink", fill=None), "pupil": m("pupil", fill=G.INK, ink=False), "eye": m("eye_white", fill=P["offwhite"]),
        "mouth": m("mouth", fill=P["red"]), "star": m("star", fill=P["mustard"]),
        "puff": m("puff", fill=P["offwhite"]), "puff_sh": m("puff_mid", fill=SH(P["offwhite"]), ink=False),
    }


HIPS = [(-0.20, 0.20), (0.18, 0.20), (-0.24, 0.18), (0.14, 0.18)]       # far hind, far front, near hind, near front
FEET = [-0.36, 0.30, -0.40, 0.26]                                        # splayed: the feet reach past the shell


def skate_leg(d, M, hip, fx, lift, far, slide):
    """A splayed hose leg out to a flat skate pad (slide tilts the pad as it glides)."""
    fz = 0.035 + lift
    knee = ((hip[0] + fx) / 2, max(hip[1], fz) + 0.07)
    G.stroke(d, G.hose_outline(G.bezier(hip, knee, (fx, fz + 0.02), n=8), 0.045), M["leg_far" if far else "leg"], O, cyclic=True)
    pad = [(x * math.cos(slide) - z * math.sin(slide) + fx, x * math.sin(slide) + z * math.cos(slide) + fz)
           for x, z in G.lumpy_ellipse(0.025, 0.0, 0.09, 0.026, n=14, lump=0.04, seed=7)]
    G.stroke(d, pad, M["pad_far" if far else "pad"], O, cyclic=True)
    G.seam(d, [(fx - 0.03, fz - 0.002), (fx + 0.06, fz - 0.004)], M["ink"])


def draw_dustskater(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(slide=(0.0, 0.0, 0.0, 0.0), antenna=0.0, dust=None))
    p.update(pose or {})
    B = K.Body(p, (0.0, 0.27))
    J = (0.24, 0.30)
    H = K.turn(J, p["head_rot"], p["head"], B)
    dh, db = G.Xf(d, H), G.Xf(d, B)
    if p["dust"] is not None:                                             # dust puffs kicked up behind (flee)
        for k in range(2):
            t = (p["dust"] + 0.5 * k) % 1.0
            r = 0.035 + 0.04 * t
            blob = G.lumpy_ellipse(-0.42 - 0.35 * t, r + 0.03, r * 1.2, r, n=14, lump=0.12, seed=80 + k)
            G.stroke(d, blob, M["puff"], I, cyclic=True)
            G.stroke(d, [q for q in blob if q[1] < r * 0.8 + 0.03] + [(-0.42 - 0.35 * t, r * 0.8 + 0.03)], M["puff_sh"], 0.0, cyclic=True)
    for i in (0, 1):                                                      # far legs (behind)
        hip = B.pt(*HIPS[i])
        skate_leg(d, M, hip, FEET[i] * B.sx + p["shift"] + p["legs"][i][0], p["legs"][i][1], True, p["slide"][i])
    for k, side in enumerate((-1, 1)):                                    # antenna stalks (behind the head), drag by p['antenna']
        base = (0.31 + 0.06 * k, 0.43)
        a = math.radians(135 - 55 * k) + p["antenna"] * (1.0 if k == 0 else 0.6)    # splayed: one back, one forward
        tip = (base[0] + 0.15 * math.cos(a), base[1] + 0.15 * math.sin(a))
        G.stroke(dh, G.hose_outline(G.bezier(base, ((base[0] + tip[0]) / 2, base[1] + 0.10), tip, n=6), 0.018), M["leg"], I, cyclic=True)
        G.stroke(dh, G.lumpy_ellipse(tip[0], tip[1], 0.03, 0.03, n=10, seed=60 + k), M["knob"], I, cyclic=True)
    shell = K.body_shape(-0.04, 0.24, 0.30, 0.17, seed + 1, chest=0.0)
    shell = [(x, max(z, 0.12)) for x, z in shell]
    G.stroke(db, shell, M["shell_f"], 0.0, cyclic=True)
    under = [(x, z) for x, z in shell if z < 0.2]
    G.stroke(db, under + [(0.2, 0.16), (-0.3, 0.16)], M["under"], 0.0, cyclic=True)
    G.stroke(db, [q for q in shell if q[1] > 0.36 and q[0] < 0.0] + [(-0.02, 0.36)], M["shell_sh"], 0.0, cyclic=True)
    for k, x in enumerate((-0.20, -0.06, 0.08)):                          # rust plate bands with seams and rivet dots
        band = [(x - 0.035, 0.18), (x + 0.035, 0.18), (x + 0.045 - 0.02 * k, 0.40 - 0.02 * abs(k - 1)), (x - 0.025, 0.41 - 0.02 * abs(k - 1))]
        G.stroke(db, band, M["band"], 0.0, cyclic=True)
        G.seam(db, [(x - 0.035, 0.19), (x - 0.025, 0.40)], M["ink"])
        G.specks(db, [(x + 0.005, 0.30), (x + 0.01, 0.24)], M["ink"])
    G.hatch(db, -0.14, 0.33, M["ink"], n=3, length=0.05, spacing=0.02, angle_deg=65, seed=seed + 5)
    G.seam(db, [(x, z) for x, z in shell if 0.16 < z < 0.22][:8], M["ink"])
    G.stroke(db, shell, M["ink"], O, cyclic=True)
    for i in (2, 3):                                                      # near legs (in front)
        hip = B.pt(*HIPS[i])
        skate_leg(d, M, hip, FEET[i] * B.sx + p["shift"] + p["legs"][i][0], p["legs"][i][1], False, p["slide"][i])
    hx, hz = 0.33, 0.30                                                   # head, snout, nose, mouth, eyes
    G.stroke(dh, G.lumpy_ellipse(hx, hz, 0.11, 0.10, n=28, lump=0.03, seed=seed + 2), M["head"], O, cyclic=True)
    G.stroke(dh, G.lumpy_ellipse(hx + 0.11, hz - 0.035, 0.065, 0.045, n=18, seed=seed + 3, rot=-0.2), M["snout"], O, cyclic=True)
    G.stroke(dh, G.lumpy_ellipse(hx + 0.172, hz - 0.03, 0.022, 0.018, n=10, seed=seed + 4), M["nose"], I, cyclic=True)
    if p["mouth"] > 0.05:
        G.stroke(dh, G.lumpy_ellipse(hx + 0.12, hz - 0.07, 0.012 + 0.01 * p["mouth"], 0.008 + 0.012 * p["mouth"], n=10, seed=seed + 5), M["mouth"], I, cyclic=True)
    else:
        G.seam(dh, G.bezier((hx + 0.08, hz - 0.065), (hx + 0.115, hz - 0.075), (hx + 0.15, hz - 0.06), n=5), M["ink"])
    K.eyes(dh, M, hx + 0.005, hz + 0.035, 0.024, 0.033, 0.045, p, seed)
    if p["stars"] is not None:
        K.stars(dh, M, hx, hz + 0.24, 0.16, p["stars"])


def poses():
    out = []
    for i in range(10):                                                   # idle: breathe, antenna bob, a blink
        ph, q = K.idle_common(i, 10)
        q.update(head_rot=0.04 * math.sin(ph - 0.8), antenna=0.25 * math.sin(ph - 1.4), blink={6: 0.6, 7: 1.0}.get(i, 0.0))
        out.append(q)
    for i in range(12):                                                   # walk: a skating glide (pads slide, little lift)
        ph = TAU * i / 12
        legs = K.walk_legs(ph, 0.10, 0.02)
        out.append(dict(legs=legs, slide=tuple(0.18 * math.sin(ph + f) for f in (math.pi, 1.5 * math.pi, 0.0, 0.5 * math.pi)),
                        bob=0.004 * math.cos(2 * ph), sz=1 + 0.015 * math.cos(2 * ph), rock=0.03 * math.sin(ph), lean=0.03,
                        head_rot=0.03 * math.sin(2 * ph - 0.5), antenna=0.30 * math.sin(2 * ph - 1.4)))
    out += [dict(sz=0.92, bob=-0.01, antenna=0.3, look=(0.7, -0.1)),     # react: eye-pop and a skid
            dict(sz=0.86, bob=-0.015, antenna=0.4, blink=0.6),
            dict(sz=1.14, bob=0.02, head=(0.0, 0.03), eye_pop=1.6, mouth=0.7, antenna=-0.7, lean=-0.06, slide=(0.3, 0.3, 0.3, 0.3)),
            dict(sz=1.10, bob=0.015, head=(0.0, 0.03), eye_pop=1.7, mouth=0.6, antenna=-0.6, lean=-0.08, shift=-0.04, slide=(0.35,) * 4),
            dict(sz=1.04, eye_pop=1.4, mouth=0.3, antenna=-0.3, shift=-0.06, slide=(0.2,) * 4),
            dict(sz=0.98, eye_pop=1.2, antenna=0.2, shift=-0.05, look=(-0.6, 0.0)),
            dict(sz=1.0, eye_pop=1.05, antenna=-0.1, shift=-0.03, look=(0.8, 0.1)),
            dict(sz=1.0, antenna=0.05)]
    out += [dict(q, antenna=q.get("ears", 0.0)) for q in K.bump_clip()]
    for i in range(12):                                                   # flee: a low dash, legs streaming back, dust behind
        ph = TAU * i / 6
        legs = K.walk_legs(ph, 0.16, 0.04)
        out.append(dict(legs=legs, slide=tuple(0.25 * math.sin(ph + f) for f in (math.pi, 1.5 * math.pi, 0.0, 0.5 * math.pi)),
                        bob=0.01 * abs(math.sin(ph)), sz=0.94, lean=0.10, rock=-0.03, head_rot=-0.06, antenna=0.6,
                        look=(0.9, 0.0), dust=(i % 6) / 6.0))
    return out


SPECIES = {"dustskater": dict(draw=draw_dustskater, poses=poses, frame=(128, 80), seed=31,
                              clips=[("idle", 10, True), ("walk", 12, True), ("react", 8, False), ("bump", 10, False), ("flee", 12, True)])}


def preview(out_dir, name="dustskater"):
    """The export's own review layout (render.py v3_sheet_review) from exact frames, on a Mars stand-in (not the Earth plains)."""
    import json
    import numpy as np
    from meridian import fakegp, pngio
    import gp_raster as GR
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    sp = SPECIES[name]
    fw, fh = sp["frame"]
    frames, widths, below = [], [], []
    for f, pose in enumerate(sp["poses"]()):
        gp = fakegp.FakeGP()
        M = mats(gp, name)
        d = fakegp.FakeDrawing()
        sp["draw"](d, M, pose, seed=5 * f)
        st = fakegp.strokes_of(d, gp, as_object=(name, "art"))
        zmin = min(float((s["xz"][:, 1] - s["radius"] * 1.2).min()) for s in st)
        if zmin * 64 < -2.0:
            below.append(f)
        img, w = GR.render_frame(st, fw, fh, 64, (0.5, 0.0), ss=4, seed=sp["seed"] * 1000 + f + 1)
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
    meta = {"key": f"creatures/mars/{name}", "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": 4,
            "frames": len(frames), "fps": 12, "pivot": [0.5, 0.0], "facing": "right", "ppu": 64, "animations": anims, "squash_root": True}
    problems = v3.validate_sheet(meta, sheet.shape)
    clipped = [i for i, im in enumerate(frames) if im[:2, :, 3].any() or im[:, :2, 3].any() or im[:, -2:, 3].any()]
    if clipped:
        problems.append(f"frames {clipped[:8]} touch the 2 px edge")
    if below:
        problems.append(f"frames {below[:8]} below the ground line")
    dd = os.path.join(out_dir, "b139_mars")
    os.makedirs(dd, exist_ok=True)
    png = os.path.join(dd, f"{name}_color.png")
    nb = pngio.write_png(png, sheet)
    with open(os.path.join(dd, f"{name}.json"), "w", encoding="utf-8", newline="\n") as f_:
        json.dump(meta, f_, indent=2)
    outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
    stats = {"outer_px": (min(w[1] for w in outer), max(w[2] for w in outer)), "inner_px": (min(w[1] for w in inner), max(w[2] for w in inner)),
             "inner_n": len(inner), "palette": v3.palette_hits(sheet, "mars"), "problems": problems,
             "sheet_wh": (sheet.shape[1], sheet.shape[0]), "png_kb": nb // 1024}
    entry = {"key": meta["key"], "planet": "mars", "bg_scene": "-", "beside": "characters/surveyor/side",
             "self_check": {"ink": "shell plate seams, rivet dots, hatch, pad seams, antenna knobs",
                            "motion": "squash on the beat, hose legs, the antennae drag and overshoot, skating pads slide; flee kicks dust",
                            "original": "our own scavenger: a butterscotch dome with rust bands on skate pads; no teeth",
                            "style": "the B-132 kit (Gus's construction); LEAD judges"},
             "ours": "a little butterscotch dome on four skate pads that glides over the rust and kicks up dust when it bolts"}
    out = os.path.join(out_dir, f"review_b139_mars_{name}_preview.png")
    boxes = review.v3_sheet_review(entry, meta, frames, png, out, stats)
    print(name, f"sheet {sheet.shape[1]}x{sheet.shape[0]} {nb // 1024} KB, ink {stats['outer_px'][0]:.2f}-{stats['outer_px'][1]:.2f} / "
          f"{stats['inner_px'][0]:.2f}-{stats['inner_px'][1]:.2f}, palette {stats['palette'][0] * 100:.1f}% {stats['palette'][1][:3]}, "
          f"problems {problems or '-'}, boxes not x: {','.join(k for k, (mk, _n) in boxes.items() if mk != 'x') or '-'}")


if __name__ == "__main__":
    preview(sys.argv[1])
