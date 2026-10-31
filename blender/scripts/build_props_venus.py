"""Builds blender/sources/props/venus.blend: Venus Aerostat and station props (B-045, Bible §7.4).

Same conventions as build_props_mercury.py: one collection per prop (`prop_<name>`), real
scale, standing on z = 0, origin = bottom centre. Venus palette: orange-cream hulls stained
sulfur-yellow, warm deck lights (emission). aerostat_balloon is translucent cream with gore
seams and rigging down to a load ring; it renders at ppu 96 in the manifest (5.3 m in 512 px,
the D-018 precedent) instead of exceeding the prop size cap. meridian_station_door shares the
Wardens' ceramic and verdigris seams (the Wardens were built on the Meridian station).

  blender --background --factory-startup --python blender/scripts/build_props_venus.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_pilgrim import box, cyl, flat_material, paint_material, sphere  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "venus.blend")
INTERACTABLE = {"buoyancy_cell", "meridian_station_door", "vent_harvester"}


def materials(rim):
    M = {
        "hull": paint_material("vhull", (226, 206, 168), (196, 170, 70)),          # cream, sulfur stain
        "hull_dark": paint_material("vhull_dark", (120, 96, 72), (90, 70, 44), seams=False),
        "orange": paint_material("vorange", (214, 120, 52), (170, 120, 50), seams=False),
        "metal": flat_material("vmetal", (110, 104, 96), metallic=0.8, rough=0.45),
        "grate": flat_material("vgrate", (70, 66, 62), metallic=0.7, rough=0.5),
        "light": flat_material("vlight", (90, 60, 20), emit=(255, 196, 110), strength=1.6),
        "glow": flat_material("vglow", (120, 50, 16), emit=(255, 130, 50), strength=1.8),
        "window": flat_material("vwindow", (60, 44, 24), emit=(255, 214, 150), strength=1.3),
        "ceramic": paint_material("vceramic", (226, 218, 198), (180, 168, 140), seams=False, scratches=False),
        "seam": flat_material("vseam", (40, 90, 70), emit=(110, 230, 170), strength=1.3),
    }
    env = bpy.data.materials.new("envelope")
    env.use_nodes = True
    pr = env.node_tree.nodes["Principled BSDF"]
    pr.inputs["Base Color"].default_value = (0.92, 0.84, 0.66, 1)
    pr.inputs["Roughness"].default_value = 0.45
    pr.inputs["Alpha"].default_value = 0.78
    M["envelope"] = env
    for m in M.values():
        m["meridian_rim"] = rim
    return M


def _link(c, ob):
    for co in list(ob.users_collection):
        co.objects.unlink(ob)
    c.objects.link(ob)
    return ob


def aerostat_deck(c, M):
    """Floating deck section 3.8 m: grated deck on a tapered cream hull keel, railings, two deck
    lights and a winch drum."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.6))
    keel = _link(c, bpy.context.active_object)
    for v in keel.data.vertices:                                  # tapered keel: narrow at the bottom
        if v.co.z < 0:
            v.co.x *= 0.6
    keel.scale = (3.6, 1.6, 1.0)
    bv = keel.modifiers.new("bev", "BEVEL"); bv.width, bv.segments = 0.08, 2
    keel.data.materials.append(M["hull"])
    box("band", (0, 0, 0.82), (3.62, 1.62, 0.14), c, M["orange"], bevel=0.03)
    box("deck", (0, 0, 1.14), (3.8, 1.7, 0.08), c, M["grate"], bevel=0.02)
    for k in range(9):                                             # railing posts + rail
        cyl(f"post{k}", (-1.8 + k * 0.45, -0.8, 1.6), 0.03, 0.9, c, M["metal"], verts=8)
    box("rail", (0, -0.8, 2.04), (3.7, 0.05, 0.05), c, M["metal"], bevel=0.01)
    for x in (-1.75, 1.75):
        cyl(f"lamppost{x}", (x, -0.8, 2.15), 0.04, 0.25, c, M["metal"], verts=8)
        sphere(f"lamp{x}", (x, -0.8, 2.32), 0.09, c, M["light"])
    cyl("winch", (0.9, 0.2, 1.42), 0.22, 0.6, c, M["orange"], rot=(math.pi / 2, 0, 0), verts=24)
    box("winch_base", (0.9, 0.2, 1.22), (0.6, 0.6, 0.12), c, M["metal"], bevel=0.02)
    for x in (-1.2, 0.0, 1.2):                                      # keel lights
        sphere(f"keel_light{x}", (x, -0.66, 0.5), 0.06, c, M["light"])


def aerostat_balloon(c, M):
    """Lift envelope ~4.6 m tall: translucent cream, gore seams, a sulfur-stained crown cap,
    rigging lines converging to a load ring at the bottom (the origin)."""
    R, H = 2.0, 2.3                                                # envelope radii (x, z)
    zc = 0.9 + H
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0, location=(0, 0, zc))
    env = _link(c, bpy.context.active_object)
    env.scale = (R, R * 0.8, H)
    bpy.ops.object.shade_smooth()
    env.data.materials.append(M["envelope"])
    for k in range(10):                                            # gore seams (meridian ribs)
        a = 2 * math.pi * k / 10
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.012, major_segments=64, minor_segments=6,
                                         location=(0, 0, zc), rotation=(math.pi / 2, 0, a))
        sm = _link(c, bpy.context.active_object)
        sm.scale = (R * 1.005, H * 1.005, R * 0.8 * 1.005)
        sm.data.materials.append(M["hull_dark"])
    cyl("crown", (0, 0, zc + H - 0.08), 0.55, 0.12, c, M["orange"], verts=32)
    for k in range(8):                                             # rigging to the load ring
        a = 2 * math.pi * k / 8
        x0, y0, z0 = R * 0.85 * math.cos(a), R * 0.68 * math.sin(a), zc - H * 0.55
        x1, y1, z1 = 0.35 * math.cos(a), 0.35 * math.sin(a), 0.12
        dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
        ln = math.sqrt(dx * dx + dy * dy + dz * dz)
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.015, depth=ln, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        line = _link(c, bpy.context.active_object)
        line.rotation_euler = (0, math.atan2(math.hypot(dx, dy), dz), math.atan2(dy, dx))
        line.data.materials.append(M["metal"])
    bpy.ops.mesh.primitive_torus_add(major_radius=0.36, minor_radius=0.05, location=(0, 0, 0.1))
    _link(c, bpy.context.active_object).data.materials.append(M["metal"])
    for k in range(4):                                             # nav lights round the equator
        a = 2 * math.pi * k / 4 + 0.4
        sphere(f"nav{k}", (R * 0.99 * math.cos(a), R * 0.79 * math.sin(a), zc), 0.07, c, M["light"])


def buoyancy_cell(c, M):
    """Float cell ~1.3 m: a strapped pill on a cradle, orange band, status light."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0, location=(0, 0, 0.62))
    cell = _link(c, bpy.context.active_object)
    cell.scale = (0.65, 0.45, 0.45)
    bpy.ops.object.shade_smooth()
    cell.data.materials.append(M["hull"])
    for x in (-0.3, 0.3):                                          # straps
        bpy.ops.mesh.primitive_torus_add(major_radius=0.46, minor_radius=0.025, location=(x, 0, 0.62), rotation=(0, math.pi / 2, 0))
        st = _link(c, bpy.context.active_object)
        st.scale = (1.0, 1.0, 1.0)
        st.data.materials.append(M["metal"])
    box("band", (0, 0, 0.62), (0.16, 0.92, 0.92), c, M["orange"], bevel=0.04)
    box("cradle", (0, 0, 0.1), (1.0, 0.6, 0.2), c, M["metal"], bevel=0.03)
    sphere("status", (0.0, -0.46, 0.82), 0.045, c, M["glow"])


def station_hull_a(c, M):
    """Station wall section 3.6 x 3 m: ribbed cream panels, a row of lit portholes."""
    box("wall", (0, 0, 1.5), (3.6, 0.4, 3.0), c, M["hull"], bevel=0.06)
    for k in range(5):                                             # ribs
        box(f"rib{k}", (-1.6 + k * 0.8, -0.22, 1.5), (0.12, 0.08, 3.0), c, M["hull_dark"], bevel=0.02)
    for k in range(4):
        x = -1.2 + k * 0.8
        cyl(f"port{k}", (x, -0.21, 1.9), 0.2, 0.06, c, M["metal"], rot=(math.pi / 2, 0, 0), verts=24)
        cyl(f"glass{k}", (x, -0.25, 1.9), 0.15, 0.03, c, M["window"], rot=(math.pi / 2, 0, 0), verts=24)
    box("base", (0, 0, 0.1), (3.6, 0.5, 0.2), c, M["orange"], bevel=0.03)


def station_hull_b(c, M):
    """Bulkhead section 3.6 x 3 m: curved top, pipes and a glowing vent grille."""
    box("wall", (0, 0, 1.3), (3.6, 0.4, 2.6), c, M["hull"], bevel=0.06)
    cyl("top", (0, 0, 2.6), 1.8, 0.4, c, M["hull"], rot=(math.pi / 2, 0, 0), verts=48).scale = (1.0, 0.22, 1.0)
    for k, z in enumerate((0.7, 0.95)):                             # pipes
        cyl(f"pipe{k}", (0, -0.26, z), 0.07, 3.5, c, M["orange" if k else "metal"], rot=(0, math.pi / 2, 0), verts=16)
    box("grille", (0.9, -0.22, 1.7), (0.9, 0.06, 0.6), c, M["grate"], bevel=0.02)
    for k in range(5):
        box(f"slot{k}", (0.9, -0.26, 1.5 + k * 0.1), (0.8, 0.02, 0.03), c, M["glow"], bevel=0.005)
    sphere("lamp", (-1.3, -0.25, 2.2), 0.08, c, M["light"])


def meridian_station_door(c, M):
    """Sowing-era hatch (Warden origin): a pale ceramic arch with verdigris seams, a heavy
    round-topped door, glowing seam trim."""
    box("frame", (0, 0, 1.2), (1.8, 0.4, 2.4), c, M["ceramic"], bevel=0.08)
    cyl("arch", (0, 0, 2.4), 0.9, 0.4, c, M["ceramic"], rot=(math.pi / 2, 0, 0), verts=40)
    # Door stands proud of the frame face (it was hidden inside the solid frame).
    box("door", (0, -0.27, 1.1), (1.2, 0.12, 2.0), c, M["hull_dark"], bevel=0.05)
    cyl("door_top", (0, -0.27, 2.1), 0.6, 0.12, c, M["hull_dark"], rot=(math.pi / 2, 0, 0), verts=40)
    box("seam_v", (0, -0.34, 1.35), (0.04, 0.02, 2.3), c, M["seam"], bevel=0.005)
    for k in range(5):
        a = math.pi * k / 4
        box(f"arc_seam{k}", (0.72 * math.cos(a), -0.22, 2.4 + 0.72 * math.sin(a)), (0.16, 0.02, 0.04), c, M["seam"],
            bevel=0.005, rot=(0, -a, 0))
    box("sill", (0, 0, 0.05), (2.0, 0.5, 0.1), c, M["ceramic"], bevel=0.02)


def vent_harvester(c, M):
    """Vent-field rig ~3 m: tripod over a vent, intake funnel glowing orange, collector tank."""
    for k, (x, y) in enumerate(((-1.1, -0.4), (1.1, -0.4), (0.0, 0.6))):
        dx, dz = -x * 0.65, 2.0
        ln = math.hypot(dx, dz)
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.06, depth=ln, location=(x + dx / 2, y * 0.6, dz / 2))
        leg = _link(c, bpy.context.active_object)
        leg.rotation_euler = (0, math.atan2(dx, dz), 0)
        leg.data.materials.append(M["metal"])
    cyl("tank", (0, 0, 2.3), 0.45, 0.8, c, M["orange"], verts=32)
    cyl("cap", (0, 0, 2.75), 0.35, 0.1, c, M["metal"], verts=32)
    cyl("funnel", (0, 0, 1.3), 0.45, 0.8, c, M["hull_dark"], verts=32, r2=0.12)
    cyl("intake", (0, 0, 0.88), 0.43, 0.04, c, M["glow"], verts=32)
    sphere("beacon", (0, 0, 2.86), 0.08, c, M["light"])
    box("pad", (0, 0, 0.05), (2.6, 1.2, 0.1), c, M["grate"], bevel=0.02)


PROPS = {"aerostat_deck": aerostat_deck, "aerostat_balloon": aerostat_balloon, "buoyancy_cell": buoyancy_cell,
         "station_hull_a": station_hull_a, "station_hull_b": station_hull_b,
         "meridian_station_door": meridian_station_door, "vent_harvester": vent_harvester}


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    for name, fn in PROPS.items():
        coll = bpy.data.collections.new(f"prop_{name}")
        scene.collection.children.link(coll)
        fn(coll, materials(0.1 if name in INTERACTABLE else 0.0))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
