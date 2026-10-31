"""Builds blender/sources/ships/waystation.blend: orbital Waystations (B-038, Bible §3), seen
top-down on the space map (camera "top": image right = +X, up = +Y; the station lies in the XY
plane with +Z toward the camera). Same space scale as the Pilgrim (PPU 36), so a ~20 m station
fills the 768 px large-ship frame. Halcyon Freight industrial look: worn white hull, Halcyon
orange band, hazard markings on the docking arms, lit windows and guide lights (emission).

  waystation_earth: the start station. Hub + large habitat ring with windows + 4 spokes,
                    two docking arms (collars with green/red guide lights), solar arrays,
                    radiator fins.
  waystation_mars:  smaller and rust-dusted, one docking arm, cargo-pod clusters, more
                    radiators: the frontier outpost.

  blender --background --factory-startup --python blender/scripts/build_waystation.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_pilgrim import box, cyl, flat_material, paint_material, sphere  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "ships", "waystation.blend")


def mats(dust):
    return {
        "hull": paint_material("ws_hull", (214, 216, 212), dust),
        "dark": paint_material("ws_dark", (58, 60, 66), (30, 30, 32), seams=False),
        "band": paint_material("ws_band", (230, 120, 40), dust, seams=False),
        "hazard": paint_material("ws_hazard", (222, 176, 40), (60, 50, 40), hazard=True),
        "solar": flat_material("ws_solar", (28, 46, 86), metallic=0.4, rough=0.25),
        "frame": flat_material("ws_frame", (150, 152, 156), metallic=0.8, rough=0.4),
        "radiator": paint_material("ws_radiator", (236, 236, 232), dust, seams=False, scratches=False),
        "window": flat_material("ws_window", (60, 50, 30), emit=(255, 220, 150), strength=1.4),
        "green": flat_material("ws_green", (20, 60, 30), emit=(110, 255, 140), strength=1.6),
        "red": flat_material("ws_red", (60, 20, 20), emit=(255, 80, 60), strength=1.6),
    }


def torus(name, R, r, coll, mat, z=0.0):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=96, minor_segments=16,
                                     location=(0, 0, z))
    ob = bpy.context.active_object
    ob.name = name
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(mat)
    return ob


def ring_windows(coll, M, R, r, n, z):
    for k in range(n):
        a = 2 * math.pi * k / n
        box(f"win_{k}", (R * math.cos(a), R * math.sin(a), z + r + 0.02), (0.22, 0.5, 0.06), coll, M["window"],
            bevel=0.01, rot=(0, 0, a))


def spoke(coll, M, a, r0, r1, w, name):
    rm = (r0 + r1) / 2
    box(name, (rm * math.cos(a), rm * math.sin(a), 0.0), (r1 - r0, w, w * 0.8), coll, M["frame"], bevel=0.04,
        rot=(0, 0, a))


def dock_arm(coll, M, a, r0, r1, name):
    """Hazard-banded arm out to a docking collar with green (port) / red (starboard) lights."""
    spoke(coll, M, a, r0, r1, 0.9, f"{name}_arm")
    rm = (r0 + r1) / 2
    box(f"{name}_haz", (rm * math.cos(a), rm * math.sin(a), 0.42), ((r1 - r0) * 0.7, 0.5, 0.06), coll, M["hazard"],
        bevel=0.01, rot=(0, 0, a))
    cx, cy = r1 * math.cos(a), r1 * math.sin(a)
    cyl(f"{name}_collar", (cx, cy, 0.0), 1.05, 0.8, coll, M["dark"], verts=32)
    cyl(f"{name}_port", (cx, cy, 0.42), 0.62, 0.06, coll, M["hull"], verts=32)
    px, py = -math.sin(a), math.cos(a)                                     # perpendicular to the arm
    sphere(f"{name}_lg", (cx + px * 0.95, cy + py * 0.95, 0.45), 0.16, coll, M["green"])
    sphere(f"{name}_lr", (cx - px * 0.95, cy - py * 0.95, 0.45), 0.16, coll, M["red"])
    for k, f in enumerate((0.35, 0.65)):                                    # approach guide lights
        gx, gy = (r0 + (r1 - r0) * f) * math.cos(a), (r0 + (r1 - r0) * f) * math.sin(a)
        sphere(f"{name}_guide{k}", (gx + px * 0.5, gy + py * 0.5, 0.48), 0.1, coll, M["green"])
        sphere(f"{name}_guide{k}b", (gx - px * 0.5, gy - py * 0.5, 0.48), 0.1, coll, M["red"])


def solar_array(coll, M, a, r0, length, width, name):
    rm = r0 + length / 2
    cx, cy = rm * math.cos(a), rm * math.sin(a)
    box(f"{name}_truss", (cx, cy, -0.1), (length, 0.25, 0.2), coll, M["frame"], bevel=0.02, rot=(0, 0, a))
    for s in (-1, 1):
        px, py = -math.sin(a) * s * (width / 2 + 0.2), math.cos(a) * s * (width / 2 + 0.2)
        box(f"{name}_panel{s}", (cx + px, cy + py, -0.1), (length * 0.95, width, 0.06), coll, M["solar"],
            bevel=0.01, rot=(0, 0, a))
        for k in range(1, 6):                                               # panel frame lines
            f = -0.5 + k / 6
            fx, fy = math.cos(a) * f * length * 0.95, math.sin(a) * f * length * 0.95
            box(f"{name}_rib{s}{k}", (cx + px + fx, cy + py + fy, -0.05), (0.05, width, 0.02), coll, M["frame"],
                bevel=0.0, rot=(0, 0, a))


def radiators(coll, M, a, r, n, name):
    """Fins crossing a spoke at angle a, spaced along it from radius r (attached, not floating)."""
    for k in range(n):
        rr = r + k * 0.6
        cx, cy = rr * math.cos(a), rr * math.sin(a)
        box(f"{name}_{k}", (cx, cy, 0.1), (0.22, 2.2, 0.12), coll, M["radiator"], bevel=0.02, rot=(0, 0, a))


def hub(coll, M, r):
    cyl("hub", (0, 0, 0), r, 1.8, coll, M["hull"], verts=48)
    torus("hub_band", r * 0.93, 0.16, coll, M["band"], z=0.9)        # Halcyon orange rim (a full disc read as solid orange)
    cyl("hub_dome", (0, 0, 1.05), r * 0.62, 0.35, coll, M["hull"], verts=48, r2=r * 0.4)
    cyl("hub_core", (0, 0, 1.24), r * 0.28, 0.06, coll, M["window"], verts=32)
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        box(f"hub_win{k}", (r * 0.78 * math.cos(a), r * 0.78 * math.sin(a), 0.93), (0.3, 0.14, 0.05), coll,
            M["window"], bevel=0.01, rot=(0, 0, a))


def waystation_earth(coll, M):
    hub(coll, M, 2.3)
    torus("ring", 7.4, 0.95, coll, M["hull"])
    torus("ring_band", 7.4, 0.97, coll, M["dark"]).scale = (1, 1, 0.25)
    ring_windows(coll, M, 7.4, 0.95, 40, 0.0)
    for k in range(4):
        spoke(coll, M, math.pi / 4 + k * math.pi / 2, 2.2, 6.6, 0.55, f"spoke{k}")
    dock_arm(coll, M, 0.0, 2.2, 9.2, "dockE")
    dock_arm(coll, M, math.pi, 2.2, 9.2, "dockW")
    solar_array(coll, M, math.pi / 2, 8.1, 2.0, 2.2, "solarN")   # truss starts inside the ring
    solar_array(coll, M, -math.pi / 2, 8.1, 2.0, 2.2, "solarS")
    radiators(coll, M, math.pi / 4, 3.4, 4, "radNE")
    radiators(coll, M, -3 * math.pi / 4, 3.4, 4, "radSW")


def waystation_mars(coll, M):
    hub(coll, M, 2.0)
    torus("ring", 5.6, 0.8, coll, M["hull"])
    torus("ring_band", 5.6, 0.82, coll, M["dark"]).scale = (1, 1, 0.25)
    ring_windows(coll, M, 5.6, 0.8, 26, 0.0)
    for k in range(3):
        spoke(coll, M, math.pi / 2 + k * 2 * math.pi / 3, 1.9, 4.9, 0.5, f"spoke{k}")
    dock_arm(coll, M, 0.0, 1.9, 8.6, "dock")
    for k, a in enumerate((2.3, 3.4, 4.1)):                                 # cargo pod clusters
        r = 7.6
        for j in range(3):
            px, py = -math.sin(a) * (j - 1) * 1.0, math.cos(a) * (j - 1) * 1.0
            cyl(f"pod{k}{j}", (r * math.cos(a) + px, r * math.sin(a) + py, 0.0), 0.45, 1.5, coll,
                M["band"] if j == 1 else M["hull"], rot=(0, math.pi / 2, a), verts=24)
        spoke(coll, M, a, 6.3, 7.2, 0.3, f"podlink{k}")
    radiators(coll, M, math.pi / 2 + 2 * math.pi / 3, 2.8, 3, "radW")     # on the 210 deg spoke
    radiators(coll, M, math.pi / 2 + 4 * math.pi / 3, 2.8, 3, "radE")     # on the 330 deg spoke
    solar_array(coll, M, -1.15, 6.0, 2.4, 1.6, "solar")


STATIONS = {"waystation_earth": (waystation_earth, (60, 56, 54)),
            "waystation_mars": (waystation_mars, (150, 84, 54))}             # rust dust in the grime


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    for name, (fn, dust) in STATIONS.items():
        coll = bpy.data.collections.new(name)
        scene.collection.children.link(coll)
        fn(coll, mats(dust))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
