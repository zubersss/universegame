"""MERIDIAN asset renderer (contract §3). Run through tools/blender_render.ps1, or:

  blender --background --factory-startup --python blender/render.py -- --asset <key>
  ... -- --category <category[/name]> | --all   [--preview]

Reads blender/manifest.json, renders every selected asset's maps through per-pass material
overrides, post-processes in numpy (dilation, normal fill, sheet packing), checks the
contract, writes Assets/_Game/Art/<category>/<name>/<variant>_<map>.png (+ <variant>.json for
sheets) and a contact sheet in blender/preview/. --preview: 25% size, low samples,
blender/preview/ only. One line per asset to logs/blender_<date>.log. Exits non-zero with a
one-line reason on any failure.
"""
import argparse
import datetime as dt
import importlib.util
import json
import os
import shutil
import sys
import time
import traceback

sys.dont_write_bytecode = True  # no __pycache__ in the repo (.gitignore is LEAD's)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "scripts"))

import numpy as np  # noqa: E402

from meridian import contract as C  # noqa: E402
from meridian import pngio, post  # noqa: E402

MANIFEST = os.path.join(HERE, "manifest.json")
ART = os.path.join(ROOT, "Assets", "_Game", "Art")
PREVIEW = os.path.join(HERE, "preview")
WORK = os.path.join(PREVIEW, "_work")
LOGS = os.path.join(ROOT, "logs")


class AssetError(Exception):
    pass


# ---------------------------------------------------------------- logging / memory

def peak_mb():
    try:
        import ctypes
        from ctypes import wintypes

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        k32 = ctypes.windll.kernel32
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        fn = k32.K32GetProcessMemoryInfo
        fn.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
        if not fn(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
            return -1
        return int(pmc.PeakWorkingSetSize / 2**20)
    except Exception:
        return -1


def log_line(text):
    os.makedirs(LOGS, exist_ok=True)
    now = dt.datetime.now()
    with open(os.path.join(LOGS, f"blender_{now:%Y-%m-%d}.log"), "a", encoding="utf-8") as f:
        f.write(f"{now:%Y-%m-%dT%H:%M:%S} {text}\n")
    print("MERIDIAN", text, flush=True)


# ---------------------------------------------------------------- manifest

def load_manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        man = json.load(f)
    assets = man.get("assets", [])
    seen = set()
    for a in assets:
        k = a.get("key", "")
        if not C.KEY_RE.match(k):
            raise AssetError(f"manifest: bad key '{k}' (category/name/variant, a-z 0-9 _)")
        if k.split("/")[0] not in C.CATEGORIES:
            raise AssetError(f"manifest: unknown category in '{k}'")
        if k in seen:
            raise AssetError(f"manifest: duplicate key '{k}'")
        seen.add(k)
    return man, assets


def select(assets, args):
    if args.all:
        return assets
    if args.asset:
        # One key, or a comma-separated list rendered in the given order in one process (so a
        # batch holds the lock as one job, D-037).
        by_key = {a["key"]: a for a in assets}
        hit = []
        for k in [k.strip() for k in args.asset.split(",") if k.strip()]:
            if k not in by_key:
                raise AssetError(f"unknown asset key '{k}' (not in blender/manifest.json)")
            hit.append(by_key[k])
        return hit
    pre = args.category.strip("/")
    hit = [a for a in assets if a["key"] == pre or a["key"].startswith(pre + "/")]
    if not hit:
        cats = pre.split("/")[0]
        if cats not in C.CATEGORIES:
            raise AssetError(f"unknown category '{pre}'")
    return hit


# ---------------------------------------------------------------- scene setup

# D-033: flat sprite passes (emission overrides) and lit icons render on Cycles CPU: no GPU
# buffers in shared RAM (EEVEE's crashed at ~0.6 GB free), ~half the peak.
CYCLES_CPU_CATEGORIES = {"props", "creatures", "characters", "ships", "icons"}


def engine_kind(entry):
    if entry.get("engine"):
        return entry["engine"]
    return "cycles_cpu" if entry["key"].split("/")[0] in CYCLES_CPU_CATEGORIES else "eevee"


def pick_engine(kind):
    import bpy
    items = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    if kind in ("cycles", "cycles_cpu") and "CYCLES" in items:
        return "CYCLES"
    for name in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        if name in items:
            return name
    raise AssetError(f"no EEVEE engine in {items}")


def set_view(scene, view):
    """view: 'Standard' (sRGB maps) or 'Raw' (linear maps)."""
    vs = scene.view_settings
    scene.display_settings.display_device = "sRGB"
    vs.view_transform = view
    try:
        vs.look = "None"
    except TypeError:
        pass
    vs.exposure = 0.0
    vs.gamma = 1.0
    vs.use_curve_mapping = False


def script_deps(path, seen=None):
    """The build script plus every local blender/scripts module it imports, recursively."""
    import re
    seen = seen if seen is not None else set()
    if path in seen or not os.path.isfile(path):
        return seen
    seen.add(path)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for name in re.findall(r"^\s*(?:from|import)\s+([A-Za-z_]\w*)", text, re.M):
        dep = os.path.join(HERE, "scripts", name + ".py")
        if os.path.isfile(dep):
            script_deps(dep, seen)
    return seen


def source_is_stale(entry):
    """True when the .blend is missing, or older than its build script or anything it imports
    (a stale scene once rendered silently because only a missing .blend triggered a build)."""
    src = os.path.join(HERE, entry["source"])
    if not os.path.isfile(src):
        return True
    if not entry.get("build"):
        return False
    newest = max(os.path.getmtime(p) for p in script_deps(os.path.join(HERE, entry["build"])))
    return newest > os.path.getmtime(src)


def open_source(entry, preview):
    import bpy
    src = os.path.join(HERE, entry["source"])
    if source_is_stale(entry):
        build = entry.get("build")
        if not build:
            raise AssetError(f"source missing: {entry['source']}")
        run_build(entry)
        if not os.path.isfile(src):
            raise AssetError(f"build {build} did not write {entry['source']}")
        log_line(f"rebuilt: {entry['source']} (from {build})")
    bpy.ops.wm.open_mainfile(filepath=src, load_ui=False)
    scene = bpy.context.scene
    coll_name = entry.get("collection")
    coll = bpy.data.collections.get(coll_name) if coll_name else scene.collection
    if coll is None:
        raise AssetError(f"collection '{coll_name}' not in {entry['source']}")
    objs = set(coll.all_objects)
    for extra in entry.get("keep", []):          # e.g. a shared light rig for beauty renders
        if bpy.data.collections.get(extra) is None:
            raise AssetError(f"keep collection '{extra}' not in {entry['source']}")
        objs |= set(bpy.data.collections[extra].all_objects)
    for ob in scene.objects:
        ob.hide_render = ob not in objs or ob.hide_render
    return scene, [o for o in objs if not o.hide_render]


def run_build(entry):
    path = os.path.join(HERE, entry["build"])
    spec = importlib.util.spec_from_file_location("meridian_build", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    getattr(mod, entry.get("build_fn", "build"))(os.path.join(HERE, entry["source"]))   # v2: one script, several sources


def setup_render(scene, entry, w, h, preview):
    import bpy
    r = scene.render
    r.engine = pick_engine(engine_kind(entry))
    r.resolution_x, r.resolution_y = w, h
    r.resolution_percentage = 25 if preview else 100
    r.film_transparent = True
    r.dither_intensity = 0.0
    r.use_compositing = False
    r.use_sequencer = False
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA"
    r.image_settings.color_depth = "8"
    r.use_persistent_data = False
    samples = min(int(entry.get("samples", 32)), 64)
    if preview:
        samples = min(samples, 8)
    if r.engine == "CYCLES":
        cy = scene.cycles
        cy.device = "CPU"
        if engine_kind(entry) == "cycles_cpu":
            cy.samples = 4 if preview else 16              # D-033: flat passes need few samples
        else:
            cy.samples = min(samples, 128)
        cy.use_denoising = True
        if hasattr(cy, "denoiser"):
            cy.denoiser = "OPENIMAGEDENOISE"
        if hasattr(cy, "use_auto_tile"):
            cy.use_auto_tile = True
        if hasattr(cy, "tile_size"):
            cy.tile_size = 256
    else:
        scene.eevee.taa_render_samples = samples
    make_camera(scene, entry, w, h)
    if entry.get("beauty"):
        return   # lit UI art (icons): keep the source's own world and lights
    # Flat black world so nothing but the override emission reaches the film.
    world = bpy.data.worlds.new("meridian_world")
    if world.node_tree is None:
        world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg is not None:
        bg.inputs["Color"].default_value = (0, 0, 0, 1)
        bg.inputs["Strength"].default_value = 0.0
    scene.world = world


def make_camera(scene, entry, w, h):
    """Orthographic camera at PPU 128 placing the asset origin at the manifest pivot
    (normalized image coords from the bottom-left, as Unity reads them)."""
    import bpy
    from mathutils import Euler, Vector
    cam_cfg = entry.get("camera", "side")
    preset = cam_cfg if isinstance(cam_cfg, str) else cam_cfg.get("preset", "side")
    origin = Vector(entry.get("origin", [0, 0, 0]))
    px, py = entry.get("pivot", [0.5, 0.5])
    ppu = float(entry.get("ppu", C.PPU))   # override only where the contract caps size below real scale
    wm, hm = w / ppu, h / ppu
    dx, dy = (0.5 - px) * wm, (0.5 - py) * hm
    cd = bpy.data.cameras.new("meridian_cam")
    cd.type = "ORTHO"
    cd.ortho_scale = max(wm, hm)
    cd.sensor_fit = "AUTO"
    cd.clip_start, cd.clip_end = 0.01, 500.0
    cam = bpy.data.objects.new("meridian_cam", cd)
    scene.collection.objects.link(cam)
    if preset == "side":      # looks +Y; image right = +X, up = +Z
        cam.location = origin + Vector((dx, -100.0, dy))
        cam.rotation_euler = Euler((np.pi / 2, 0, 0))
    elif preset == "top":     # looks -Z; image right = +X, up = +Y
        cam.location = origin + Vector((dx, dy, 100.0))
        cam.rotation_euler = Euler((0, 0, 0))
    elif preset == "icon":    # 3/4 view from front-right, above; frame centred on the origin
        view = Vector((-0.55, 0.75, -0.5)).normalized()          # direction the camera looks
        cam.rotation_euler = view.to_track_quat("-Z", "Y").to_euler()
        cam.location = origin - view * 100.0
    else:
        raise AssetError(f"unknown camera preset '{preset}'")
    scene.camera = cam


# ---------------------------------------------------------------- rendering

def render_pass(entry, pass_name, w, h, preview, frames):
    """Reopen the source, override materials for `pass_name`, render each frame. Returns list
    of float HxWx4 arrays."""
    import bpy
    from meridian import passes
    scene, objs = open_source(entry, preview)
    setup_render(scene, entry, w, h, preview)
    set_view(scene, "Standard" if pass_name in ("color", "emission") else "Raw")
    if not (entry.get("beauty") and pass_name == "color"):
        passes.apply(objs, pass_name)
    if scene.render.engine == "CYCLES":
        # Flat emission passes have no noise; denoising would only nudge exact albedo/normal
        # values. Only AO (mask G) and lit beauty renders need it.
        scene.cycles.use_denoising = pass_name == "mask" or bool(entry.get("beauty"))
    os.makedirs(WORK, exist_ok=True)
    out = []
    for i, fr in enumerate(frames):
        scene.frame_set(fr)
        path = os.path.join(WORK, f"{entry['key'].replace('/', '__')}_{pass_name}_{i:03d}.png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        out.append(pngio.read_png(path))
    return out


def frame_list(entry):
    anim = entry.get("animations")
    if not anim:
        return [entry.get("frame", 1)], None
    frames, clips, idx = [], [], 0
    for clip in anim["clips"]:
        n = int(clip["length"])
        frames += [int(clip.get("frame_start", 1)) + i for i in range(n)]
        clips.append({"name": clip["name"], "start": idx, "length": n, "loop": bool(clip.get("loop", False))})
        idx += n
    return frames, clips


def autofit(entry, frames):
    """Frame sheets with `"autofit": true`: measure the posed geometry over every frame and
    return entry with `ppu` and `origin` x set so all frames fit inside the margin, feet on the
    pivot line. One ppu for the whole sheet (sizes stay consistent between clips)."""
    import bpy
    from mathutils import Vector
    scene, objs = open_source(entry, False)
    meshes = [o for o in objs if o.type == "MESH"]
    xs, zs = [], []
    for fr in frames:
        scene.frame_set(fr)
        dg = bpy.context.evaluated_depsgraph_get()
        for o in meshes:
            # Exact extents from the evaluated vertices (rotated bounding boxes overestimate:
            # the stag's antler boxes alone added ~0.4 m).
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            mw = ev.matrix_world
            for v in me.vertices:
                p = mw @ v.co
                xs.append(p.x)
                zs.append(p.z)
            ev.to_mesh_clear()
    w, h = entry["size"]
    px, py = entry.get("pivot", [0.5, 0.5])
    slack = C.PADDING + 4
    width_m = max(xs) - min(xs)
    top_m = max(zs)                                   # ground (z = 0) sits on the pivot line
    ppu = min((w - 2 * slack) / max(width_m, 1e-3), (h * (1 - py) - slack) / max(top_m, 1e-3))
    if min(zs) < -1e-3:                               # fliers (B-032): centred pivot, body below z = 0
        ppu = min(ppu, (h * py - slack) / -min(zs))
    ppu = float(int(ppu * 4) / 4)                     # quarter-px/m steps: stable, readable value
    cx = (max(xs) + min(xs)) / 2
    print(f"MERIDIAN autofit {entry['key']}: x [{min(xs):.2f}, {max(xs):.2f}] top {top_m:.2f} m -> ppu {ppu}, origin x {cx:.3f}")
    if ppu < float(entry.get("ppu_min", 0)):    # D-034: per-sheet ppu >= 100 for creatures
        raise AssetError(f"{entry['key']}: autofit ppu {ppu} < ppu_min {entry['ppu_min']} "
                         f"(sweep {max(xs) - min(xs):.2f} m x {top_m:.2f} m doesn't fit {w}x{h} px)")
    return dict(entry, ppu=ppu, origin=[cx, 0.0, 0.0])


def run_generator(entry, preview):
    """Generator assets (planet bakes, tile sets) produce their maps in a script:
    module.generate(entry, ctx) -> {map: HxWx4 uint8}."""
    path = os.path.join(HERE, entry["generator"])
    spec = importlib.util.spec_from_file_location("meridian_gen", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ctx = {"root": ROOT, "blender_dir": HERE, "preview": preview, "work": WORK}
    return mod.generate(entry, ctx)


def produce(entry, preview):
    key = entry["key"]
    cat = key.split("/")[0]
    rules = C.CATEGORIES[cat]
    maps_wanted = entry.get("maps", ["color"])
    if "color" not in maps_wanted:
        raise AssetError(f"{key}: 'color' map is required")
    if rules["lit"] and "normal" not in maps_wanted:
        raise AssetError(f"{key}: lit category '{cat}' requires a normal map")
    w, h = entry["size"]
    scale = 0.25 if preview else 1.0

    if entry.get("generator"):
        res = run_generator(entry, preview)
        clips = None
        if "frames" in res:   # generator frame sheet: pack like rendered sheets, write the .json
            _, clips = frame_list(entry)
            cols = int(entry["animations"].get("columns", 8))
            maps = {m: post.pack_sheet([f[m] for f in res["frames"]], cols,
                                       fill=(0, 0, 0, 0) if m == "color" else (0, 0, 0, 255))
                    for m in maps_wanted}
        else:
            maps = res
    else:
        frames, clips = frame_list(entry)
        if entry.get("autofit"):
            entry = autofit(entry, frames)
        raw = {m: render_pass(entry, m, w, h, preview, frames) for m in maps_wanted}
        per_frame = []
        for i in range(len(frames)):
            col = post.finish_color(raw["color"][i])
            alpha = raw["color"][i][..., 3]
            fm = {"color": col}
            if "normal" in raw:
                fm["normal"] = post.finish_normal(raw["normal"][i], alpha)
            if "emission" in raw:
                fm["emission"] = post.finish_emission(raw["emission"][i], alpha)
            if "mask" in raw:
                fm["mask"] = post.finish_mask(raw["mask"][i], alpha)
            per_frame.append(fm)
        if clips:
            cols = int(entry["animations"].get("columns", 8))
            maps = {m: post.pack_sheet([f[m] for f in per_frame], cols,
                                       fill=(0, 0, 0, 0) if m == "color" else
                                       (*C.NORMAL_FILL, 255) if m == "normal" else (0, 0, 0, 255))
                    for m in maps_wanted}
        else:
            maps = per_frame[0]
    return maps, clips, (w, h), entry      # entry may carry autofit's ppu/origin


def check(entry, maps, clips, wh, preview):
    key = entry["key"]
    cat, _n, variant = key.split("/")
    cap, rules = C.size_cap(key, entry)
    w, h = wh
    problems = []
    for m, img in maps.items():
        if m not in C.MAPS:
            problems.append(f"unknown map '{m}'")
        ih, iw = img.shape[:2]
        if not preview:
            if clips is None and (iw, ih) != (w, h):
                problems.append(f"{m} is {iw}x{ih}, manifest says {w}x{h}")
            if iw > cap[0] or ih > cap[1]:
                problems.append(f"{m} {iw}x{ih} over the {cat}/{variant} cap {cap[0]}x{cap[1]}")
            if rules.get("exact") and clips is None and (iw, ih) != cap:
                problems.append(f"{m} must be exactly {cap[0]}x{cap[1]}")
    if clips:
        fmax = rules.get("frame")
        if fmax and not preview and max(w, h) > fmax:
            problems.append(f"frame {w}x{h} over the {cat} frame cap {fmax}")
    if entry.get("padded", rules["padded"]):   # tileable strips (e.g. fx/escape_band) opt out
        if clips:
            fw, fh = (int(w * (0.25 if preview else 1)), int(h * (0.25 if preview else 1)))
        else:
            fw, fh = maps["color"].shape[1], maps["color"].shape[0]
        # At 25% a margin edge lands mid-pixel, so previews allow 1 px of rounding.
        pad = max(1, int(C.PADDING * 0.25) - 1) if preview else C.PADDING
        tiles = []
        col = maps["color"]
        if clips:
            n = sum(c["length"] for c in clips)
            cols = int(entry["animations"].get("columns", 8))
            for i in range(n):
                r, c = divmod(i, cols)
                y, x = r * (fh + C.GUTTER), c * (fw + C.GUTTER)
                tiles.append(col[y:y + fh, x:x + fw])
        else:
            tiles = [col]
        bad = [i for i, t in enumerate(tiles) if not post.check_padding(t, pad)[0]]
        if bad:
            problems.append(f"padding: frames {bad} reach into the {pad} px margin")
    tile = entry.get("tileable")
    seam = ""
    if tile:
        ok, seam = post.check_tileable(tile_image(entry, maps["color"]), tile, float(entry.get("seam_limit", 2.0)))
        if not ok:
            problems.append(f"tile check failed: {seam}")
    return problems, seam


def tile_image(entry, color):
    """What the 2x tile check looks at: the whole image, or for tile sets (`tile_index` +
    `tile_size`) the one cell that must tile with itself (the fully surrounded block)."""
    idx = entry.get("tile_index")
    if idx is None:
        return color
    full = entry["size"][0]
    ts = int(entry.get("tile_size", 128) * color.shape[1] / full)
    cols = color.shape[1] // ts
    r, c = divmod(int(idx), cols)
    return color[r * ts:(r + 1) * ts, c * ts:(c + 1) * ts]


def write_outputs(entry, maps, clips, wh, preview):
    key = entry["key"]
    cat, name, variant = key.split("/")
    dest = os.path.join(PREVIEW, key.replace("/", "__")) if preview else os.path.join(ART, cat, name)
    os.makedirs(dest, exist_ok=True)
    sizes = []
    for m in C.MAPS:
        if m not in maps:
            continue
        path = os.path.join(dest, f"{variant}_{m}.png")
        n = pngio.write_png(path, maps[m])
        if n > C.MAX_FILE_BYTES and not preview:
            raise AssetError(f"{key}: {variant}_{m}.png is {n / 2**20:.1f} MB, over the 4 MB cap")
        sizes.append(f"{m} {maps[m].shape[1]}x{maps[m].shape[0]} {n // 1024}KB")
    if clips:
        w, h = wh
        s = 0.25 if preview else 1.0
        anim = entry["animations"]
        meta = {
            "key": key,
            "frame_width": int(w * s), "frame_height": int(h * s),
            "columns": int(anim.get("columns", 8)),
            "gutter": C.GUTTER,
            "frames": sum(c["length"] for c in clips),
            "fps": int(anim.get("fps", 12)),
            "pivot": entry.get("pivot", [0.5, 0.0]),
            "facing": anim.get("facing", "right"),
            "animations": clips,
        }
        if "hitbox" in anim:
            meta["hitbox"] = anim["hitbox"]
        if "ppu" in entry:      # frames drawn below PPU 128 (creatures that don't fit their class frame)
            meta["ppu"] = entry["ppu"]
        with open(os.path.join(dest, f"{variant}.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        sizes.append("json")
    elif entry.get("sidecar"):          # v3 single images (e.g. film overlays, §11.6): {"key", "style": "v3", ...}
        with open(os.path.join(dest, f"{variant}.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"key": key, **entry["sidecar"]}, f, indent=2)
            f.write("\n")
        sizes.append("json")
    sheet = post.contact_sheet(maps, entry.get("tileable"), tile_img=tile_image(entry, maps["color"]))
    os.makedirs(PREVIEW, exist_ok=True)
    pngio.write_png(os.path.join(PREVIEW, f"{key.replace('/', '__')}_contact.png"), sheet)
    return sizes


STALE = os.path.join(HERE, "preview", "STALE.txt")


def mark_stale(key, stale):
    """Process guard (LEAD, B-026): a failed render leaves the previous export in place, which
    once got reviewed as if it were new. Failed keys are listed in preview/STALE.txt (exports
    stay put so UNITY's tree never loses art); a successful render removes the key."""
    keys = set()
    if os.path.isfile(STALE):
        with open(STALE, encoding="utf-8") as fh:
            keys = {ln.split(" | ")[0] for ln in fh.read().splitlines() if ln.strip()}
    keys.discard(key)
    if stale:
        keys.add(key)
    os.makedirs(os.path.dirname(STALE), exist_ok=True)
    with open(STALE, "w", encoding="utf-8") as fh:
        for k in sorted(keys):
            fh.write(f"{k} | exports are from an earlier render; the latest one failed\n")
    if stale:
        log_line(f"STALE {key}: exports on disk are from an earlier render (see preview/STALE.txt)")


def do_model(entry, preview):
    """Contract v2 (§9, B-077): export a glb + four maps + json and a stamped turntable."""
    t0 = time.time()
    if preview:
        raise AssetError(f"{entry['key']}: models have no preview mode (render the turntable instead)")
    from meridian import model
    sys.path.insert(0, HERE)
    import review
    scene, objs = open_source(entry, preview)
    for ob in objs:
        if ob.type == "ARMATURE":
            ob.hide_render = False
    stale = review.stale_keys()

    def stamp_fn(img, path):
        review.draw(img, review.stamp_text(path), 2, img.shape[0] - 16, (1.0, 1.0, 0.85))
        if entry["key"] in stale:
            review.draw(img, "STALE", 2, 2, (1.0, 0.15, 0.1), scale=4)
    try:
        info = model.export_model(entry, ART, PREVIEW, objs, stamp_fn)
    except model.ModelError as e:
        raise AssetError(f"{entry['key']}: {e}")
    mark_stale(entry["key"], False)
    log_line(f"OK {entry['key']} | glb {info['triangles']} tris, maps {info['texture']}^2"
             f"{', emissive' if info['emissive'] else ''}, clips {','.join(info['clips']) or '-'} "
             f"| review {os.path.basename(info['review'])} | {time.time() - t0:.1f}s | peak {peak_mb()}MB")


def do_terrain3d(entry, preview):
    """Contract v2 terrain block materials (§9 terrain row, B-080): numpy only."""
    t0 = time.time()
    if preview:
        raise AssetError(f"{entry['key']}: terrain3d has no preview mode")
    import gen_terrain3d as GT3
    sys.path.insert(0, HERE)
    import review
    res = GT3.export_terrain3d(entry, ART)
    key = entry["key"]
    sheet = os.path.join(PREVIEW, f"review_{key.replace('/', '_')}.png")
    first = next(iter(res))
    _, planet, material = key.split("/")
    src = (os.path.join(ART, "terrain", planet, "backwall_color.png") if material == "backwall"
           else os.path.join(ART, "terrain", planet, material, f"{first}_color.png"))
    GT3.contact(list(res.items()), sheet,
                lambda img, p: review.draw(img, review.stamp_text(p), 2, img.shape[0] - 16, (1.0, 1.0, 0.85)), src)
    mark_stale(key, False)
    seams = ", ".join(f"{k} seam {v[1][0]}/{v[1][1]}" for k, v in res.items())
    log_line(f"OK {key} | {', '.join(res)} 512^2 color/normal/mask | {seams} | {time.time() - t0:.1f}s | peak {peak_mb()}MB")


def do_skydome(entry, preview):
    """Contract v2 skydome (§9 depth bands, B-083): 2048x1024 equirect colour, numpy only."""
    t0 = time.time()
    import gen_skydome as SD
    sys.path.insert(0, HERE)
    import review
    path, img, seam = SD.export_skydome(entry, ART)
    sheet = img[::2, ::2].copy()
    review.draw(sheet, review.stamp_text(path), 2, sheet.shape[0] - 16, (1.0, 1.0, 0.85))
    out = os.path.join(PREVIEW, f"review_{entry['key'].replace('/', '_')}.png")
    pngio.write_png(out, np.dstack([pngio.to_u8(np.clip(sheet, 0, 1)), np.full(sheet.shape[:2], 255, np.uint8)]))
    mark_stale(entry["key"], False)
    log_line(f"OK {entry['key']} | skydome 2048x1024 color | seam_x={seam} | {time.time() - t0:.1f}s | peak {peak_mb()}MB")


def do_flora_atlas(entry, preview):
    """B-085 shared flora atlas (2048^2, 4x4 material tiles), numpy only."""
    t0 = time.time()
    import gen_flora_atlas as FA
    sys.path.insert(0, HERE)
    import review
    paths, maps = FA.export_atlas(entry, ART)
    sheet = maps["color"][::4, ::4, :3].copy()
    review.draw(sheet, review.stamp_text(paths["color"]), 2, sheet.shape[0] - 16, (1.0, 1.0, 0.85))
    out = os.path.join(PREVIEW, f"review_{entry['key'].replace('/', '_')}.png")
    pngio.write_png(out, np.dstack([pngio.to_u8(np.clip(sheet, 0, 1)), np.full(sheet.shape[:2], 255, np.uint8)]))
    mark_stale(entry["key"], False)
    log_line(f"OK {entry['key']} | atlas 2048^2 color/normal/mask/emission, {len(FA.TILE_SETS[entry.get("set", "earth")])} tiles | {time.time() - t0:.1f}s | peak {peak_mb()}MB")


def do_deck_plane(entry, preview):
    """B-097 giant deck planes: a painted cloud bank (RGBA) on a 256 x 128 m quad."""
    t0 = time.time()
    if preview:
        raise AssetError(f"{entry['key']}: deck planes have no preview mode (the review sheet is written on export)")
    import gen_deckplane as DP
    sys.path.insert(0, HERE)
    import review
    stale = review.stale_keys()

    def stamp(img, path):
        review.draw(img, review.stamp_text(path), 2, img.shape[0] - 16, (1.0, 1.0, 0.85))
        if entry["key"] in stale:
            review.draw(img, "STALE", 2, 2, (1.0, 0.15, 0.1), scale=4)
    info = DP.export_deck_plane(entry, ART, PREVIEW, stamp)
    mark_stale(entry["key"], False)
    log_line(f"OK {entry['key']} | deck plane 256x128 m, color{'+emission' if 'emission' in info['maps'] else ''} 2048x1024 RGBA, "
             f"coverage {info['coverage']}, seam {info['seam']} | review {os.path.basename(info['review'])}"
             f"{' + stack' if info['stack'] else ''} | {time.time() - t0:.1f}s | peak {peak_mb()}MB")



def _v3_dest(entry, preview):
    cat, name, _variant = entry["key"].split("/")
    return os.path.join(PREVIEW, entry["key"].replace("/", "__")) if preview else os.path.join(ART, cat, name)


def _v3_write_png(path, img, key):
    from meridian import v3
    n = pngio.write_png(path, img)
    if n > v3.MAX_FILE_BYTES:
        raise AssetError(f"{key}: {os.path.basename(path)} is {n / 2**20:.1f} MB, over the 4 MB cap")
    return n


def _v3_ink_stats(widths):
    from meridian import v3
    outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
    rng = lambda ws: (min(w[1] for w in ws), max(w[2] for w in ws)) if ws else (0, 0)  # noqa: E731
    return rng(outer), rng(inner)


def do_v3_sheet(entry, preview):
    """Contract v3.0 §11.2 (B-110): Grease Pencil drawings -> 1x frames at 12 fps -> one sheet
    + json + the §11.7 review sheet. Clips start at the timeline markers named after them."""
    import gp_raster as GR
    from meridian import v3
    sys.path.insert(0, HERE)
    import review
    t0 = time.time()
    key = entry["key"]
    variant = key.split("/")[2]
    if entry.get("preview_only") and not preview:
        raise AssetError(f"{key}: preview-only entry (run with -Preview)")
    scene, objs = open_source(entry, preview)
    fw, fh = entry["frame"]
    pivot = tuple(entry.get("pivot", [0.5, 0.0]))
    ss = 2 if preview else 4
    scale = float(entry.get("ppu_scale", 1.0))   # preview-only design sheets of big assets (B-117: 0.5x)
    if scale != 1.0 and not entry.get("preview_only"):
        raise AssetError(f"{key}: ppu_scale is for preview-only design sheets")
    base = int(entry.get("ppu", v3.PPU))       # a big hero may be drawn below PPU 64 only with a LEAD ruling (B-122)
    markers = {m.name: m.frame for m in scene.timeline_markers}
    frames, clips, widths = [], [], []
    below = []
    sock_src = json.loads(scene.get("sockets", "{}"))   # per drawing: {frame: {socket: [x_m, y_m]}} (B-122)
    sockets = {}
    for c in entry["clips"]:
        mname = c.get("marker", c["name"])     # a clip may read another marker (B-122: top_idle -> idle)
        if mname not in markers:
            raise AssetError(f"{key}: no timeline marker '{mname}' in {entry['source']}")
        clips.append({"name": c["name"], "start": len(frames), "length": int(c["frames"]),
                      "loop": bool(c.get("loop", False))})
        if c.get("loop"):
            clips[-1]["loop_from"] = int(c.get("loop_from", 0))
        for k in range(int(c["frames"])):
            f = markers[mname] + k
            for sname, xy in sock_src.get(str(f), {}).items():
                sockets.setdefault(sname, []).append(xy)
            strokes = GR.collect(scene, objs, f)
            if pivot[1] == 0 and strokes:
                zmin = min(float((s_["xz"][:, 1] - s_["radius"] * (1 + GR.JITTER)).min()) for s_ in strokes)
                if zmin * base * scale < -2.0:
                    below.append(len(frames))
            img, w = GR.render_frame(strokes, fw, fh, base * scale, pivot, ss=ss,
                                     seed=int(entry.get("seed", 1)) * 1000 + f)
            frames.append(img)
            widths += [(nm / scale, lo / scale, hi / scale) for nm, lo, hi in w]   # reported at 1x
    m = v3.EDGE_MARGIN
    clipped = [i for i, im in enumerate(frames)
               if im[:m, :, 3].any() or (pivot[1] > 0 and im[-m:, :, 3].any()) or im[:, :m, 3].any() or im[:, -m:, 3].any()]
    cols = int(entry.get("columns", v3.columns_for(fw, len(frames))))
    sheet = post.pack_sheet(frames, cols, gutter=v3.GUTTER, fill=(0, 0, 0, 0))
    meta = {"key": key, "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols,
            "gutter": v3.GUTTER, "frames": len(frames), "fps": v3.FPS, "pivot": list(pivot),
            "facing": entry.get("facing", "right"), "ppu": base, "animations": clips,
            "squash_root": bool(entry.get("squash_root", True))}
    if sockets and all(len(v) == len(frames) for v in sockets.values()):
        meta["sockets"] = sockets
        meta["sockets_units"] = "metres in sprite space from the pivot, one [x, y] per frame in sheet order"
    problems = v3.validate_sheet(meta, sheet.shape, ppu=base)
    if base != v3.PPU and not entry.get("ppu_exception"):
        problems.append(f"ppu {base} needs a LEAD-approved ppu_exception (contract §11.1: 64)")
    if clipped:
        problems.append(f"frames {clipped[:8]} touch the {m} px frame edge (drawing clipped)")
    if below:
        problems.append(f"frames {below[:8]} draw more than 2 px below the ground line (clipped at the pivot edge)")
    dest = _v3_dest(entry, preview)
    os.makedirs(dest, exist_ok=True)
    png = os.path.join(dest, f"{variant}_color.png")
    if problems and not preview:
        raise AssetError(f"{key}: " + "; ".join(problems))
    n = _v3_write_png(png, sheet, key)
    with open(os.path.join(dest, f"{variant}.json"), "w", encoding="utf-8", newline="\n") as fh_:
        json.dump(meta, fh_, indent=2)
        fh_.write("\n")
    removed = v3.remove_v2(dest, variant) if entry.get("replaces_v2") and not preview else []   # D-117 / D-119
    outer, inner = _v3_ink_stats(widths)
    stats = {"outer_px": outer, "inner_px": inner, "inner_n": sum(1 for w in widths if w[0] < v3.OUTER_SPLIT), "palette": v3.palette_hits(sheet, entry.get("planet", "earth"), tints=[tuple(t) for t in entry.get("palette_tints", [])]),
             "problems": problems, "sheet_wh": (sheet.shape[1], sheet.shape[0]), "png_kb": n // 1024}
    task = entry.get("review_name", key.replace("/", "_"))
    out = os.path.join(PREVIEW, f"review_{task}{'_preview' if preview else ''}.png")
    z = int(entry.get("design_zoom", 0))
    if z:                               # design sheets: every drawing again at z x (same strokes, PPU x z)
        stats["zoom_frames"] = [GR.render_frame(GR.collect(scene, objs, markers[c.get("marker", c["name"])] + k), fw * z, fh * z,
                                                base * scale * z, pivot, ss=2, seed=int(entry.get("seed", 1)) * 1000 + markers[c.get("marker", c["name"])] + k)[0]
                                for c in entry["clips"] for k in range(int(c["frames"]))]
    boxes = review.v3_sheet_review(entry, meta, frames, png, out, stats)
    if not preview:
        mark_stale(key, False)
    open_boxes = [k for k, (mk, _n) in boxes.items() if mk != "x"]
    log_line(f"{'PREVIEW' if preview else 'OK'} {key} | v3 sheet {sheet.shape[1]}x{sheet.shape[0]} {n // 1024}KB, "
             f"{len(frames)} frames {fw}x{fh} @12fps ({', '.join(c['name'] + ' ' + str(c['length']) for c in clips)}) "
             f"| ink outer {outer[0]:.1f}-{outer[1]:.1f}px inner {inner[0]:.1f}-{inner[1]:.1f}px "
             f"| palette {stats['palette'][0] * 100:.1f}% | boxes not x: {','.join(open_boxes) or '-'} "
             f"| review {os.path.basename(out)} | {time.time() - t0:.1f}s | peak {peak_mb()}MB"
             + (f" | removed v2 {', '.join(removed)}" if removed else "")
             + (f" | PROBLEMS {'; '.join(problems)}" if problems else ""))
    if problems:
        raise AssetError(f"{key}: " + "; ".join(problems))


def do_v3_rigset(entry, preview):
    """Contract v3.0 §11.3 (B-110): every GP object `part_<name>` in the collection is one rig
    part, drawn at frame 1 around its object origin (= the part's pivot); parts are shelf-packed
    into one <= 2048 sheet; the json carries the rects (bottom-left origin, px), pivots and the
    manifest's plants (bones, swaps, idle, react)."""
    import gp_raster as GR
    from meridian import v3
    sys.path.insert(0, HERE)
    import review
    t0 = time.time()
    key = entry["key"]
    variant = key.split("/")[2]
    if entry.get("preview_only") and not preview:
        raise AssetError(f"{key}: preview-only test entry (run with -Preview)")
    scene, objs = open_source(entry, preview)
    ss = 2 if preview else 4
    pad = 4
    parts = sorted([o for o in objs if o.type == "GREASEPENCIL" and o.name.startswith("part_")], key=lambda o: o.name)
    if not parts:
        raise AssetError(f"{key}: no part_<name> Grease Pencil objects in the collection")
    imgs, piv = [], []
    for ob in parts:
        strokes = GR.collect(scene, [ob], int(entry.get("frame_number", 1)))
        if not strokes:
            raise AssetError(f"{key}: {ob.name} has no strokes at frame 1")
        ox, oz = ob.matrix_world.translation.x, ob.matrix_world.translation.z
        allp = np.vstack([s["xz"] for s in strokes])
        rmax = max(float(s["radius"].max()) for s in strokes) * 1.25
        x0, x1 = allp[:, 0].min() - rmax, allp[:, 0].max() + rmax
        z0, z1 = allp[:, 1].min() - rmax, allp[:, 1].max() + rmax
        w = int(np.ceil((x1 - x0) * v3.PPU)) + 2 * pad
        h = int(np.ceil((z1 - z0) * v3.PPU)) + 2 * pad
        w, h = -(-w // 4) * 4, -(-h // 4) * 4
        px_piv = ((ox - x0) * v3.PPU + pad) / w, ((oz - z0) * v3.PPU + pad) / h
        for s in strokes:              # re-centre: the frame's pivot is the part's pivot
            s["xz"] = s["xz"] - np.array([ox, oz])
        img, _w = GR.render_frame(strokes, w, h, v3.PPU, px_piv, ss=ss, seed=int(entry.get("seed", 1)))
        imgs.append(img)
        piv.append(px_piv)
    pos, W, H = v3.shelf_pack([(im.shape[1], im.shape[0]) for im in imgs])
    sheet = np.zeros((H, W, 4), np.uint8)
    part_meta = []
    for ob, im, (x, ytop), pv in zip(parts, imgs, pos, piv):
        h, w = im.shape[:2]
        sheet[ytop:ytop + h, x:x + w] = im
        part_meta.append({"name": ob.name[len("part_"):], "rect": [x, H - (ytop + h), w, h],
                          "pivot": [round(pv[0], 4), round(pv[1], 4)]})
    meta = {"key": key, "style": "v3", "ppu": v3.PPU, "rect_origin": "bottom_left",
            "parts": part_meta, "plants": entry.get("plants") or json.loads(scene.get("rig_plants", "[]"))}
    problems = v3.validate_rigset(meta, sheet.shape)
    if problems and not preview:
        raise AssetError(f"{key}: " + "; ".join(problems))
    dest = _v3_dest(entry, preview)
    os.makedirs(dest, exist_ok=True)
    png = os.path.join(dest, f"{variant}_color.png")
    n = _v3_write_png(png, sheet, key)
    with open(os.path.join(dest, f"{variant}.json"), "w", encoding="utf-8", newline="\n") as fh_:
        json.dump(meta, fh_, indent=2)
        fh_.write("\n")
    task = entry.get("review_name", key.replace("/", "_"))
    out = os.path.join(PREVIEW, f"review_{task}{'_preview' if preview else ''}.png")
    loop = None
    if entry.get("loop"):                       # §11.7 (B-118): the assembled preview loop on the review
        _m, assets = load_manifest()
        le = next((a for a in assets if a["key"] == entry["loop"]), None)
        if le is None:
            raise AssetError(f"{key}: loop entry '{entry['loop']}' not in the manifest")
        lscene, lobjs = open_source(le, True)
        mk = {m.name: m.frame for m in lscene.timeline_markers}
        c0 = le["clips"][0]
        lfw, lfh = le["frame"]
        loop = [GR.render_frame(GR.collect(lscene, lobjs, mk[c0["name"]] + k), lfw, lfh, v3.PPU,
                                tuple(le.get("pivot", [0.5, 0.0])), ss=ss, seed=int(le.get("seed", 1)) * 1000 + mk[c0["name"]] + k)[0]
                for k in range(int(c0["frames"]))]
    if not preview and not problems:              # the exports are written and valid: no STALE banner from an earlier failed run on this
        mark_stale(key, False)                    # review (a later raise re-marks it; 11-08: the whale's first good render after 18:27)
    review.v3_rigset_review(entry, meta, sheet, png, out, imgs, {"problems": problems, "png_kb": n // 1024, "loop": loop})
    if entry.get("review_script"):                # e.g. the assembled Pilgrim rig (B-122): rig + bones + clips at 1x
        spec = importlib.util.spec_from_file_location("meridian_review_script", os.path.join(HERE, entry["review_script"]))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out2 = os.path.join(PREVIEW, f"review_{task}_assembled{'_preview' if preview else ''}.png")
        extra = mod.main(out2)
        if extra:
            problems = list(problems) + list(extra)
    if not preview:
        mark_stale(key, False)
    log_line(f"{'PREVIEW' if preview else 'OK'} {key} | v3 rig set {W}x{H} {n // 1024}KB, {len(part_meta)} parts, "
             f"{len(meta['plants'])} plants | review {os.path.basename(out)} | {time.time() - t0:.1f}s | peak {peak_mb()}MB"
             + (f" | PROBLEMS {'; '.join(problems)}" if problems else ""))
    if problems:
        raise AssetError(f"{key}: " + "; ".join(problems))


def do_painted_bg(entry, preview):
    """Contract v3.0 §11.4 (B-114): painted watercolour parallax layers + <scene>.json, numpy
    only; review: the layers stacked and tiled 2x, the surveyor's sheet frames at 1x on top."""
    import gen_painted_bg as BG
    sys.path.insert(0, HERE)
    import review
    t0 = time.time()
    if preview:
        raise AssetError(f"{entry['key']}: painted backgrounds have no preview mode")
    info, meta = BG.export_background(entry, ART)
    bad = [f"layer{i} seam {s:.2f}" for i, (_p, _img, _n, s) in enumerate(info) if s > float(entry.get("seam_limit", 2.0))]
    if bad:
        raise AssetError(f"{entry['key']}: tile check failed: {', '.join(bad)}")
    H = max(img.shape[0] for _p, img, _n, _s in info)
    Wd = info[0][1].shape[1] * 2
    canvas = np.zeros((H, Wd, 3), np.float32)
    ground = 64                                           # px of near layer under the surface line in the review
    for (_p, img, _n, _s), L in zip(info, meta["layers"]):
        f = np.tile(img.astype(np.float32) / 255.0, (1, 2, 1))
        h = f.shape[0]
        y0 = H - h - max(0, int(round((L["y_m"] + 0.5) * v3_ppu())))
        y0 = max(0, min(H - h, y0))
        a = f[..., 3:4]
        canvas[y0:y0 + h] = f[..., :3] * a + canvas[y0:y0 + h] * (1 - a)
    sv = os.path.join(ART, "characters", "surveyor", "side_color.png")
    js = os.path.join(ART, "characters", "surveyor", "side.json")
    if os.path.isfile(sv) and os.path.isfile(js):
        sheet = pngio.to_u8(pngio.read_png(sv))
        sm = json.load(open(js, encoding="utf-8"))
        fw, fh, cols, g = sm["frame_width"], sm["frame_height"], sm["columns"], sm.get("gutter", 4)
        for k, idx in enumerate((0, 12, 25, 46)):         # idle, walk, jump stretch, look_camera front
            r, c = divmod(idx, cols)
            fr = sheet[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw]
            review._over(canvas, fr, 200 + k * 900, H - fh - ground)
    for i, (p, _img, _n, _s) in enumerate(info):
        review.draw(canvas, f"layer{i} " + review.stamp_text(p), 4, 4 + 18 * i, (1.0, 1.0, 0.85))
    review.draw(canvas, "2x tiled, seam at the centre; surveyor at 1x", 4, H - 18, (1.0, 1.0, 0.85))
    out = os.path.join(PREVIEW, f"review_{entry.get('review_name', entry['key'].replace('/', '_'))}.png")
    review.write(out, canvas)
    dip = ""
    if entry.get("dip_review"):                           # D-169: the set over a 1.5 m and a 3 m valley and a rise, from the exported layers
        import build_backdrop_v3 as BB
        _c, planet, scene = entry["key"].split("/")
        dout = os.path.join(PREVIEW, f"review_{entry.get('review_name', scene)}_dip.png")
        BB.preview_dip(PREVIEW, scene, from_png=True, out=dout, planet=planet,
                       footnote="exported " + "; ".join(f"layer{i} " + review.stamp_text(p) for i, (p, _img, _n, _s) in enumerate(info)))
        dip = f" + {os.path.basename(dout)}"
    if entry.get("underwater_review"):                    # B-202: sea_under seen by the swimmer at 3 / 8 / 15 / 40 m (U-040's tint)
        import build_backdrop_v3 as BB
        uout = os.path.join(PREVIEW, f"review_{entry.get('review_name', 'sea_under')}_underwater.png")
        BB.preview_sea_under(PREVIEW, from_png=True, out=uout,
                             footnote="exported " + "; ".join(f"layer{i} " + review.stamp_text(p) for i, (p, _img, _n, _s) in enumerate(info)))
        dip += f" + {os.path.basename(uout)}"
    mark_stale(entry["key"], False)
    log_line(f"OK {entry['key']} | painted {len(info)} layers "
             + ", ".join(f"layer{i} {img.shape[1]}x{img.shape[0]} {n // 1024}KB seam {s:.2f}" for i, (_p, img, n, s) in enumerate(info))
             + f" + {entry['key'].split('/')[2]}.json | review {os.path.basename(out)}{dip} | {time.time() - t0:.1f}s | peak {peak_mb()}MB")
    parts = entry["key"].split("/")
    if len(parts) == 3 and parts[1] == "uranus" and parts[2].endswith("_survey"):                  # B-166: a deck's four lights are in (survey last)
        import build_backdrop_v3 as BB
        deck = parts[2].rsplit("_", 1)[0]
        ok = BB.uranus_deck_check(ART, deck, art=True)
        log_line(f"URANUS-CHECK {deck} {'PASS' if ok else 'FAIL'} (D-142: one alpha per layer across the four lights)")
        if not ok:
            raise AssetError(f"{entry['key']}: the uranus check failed for {deck} (the alpha differs across the lights, or a light is missing)")


def v3_ppu():
    from meridian import v3
    return v3.PPU


def do_palette_strip(entry, preview):
    """Bible §9.1 planet palette as an 8x1 strip + json (B-114)."""
    import gen_painted_bg as BG
    t0 = time.time()
    if preview:
        raise AssetError(f"{entry['key']}: palette strips have no preview mode")
    p, strip = BG.export_palette(entry, ART)
    mark_stale(entry["key"], False)
    log_line(f"OK {entry['key']} | strip {strip.shape[1]}x{strip.shape[0]} + strip.json | {time.time() - t0:.1f}s | peak {peak_mb()}MB")


def do_disc_set(entry, preview):
    """Contract §11.5 + D-098 (B-119): every planet disc sheet + json, Luna, Saturn's ring parts
    and disc_rig.json in one job (numpy painting); review_b119_discs.png from the same frames."""
    import build_discs_v3 as DS
    t0 = time.time()
    if preview:
        raise AssetError(f"{entry['key']}: the disc set has no preview mode (python build_discs_v3.py <dir>)")
    members = [f"planets/{p_}/disc" for p_ in DS.ORDER] + ["planets/earth/luna", "planets/saturn/rings_back", "planets/saturn/rings_front"]
    try:
        out, tiles = DS.export(ART, PREVIEW)
    except Exception:
        for k in members:
            mark_stale(k, True)
        raise
    stamps = [os.path.join(ART, *k.split("/")[:2], k.split("/")[2] + "_color.png") for k, *_r in out]
    DS.preview(PREVIEW, tiles=tiles, out_name=f"review_{entry.get('review_name', 'b119_discs')}.png", stamp_paths=stamps)
    for k, *_r in out:
        mark_stale(k, False)
    mark_stale(entry["key"], False)
    log_line(f"OK {entry['key']} | " + ", ".join(f"{k.split('/')[1]}/{k.split('/')[2]} {w}x{h} {nf}f {kb}KB" for k, w, h, nf, kb in out)
             + f" | space_ppu {DS.SPACE_PPU:g} | {time.time() - t0:.1f}s | peak {peak_mb()}MB")


def do_space_starfield(entry, preview):
    """Contract §11.4 space (B-120): starfield 2048^2 tileable + 3 nebula cards + starfield.json;
    the 2x2 tile check on the exported starfield in x and y; review_b120_starfield.png."""
    import gen_painted_bg as BG
    sys.path.insert(0, HERE)
    import review
    t0 = time.time()
    if preview:
        raise AssetError(f"{entry['key']}: the starfield has no preview mode")
    info, meta = BG.export_space(entry, ART)
    lim = float(entry.get("seam_limit", 2.0))
    p0, img0, n0, sx, sy = info[0]
    if sx > lim or sy > lim:
        raise AssetError(f"{entry['key']}: tile check failed: seam_x {sx:.2f} seam_y {sy:.2f} (limit {lim})")
    sf = img0.astype(np.float32) / 255.0
    Hs, Ws = sf.shape[:2]
    big = np.tile(sf[..., :3], (2, 2, 1))[Hs // 2:Hs // 2 + Hs, Ws // 2:Ws // 2 + Ws].copy()   # the 4-tile seam crossing at the centre
    for k, (pk, im, _n, _a, _b) in enumerate(info[1:]):
        review._over(big, np.ascontiguousarray(im[::2, ::2]), 60 + k * 660, Hs - 560)
    big[Hs // 2 - 2:Hs // 2 + 2, :12] = (0.85, 0.1, 0.1)
    big[:12, Ws // 2 - 2:Ws // 2 + 2] = (0.85, 0.1, 0.1)
    half = big[::2, ::2].copy()
    for i, (pk, *_r) in enumerate(info):
        review.draw(half, os.path.basename(pk) + " " + review.stamp_text(pk), 4, 4 + 18 * i, (1.0, 1.0, 0.85))
    out = os.path.join(PREVIEW, f"review_{entry.get('review_name', 'b120_starfield')}.png")
    review.write(out, half)
    mark_stale(entry["key"], False)
    log_line(f"OK {entry['key']} | layer0 starfield {img0.shape[1]}x{img0.shape[0]} {n0 // 1024}KB seam_x {sx:.2f} seam_y {sy:.2f}, "
             + ", ".join(f"{os.path.basename(pk)[:-10]} {im.shape[1]}x{im.shape[0]} {n // 1024}KB" for pk, im, n, _a, _b in info[1:])
             + f" + starfield.json | review {os.path.basename(out)} | {time.time() - t0:.1f}s | peak {peak_mb()}MB")


def do_hud(entry, preview):
    """Contract §11.6 (B-121): ui/hud/gauges (1024^2, dials + needles + json), escape_line
    (512x64 tile), escape_sign; review at 1080p over the B-114 plains (needles at 30/60/90 %)."""
    import build_hud_v3 as HUD
    t0 = time.time()
    if preview:
        raise AssetError(f"{entry['key']}: the HUD has no preview mode (python build_hud_v3.py <dir>)")
    files, meta = HUD.build(ART, art=True)
    d = os.path.join(ART, "ui", "hud")
    ok, seam = post.check_tileable(files["escape_line_color.png"], "x", float(entry.get("seam_limit", 2.0)))
    if not ok:
        raise AssetError(f"{entry['key']}: escape_line tile check failed: {seam}")
    stamps = [os.path.join(d, fn) for fn in files]
    HUD.review_sheet(PREVIEW, files, meta_dir=d, out_name=f"review_{entry.get('review_name', 'b121_hud')}.png", stamp_paths=stamps)
    mark_stale(entry["key"], False)
    log_line(f"OK {entry['key']} | " + ", ".join(f"{fn[:-10]} {im.shape[1]}x{im.shape[0]}" for fn, im in files.items())
             + f" | escape_line {seam} | sign blank (lettered at runtime, U-104) | {time.time() - t0:.1f}s | peak {peak_mb()}MB")


def do_ui_set(entry, preview):
    """B-151 (from B-146; contract 11.6): ui/panels/{pause,settings,inventory,sign,scroll} as 9-slice PNGs with "slice" in
    the json, ui/titlecards/{earth,mars,mercury} (<= 1920x540), ui/hud/film_switch (parts off / on), fakegp + numpy;
    the checks raise inside export() before anything is written; the review re-renders the preview, stamped."""
    from meridian import fakegp
    t0 = time.time()
    if preview:
        raise AssetError(f"{entry['key']}: no preview mode (python build_ui_v3.py <png>)")
    import build_ui_v3 as UI
    cards = tuple(entry.get("cards", UI.CARDS))          # B-170: a cards-only row ("panels": false) leaves B-151's panels alone
    panels = bool(entry.get("panels", True))
    fakegp.install()                    # an earlier review script in this batch may have restored gp_draw.mat
    try:
        try:
            out = UI.export(ART, ss_card=int(entry.get("card_ss", 4)), cards=cards, panels=panels)
        except Exception:
            for k in UI.keys(cards, panels):
                mark_stale(k, True)
            raise
        note = f"exported {time.strftime('%m-%d %H:%M')}"
        if panels:
            UI.preview(os.path.join(PREVIEW, f"review_{entry.get('review_name', 'b151_ui')}.png"), note=note)
        else:
            UI.preview_cards(os.path.join(PREVIEW, f"review_{entry.get('review_name', 'b170_titlecards')}.png"), art=ART, cards=cards, note=note)
    finally:
        fakegp.restore()
    for k, _w, _h, _n in out:
        mark_stale(k, False)
        if not panels:                 # B-170: one OK line per card
            log_line(f"OK {k} | {_w}x{_h} {_n // 1024}KB + json | peak {peak_mb()}MB")
    mark_stale(entry["key"], False)
    log_line(f"OK {entry['key']} | " + ", ".join(f"{k.split('/', 1)[1]} {w}x{h} {n // 1024}KB" for k, w, h, n in out)
             + f" | {time.time() - t0:.1f}s | peak {peak_mb()}MB")


def do_skilltree_set(entry, preview):
    """B-204 (D-174): the Skill Tree panel kit ui/skilltree/* (the aged 9-slice panel, the round chart, the hub, six branch
    emblems, node frames in three states + ring 5's caps, the select ring, tiling links, the cost tag), fakegp + numpy; the
    checks raise inside export() before anything is written; the review is the 1080p mock-up, stamped."""
    from meridian import fakegp
    t0 = time.time()
    if preview:
        raise AssetError(f"{entry['key']}: no preview mode (python build_skilltree_v3.py <dir>)")
    import build_skilltree_v3 as ST
    fakegp.install()                    # an earlier review script in this batch may have restored gp_draw.mat
    try:
        try:
            out = ST.export(ART)
        except Exception:
            for k in ST.keys():
                mark_stale(k, True)
            raise
        ST.preview(PREVIEW, out=os.path.join(PREVIEW, f"review_{entry.get('review_name', 'b204_skilltree')}.png"),
                   footnote=f"exported {time.strftime('%m-%d %H:%M')}")
    finally:
        fakegp.restore()
    for k, _w, _h, _n in out:
        mark_stale(k, False)
    mark_stale(entry["key"], False)
    log_line(f"OK {entry['key']} | " + ", ".join(f"{k.split('/')[-1]} {w}x{h} {n // 1024}KB" for k, w, h, n in out)
             + f" | {time.time() - t0:.1f}s | peak {peak_mb()}MB")


def do_node_icon_set(entry, preview):
    """B-204: the Skill Tree's node icons icons/nodes/<id> (128x128 + json), LEAD-accepted batches only (the row's "batches",
    default build_icons_nodes_v3.EXPORT_BATCHES); the checks raise before anything is written; the review is each batch's sheet."""
    from meridian import fakegp
    t0 = time.time()
    if preview:
        raise AssetError(f"{entry['key']}: no preview mode (python build_icons_nodes_v3.py <png> <batch>)")
    import build_icons_nodes_v3 as NI
    batches = tuple(entry.get("batches", NI.EXPORT_BATCHES))
    names = [n for b in batches for n in NI.BATCHES[b]]
    fakegp.install()                    # an earlier review script in this batch may have restored gp_draw.mat
    try:
        try:
            out = NI.export(ART, names)
        except Exception:
            for n in names:
                mark_stale(NI.KEY.format(n), True)
            raise
        for b in batches:
            NI.preview(os.path.join(PREVIEW, f"review_b204_node_icons_batch{b}.png"), batch=b, footnote=f"exported {time.strftime('%m-%d %H:%M')}")
    finally:
        fakegp.restore()
    for k, _w, _h, _n in out:
        mark_stale(k, False)
    mark_stale(entry["key"], False)
    log_line(f"OK {entry['key']} | " + ", ".join(f"{k.split('/')[-1]} {n // 1024}KB" for k, _w, _h, n in out)
             + f" | {time.time() - t0:.1f}s | peak {peak_mb()}MB")


def do_icon_set(entry, preview):
    """B-128: v3.1 tile-item icons (icons/<item>/base, 64x64) drawn with fakegp + numpy (no scene);
    the preview sheet doubles as the review."""
    from meridian import fakegp
    t0 = time.time()
    if preview:
        raise AssetError(f"{entry['key']}: the icon set has no preview mode (python build_icons_v3.py <png>)")
    import build_icons_v3 as IC
    fakegp.install()                    # again: an earlier review script in this batch may have restored gp_draw.mat
    try:
        out = IC.export(ART, entry.get("items"))
        IC.preview(os.path.join(PREVIEW, f"review_{entry.get('review_name', 'b128_icons')}.png"))
    finally:
        fakegp.restore()
    for k, _n, _w in out:
        mark_stale(f"icons/{k}/base", False)
    mark_stale(entry["key"], False)
    log_line(f"OK {entry['key']} | " + ", ".join(f"icons/{k} 64x64 {n // 1024}KB" for k, n, _w in out)
             + f" | {time.time() - t0:.1f}s | peak {peak_mb()}MB")


def do_ground_strip_set(entry, preview):
    """B-130: terrain/earth/ground_strip{,_soil,_stone} (GroundStrip.cs: 8 frames 64x152, pivot on the
    ground line, "tile": true), drawn with fakegp + numpy; the accept checks raise inside export();
    review_b130_ground_strips.png = the frames at 3x + the 1x assembled scene on the plains."""
    from meridian import fakegp
    t0 = time.time()
    mod = os.path.splitext(os.path.basename(entry.get("generator", "scripts/build_c2_ground_strip.py")))[0]
    if preview:
        raise AssetError(f"{entry['key']}: no preview mode (python {mod}.py <png>)")
    GS = __import__(mod)                # build_c2_ground_strip (Earth) or build_c2_mars_ground (B-140): sheets / export / main
    if entry.get("planet") and hasattr(GS, "use_planet"):
        if entry.get("part"):           # B-180: build_ground_variants_v3's lips are their own rows (part "lips")
            GS.use_planet(entry["planet"], entry["part"])
        else:
            GS.use_planet(entry["planet"])  # B-175: build_ground_v3 serves every planet's ground set (contract 11.9), one row each
    keys = list(GS.KEYS.values())
    fakegp.install()                    # an earlier review script in this batch may have restored gp_draw.mat
    try:
        S, allw = GS.sheets()
        try:
            out, within, across = GS.export(ART, S)
        except Exception:
            for k in keys:
                mark_stale(k, True)
            raise
        GS.main(os.path.join(PREVIEW, f"review_{entry.get('review_name', 'b130_ground_strips')}.png"), S, allw,
                footnote=f"exported {time.strftime('%m-%d %H:%M')}")
    finally:
        fakegp.restore()
    for k in keys:
        mark_stale(k, False)
    mark_stale(entry["key"], False)
    log_line(f"OK {entry['key']} | " + ", ".join(f"{k.split('/')[2]} {w}x{h} {n // 1024}KB" for k, w, h, n in out)
             + " | joins " + ", ".join(f"{k} {v:.2f}" for k, v in within.items()) + f"/255 | silhouette {across}"
             + f" | {time.time() - t0:.1f}s | peak {peak_mb()}MB")


def do_prop_sheet_set(entry, preview):
    """B-131 (D-117): props/common/{landing_pad, shelter_wall, shelter_door, smelter, storage_crate, lamp} as v3.1
    sheets (colour + json only, one sheet <= 512^2 each), drawn with fakegp + numpy. The export removes each key's v2
    model files (.glb + normal/mask/emission; UNITY deletes the .meta files, D-016). The set entry exports all six +
    review_b131_props.png; a single prop row (`prop_sheet`) exports that prop only. The row's `generator` names the
    module (default build_props_common_v3; build_props_mars_v3 has the same API: PROPS, KEY, render_all, export, main).
    A row with both flags exports its one prop and writes its review (props/mars/tube_mound, D-126)."""
    from meridian import fakegp
    t0 = time.time()
    mod = os.path.splitext(os.path.basename(entry.get("generator", "scripts/build_props_common_v3.py")))[0]
    if preview:
        raise AssetError(f"{entry['key']}: no preview mode (python {mod}.py <png>)")
    PC = __import__(mod)
    names = [entry["key"].split("/")[2]] if entry.get("prop_sheet") else list(PC.PROPS)
    keys = [PC.KEY.format(n) for n in names]
    fakegp.install()                    # an earlier review script in this batch may have restored gp_draw.mat
    try:
        imgs, widths = PC.render_all()
        try:
            out, jn, removed = PC.export(ART, imgs, names)
        except Exception:
            for k in keys:
                mark_stale(k, True)
            raise
        if entry.get("prop_sheet_set"):
            stamps = [os.path.join(ART, *PC.KEY.format(n).split("/")) + "_color.png" for n in names]
            review_fn = getattr(PC, entry.get("review_fn", "main"))     # e.g. props/mars/tube_mound: den_review (the lurker behind it)
            review_fn(os.path.join(PREVIEW, f"review_{entry.get('review_name', 'b131_props')}.png"), imgs, widths, stamp_paths=stamps)
    finally:
        fakegp.restore()
    for k in keys:
        mark_stale(k, False)
    mark_stale(entry["key"], False)
    log_line(f"OK {entry['key']} | " + ", ".join(f"{k.split('/')[2]} {w}x{h} {n // 1024}KB" for k, w, h, n in out)
             + " | joins " + ", ".join(f"{k} {v:.2f}" for k, v in jn.items()) + "/255"
             + f" | removed {len(removed)} v2 files ({', '.join(sorted({os.path.basename(p) for p in removed})) or '-'})"
             + f" | {time.time() - t0:.1f}s | peak {peak_mb()}MB")


def do_sun_rig(entry, preview):
    """B-137 (D-123): planets/sun/disc_rig_color.png (body, one flame tongue, corona, two prominences at 0.5x) +
    disc_rig.json, numpy only (build_sun_v3.export); review = the Sun assembled at the game's size, stamped."""
    t0 = time.time()
    if preview:
        raise AssetError(f"{entry['key']}: no preview mode (python build_sun_v3.py <dir> --parts)")
    import build_sun_v3 as SUN
    out = os.path.join(PREVIEW, f"review_{entry.get('review_name', 'b137_sun_rig')}.png")
    try:
        info = SUN.export(ART, out)
    except Exception:
        mark_stale(entry["key"], True)
        raise
    mark_stale(entry["key"], False)
    log_line(f"OK {entry['key']} | sheet {info['sheet'][0]}x{info['sheet'][1]} {info['bytes'] // 1024}KB | parts "
             + ", ".join(f"{k} {w}x{h}" for k, (w, h) in info["parts"].items())
             + f" | ink on screen outer {info['ink'][0][0]:.1f}-{info['ink'][0][1]:.1f} inner {info['ink'][1][0]:.1f}-{info['ink'][1][1]:.1f}px"
             + f" | review {os.path.basename(out)} | {time.time() - t0:.1f}s | peak {peak_mb()}MB")


def do_asset(entry, preview):
    if entry.get("sun_rig"):            # the painted Sun as parts (B-137, D-123)
        return do_sun_rig(entry, preview)
    if entry.get("prop_sheet_set") or entry.get("prop_sheet"):   # v3.1 camp props (B-131, D-117)
        return do_prop_sheet_set(entry, preview)
    if entry.get("ground_strip_set"):   # v3.1 Earth ground strips (B-130)
        return do_ground_strip_set(entry, preview)
    if entry.get("icon_set"):           # v3.1 tile-item icons (B-128)
        return do_icon_set(entry, preview)
    if entry.get("ui_set"):             # v3.1 C3 UI: panels, title cards, the film switch (B-151)
        return do_ui_set(entry, preview)
    if entry.get("skilltree_set"):      # the Skill Tree panel kit (B-204)
        return do_skilltree_set(entry, preview)
    if entry.get("node_icon_set"):      # the Skill Tree's node icons (B-204), by accepted batch
        return do_node_icon_set(entry, preview)
    if entry.get("disc_set"):           # v3 §11.5 planet discs (B-119, D-098)
        return do_disc_set(entry, preview)
    if entry.get("space_starfield"):    # v3 §11.4 space starfield + nebula cards (B-120)
        return do_space_starfield(entry, preview)
    if entry.get("hud"):                # v3 §11.6 HUD gauges + Escape Line (B-121)
        return do_hud(entry, preview)
    if entry.get("painted_bg"):         # v3 §11.4 painted layers (B-114)
        return do_painted_bg(entry, preview)
    if entry.get("palette_strip"):
        return do_palette_strip(entry, preview)
    if entry.get("style") == "v3":      # contract v3.0 §11 cartoon assets (B-110)
        return do_v3_rigset(entry, preview) if entry.get("rigset") else do_v3_sheet(entry, preview)
    if entry.get("model"):
        return do_model(entry, preview)
    if entry.get("deck_plane"):
        return do_deck_plane(entry, preview)
    if entry.get("flora_atlas"):
        return do_flora_atlas(entry, preview)
    if entry.get("skydome"):
        return do_skydome(entry, preview)
    if entry.get("terrain3d"):
        return do_terrain3d(entry, preview)
    t0 = time.time()
    maps, clips, wh, entry = produce(entry, preview)
    problems, seam = check(entry, maps, clips, wh, preview)
    if problems:
        if preview:  # previews are for diagnosis: write them anyway, still fail
            write_outputs(entry, maps, clips, wh, preview)
        raise AssetError(f"{entry['key']}: " + "; ".join(problems))
    sizes = write_outputs(entry, maps, clips, wh, preview)
    if not preview:
        mark_stale(entry["key"], False)
    mode = "PREVIEW" if preview else "OK"
    log_line(f"{mode} {entry['key']} | {', '.join(sizes)}{' | ' + seam if seam else ''} "
             f"| {time.time() - t0:.1f}s | peak {peak_mb()}MB")


def main(argv):
    ap = argparse.ArgumentParser(prog="render.py")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--asset")
    g.add_argument("--category")
    g.add_argument("--all", action="store_true")
    g.add_argument("--sheet", help="a v3 sheet or rig set key (contract §11); same as --asset for style v3")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args(argv)
    if args.sheet:
        args.asset = args.sheet
    _man, assets = load_manifest()
    chosen = select(assets, args)
    target = args.asset or args.category or "all"
    if not chosen:
        log_line(f"OK {target} | 0 assets selected")
        return 0
    failed = 0
    for entry in chosen:
        try:
            do_asset(entry, args.preview)
        except AssetError as e:
            failed += 1
            log_line(f"FAIL {e}")
            if not args.preview:
                mark_stale(entry["key"], True)
        except Exception as e:  # noqa: BLE001 - any failure is one line + nonzero exit
            failed += 1
            traceback.print_exc()
            log_line(f"FAIL {entry['key']}: {type(e).__name__}: {e}")
            if not args.preview:
                mark_stale(entry["key"], True)
    shutil.rmtree(WORK, ignore_errors=True)
    if failed:
        log_line(f"FAIL {target} | {failed}/{len(chosen)} assets failed")
        return 1
    log_line(f"OK {target} | {len(chosen)} assets")
    return 0


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    try:
        code = main(argv)
    except AssetError as e:
        log_line(f"FAIL {e}")
        code = 1
    except SystemExit as e:  # argparse
        code = e.code if isinstance(e.code, int) else 2
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        log_line(f"FAIL {type(e).__name__}: {e}")
        code = 1
    sys.stdout.flush()
    os._exit(code)
