"""Builds blender/sources/props/asteroids.blend: asteroids batch (B-017), seen top-down.

Six collections `asteroid_01..06`, 1 to 6 m across, each with a distinct silhouette (round,
elongated, contact binary, angular, flattened, large lumpy) and material class (rocky S-type,
dark carbonaceous C-type, metallic M-type). Centred on the origin for a centre pivot. Rendered
with the `top` camera at 64 px/m, half of PPU 128 (contract §4 caps props at 512 px; 6 m plus
displacement at PPU 128 would be ~960). Deterministic:

  blender --background --factory-startup --python blender/scripts/build_asteroids.py
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_icons import mat, rock  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "asteroids.blend")

# name: (diameter m, shape, material) — shape -> extra lobes or flattening
ASTEROIDS = {
    "asteroid_01": (1.0, "round", "s"),
    "asteroid_02": (1.8, "elongated", "c"),
    "asteroid_03": (2.6, "binary", "s"),
    "asteroid_04": (3.5, "angular", "m"),
    "asteroid_05": (4.6, "flat", "c"),
    "asteroid_06": (6.0, "lumpy", "s"),
}


def materials():
    return {
        "s": mat("s_type", (140, 124, 104), (104, 92, 80), 0.0, 0.8, 1.2, 0.5),
        "c": mat("c_type", (66, 64, 62), (46, 44, 44), 0.0, 0.85, 1.4, 0.5),
        "m": mat("m_type", (150, 146, 140), (98, 94, 90), 0.7, 0.4, 1.6, 0.5),
    }


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    M = materials()
    for k, (name, (dia, shape, cls)) in enumerate(ASTEROIDS.items()):
        coll = bpy.data.collections.new(name)
        scene.collection.children.link(coll)
        r = dia / 2
        if shape == "round":
            rock(coll, "body", M[cls], k + 1, (r, r * 0.92, r * 0.85), subdiv=4, strength=0.25 * r, scale=0.6 * r)
        elif shape == "elongated":
            rock(coll, "body", M[cls], k + 1, (r, r * 0.48, r * 0.42), subdiv=4, strength=0.22 * r, scale=0.7 * r)
        elif shape == "binary":
            rock(coll, "lobe_a", M[cls], k + 1, (r * 0.58, r * 0.52, r * 0.5), subdiv=4, strength=0.2 * r, scale=0.6 * r, loc=(-r * 0.42, 0, 0))
            rock(coll, "lobe_b", M[cls], k + 11, (r * 0.46, r * 0.42, r * 0.4), subdiv=4, strength=0.2 * r, scale=0.6 * r, loc=(r * 0.5, r * 0.08, 0))
        elif shape == "angular":
            rock(coll, "body", M[cls], k + 1, (r * 0.95, r * 0.75, r * 0.7), subdiv=2, strength=0.3 * r, scale=1.2 * r, flat=True)
        elif shape == "flat":
            rock(coll, "body", M[cls], k + 1, (r * 0.95, r * 0.8, r * 0.35), subdiv=4, strength=0.25 * r, scale=0.5 * r)
        else:  # lumpy
            rock(coll, "body", M[cls], k + 1, (r * 0.92, r * 0.82, r * 0.7), subdiv=4, strength=0.32 * r, scale=0.45 * r)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
