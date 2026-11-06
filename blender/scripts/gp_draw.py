"""Grease Pencil drawing helpers for v3 cartoon assets (contract §11, Bible §9 v4).

Builders draw in metres in the XZ plane (x right, z up; the camera looks along +Y), one GP
drawing per frame number. render.py --sheet rasterizes the strokes (gp_raster.py), so what
is written here is exactly what reaches the sheet:

  - a stroke's material decides fill and/or ink (`mat(gp, name, fill=..., ink=True)`),
  - a point's radius is half the ink width in metres (OUTER = 5 px wide, INNER = 2.25 px at
    PPU 64); the ±20 % jitter is applied at render time, never here,
  - shapes are a little lumpy and lines bow (no perfect geometry, Bible §9.1).

Colours are sRGB hex from the planet palette (PALETTES); each material stores its hex in a
custom property "srgb" so the rasterizer never round-trips through linear colour.
"""
import math
import random

import bpy

from meridian.v3 import (INK, PALETTE_ORDER, PALETTES, PPU, hex_rgb,  # noqa: F401,E402
                         palette_with_shadows, rgb_hex, shadow_of)

OUTER = 2.5 / PPU          # radius (half width) of the outer silhouette: 5 px
INNER = 1.1 / PPU          # interior lines: 2.2 px


def _lin(c8):
    c = c8 / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _set_colour(style, prop, h, alpha=1.0):
    rgb = hex_rgb(h)
    sub = style.bl_rna.properties[prop].subtype
    vals = [v / 255.0 for v in rgb] if sub == "COLOR_GAMMA" else [_lin(v) for v in rgb]
    setattr(style, prop, (*vals, alpha))


# ---------------------------------------------------------------- scene / objects

def new_scene(path_hint=""):
    """Empty the factory scene (cube, light, camera)."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    scene = bpy.context.scene
    scene.render.fps = 12          # on twos: 12 drawings per second (contract §11.2)
    scene.frame_start = 1
    return scene


def gp_object(name, collection):
    gp = bpy.data.grease_pencils.new(name)
    ob = bpy.data.objects.new(name, gp)
    collection.objects.link(ob)
    return ob, gp


def collection(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def mat(gp, name, fill=None, ink=True, ink_hex=INK, behind=False):
    """Material slot on gp: fill colour hex (or None) + ink stroke. Returns its index.
    behind=True: the ink is drawn under the fill at twice the radius (gp_raster), for parts too
    small for a centred line to leave any colour (beaks, feet, thin feathers)."""
    for i, m in enumerate(gp.materials):
        if m and m.name == name:
            return i
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        bpy.data.materials.create_gpencil_data(m)
        st = m.grease_pencil
        st.show_stroke = bool(ink)
        st.show_fill = fill is not None
        _set_colour(st, "color", ink_hex)
        if fill is not None:
            _set_colour(st, "fill_color", fill)
        m["srgb_ink"] = ink_hex
        if fill is not None:
            m["srgb_fill"] = fill
        if behind:
            m["ink_behind"] = True
    gp.materials.append(m)
    return len(gp.materials) - 1


def drawing(layer, frame):
    fr = layer.frames.new(frame)
    return fr.drawing


class Xf:
    """A drawing seen through a 2D transform: stroke(Xf(d, f), pts) draws f(pts) into d. Lets
    helpers such as pie_eye draw rig parts posed by a bone chain (B-112 preview loops)."""
    def __init__(self, d, f):
        self.d, self.f = d, f


def stroke(d, pts, mat_index, radius=OUTER, cyclic=False, radii=None):
    """pts: [(x, z), ...] in metres. radii: optional per-point radius list."""
    while isinstance(d, Xf):
        pts, d = d.f(list(pts)), d.d
    d.add_strokes([len(pts)])
    s = d.strokes[len(d.strokes) - 1]
    s.material_index = mat_index
    s.cyclic = cyclic
    for i, (p, (x, z)) in enumerate(zip(s.points, pts)):
        p.position = (x, 0.0, z)
        p.radius = radii[i] if radii else radius
        p.opacity = 1.0
    return s


# ---------------------------------------------------------------- shapes (metres, XZ)

def lumpy_ellipse(cx, cz, rx, rz, n=48, lump=0.035, seed=0, rot=0.0):
    """A hand-drawn oval: radius wobbles by ±lump (fraction) with 3 slow harmonics."""
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6.283) for _ in range(3)]
    amp = [lump, lump * 0.6, lump * 0.35]
    out = []
    cr, sr = math.cos(rot), math.sin(rot)
    for i in range(n):
        t = 6.283185 * i / n
        k = 1.0 + sum(a * math.sin((j + 2) * t + p) for j, (a, p) in enumerate(zip(amp, ph)))
        x, z = rx * k * math.cos(t), rz * k * math.sin(t)
        out.append((cx + x * cr - z * sr, cz + x * sr + z * cr))
    return out


def bowed_line(a, b, bow=0.04, n=12):
    """A straight line that bows slightly (bow = fraction of its length, sideways)."""
    (x0, z0), (x1, z1) = a, b
    dx, dz = x1 - x0, z1 - z0
    L = math.hypot(dx, dz) or 1.0
    nx, nz = -dz / L, dx / L
    return [(x0 + dx * t + nx * bow * L * math.sin(math.pi * t),
             z0 + dz * t + nz * bow * L * math.sin(math.pi * t)) for t in (i / (n - 1) for i in range(n))]


def bezier(p0, p1, p2, p3=None, n=16):
    """Quadratic (3 points) or cubic (4 points) curve as a polyline."""
    out = []
    for i in range(n):
        t = i / (n - 1)
        u = 1 - t
        if p3 is None:
            x = u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0]
            z = u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]
        else:
            x = u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0]
            z = u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]
        out.append((x, z))
    return out


def hose_outline(center, width, cap_n=6):
    """A rubber-hose limb: the closed outline of a tube of `width` around the centre polyline,
    with round ends. Draw it as one cyclic fill+ink stroke so the ink runs down both sides."""
    if len(center) < 2:
        raise ValueError("hose needs >= 2 points")
    r = width / 2
    left, right = [], []
    for i, (x, z) in enumerate(center):
        a = center[max(i - 1, 0)]
        b = center[min(i + 1, len(center) - 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz) or 1.0
        nx, nz = -dz / L, dx / L
        left.append((x + nx * r, z + nz * r))
        right.append((x - nx * r, z - nz * r))

    def cap(c, d_from, sign):
        (x, z), (px, pz) = c, d_from
        ang = math.atan2(z - pz, x - px)
        return [(x + r * math.cos(ang + sign * (math.pi / 2 - math.pi * k / cap_n)),
                 z + r * math.sin(ang + sign * (math.pi / 2 - math.pi * k / cap_n))) for k in range(1, cap_n)]
    end_cap = cap(center[-1], center[-2], 1)
    start_cap = cap(center[0], center[1], 1)
    return left + end_cap + right[::-1] + start_cap


def pie_eye(d, cx, cz, rx, rz, m_black, m_white, look=(0.0, 0.0), wedge_deg=50, wedge_dir=40, seed=0,
            m_lid=None, closed=0.0):
    """Era eye: white oval, black pupil with a pie wedge cut out (Bible §9.1 characters).
    look: pupil offset as a fraction of the eye radii. closed: 0 open .. 1 shut (blink)."""
    if closed >= 0.95:            # a blink: one curved lid line
        stroke(d, bezier((cx - rx, cz), (cx, cz - rz * 0.5), (cx + rx, cz)),
               m_lid if m_lid is not None else m_black, INNER)
        return
    zr = rz * (1.0 - closed)
    stroke(d, lumpy_ellipse(cx, cz, rx, zr, n=28, lump=0.03, seed=seed), m_white, INNER, cyclic=True)
    px, pz = cx + look[0] * rx * 0.45, cz + look[1] * zr * 0.4
    prx, prz = rx * 0.55, zr * 0.62
    a0, a1 = math.radians(wedge_dir - wedge_deg / 2), math.radians(wedge_dir + wedge_deg / 2)
    pts = [(px, pz)]
    n = 22
    for k in range(n + 1):        # the pupil minus its wedge: arc from a1 round to a0 + 360
        t = a1 + (a0 + 2 * math.pi - a1) * k / n
        pts.append((px + prx * math.cos(t), pz + prz * math.sin(t)))
    stroke(d, pts, m_black, 0.0001, cyclic=True)


def mark_clips(scene, clips):
    """Timeline markers name each clip's first drawing (render.py --sheet reads them)."""
    scene.timeline_markers.clear()
    f = 1
    for name, n in clips:
        scene.timeline_markers.new(name, frame=f)
        f += n
    scene.frame_end = f - 1
