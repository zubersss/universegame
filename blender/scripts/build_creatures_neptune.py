"""Builds blender/sources/creatures/neptune.blend: Neptune creatures (B-065, Bible §7.9).

Same conventions as build_creatures_jupiter.py (rigid parts on bones, standard clip frames).
They must read against the B-063 indigo decks: pale or rim-lit silhouettes, emissive accents.

  * windrider (~2.2 m, 320 px): sail-finned floater. Pale blue-grey body, a tall translucent
    sail fin (cream-white with blue veins, faint glow) that cants with the wind.
  * shadow_shoal (~0.5 m swarm unit, 128 px): dark, fast, fish-like; a faint cyan rim light
    (emissive edge strips) and eyes so it reads on indigo.
  * pressure_phantom (~1.8 m, 320 px, Deck 3): translucent ghostly drifter, a glowing violet
    core and trailing veils.
  * anchor_worm (~3 m, 320 px): holds floes against the wind. Segmented grey-violet body with a
    hooked anchor head. Standard clips are its "free" motion; extra clip "anchored" (frames
    47-52): coiled tight, hook set, body braced and shivering in the wind.

  blender --background --factory-startup --python blender/scripts/build_creatures_neptune.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_creatures_earth import CLIP_LEN, set_pose  # noqa: E402
from build_creatures_jupiter import _frames, finish, key_all, make_rig, new_coll, part  # noqa: E402
from build_creatures_saturn import _translucent  # noqa: E402
from build_pilgrim import flat_material, paint_material  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "creatures", "neptune.blend")
ANCHOR_START, ANCHOR_LEN = 47, 6


# ---------------------------------------------------------------- windrider

def build_windrider(scene):
    sp = "windrider"
    coll = new_coll(scene, sp)
    rig = make_rig(sp, coll, [
        ("root", (-0.3, 0, 0), (0.3, 0, 0), None),
        ("sail", (0.0, 0, 0.15), (0.0, 0, 0.9), "root"),
        ("tail", (-0.6, 0, 0), (-1.1, 0, -0.05), "root"),
        ("fin", (0.1, 0, -0.15), (0.2, 0, -0.45), "root"),
    ])
    body = paint_material(f"{sp}_body", (178, 196, 222), (130, 150, 186), seams=False, scratches=False)
    belly = flat_material(f"{sp}_belly", (220, 228, 240), rough=0.6)
    sail = _translucent(f"{sp}_sail", (236, 240, 250), 0.7, (170, 200, 255), 0.5)
    vein = flat_material(f"{sp}_vein", (90, 120, 200), emit=(140, 180, 255), strength=1.4)
    eye = flat_material(f"{sp}_eye", (30, 40, 70), emit=(160, 200, 255), strength=1.2)
    part(coll, rig, "root", "body", body, (0.0, 0, 0.0), (0.62, 0.2, 0.18))
    part(coll, rig, "root", "belly", belly, (0.0, 0, -0.07), (0.56, 0.17, 0.1))
    part(coll, rig, "root", "eye", eye, (0.48, -0.14, 0.05), (0.03, 0.02, 0.03), segs=10)
    part(coll, rig, "sail", "sail", sail, (-0.05, 0, 0.55), (0.42, 0.015, 0.42), rot=(0, 0.2, 0))
    for k in range(4):
        part(coll, rig, "sail", f"vein{k}", vein, (-0.25 + 0.14 * k, -0.02, 0.5), (0.012, 0.006, 0.34), rot=(0, 0.25 - 0.1 * k, 0))
    part(coll, rig, "tail", "tail", body, (-0.85, 0, -0.03), (0.3, 0.07, 0.07))
    part(coll, rig, "tail", "fluke", sail, (-1.15, 0, -0.04), (0.1, 0.012, 0.14))
    part(coll, rig, "fin", "fin", sail, (0.15, 0, -0.32), (0.12, 0.012, 0.16))
    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        s2 = math.sin(2 * math.pi * t)
        pitch, z, sail_a, tail = 0.0, 0.0, -8.0, 0.0
        if name == "idle":
            z, sail_a, tail = 0.04 * s2, -8 + 4 * s2, 6 * s2
        elif name == "walk":
            sail_a, pitch, tail = -22.0, -5.0, 12 * math.sin(4 * math.pi * t)   # sail cants back, rides the wind
        elif name == "attack":
            k = [0.0, 0.5, 1.0, 1.0, 0.6, 0.2][i]
            pitch, sail_a = -20 * k, -8 + 20 * k
        elif name == "hurt":
            k = [1.0, 0.5][i]
            pitch, sail_a = 12 * k, 15 * k
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            pitch, z, sail_a, tail = 70 * k, -0.35 * k, 40 * k, -20 * k
        rig.rotation_euler = (0.0, math.radians(pitch), 0.0)
        rig.location = (0.0, 0.0, z)
        set_pose(rig, "sail", sail_a)
        set_pose(rig, "tail", tail)
        set_pose(rig, "fin", 0.5 * tail)
        key_all(rig, f)
    finish([rig])


# ---------------------------------------------------------------- shadow shoal

def build_shadow_shoal(scene):
    sp = "shadow_shoal"
    coll = new_coll(scene, sp)
    rig = make_rig(sp, coll, [
        ("root", (-0.05, 0, 0), (0.08, 0, 0), None),
        ("tail", (-0.08, 0, 0), (-0.2, 0, 0), "root"),
    ])
    dark = flat_material(f"{sp}_dark", (22, 24, 40), rough=0.4)
    rim = flat_material(f"{sp}_rim", (60, 120, 160), emit=(120, 220, 255), strength=1.6)
    eye = flat_material(f"{sp}_eye", (120, 200, 230), emit=(190, 240, 255), strength=2.4)
    part(coll, rig, "root", "body", dark, (0.02, 0, 0), (0.11, 0.03, 0.045))
    part(coll, rig, "root", "rim_top", rim, (0.02, -0.012, 0.038), (0.09, 0.008, 0.006))
    part(coll, rig, "root", "rim_bot", rim, (0.02, -0.012, -0.036), (0.08, 0.008, 0.005))
    part(coll, rig, "root", "dorsal", dark, (0.0, 0, 0.055), (0.035, 0.006, 0.025), kind="cone", segs=4)
    part(coll, rig, "root", "eye", eye, (0.1, -0.022, 0.01), (0.009, 0.006, 0.009), segs=8)
    part(coll, rig, "tail", "tail", dark, (-0.15, 0, 0), (0.05, 0.006, 0.04))
    part(coll, rig, "tail", "tail_rim", rim, (-0.17, -0.008, 0), (0.025, 0.004, 0.035))
    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        s2 = math.sin(2 * math.pi * t * 2)
        pitch, z, tail = 0.0, 0.0, 20 * s2
        if name == "idle":
            z, tail = 0.008 * math.sin(2 * math.pi * t), 12 * s2
        elif name == "walk":
            pitch, tail = -4.0, 30 * s2
        elif name == "attack":
            k = [0.0, 0.5, 1.0, 1.0, 0.6, 0.2][i]
            pitch, tail = -18 * k, 35 * s2                                # lunges
        elif name == "hurt":
            pitch, tail = 30 * [1.0, 0.5][i], 0.0
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            pitch, z, tail = 160 * k, -0.06 * k, 0.0                    # belly-up
        rig.rotation_euler = (0.0, math.radians(pitch), 0.0)
        rig.location = (0.0, 0.0, z)
        set_pose(rig, "tail", tail)
        key_all(rig, f)
    finish([rig])


# ---------------------------------------------------------------- pressure phantom

def build_pressure_phantom(scene):
    sp = "pressure_phantom"
    coll = new_coll(scene, sp)
    bones = [("root", (0, 0, 0.1), (0, 0, 0.5), None)]
    for k in range(4):
        x = -0.3 + 0.2 * k
        bones.append((f"vA{k}", (x, 0, -0.2), (x - 0.15, 0, -0.65), "root"))
        bones.append((f"vB{k}", (x - 0.15, 0, -0.65), (x - 0.35, 0, -1.05), f"vA{k}"))
    rig = make_rig(sp, coll, bones)
    body = _translucent(f"{sp}_body", (190, 196, 236), 0.4, (150, 150, 255), 0.5)
    core = flat_material(f"{sp}_core", (150, 110, 230), emit=(200, 160, 255), strength=2.6)
    veil = _translucent(f"{sp}_veil", (200, 206, 240), 0.35, (160, 160, 255), 0.4)
    eye = flat_material(f"{sp}_eye", (200, 210, 255), emit=(230, 236, 255), strength=2.0)
    hood = part(coll, rig, "root", "hood", body, (0, 0, 0.1), (0.5, 0.42, 0.42), segs=32)
    c = part(coll, rig, "root", "core", core, (0, 0, 0.05), (0.13, 0.12, 0.13), segs=16)
    for k, s in enumerate((-1, 1)):
        part(coll, rig, "root", f"eye{k}", eye, (0.36, -0.15, 0.2 + 0.04 * s), (0.03, 0.015, 0.02), segs=8)
    for k in range(4):
        x = -0.3 + 0.2 * k
        part(coll, rig, f"vA{k}", f"va{k}", veil, (x - 0.07, 0, -0.42), (0.08, 0.1, 0.25), segs=12)
        part(coll, rig, f"vB{k}", f"vb{k}", veil, (x - 0.25, 0, -0.85), (0.05, 0.08, 0.23), segs=12)
    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        s2 = math.sin(2 * math.pi * t)
        z, sw, lag, pitch, glow = 0.0, 8 * s2, 0.0, 0.0, 1.0
        if name == "idle":
            z, glow = 0.05 * s2, 1.0 + 0.15 * s2
        elif name == "walk":
            lag, pitch = 20.0, -10.0
        elif name == "attack":
            k = [0.0, 0.5, 1.0, 1.0, 0.6, 0.2][i]
            lag, glow, pitch = -25 * k, 1.0 + 0.5 * k, -12 * k            # veils reach forward, core flares
        elif name == "hurt":
            sw, glow = -18 * [1.0, 0.5][i], 0.7
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            glow, z, lag = 1.0 - 0.85 * k, -0.2 * k, 30 * k
        rig.rotation_euler = (0.0, math.radians(pitch), 0.0)
        rig.location = (0.0, 0.0, z)
        for k in range(4):
            set_pose(rig, f"vA{k}", lag + sw * math.cos(0.8 * k))
            set_pose(rig, f"vB{k}", 0.6 * lag + 1.4 * sw * math.cos(0.8 * k + 1.0))
        c.scale = (0.13 * glow, 0.12 * glow, 0.13 * glow)
        key_all(rig, f, extra=[(c, "scale")])
    finish([rig, c])


# ---------------------------------------------------------------- anchor worm

def build_anchor_worm(scene):
    sp = "anchor_worm"
    coll = new_coll(scene, sp)
    n, seg = 9, 0.32
    bones = [("root", (1.5, 0, 0), (1.2, 0, 0), None)]
    for k in range(n):
        x0 = 1.5 - k * seg
        bones.append((f"s{k}", (x0, 0, 0), (x0 - seg, 0, 0), "root" if k == 0 else f"s{k - 1}"))
    rig = make_rig(sp, coll, bones)
    skin = paint_material(f"{sp}_skin", (150, 140, 176), (110, 100, 140), seams=False, scratches=False)
    ring = flat_material(f"{sp}_ring", (96, 86, 120), rough=0.6)
    hook = flat_material(f"{sp}_hook", (60, 56, 70), metallic=0.3, rough=0.4)
    eye = flat_material(f"{sp}_eye", (120, 160, 230), emit=(170, 210, 255), strength=1.4)
    for k in range(n):
        cx = 1.5 - (k + 0.5) * seg
        r = 0.14 * (1 - 0.5 * (k / (n - 1)))
        part(coll, rig, f"s{k}", f"seg{k}", skin, (cx, 0, 0), (seg * 0.6, r, r))
        part(coll, rig, f"s{k}", f"ring{k}", ring, (cx + seg * 0.45, 0, 0), (0.025, r * 1.05, r * 1.05), segs=16)
    part(coll, rig, "s0", "head", skin, (1.55, 0, 0), (0.15, 0.13, 0.13))
    for k, a in enumerate((0.6, -0.6, 0.0)):                         # anchor hooks
        part(coll, rig, "s0", f"hook{k}", hook, (1.7, 0.0, 0.08 * math.sin(a) * 2), (0.12, 0.025, 0.025),
             kind="cone", segs=6, rot=(0, math.pi / 2 - a, 0))
    part(coll, rig, "s0", "eye", eye, (1.6, -0.11, 0.06), (0.022, 0.012, 0.022), segs=8)
    frames = list(_frames()) + [("anchored", i, ANCHOR_START + i) for i in range(ANCHOR_LEN)]
    for name, i, f in frames:
        ln = ANCHOR_LEN if name == "anchored" else CLIP_LEN[name]
        t = i / ln
        ph = 2 * math.pi * t
        amp, coil, pitch, z = 10.0, 0.0, 0.0, 0.0
        if name == "idle":
            amp, z = 7.0, 0.03 * math.sin(ph)
        elif name == "walk":
            amp = 16.0
        elif name == "attack":
            k = [0.0, 0.5, 1.0, 1.0, 0.6, 0.2][i]
            amp, pitch = 8.0, -20 * k                                   # hook strikes down
        elif name == "hurt":
            amp, pitch = 22.0 * [1.0, 0.5][i], 10.0
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            amp, pitch, z = 10 * (1 - k), 60 * k, -0.4 * k
        elif name == "anchored":
            amp, coil, pitch = 2.5, 34.0, 75.0                          # hook set below, body coiled and braced
        rig.rotation_euler = (0.0, math.radians(pitch), 0.0)
        rig.location = (0.0, 0.0, z)
        for k in range(n):
            set_pose(rig, f"s{k}", coil + amp * math.sin(ph - 0.8 * k) * (0.4 + 0.6 * k / n))
        key_all(rig, f)
    finish([rig])


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    build_windrider(scene)
    build_shadow_shoal(scene)
    build_pressure_phantom(scene)
    build_anchor_worm(scene)
    scene.frame_start = 1
    scene.frame_end = ANCHOR_START + ANCHOR_LEN - 1
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
