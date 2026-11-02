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
    build_ring(scene)                                        # B-059, after batch 1 (unchanged)
    build_ringmite(scene)
    scene.frame_start, scene.frame_end = 1, RINGMITE_END
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


# ---------------------------------------------------------------- B-059 ring mining (Saturn)
# Same top camera and 64 px/m as the asteroids (D-018). Ice: bright, rounded, faintly blue;
# rock: grey-brown silicate, angular.
RING = {
    "ring_ice_01": (0.6, "round", "ice"), "ring_ice_02": (1.0, "lumpy", "ice"),
    "ring_ice_03": (1.6, "slab", "ice"), "ring_ice_04": (2.4, "binary", "ice"),
    "ring_rock_01": (0.5, "angular", "rock"), "ring_rock_02": (0.9, "round", "rock"),
    "ring_rock_03": (1.4, "angular", "rock"), "ring_rock_04": (2.0, "elongated", "rock"),
}


def _ice_chunk(coll, M, name, seed, size, loc=(0, 0, 0)):
    """v2 (LEAD cycle 170): a hard faceted ice chunk, not a soft puff: low-subdivision
    displaced icosphere, flat-shaded (cleavage planes), glossy white grading to a cool blue,
    weak bump (the strong noise bump read as fuzz)."""
    return rock(coll, name, M["ice"], seed, size, subdiv=2, strength=0.45 * max(size), scale=1.0 * max(size), flat=True, loc=loc)


def _ice_cracks(coll, M, seed, r, top):
    """Two or three dark cracks across the top face (seen from the top camera)."""
    import math
    import random
    from build_icons import box
    rnd = random.Random(seed)
    for k in range(rnd.choice((2, 3))):
        a = rnd.uniform(0, math.pi)
        ln = r * rnd.uniform(0.45, 0.75)                                 # stays inside the silhouette
        ox, oy = rnd.uniform(-0.15, 0.15) * r, rnd.uniform(-0.15, 0.15) * r
        box(coll, f"crack{k}", M["crack"], (ln, 0.012 + 0.01 * r, 0.01), (ox, oy, top), rot=(0, 0, a), bevel=0.002)


def build_ring(scene):
    M = {"ice": mat("ring_ice", (246, 250, 255), (150, 190, 228), 0.0, 0.08, 1.4, 0.06),
         "rock": mat("ring_rock", (134, 118, 102), (96, 84, 74), 0.0, 0.85, 1.6, 0.55),
         "crack": mat("ring_ice_crack", (60, 84, 112))}
    for k, (name, (dia, shape, cls)) in enumerate(RING.items()):
        coll = bpy.data.collections.new(name)
        scene.collection.children.link(coll)
        r, seed = dia / 2, 101 + k
        if cls == "ice":
            if shape == "binary":
                _ice_chunk(coll, M, "lobe_a", seed, (r * 0.6, r * 0.52, r * 0.5), loc=(-r * 0.4, 0, 0))
                _ice_chunk(coll, M, "lobe_b", seed + 50, (r * 0.45, r * 0.42, r * 0.4), loc=(r * 0.5, r * 0.1, 0))
                _ice_cracks(coll, M, seed, r * 0.55, r * 0.62)
            else:
                sz = {"round": (r, r * 0.9, r * 0.8), "lumpy": (r * 0.95, r * 0.8, r * 0.7),
                      "slab": (r, r * 0.7, r * 0.32)}[shape]
                _ice_chunk(coll, M, "body", seed, sz)
                _ice_cracks(coll, M, seed, r, sz[2] * 1.15)                 # a little high: displacement must not bury them (top camera)
            continue
        if shape == "round":
            rock(coll, "body", M[cls], seed, (r, r * 0.9, r * 0.85), subdiv=4, strength=0.18 * r, scale=0.7 * r)
        elif shape == "lumpy":
            rock(coll, "body", M[cls], seed, (r * 0.95, r * 0.85, r * 0.75), subdiv=4, strength=0.3 * r, scale=0.45 * r)
        elif shape == "slab":
            rock(coll, "body", M[cls], seed, (r, r * 0.7, r * 0.3), subdiv=3, strength=0.2 * r, scale=0.8 * r, flat=True)
        elif shape == "binary":
            rock(coll, "lobe_a", M[cls], seed, (r * 0.6, r * 0.52, r * 0.5), subdiv=4, strength=0.2 * r, scale=0.6 * r, loc=(-r * 0.4, 0, 0))
            rock(coll, "lobe_b", M[cls], seed + 50, (r * 0.45, r * 0.42, r * 0.4), subdiv=4, strength=0.2 * r, scale=0.6 * r, loc=(r * 0.5, r * 0.1, 0))
        elif shape == "angular":
            rock(coll, "body", M[cls], seed, (r * 0.95, r * 0.75, r * 0.7), subdiv=2, strength=0.3 * r, scale=1.2 * r, flat=True)
        else:  # elongated
            rock(coll, "body", M[cls], seed, (r, r * 0.5, r * 0.45), subdiv=3, strength=0.25 * r, scale=0.8 * r, flat=True)


# Ringmite (~0.6 m swarm unit, top view, faces +x): clips idle 4, chew 4, hurt 2, death 4.
RINGMITE_CLIPS = {"idle": (1, 4), "chew": (7, 4), "hurt": (13, 2), "death": (17, 4)}
RINGMITE_END = 20


def _key(ob, f, rot=True, loc=False, scale=False):
    if rot:
        ob.keyframe_insert("rotation_euler", frame=f)
    if loc:
        ob.keyframe_insert("location", frame=f)
    if scale:
        ob.keyframe_insert("scale", frame=f)


def build_ringmite(scene):
    import math
    from build_pilgrim import flat_material
    from build_surveyor import _constant
    coll = bpy.data.collections.new("ringmite")
    scene.collection.children.link(coll)
    shell = mat("mite_shell", (78, 70, 92), (52, 46, 62), 0.3, 0.4, 3.0, 0.4)
    leg_m = flat_material("mite_leg", (40, 36, 46), rough=0.5)
    jaw_m = flat_material("mite_jaw", (150, 140, 120), metallic=0.6, rough=0.3)
    eye_m = flat_material("mite_eye", (120, 30, 20), emit=(255, 80, 50), strength=1.6)
    frost = flat_material("mite_frost", (214, 226, 236), rough=0.8)
    root = bpy.data.objects.new("ringmite_root", None)
    coll.objects.link(root)

    def add(prim, name, m, loc, scale, rot=(0, 0, 0)):
        prim(location=loc)
        ob = bpy.context.active_object
        for co in list(ob.users_collection):
            co.objects.unlink(ob)
        coll.objects.link(ob)
        ob.name, ob.scale, ob.rotation_euler = f"ringmite_{name}", scale, rot
        ob.data.materials.append(m)
        ob.parent = root
        return ob

    sph = lambda location: bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=10, radius=1.0, location=location)  # noqa: E731
    cube = lambda location: bpy.ops.mesh.primitive_cube_add(size=2.0, location=location)  # noqa: E731
    add(sph, "body", shell, (0, 0, 0.08), (0.22, 0.15, 0.08))
    add(sph, "head", shell, (0.2, 0, 0.07), (0.08, 0.09, 0.06))
    for k in range(5):
        add(sph, f"frost{k}", frost, (-0.12 + 0.06 * k, 0.04 * ((-1) ** k), 0.15), (0.02, 0.02, 0.008))
    for s in (-1, 1):
        add(sph, f"eye{s}", eye_m, (0.25, 0.05 * s, 0.1), (0.014, 0.014, 0.012))
    jaws = []
    for s in (-1, 1):
        j = add(cube, f"jaw{s}", jaw_m, (0.3, 0.035 * s, 0.06), (0.06, 0.012, 0.01))
        jaws.append((j, s))
    legs = []
    for k, x in enumerate((0.08, 0.0, -0.08)):
        for s in (-1, 1):
            lg = add(cube, f"leg{k}{s}", leg_m, (x, 0.2 * s, 0.03), (0.012, 0.08, 0.01), rot=(0, 0, 0.3 * s * (1 - k)))
            legs.append((lg, s, k))
    for name, (start, n) in RINGMITE_CLIPS.items():
        for i in range(n):
            f = start + i
            t = i / n
            jaw_open, sway, scl, rz = 0.15, 0.0, 1.0, 0.0
            if name == "idle":
                sway = 0.15 * math.sin(2 * math.pi * t)
            elif name == "chew":
                jaw_open = 0.55 * (0.5 + 0.5 * math.cos(2 * math.pi * t * 2))       # two bites per loop
            elif name == "hurt":
                scl, rz = 0.9, 0.25 * (1 - i)
            elif name == "death":
                k = (i + 1) / n
                scl, rz, jaw_open = 1.0 - 0.3 * k, 0.8 * k, 0.6
            for j, s in jaws:
                j.rotation_euler = (0, 0, -s * jaw_open)
                _key(j, f)
            for lg, s, k in legs:
                ph = sway * (1 if (k + (s > 0)) % 2 else -1)
                lg.rotation_euler = (0, 0, 0.3 * s * (1 - k) + ph * (0 if name == "death" else 1) + (0.4 * s if name == "death" else 0))
                _key(lg, f)
            root.rotation_euler = (0, 0, rz)
            root.scale = (scl, scl, scl)
            _key(root, f, scale=True)
    for ob in [root] + [j for j, _ in jaws] + [lg for lg, _, _ in legs]:
        if ob.animation_data and ob.animation_data.action:
            _constant(ob.animation_data.action)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
