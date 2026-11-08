"""Lock-free: the Grand rigs' parts at 1x (stroke bounds + a 16 px margin, as render.py's packer sees them) through
v3.shelf_pack, so no rig fails its slot the way the Vortex Whale did (D-153). Draws nothing, renders nothing."""
import importlib
import sys
import numpy as np
sys.path.insert(0, r"C:\dev\universegame\blender\scripts")
from meridian import fakegp, v3
for modname in ("build_vortex_whale_v3", "build_polar_hydra_v3", "build_diamondback_v3", "build_umbral_leviathan_v3"):
    W = importlib.import_module(modname)
    sizes = []
    for name, fn in W.PARTS.items():
        gp = fakegp.FakeGP(); M = W.mats(gp); d = fakegp.FakeDrawing()
        fn(d, M)
        allp = np.vstack([s["xz"] for s in fakegp.strokes_of(d, gp)])
        w = (max(allp[:, 0].max(), 0) - min(allp[:, 0].min(), 0)) * 64 + 16
        h = (max(allp[:, 1].max(), 0) - min(allp[:, 1].min(), 0)) * 64 + 16
        sizes.append((name, int(w), int(h)))
    area = sum(w * h for _n, w, h in sizes) / 2048 ** 2
    try:
        v3.shelf_pack([(w, h) for _n, w, h in sizes])
        fit = "FITS"
    except ValueError as e:
        fit = f"DOES NOT FIT ({e})"
    big = max(sizes, key=lambda s: s[1] * s[2])
    print(f"{modname}: {len(sizes)} parts, {area:.2f} of 2048^2, largest {big[0]} {big[1]}x{big[2]}: {fit}")
