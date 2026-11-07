"""Lock-free previews of Grease Pencil builders (D-109): run gp_draw-based drawing code against an
in-memory drawing and rasterize it with gp_raster, all in Blender's bundled python without
blender.exe (no lock, ~100-200 MB).

    from meridian import fakegp
    G = fakegp.install()                 # a fake `bpy` + patched gp_draw.mat / drawing helpers
    import build_flora_earth_v3 as F     # builders import gp_draw after install()
    gp = fakegp.FakeGP()
    M = F.mats(gp)                       # materials resolve to the fake table
    d = fakegp.FakeDrawing()
    F.PARTS["head_open"](d, M)           # any (d, M, ...) drawing function
    img, widths = fakegp.render(d, gp, fw=128, fh=128, pivot=(0.5, 0.0))

Paint order = stroke order (one drawing). Colours come from the hex the builder passed to
gp_draw.mat, so the output matches render.py for a single-object drawing.
"""
import sys
import types
import zlib

import numpy as np


class _Pt:
    __slots__ = ("position", "radius", "opacity")

    def __init__(self):
        self.position, self.radius, self.opacity = (0.0, 0.0, 0.0), 0.0, 1.0


class _Stroke:
    def __init__(self, n):
        self.points = [_Pt() for _ in range(n)]
        self.material_index, self.cyclic = 0, False


class FakeDrawing:
    def __init__(self):
        self.strokes = []

    def add_strokes(self, ns):
        for n in ns:
            self.strokes.append(_Stroke(n))


class FakeGP:
    """Stands in for a GreasePencil datablock: a material table."""
    def __init__(self):
        self.materials = []


def install():
    """Make `import bpy` succeed and patch gp_draw so builders run without Blender. Returns gp_draw."""
    if "bpy" not in sys.modules:
        sys.modules["bpy"] = types.ModuleType("bpy")
    import gp_draw as G

    def mat(gp, name, fill=None, ink=True, ink_hex=G.INK, behind=False, fill_alpha=1.0):
        for i, m in enumerate(gp.materials):
            if m["name"] == name:
                return i
        gp.materials.append({"name": name, "fill": fill, "ink": ink_hex if ink else None,
                             "behind": bool(behind), "fill_alpha": float(fill_alpha)})
        return len(gp.materials) - 1
    G.mat = mat
    return G


def _rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


def strokes_of(d, gp, xf=None):
    """FakeDrawing -> the stroke dicts gp_raster.render_frame expects (same as gp_raster.collect)."""
    out = []
    for si, s in enumerate(d.strokes):
        m = gp.materials[s.material_index]
        xz = np.array([(p.position[0], p.position[2]) for p in s.points], np.float64)
        if xf is not None:
            xz = np.array(xf([tuple(q) for q in xz]), np.float64)
        out.append({"xz": xz, "radius": np.array([p.radius for p in s.points], np.float32),
                    "cyclic": bool(s.cyclic), "fill": _rgb(m["fill"]) if m["fill"] else None,
                    "ink": _rgb(m["ink"]) if m["ink"] else None, "behind": m["behind"],
                    "fill_alpha": m["fill_alpha"], "id": zlib.crc32(f"fake|{si}".encode()) & 0xFFFFFF})
    return out


def render(d, gp, fw, fh, pivot=(0.5, 0.0), ppu=64, ss=2, seed=1):
    import gp_raster as GR
    return GR.render_frame(strokes_of(d, gp), fw, fh, ppu, pivot, ss=ss, seed=seed)
