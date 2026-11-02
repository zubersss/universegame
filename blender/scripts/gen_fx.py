"""FX frame sheets (B-012, contract §4 `fx/<name>`), called by render.py as a generator.

Seeded numpy, returns {"frames": [{map: HxWx4 uint8}, ...]}; render.py packs the sheet
(4 px gutters) and writes base.json from the manifest's `animations`. Looping effects use
noise that loops in time: either rolled by exactly one period over the cycle, or a
cos/sin blend of two fields. Emission is the colour premultiplied by intensity (black where
nothing glows); colour alpha is coverage.

  thruster     : downward exhaust flame, nozzle at the top (pivot), hot core -> orange -> red
  dust         : rising, spreading puff (neutral tan; tint per planet in Unity), no emission
  dig_sparks   : burst of hot streaks from the centre, fading
  escape_band  : horizontal glowing band that flows along x; tiles in x (no side padding)
  heat_shimmer : entry plasma: bright bow-shock arc + orange-white streaks flowing up (B-030)
  beam_ray, lance_bolt, survey_scan, builder_ghost : Rig module FX (B-037)
"""
import math

import numpy as np

from meridian.noise import fft_noise

PAD = 8


def C(c):
    return np.array(c, np.float32) / 255.0


def _u8(a):
    return np.clip(np.rint(a * 255.0), 0, 255).astype(np.uint8)


def _frame(rgb, a, glow=None):
    """uint8 maps for one frame; RGB under alpha 0 stays the local colour (no halos)."""
    a = np.clip(a, 0, 1)
    out = {"color": np.dstack([_u8(rgb), _u8(a)])}
    if glow is not None:
        out["emission"] = np.dstack([_u8(rgb * np.clip(glow, 0, 1)[..., None]), np.full(a.shape, 255, np.uint8)])
    return out


def _ramp(t, stops):
    """Piecewise-linear colour ramp; stops = [(pos, rgb0-1), ...] ascending."""
    t = np.clip(t, 0, 1)[..., None]
    out = np.zeros(t.shape[:-1] + (3,), np.float32) + stops[0][1]
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        k = np.clip((t - p0) / max(p1 - p0, 1e-6), 0, 1)
        out = np.where(t >= p0, c0 + (c1 - c0) * k, out)
    return out


def thruster(rng, w, h, n):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = (xx + 0.5 - w / 2) / (w / 2 - PAD)
    v = (yy + 0.5 - PAD) / (h - 2 * PAD)                  # 0 at the nozzle (top), 1 at the tail
    base1 = fft_noise(rng, h, w, 6, 60, 0.8)
    base2 = fft_noise(rng, h, w, 3, 16, 0.4)
    frames = []
    for i in range(n):
        shift = int(round(i * h / n))                     # flows down one full period per loop
        nz = 0.65 * np.roll(base1, shift, axis=0) + 0.35 * np.roll(base2, 2 * shift, axis=0)
        vv = np.clip(v, 0, 1)
        width = 0.5 * (0.35 + 0.65 * (1 - vv) ** 0.6) * (1 + 0.12 * nz)
        I = np.exp(-2.2 * (u / np.maximum(width, 1e-3)) ** 2) * (1 - vv) ** 1.3 * (0.85 + 0.3 * nz)
        I *= ((v > 0) & (v < 1)) * _inside(h, w)
        core =np.exp(-(u / (0.35 * width)) ** 2) * np.exp(-vv * 5.0)
        heat = np.clip(0.75 * I + 0.6 * core, 0, 1)
        col = _ramp(heat, [(0.0, C((150, 40, 16))), (0.35, C((235, 110, 36))), (0.7, C((255, 196, 110))),
                           (1.0, C((228, 238, 255)))])
        frames.append(_frame(col, I * 1.5, glow=np.clip(I * 1.3 + core * _inside(h, w), 0, 1)))
    return frames


def dust(rng, w, h, n):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nz = fft_noise(rng, h, w, 4, 40, 0.7)
    frames = []
    for i in range(n):
        t = i / max(n - 1, 1)
        r = (14 + 38 * t) * w / 128
        cx, cy = w / 2, h - PAD - r * 0.9 - 6 * t * h / 128
        d = np.hypot((xx - cx) / 1.25, yy - cy) / r
        dens = np.clip(1 - d + 0.32 * np.roll(nz, int(-t * 20), axis=0), 0, 1)
        a = dens ** 1.3 * 0.85 * (1 - t) ** 1.2
        shade = np.clip(0.88 + 0.22 * ((xx - cx) - (yy - cy)) / (2 * r), 0.7, 1.15)   # lit upper-right
        col = C((188, 170, 146))[None, None, :] * shade[..., None]
        frames.append(_frame(col, a * _inside(h, w)))
    return frames


def dig_sparks(rng, w, h, n):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    k = 46
    ang = rng.uniform(-np.pi * 0.95, -np.pi * 0.05, k)    # mostly upward (image y down)
    spd = rng.uniform(0.55, 1.15, k) * (w / 2 - PAD - 4)
    life = rng.uniform(0.55, 1.0, k)
    frames = []
    for i in range(n):
        t = (i + 1) / n
        I = np.zeros((h, w), np.float32)
        for a0, s, L in zip(ang, spd, life):
            if t > L:
                continue
            p1 = np.array([w / 2 + np.cos(a0) * s * t, h / 2 + np.sin(a0) * s * t + 30 * t * t * h / 128])
            p0 = np.array([w / 2 + np.cos(a0) * s * max(t - 0.12, 0), h / 2 + np.sin(a0) * s * max(t - 0.12, 0)
                           + 30 * max(t - 0.12, 0) ** 2 * h / 128])
            d = _seg_dist(xx, yy, p0, p1)
            I = np.maximum(I, np.exp(-(d / 1.4) ** 2) * (1 - (t / L) ** 2.5))   # bright until late
        I *= _inside(h, w)
        col = _ramp(I, [(0.0, C((220, 90, 30))), (0.5, C((255, 170, 70))), (1.0, C((255, 240, 200)))])
        frames.append(_frame(col, I * 1.4, glow=I))
    return frames


def escape_band(rng, w, h, n):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    n1 = fft_noise(rng, h, w, 8, 128, 1.0)
    n2 = fft_noise(rng, h, w, 4, 32, 0.6)
    frames = []
    for i in range(n):
        shift = int(round(i * w / n))                     # flows along x one full period per loop
        a1, a2 = np.roll(n1, shift, axis=1), np.roll(n2, -2 * shift, axis=1)
        cy = h / 2 + 3 * a1
        sig = 6 + 2.5 * a2
        I = np.exp(-((yy - cy) / np.maximum(sig, 2)) ** 2) * (0.65 + 0.35 * np.tanh(a1))
        I *= ((yy >= PAD) & (yy < h - PAD))
        col = _ramp(I, [(0.0, C((40, 140, 210))), (0.6, C((120, 220, 255))), (1.0, C((236, 250, 255)))])
        frames.append(_frame(col, I, glow=I))
    return frames


def heat_shimmer(rng, w, h, n):
    """B-030: entry plasma / heat haze, additive. A bright bow-shock arc at the bottom (the
    leading face) and orange-white plasma streaks flowing up and out, flickering; reads over
    a dark sky. Loops: the streak noise rolls exactly one period per cycle."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = (xx + 0.5 - w / 2) / (w / 2 - PAD)                # -1..1 across
    v = (h - PAD - yy - 0.5) / (h - 2 * PAD)              # 0 at the leading (bottom) edge, 1 at the top
    base = fft_noise(rng, h, w, 24, 128, 1.0)            # long wavelengths only: smooth streaks, no speckle
    fine = fft_noise(rng, h, w, 10, 40, 1.0)
    inside = _inside(h, w)
    frames = []
    for i in range(n):
        shift = int(round(-i * h / n))                    # streaks travel up one period per loop
        s1, s2 = np.roll(base, shift, axis=0), np.roll(fine, 2 * shift, axis=0)
        arc = v - 0.18 * u ** 2                           # bow shock: curved, hugging the bottom
        shock = np.exp(-((arc - 0.08) / 0.07) ** 2) * np.clip(1 - np.abs(u) ** 3, 0, 1)
        spread = 0.55 + 0.45 * np.clip(v, 0, 1)           # the wake widens as it trails
        streak = np.clip(np.sin(u * 9.0 / spread + 0.9 * s1 + 0.35 * s2) * 0.5 + 0.5, 0, 1) ** 3
        wake = streak * np.exp(-2.4 * np.clip(arc, 0, None)) * np.exp(-(u / spread) ** 2 * 1.4) * (arc > 0.02)
        I = np.clip(1.15 * shock + 0.9 * wake * (0.8 + 0.2 * s2), 0, 1) * inside
        col = _ramp(I, [(0.0, C((170, 50, 18))), (0.35, C((240, 120, 40))), (0.7, C((255, 206, 128))),
                        (1.0, C((255, 246, 232)))])
        frames.append(_frame(col, np.clip(I * 1.4, 0, 1), glow=I))
    return frames


def beam_ray(rng, w, h, n):
    """B-037 Beam: horizontal cyan mining ray that tiles in x (Unity stretches it from the
    muzzle to the hit point); flickering width, white-hot core; no side padding."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    n1 = fft_noise(rng, h, w, 8, 128, 1.0)
    n2 = fft_noise(rng, h, w, 3, 24, 0.6)
    frames = []
    for i in range(n):
        shift = int(round(i * w / n))                     # flows along x one period per loop
        a1, a2 = np.roll(n1, shift, axis=1), np.roll(n2, 2 * shift, axis=1)
        sig = 4.5 + 1.1 * a1 + 0.5 * a2                   # body: a thin filament read as a wire
        I = np.exp(-((yy - h / 2) / np.maximum(sig, 1.0)) ** 2) * (0.85 + 0.15 * np.tanh(a2))
        core = np.exp(-((yy - h / 2) / np.maximum(sig * 0.35, 0.6)) ** 2)
        I = np.clip(I + 0.5 * core, 0, 1) * ((yy >= PAD) & (yy < h - PAD))
        col = _ramp(I, [(0.0, C((30, 120, 200))), (0.55, C((110, 230, 255))), (1.0, C((240, 252, 255)))])
        frames.append(_frame(col, np.clip(I * 1.3, 0, 1), glow=I))
    return frames


def lance_bolt(rng, w, h, n):
    """B-037 Lance: an orange-white bolt, head at 3/4 width (pivot), trailing streak to the
    left that flickers; Unity moves the sprite, so it doesn't tile."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    hx, cy = 0.75 * w, h / 2
    nz = fft_noise(rng, h, w, 4, 40, 0.8)
    frames = []
    for i in range(n):
        s = np.roll(nz, int(round(i * w / n)), axis=1)
        behind = np.clip((hx - xx) / (hx - PAD), 0, 1)                      # 0 at the head
        tail = np.where(xx <= hx, np.exp(-3.2 * behind) * (0.75 + 0.25 * s), np.exp(-((xx - hx) / 3.5) ** 2))
        sig = 1.6 + 2.2 * behind
        I = np.exp(-((yy - cy) / sig) ** 2) * tail
        head = np.exp(-(((xx - hx) / 5.0) ** 2 + ((yy - cy) / 3.0) ** 2))
        I = np.clip(I + head, 0, 1) * _inside(h, w)
        col = _ramp(I, [(0.0, C((160, 40, 20))), (0.4, C((255, 110, 50))), (0.75, C((255, 200, 140))),
                        (1.0, C((255, 250, 240)))])
        frames.append(_frame(col, np.clip(I * 1.4, 0, 1), glow=I))
    return frames


def survey_scan(rng, w, h, n):
    """B-037 Survey: a ring expanding from the centre and fading (one-shot), slightly broken
    up, green-cyan with a bright leading edge and a faint wash inside."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot(xx + 0.5 - w / 2, yy + 0.5 - h / 2)
    R = w / 2 - PAD - 2
    ang = np.arctan2(yy - h / 2, xx - w / 2)
    brk = 0.8 + 0.2 * np.sin(ang * 7 + rng.uniform(0, 6.28)) * np.sin(ang * 3)
    frames = []
    for i in range(n):
        t = (i + 1) / n
        rr = R * (0.08 + 0.92 * t ** 0.8)
        wd = 2.0 + 5.0 * t
        ring = np.exp(-((r - rr) / wd) ** 2) * brk
        wash = 0.12 * np.clip(1 - r / rr, 0, 1) * (r < rr)
        I = np.clip((ring + wash) * (1 - t) ** 1.1 * 1.3, 0, 1) * _inside(h, w)
        col = _ramp(I, [(0.0, C((40, 160, 140))), (0.6, C((120, 255, 200))), (1.0, C((236, 255, 246)))])
        frames.append(_frame(col, I, glow=I))
    return frames


def builder_ghost(rng, w, h, n):
    """B-037 Builder: placement preview of one 1 m block (128 px inside the 8 px padding):
    translucent amber fill, scanlines drifting up, bright edges and corner brackets; pulses.
    Unity tints it red when placement is blocked."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    x0, x1, y0, y1 = PAD, w - PAD, PAD, h - PAD
    inside = ((xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)).astype(np.float32)
    d = np.minimum.reduce([xx - x0, x1 - 1 - xx, yy - y0, y1 - 1 - yy])        # px to the edge
    edge = inside * np.clip(1.0 - d / 2.0, 0, 1)
    cl = 0.28 * (x1 - x0)                                                        # corner bracket length
    near_x = np.minimum(xx - x0, x1 - 1 - xx) < cl
    near_y = np.minimum(yy - y0, y1 - 1 - yy) < cl
    bracket = inside * np.clip(1.0 - d / 4.0, 0, 1) * (near_x & near_y)
    frames = []
    for i in range(n):
        t = i / n
        pulse = 0.85 + 0.15 * math.cos(2 * math.pi * t)
        scan = 0.5 + 0.5 * np.sin((yy + t * 16) * (2 * math.pi / 8))           # 8 px lines drift up
        a = np.clip(inside * (0.09 + 0.04 * scan) + 0.7 * edge + 0.3 * bracket, 0, 1) * pulse   # light fill: edges carry it
        I = np.clip(edge + bracket + 0.35 * inside * scan, 0, 1) * pulse
        col = _ramp(I, [(0.0, C((200, 130, 40))), (0.6, C((255, 184, 70))), (1.0, C((255, 236, 190)))])
        frames.append(_frame(col, a, glow=I))
    return frames


def warden_bolt(rng, w, h, n):
    """B-043 Warden shot: a teal-green bolt with a bright ring at the head (the sentinel's
    lens colour) and a braided twin trail; head at 3/4 width (pivot)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    hx, cy = 0.75 * w, h / 2
    frames = []
    for i in range(n):
        ph = 2 * math.pi * i / n
        behind = np.clip((hx - xx) / (hx - PAD), 0, 1)
        fade = np.exp(-4.5 * behind) * (xx <= hx)                    # B-052: short trail
        braid = 0.0
        for k in (0, math.pi):                                       # two strands twisting
            yc = cy + 3.5 * np.sin(behind * 14 + ph + k) * behind ** 0.5
            braid = braid + np.exp(-((yy - yc) / 2.4) ** 2)
        I = np.clip(braid, 0, 1) * fade
        r = np.hypot(xx - hx, yy - cy)
        # B-052: head ~2x in area within the 16 px inner band of the 32 px frame (size kept):
        # solid bright core r~5, rim ring at the band edge, soft halo.
        ring = np.exp(-((r - 6.6) / 1.2) ** 2)
        head = np.clip(1.05 * np.exp(-(r / 5.0) ** 2), 0, 1)        # keeps a teal tint (1.6 clipped to flat white)
        halo = 0.5 * np.exp(-(r / 9.0) ** 2)
        I = np.clip(I + ring + head + halo, 0, 1) * _inside(h, w)
        col = _ramp(I, [(0.0, C((20, 110, 90))), (0.5, C((90, 230, 200))), (1.0, C((236, 255, 248)))])
        frames.append(_frame(col, np.clip(I * 1.6, 0, 1), glow=np.clip(I * 1.3, 0, 1)))
    return frames


# ---------------------------------------------------------------- B-067 giant-world FX

def _bolt_path(rng, x0, y0, y1, w, rough, steps=48):
    """Jagged vertical path (midpoint-free random walk with a pull back to the centre line)."""
    xs, ys = [x0], [y0]
    x = x0
    for k in range(1, steps + 1):
        x += rng.normal(0, rough) - 0.08 * (x - x0)
        x = float(np.clip(x, PAD + 4, w - PAD - 4))
        xs.append(x)
        ys.append(y0 + (y1 - y0) * k / steps)
    return list(zip(xs, ys))


def _polyline_dist(xx, yy, pts):
    d = np.full(xx.shape, 1e9, np.float32)
    for p0, p1 in zip(pts, pts[1:]):
        d = np.minimum(d, _seg_dist(xx, yy, np.array(p0), np.array(p1)))
    return d


def lightning(rng, w, h, n):
    """Deck 2-3 lightning: a jagged white-violet bolt top to bottom with 2-3 branches, a soft
    lilac flash halo; frames: build, strike, flicker, re-strike, fade (one-shot)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    main = _bolt_path(rng, w / 2 + rng.uniform(-10, 10), PAD, h - PAD, w, 3.2)
    branches = []
    for _ in range(rng.integers(2, 4)):
        k = int(rng.integers(8, 32))
        bx, by = main[k]
        end = by + rng.uniform(0.2, 0.4) * h
        br = _bolt_path(rng, bx, by, min(end, h - PAD), w, 4.0, steps=16)
        drift = float(rng.choice((-1.6, 1.6)))                       # each branch leans one way
        branches.append([(float(np.clip(x + i * drift, PAD + 2, w - PAD - 2)), y) for i, (x, y) in enumerate(br)])
    d_main = _polyline_dist(xx, yy, main)
    d_br = np.minimum.reduce([_polyline_dist(xx, yy, b) for b in branches]) if branches else d_main
    core = np.exp(-(d_main / 1.3) ** 2) + 0.7 * np.exp(-(d_br / 1.0) ** 2)
    halo = np.exp(-(d_main / 14.0) ** 2)
    level = [0.25, 1.0, 0.55, 0.9, 0.35, 0.1, 0.0, 0.0][:n] + [0.0] * max(0, n - 8)
    frames = []
    for i in range(n):
        k = level[i]
        I = np.clip(core * k * (1.0 if i != 0 else 0.4) + 0.45 * halo * k, 0, 1) * _inside(h, w)
        col = _ramp(I, [(0.0, C((120, 90, 200))), (0.5, C((190, 170, 255))), (1.0, C((248, 246, 255)))])
        frames.append(_frame(col, np.clip(I * 1.3, 0, 1), glow=I))
    return frames


def _falling(rng, w, h, n, count, size, streak, cols, glint):
    """Tileable (x and y) falling particles: each moves down exactly one period over the loop."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    px = rng.uniform(0, w, count)
    py = rng.uniform(0, h, count)
    sz = rng.uniform(*size, count)
    spd = rng.choice([1, 2], count)                     # whole periods per loop: still tiles
    tw = rng.uniform(0, 2 * math.pi, count)
    frames = []
    for i in range(n):
        t = i / n
        I = np.zeros((h, w), np.float32)
        G = np.zeros((h, w), np.float32)
        for x, y0, s, v, ph in zip(px, py, sz, spd, tw):
            y = (y0 + v * h * t) % h
            dx = (xx - x + w / 2) % w - w / 2
            dy = (yy - y + h / 2) % h - h / 2
            body = np.exp(-(dx / s) ** 2 - (np.clip(dy, None, 0) / (s * streak)) ** 2 - (np.clip(dy, 0, None) / s) ** 2)
            I = np.maximum(I, body)
            if glint:
                sp = max(0.0, math.sin(ph + 2 * math.pi * 3 * t)) ** 4
                cross = (np.exp(-(dx / 0.8) ** 2 - (dy / (s * 3)) ** 2) + np.exp(-(dy / 0.8) ** 2 - (dx / (s * 3)) ** 2))
                G = np.maximum(G, sp * cross * (np.abs(dx) < s * 4) * (np.abs(dy) < s * 4))
        I = np.clip(I + G, 0, 1)
        col = _ramp(I, cols)
        frames.append(_frame(col, np.clip(I * 1.2, 0, 1), glow=np.clip(G + 0.3 * I, 0, 1) if glint else None))
    return frames


def diamond_rain(rng, w, h, n):
    """Uranus diamond rain: small bright diamonds (5-20 cm at 128 px/m is 6-26 px; drawn as
    2-5 px bodies with motion streaks) with sparkle crosses; tiles in x and y."""
    return _falling(rng, w, h, n, 26, (1.2, 2.6), 5.0,
                    [(0.0, C((150, 190, 220))), (0.6, C((210, 236, 252))), (1.0, C((255, 255, 255)))], True)


def methane_hail(rng, w, h, n):
    """Methane hail: pale cyan pellets with short streaks, denser, no sparkle; tiles in x and y."""
    return _falling(rng, w, h, n, 44, (1.4, 2.4), 3.0,
                    [(0.0, C((130, 190, 196))), (0.7, C((196, 236, 236))), (1.0, C((236, 252, 250)))], False)


def wind_streaks(rng, w, h, n):
    """Neptune lateral gusts: long soft white streaks flowing along x; tiles in x (no side padding)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rows = [(rng.uniform(PAD + 4, h - PAD - 4), rng.uniform(2.0, 5.0)) for _ in range(9)]
    fields = [fft_noise(rng, 1, w, w / 2.5, w, 0.6)[0] for _ in rows]      # long streaks (short wavelengths read as dashes)
    frames = []
    for i in range(n):
        sh = int(round(i * w / n))
        I = np.zeros((h, w), np.float32)
        for (y0, th), f in zip(rows, fields):
            s = np.clip((np.roll(f, sh) + 0.5) / 1.8, 0, 1) ** 1.5
            I += np.exp(-((yy - y0) / th) ** 2) * s[None, :]
        I = np.clip(I, 0, 1) * ((yy >= PAD) & (yy < h - PAD))
        col = _ramp(I, [(0.0, C((170, 190, 236))), (1.0, C((246, 248, 255)))])
        frames.append(_frame(col, np.clip(I * 0.8, 0, 1)))
    return frames


GLYPH = {"C": "111100100100111", "R": "110101110101101", "U": "101101101101111",
         "S": "111100111001111", "H": "101101111101101"}


def _text_mask(h, w, text, scale, cx, cy):
    m = np.zeros((h, w), np.float32)
    cw = 4 * scale
    x0 = int(round(cx - (len(text) * cw - scale) / 2))
    y0 = int(round(cy - 2.5 * scale))
    for k, ch in enumerate(text):
        g = GLYPH[ch]
        for r in range(5):
            for c in range(3):
                if g[r * 3 + c] == "1":
                    ys, xs = y0 + r * scale, x0 + k * cw + c * scale
                    m[ys:ys + scale, xs:xs + scale] = 1
    return m


def crush_pulse(rng, w, h, n):
    """The Crush Line (Bible §7.5): a pulsing dark band with glowing dark-red edges and the label
    "CRUSH"; tiles in x (one label per tile), loops."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = (yy + 0.5 - h / 2) / (h / 2 - PAD)
    nz = fft_noise(rng, 1, w, w / 8, w, 1.0)[0][None, :]
    label = _text_mask(h, w, "CRUSH", 4, w / 2, h / 2)
    frames = []
    for i in range(n):
        p = 0.5 + 0.5 * math.cos(2 * math.pi * i / n)
        band = np.clip(1.2 - np.abs(v) * 1.4, 0, 1)
        edge = np.exp(-((np.abs(v) - 0.62) / 0.12) ** 2) * (0.7 + 0.3 * nz) * (0.55 + 0.45 * p)
        I = np.clip(edge + label * (0.7 + 0.3 * p), 0, 1) * ((yy >= PAD) & (yy < h - PAD))
        col = _ramp(I, [(0.0, C((40, 8, 8))), (0.5, C((200, 40, 24))), (1.0, C((255, 210, 190)))])
        a = np.clip(np.maximum(band * (0.75 + 0.15 * p), I), 0, 1) * ((yy >= PAD) & (yy < h - PAD))
        frames.append(_frame(col, a, glow=I))
    return frames


def skip_spool(rng, w, h, n):
    """Skip Drive spool-up (top-down, one-shot): a violet ring contracting around the ship with
    two spiral arms, brightening to a white flash on the last frames."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot(xx + 0.5 - w / 2, yy + 0.5 - h / 2) / (w / 2 - PAD)
    ang = np.arctan2(yy - h / 2, xx - w / 2)
    frames = []
    for i in range(n):
        t = (i + 1) / n
        rr = 0.95 - 0.6 * t
        ring = np.exp(-((r - rr) / (0.05 + 0.03 * t)) ** 2)
        arms = np.clip(np.cos(2 * ang - 9 * r + 10 * t), 0, 1) ** 6 * np.exp(-((r - rr * 0.8) / 0.35) ** 2) * t
        core = np.exp(-(r / (0.12 + 0.25 * t ** 3)) ** 2) * t ** 2
        I = np.clip((ring * (0.4 + 0.6 * t) + 0.6 * arms + core), 0, 1) * _inside(h, w)
        col = _ramp(I, [(0.0, C((70, 40, 160))), (0.5, C((160, 120, 255))), (1.0, C((246, 240, 255)))])
        frames.append(_frame(col, np.clip(I * 1.3, 0, 1), glow=I))
    return frames


def skip_streak(rng, w, h, n):
    """Skip travel streak (top-down): a violet-white streak flowing along x with thin parallel
    filaments; tiles in x (no side padding), loops."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    n1 = fft_noise(rng, h, w, 6, w, 1.0)
    frames = []
    for i in range(n):
        a = np.roll(n1, int(round(i * w / n)), axis=1)
        dy = (yy + 0.5 - h / 2)
        core = np.exp(-(dy / (3.0 + 0.6 * a)) ** 2)
        fil = sum(np.exp(-((dy - o) / 1.0) ** 2) * np.clip(0.5 + 0.5 * np.roll(a, 17 * k, axis=1), 0, 1)
                  for k, o in enumerate((-9, -5, 5, 9)))
        I = np.clip(core + 0.5 * fil, 0, 1) * ((yy >= PAD) & (yy < h - PAD))
        col = _ramp(I, [(0.0, C((80, 50, 170))), (0.5, C((170, 140, 255))), (1.0, C((250, 248, 255)))])
        frames.append(_frame(col, np.clip(I * 1.3, 0, 1), glow=I))
    return frames


def floe_sublimate(rng, w, h, n):
    """A floe block fading to vapour (one-shot): the pale ice block (1 m in the 128 px frame)
    thins and loses alpha from the top while white vapour wisps rise and spread."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nz = fft_noise(rng, h, w, 6, 48, 0.8)
    soft = fft_noise(rng, h, w, 20, 128, 1.2)          # vapour: long wavelengths only (fine noise read as dark smoke)
    x0, x1, y0, y1 = PAD + 16, w - PAD - 16, h / 2, h - PAD - 4
    frames = []
    for i in range(n):
        t = (i + 1) / n
        top = y0 + (y1 - y0) * t ** 1.4 + 3 * nz
        block = ((xx >= x0) & (xx < x1) & (yy >= top) & (yy < y1)).astype(np.float32) * (1 - t ** 3)
        rise = np.roll(soft, -int(10 + 30 * t), axis=0)
        vap = np.clip(0.75 + 0.35 * rise, 0, 1) * np.exp(-((xx - w / 2) / (22 + 30 * t)) ** 2)
        vap *= np.clip((top - yy) / 40, 0, 1) * np.clip(1 - (top - yy) / (90 * (0.4 + t)), 0, 1) * math.sin(math.pi * min(1.0, t * 1.3))
        ice = _ramp(np.clip(0.5 + 0.2 * nz, 0, 1), [(0.0, C((196, 210, 222))), (1.0, C((240, 246, 250)))])
        col = ice * block[..., None] + C((244, 246, 250)) * (1 - block[..., None])
        a = np.maximum(block, np.clip(vap * 1.9, 0, 0.9)) * _inside(h, w)    # the fades multiply: boost the vapour (only) so it reads white
        frames.append(_frame(col, a))
    return frames


def _inside(h, w):
    """1 inside the padded area, 0 in the 8 px margin."""
    m = np.zeros((h, w), np.float32)
    m[PAD:h - PAD, PAD:w - PAD] = 1
    return m


def _seg_dist(xx, yy, p0, p1):
    d = p1 - p0
    L2 = max(float(d @ d), 1e-6)
    t = np.clip(((xx - p0[0]) * d[0] + (yy - p0[1]) * d[1]) / L2, 0, 1)
    return np.hypot(xx - (p0[0] + t * d[0]), yy - (p0[1] + t * d[1]))


GEN = {"thruster": thruster, "dust": dust, "dig_sparks": dig_sparks, "escape_band": escape_band,
       "heat_shimmer": heat_shimmer, "beam_ray": beam_ray, "lance_bolt": lance_bolt,
       "survey_scan": survey_scan, "builder_ghost": builder_ghost, "warden_bolt": warden_bolt,
       "lightning": lightning, "diamond_rain": diamond_rain, "methane_hail": methane_hail,
       "wind_streaks": wind_streaks, "crush_pulse": crush_pulse, "skip_spool": skip_spool,
       "skip_streak": skip_streak, "floe_sublimate": floe_sublimate}


def generate(entry, ctx):
    name = entry["key"].split("/")[1]
    w, h = entry["size"]
    n = sum(int(c["length"]) for c in entry["animations"]["clips"])
    frames = GEN[name](np.random.default_rng(int(entry.get("seed", 1))), w, h, n)
    if ctx["preview"]:
        frames = [{k: v[::4, ::4].copy() for k, v in f.items()} for f in frames]
    return {"frames": frames}
