"""Planet discs for the space view (contract v3.0 §11.5, Bible §9.3; B-119). numpy only.

Painted watercolour discs with an ink outline that still read as the real planets, each with a
subtle personality idle at 12 fps. Space scale: SPACE_PPU px per space unit (PlanetConfig
.visualRadius), so Jupiter is ~636 px across; Jupiter and the Saturn body get 9-frame idles
(3x3 sheet <= 2048), the others 12. Saturn's rings are two static parts (behind / in front of
the body) whose wobble Unity plays from disc_rig.json.

Look: flat washes with pigment variation and paper grain (gen_painted_bg), one shadow tone on
the night side (light from the upper right, as the Sun sits screen-left of most views is NOT
assumed: the space view lights discs from the Sun at runtime is not v4; the crescent is drawn),
ink only on the outline and on drawn features (Neptune's face, ring edges).

  python build_discs_v3.py <out_dir>      writes every disc + a review sheet (preview)
"""
import math
import os
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gp_raster as GR  # noqa: E402
from meridian import pngio, v3  # noqa: E402

SPACE_PPU = 3.0
RADIUS_U = {"mercury": 14, "venus": 24, "earth": 25, "mars": 17, "jupiter": 106, "saturn": 96,
            "uranus": 57, "neptune": 56, "luna": 7}
FRAMES = {"jupiter": 9, "saturn": 9}
SS = 2
OUT_PX = 5.0                     # outline width (px at 1x), jitter +-20 %
IN_PX = 2.2
PAL = {k: np.array(v3.hex_rgb(h), np.float32) / 255 for k, h in v3.PALETTES["earth"].items()}


def mix(a, b, t):
    return a * (1 - t) + b * t


def shade(c):
    return mix(c, PAL["brown"], 0.3)          # the one shadow tone (v3.shadow_of)


def noise2(rng, n, sigma):
    """Smooth periodic noise on an n x n torus (unit std)."""
    sigma = min(sigma, n / 8)                # small discs: keep some variance (no NaN)
    w = rng.standard_normal((n, n))
    f = np.fft.fftfreq(n)
    g = np.exp(-2 * np.pi ** 2 * sigma ** 2 * (f[:, None] ** 2 + f[None, :] ** 2))
    o = np.real(np.fft.ifft2(np.fft.fft2(w) * g))
    return np.clip(o / max(float(o.std()), 1e-3), -3, 3)


class Disc:
    """Pixel grid of one disc frame at SS supersampling: u, v in [-1, 1] (v up), r, a lumpy rim."""
    def __init__(self, name, R_px, pad, seed):
        self.name, self.R = name, R_px
        self.size = int(2 * (R_px + pad))
        self.size += (-self.size) % 4
        n = self.size * SS
        c = n / 2
        yy, xx = np.mgrid[0:n, 0:n] + 0.5
        self.u = (xx - c) / (R_px * SS)
        self.v = -(yy - c) / (R_px * SS)
        rng = np.random.default_rng(seed)
        ang = np.arctan2(self.v, self.u)
        self.rim = 1.0 + 0.012 * np.sin(3 * ang + rng.uniform(0, 6)) + 0.008 * np.sin(5 * ang + rng.uniform(0, 6))
        self.r = np.hypot(self.u, self.v)
        self.inside = self.r <= self.rim
        self.grain = 1 + 0.03 * noise2(rng, n, 0.8 * SS) + 0.03 * noise2(rng, n, 30 * SS)
        self.pig = 1 + 0.05 * noise2(rng, n, 60 * SS)
        self.rng = rng



def finish(d, rgb, extra_ink=(), extra_rgba=()):
    """Paint -> premultiplied canvas: disc colour (+ grain), extra rgba layers, outline ink,
    extra ink strokes [(pts_px_at_ss, width_px_1x)]; box-down to 1x straight alpha uint8."""
    n = d.size * SS
    a = d.inside.astype(np.float32)
    col = np.clip(rgb * (d.grain * d.pig)[..., None], 0, 1) * a[..., None]
    acc = np.dstack([col, a])
    for lay in extra_rgba:                      # rgba float layers over the disc (rings front etc.)
        la = lay[..., 3:4]
        acc[..., :3] = lay[..., :3] * la + acc[..., :3] * (1 - la)
        acc[..., 3:] = la + acc[..., 3:] * (1 - la)
    ink = PAL["ink"]
    t = np.linspace(0, 2 * np.pi, 160, endpoint=False)
    ux = np.cos(t)
    vy = np.sin(t)
    k = d.R * SS
    c = n / 2
    rimv = np.array([d.rim[int(np.clip(c - vv * k, 0, n - 1)), int(np.clip(c + uu * k, 0, n - 1))] for uu, vv in zip(ux, vy)])
    px, py = c + ux * rimv * k, c - vy * rimv * k
    strokes = [(px, py, OUT_PX, True)] + [(p[:, 0], p[:, 1], w, False) for p, w in extra_ink]
    for i, (sx, sy, w, cyc) in enumerate(strokes):
        xz = np.c_[sx, -sy] / (SS * 64.0)        # jitter along arclength in "metres" at 64 px/m
        r = GR.jittered_radius(xz, np.full(len(sx), w / 2 / 64.0), 977 * i + len(sx), 64.0) * 64.0 * SS
        m = GR._ink_mask(sx, sy, r, cyc, n, n).astype(np.float32)[..., None]
        acc[..., :3] = ink * m + acc[..., :3] * (1 - m)
        acc[..., 3:] = m + acc[..., 3:] * (1 - m)
    small = acc.reshape(d.size, SS, d.size, SS, 4).mean(axis=(1, 3))
    al = small[..., 3:4]
    rgbo = np.where(al > 1e-6, small[..., :3] / np.maximum(al, 1e-6), 0)
    return np.clip(np.rint(np.dstack([rgbo, al]) * 255), 0, 255).astype(np.uint8)


def bands(d, spec, phase, wob=0.05, freq=3.0):
    """Horizontal bands: spec [(v_top, colour)] from the top; edges wobble with u + phase."""
    v = d.v + wob * np.sin(freq * np.pi * d.u + phase) * (1 - d.v ** 2)
    out = np.zeros(d.u.shape + (3,), np.float32)
    out[:] = spec[-1][1]
    for vt, col in reversed(spec):
        out[v <= vt] = out[v <= vt]
    for i, (vt, col) in enumerate(spec):
        lo = spec[i + 1][0] if i + 1 < len(spec) else -2
        out[(v <= vt) & (v > lo)] = col
    return out


def sphere_u(d, shift):
    """Surface longitude coordinate for features that rotate across the disc (periodic)."""
    s = np.arcsin(np.clip(d.u / np.sqrt(np.maximum(1 - d.v ** 2, 1e-6)), -1, 1)) / np.pi   # -0.5..0.5 on the face
    return (s + shift) % 1.0


def blobs(d, pts, su):
    m = np.zeros(d.u.shape, bool)
    for (lon, lat, rad) in pts:
        dl = np.minimum(np.abs(su - lon), 1 - np.abs(su - lon)) * np.pi * np.sqrt(np.maximum(1 - d.v ** 2, 0))
        m |= (dl ** 2 + (d.v - lat) ** 2) < rad ** 2
    return m


def paint(name, d, f, nf):
    t = f / nf
    rng = np.random.default_rng(91 + zlib.crc32(name.encode()) % 7)
    nightm = d.inside & (np.hypot(d.u - 0.30, d.v - 0.30) > 1.06)  # curved terminator: night crescent lower left
    extra_ink, extra_rgba = [], []
    if name == "mercury":
        base = mix(PAL["brown"], PAL["offwhite"], 0.55)
        rgb = np.broadcast_to(base, d.u.shape + (3,)).copy()
        su = sphere_u(d, t * 0.25)
        cr = [(rng.uniform(0, 1), rng.uniform(-0.8, 0.8), rng.uniform(0.07, 0.18)) for _ in range(14)]
        m = blobs(d, cr, su)
        rgb[m] = shade(base)
        rim = blobs(d, [(a, b, c * 0.75) for a, b, c in cr], su)
        rgb[m & ~rim] = mix(base, PAL["offwhite"], 0.4)
    elif name == "venus":
        a, b = mix(PAL["mustard"], PAL["offwhite"], 0.55), mix(PAL["mustard"], PAL["offwhite"], 0.25)
        vv = d.v + 0.22 * np.abs(d.u) ** 1.6 + 0.06 * np.sin(2 * np.pi * (sphere_u(d, t) * 2))
        rgb = np.where((np.floor(vv * 4.5) % 2 == 0)[..., None], a, b)
    elif name == "earth" or name == "luna":
        if name == "luna":
            base = mix(PAL["offwhite"], PAL["sky"], 0.35)
            rgb = np.broadcast_to(base, d.u.shape + (3,)).copy()
            m = blobs(d, [(0.2, 0.3, 0.25), (0.45, -0.1, 0.3), (0.05, -0.4, 0.2)], sphere_u(d, 0.0))
            rgb[m] = shade(base)
        else:
            rgb = np.broadcast_to(PAL["teal"], d.u.shape + (3,)).copy()
            su = sphere_u(d, t * 0.5)
            land = blobs(d, [(0.10, 0.35, 0.30), (0.18, 0.05, 0.22), (0.22, -0.35, 0.28), (0.52, 0.40, 0.34),
                             (0.60, -0.05, 0.25), (0.78, 0.30, 0.22), (0.83, -0.45, 0.2)], su)
            rgb[land] = PAL["green"]
            dry = land & blobs(d, [(0.20, -0.30, 0.15), (0.58, 0.30, 0.15)], su)
            rgb[dry] = mix(PAL["green"], PAL["mustard"], 0.5)
            rgb[np.abs(d.v) > 0.84 + 0.04 * np.sin(9 * d.u + 1.3)] = PAL["offwhite"]
            streaks = [(lon + 0.012 * j, lat + 0.03 * math.sin(0.5 * j), 0.075) for lon, lat in
                       ((0.05, 0.55), (0.30, -0.15), (0.48, 0.12), (0.70, -0.60), (0.90, 0.25)) for j in range(-8, 9)]
            cl = blobs(d, streaks, sphere_u(d, t * 0.75 + 0.1))
            rgb[cl] = PAL["offwhite"]
    elif name == "mars":
        base = mix(PAL["red"], PAL["mustard"], 0.25)
        rgb = np.broadcast_to(base, d.u.shape + (3,)).copy()
        su = sphere_u(d, t * 0.5)
        rgb[blobs(d, [(0.1, 0.2, 0.25), (0.35, -0.2, 0.3), (0.62, 0.1, 0.22), (0.85, -0.3, 0.2)], su)] = shade(base)
        rgb[d.v > 0.80] = PAL["offwhite"]
        rgb[d.v < -0.88] = mix(PAL["offwhite"], base, 0.3)
    elif name == "jupiter":
        ph = 2 * np.pi * t
        spec = [(1.1, mix(PAL["offwhite"], PAL["mustard"], 0.3)), (0.62, mix(PAL["brown"], PAL["mustard"], 0.45)),
                (0.42, PAL["offwhite"]), (0.18, mix(PAL["mustard"], PAL["red"], 0.25)), (-0.05, PAL["offwhite"]),
                (-0.25, mix(PAL["brown"], PAL["red"], 0.35)), (-0.52, mix(PAL["offwhite"], PAL["mustard"], 0.4)),
                (-0.75, mix(PAL["brown"], PAL["mustard"], 0.5))]
        rgb = bands(d, spec, ph, wob=0.045, freq=4.0)
        su = sphere_u(d, t * 0.35)
        spot = blobs(d, [(0.25, -0.38, 0.13)], su)
        rgb[spot] = PAL["red"]
    elif name == "saturn":
        spec = [(1.1, mix(PAL["mustard"], PAL["offwhite"], 0.6)), (0.5, mix(PAL["mustard"], PAL["offwhite"], 0.3)),
                (0.15, mix(PAL["mustard"], PAL["offwhite"], 0.55)), (-0.2, mix(PAL["mustard"], PAL["brown"], 0.15)),
                (-0.6, mix(PAL["mustard"], PAL["offwhite"], 0.5))]
        rgb = bands(d, spec, 2 * np.pi * t, wob=0.025, freq=3.0)
    elif name == "uranus":
        rgb = bands(d, [(1.1, mix(PAL["sky"], PAL["teal"], 0.2)), (0.3, mix(PAL["sky"], PAL["offwhite"], 0.3)),
                        (-0.3, mix(PAL["sky"], PAL["teal"], 0.3))], 2 * np.pi * t, wob=0.02)
    elif name == "neptune":
        rgb = bands(d, [(1.1, PAL["teal"]), (0.35, mix(PAL["teal"], PAL["sky"], 0.4)), (-0.1, PAL["teal"]),
                        (-0.5, mix(PAL["teal"], PAL["brown"], 0.25))], 2 * np.pi * t, wob=0.03)
        rgb[blobs(d, [(0.22, -0.25, 0.12)], sphere_u(d, t * 0.4))] = shade(PAL["teal"])
        # the grumpy face (Bible §9.3): low heavy brows, half-lidded eyes, a pout; a slow blink
        k, c = d.R * SS, d.size * SS / 2
        blink = 1.0 if f in (7, 8) else 0.55
        for s in (-1, 1):
            ex, ez = s * 0.30, 0.22
            pts = [(c + (ex + 0.13 * math.cos(a)) * k, c - (ez + 0.10 * math.sin(a) * (1 - blink)) * k)
                   for a in np.linspace(math.pi, 2 * math.pi, 12)]
            extra_ink.append((np.array(pts), IN_PX))
            brow = [(c + (ex - 0.17 * s) * k, c - (ez + 0.05) * k), (c + (ex + 0.17 * s) * k, c - (ez + 0.17) * k)]   # V: inner ends low = a scowl
            lid = [(c + (ex - 0.13) * k, c - (ez + 0.005) * k), (c + (ex + 0.13) * k, c - (ez + 0.005) * k)]
            extra_ink.append((np.array(lid), IN_PX))
            extra_ink.append((np.array(brow), IN_PX + 0.6))
        mouth = [(c + (x) * k, c - (-0.22 + 0.05 * math.cos(x / 0.18 * math.pi / 2)) * k) for x in np.linspace(-0.18, 0.18, 10)]
        extra_ink.append((np.array(mouth), IN_PX))
    rgb = np.asarray(rgb, np.float32)
    rgb[nightm] = shade(rgb[nightm])
    return rgb, extra_ink, extra_rgba


def saturn_rings(R, tilt=0.30):
    """Rings as two static parts (back = the half behind the body, front = in front): bands
    1.24-2.27 R with the Cassini gap, ink on the outer and inner edges. -> (back, front) uint8."""
    Rr = 2.27 * R
    W = int(2 * Rr + 24)
    W += (-W) % 4
    H = int(2 * Rr * tilt + 24)
    H += (-H) % 4
    n_w, n_h = W * SS, H * SS
    yy, xx = np.mgrid[0:n_h, 0:n_w] + 0.5
    u = (xx - n_w / 2) / (R * SS)
    v = (yy - n_h / 2) / (R * SS * tilt)
    rr = np.hypot(u, v)
    ring = (rr >= 1.24) & (rr <= 2.27) & ~((rr > 1.95) & (rr < 2.03))
    col = np.zeros((n_h, n_w, 3), np.float32)
    col[:] = mix(PAL["mustard"], PAL["offwhite"], 0.55)
    col[(rr > 1.55) & (rr < 1.95)] = mix(PAL["mustard"], PAL["offwhite"], 0.25)
    col[(rr > 2.03)] = mix(PAL["brown"], PAL["mustard"], 0.5)
    acc = np.dstack([col * ring[..., None], ring.astype(np.float32)])
    t = np.linspace(0, 2 * np.pi, 220, endpoint=False)
    for i, rad in enumerate((2.27, 1.24)):
        px = n_w / 2 + np.cos(t) * rad * R * SS
        py = n_h / 2 + np.sin(t) * rad * R * SS * tilt
        xz = np.c_[px, -py] / (SS * 64.0)
        w = OUT_PX if i == 0 else IN_PX
        r = GR.jittered_radius(xz, np.full(len(px), w / 2 / 64.0), 31 + i, 64.0) * 64.0 * SS
        m = GR._ink_mask(px, py, r, True, n_h, n_w).astype(np.float32)[..., None]
        acc[..., :3] = PAL["ink"] * m + acc[..., :3] * (1 - m)
        acc[..., 3:] = m + acc[..., 3:] * (1 - m)
    small = acc.reshape(H, SS, W, SS, 4).mean(axis=(1, 3))
    al = small[..., 3:4]
    img = np.clip(np.rint(np.dstack([np.where(al > 1e-6, small[..., :3] / np.maximum(al, 1e-6), 0), al]) * 255), 0, 255).astype(np.uint8)
    back, front = img.copy(), img.copy()
    back[H // 2:] = 0                          # upper half passes behind the body
    front[:H // 2] = 0
    return back, front


def build_disc(name):
    R = RADIUS_U[name] * SPACE_PPU
    nf = FRAMES.get(name, 12)
    pad = 10 if name != "uranus" else 10
    frames = []
    for f in range(nf):
        d = Disc(name, R, pad, seed=zlib.crc32(name.encode()) % 1000)
        rgb, ink, rgba = paint(name, d, f, nf)
        frames.append(finish(d, rgb, ink, rgba))
    return frames, R


def sheet_meta(key, frames, R_px, name):
    fw = frames[0].shape[1]
    cols = v3.columns_for(fw, len(frames))
    return {"key": key, "style": "v3", "frame_width": fw, "frame_height": frames[0].shape[0], "columns": cols,
            "gutter": v3.GUTTER, "frames": len(frames), "fps": v3.FPS, "pivot": [0.5, 0.5], "facing": "right",
            "ppu": SPACE_PPU, "space_ppu": SPACE_PPU, "radius_u": RADIUS_U[name], "radius_px": round(R_px, 1),
            "animations": [{"name": "idle", "start": 0, "length": len(frames), "loop": True, "loop_from": 0}]}


ORDER = ["mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune"]


def export(art, preview_dir, stamp=None):
    """D-098 / contract §11.5: planets/<planet>/disc_color.png + disc.json (Luna: planets/earth/
    luna_*), Saturn's rings_back / rings_front + disc_rig.json; validated; then the review sheet
    (built from the same frames). Returns [(key, w, h, frames, kb)]."""
    import json as _json
    out = []
    tiles = {}
    for name in ORDER + ["luna"]:
        frames, R = build_disc(name)
        tiles[name] = (frames, R)
        planet, variant = ("earth", "luna") if name == "luna" else (name, "disc")
        key = f"planets/{planet}/{variant}"
        meta = sheet_meta(key, frames, R, name)
        sheet = pack(frames, meta["columns"])
        probs = v3.validate_sheet(meta, sheet.shape, ppu=SPACE_PPU)
        if probs:
            raise ValueError(f"{key}: " + "; ".join(probs))
        d = os.path.join(art, "planets", planet)
        os.makedirs(d, exist_ok=True)
        n = pngio.write_png(os.path.join(d, f"{variant}_color.png"), sheet)
        if n > v3.MAX_FILE_BYTES:
            raise ValueError(f"{key}: {n / 2**20:.1f} MB over 4 MB")
        with open(os.path.join(d, f"{variant}.json"), "w", encoding="utf-8", newline="\n") as f:
            _json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((key, sheet.shape[1], sheet.shape[0], len(frames), n // 1024))
    back, front = saturn_rings(RADIUS_U["saturn"] * SPACE_PPU)
    d = os.path.join(art, "planets", "saturn")
    for nm, im in (("rings_back", back), ("rings_front", front)):
        n = pngio.write_png(os.path.join(d, f"{nm}_color.png"), im)
        out.append((f"planets/saturn/{nm}", im.shape[1], im.shape[0], 1, n // 1024))
    rig = {"key": "planets/saturn/disc_rig", "style": "v3", "space_ppu": SPACE_PPU,
           "parts": [{"name": "rings_back", "order": 0, "pivot": [0.5, 0.5]}, {"name": "disc", "order": 1},
                     {"name": "rings_front", "order": 2, "pivot": [0.5, 0.5]}],
           "wobble": {"parts": ["rings_back", "rings_front"], "scale_y": 0.04, "rotate_deg": 1.5, "beat_bpm": 110,
                      "stepped_hz": 12}}
    with open(os.path.join(d, "disc_rig.json"), "w", encoding="utf-8", newline="\n") as f:
        _json.dump(rig, f, indent=2)
        f.write("\n")
    return out, tiles


def pack(frames, cols, gutter=v3.GUTTER):
    fh, fw = frames[0].shape[:2]
    rows = -(-len(frames) // cols)
    c = min(cols, len(frames))
    s = np.zeros((rows * fh + (rows - 1) * gutter, c * fw + (c - 1) * gutter, 4), np.uint8)
    for i, f in enumerate(frames):
        r, k = divmod(i, cols)
        s[r * (fh + gutter):r * (fh + gutter) + fh, k * (fw + gutter):k * (fw + gutter) + fw] = f
    return s


def preview(out_dir):
    """All eight side by side at the space scale (+ Luna, Saturn's rings) + 2x detail of frame 0."""
    import time
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()
    tiles = {}
    for name in ORDER + ["luna"]:
        frames, R = build_disc(name)
        tiles[name] = (frames, R)
        print(name, len(frames), frames[0].shape, f"{time.time() - t0:.1f}s", flush=True)
    back, front = saturn_rings(RADIUS_U["saturn"] * SPACE_PPU)
    H = 760
    W = 16 + sum(tiles[n][0][0].shape[1] + 24 for n in ORDER) + 700
    canvas = np.zeros((H, W, 3), np.float32)
    canvas[:] = mix(PAL["ink"], PAL["teal"], 0.18)
    x = 16
    for n in ORDER:
        fr = tiles[n][0][0]
        h, w = fr.shape[:2]
        y = H // 2 - h // 2
        if n == "saturn":
            bh, bw = back.shape[:2]
            review._over(canvas, back, x + w // 2 - bw // 2, H // 2 - bh // 2)
        review._over(canvas, fr, x, y)
        if n == "saturn":
            review._over(canvas, front, x + w // 2 - bw // 2, H // 2 - bh // 2)
        if n == "earth":
            lf = tiles["luna"][0][0]
            review._over(canvas, lf, x + w - 10, y - lf.shape[0] // 2)
        review.draw(canvas, n, x, 8, (1.0, 0.97, 0.85))
        x += w + 24 + (420 if n == "saturn" else 0)
    review.draw(canvas, f"planet discs at the space scale ({SPACE_PPU:g} px per unit), frame 0 each; sky = placeholder", 8, H - 18, (1.0, 0.97, 0.85))
    # 2x detail row: every frame of Earth and the Neptune face
    rows = [canvas]
    for n in ("earth", "neptune", "jupiter"):
        frs = tiles[n][0]
        fh, fw = frs[0].shape[:2]
        sc = 2 if n != "jupiter" else 1
        per = max(1, (W - 16) // (fw * sc + 8))
        row = np.tile(mix(PAL["ink"], PAL["teal"], 0.18), (fh * sc + 30, W, 1)).astype(np.float32)
        for i, fr in enumerate(frs[:per]):
            big = np.repeat(np.repeat(fr, sc, 0), sc, 1)
            review._over(row, big, 8 + i * (fw * sc + 8), 26)
            review.draw(row, f"{n} {i}", 8 + i * (fw * sc + 8), 6, (1.0, 0.97, 0.85))
        rows.append(row)
    img = np.vstack(rows)
    review.write(os.path.join(out_dir, "review_b119_discs_preview.png"), img)
    print("review written", img.shape, f"{time.time() - t0:.1f}s")


if __name__ == "__main__":
    preview(sys.argv[1])
