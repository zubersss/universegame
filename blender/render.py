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
        hit = [a for a in assets if a["key"] == args.asset]
        if not hit:
            raise AssetError(f"unknown asset key '{args.asset}' (not in blender/manifest.json)")
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


def open_source(entry, preview):
    import bpy
    src = os.path.join(HERE, entry["source"])
    if not os.path.isfile(src):
        build = entry.get("build")
        if not build:
            raise AssetError(f"source missing: {entry['source']}")
        run_build(entry)
        if not os.path.isfile(src):
            raise AssetError(f"build {build} did not write {entry['source']}")
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
    mod.build(os.path.join(HERE, entry["source"]))


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
    sheet = post.contact_sheet(maps, entry.get("tileable"), tile_img=tile_image(entry, maps["color"]))
    os.makedirs(PREVIEW, exist_ok=True)
    pngio.write_png(os.path.join(PREVIEW, f"{key.replace('/', '__')}_contact.png"), sheet)
    return sizes


def do_asset(entry, preview):
    t0 = time.time()
    maps, clips, wh, entry = produce(entry, preview)
    problems, seam = check(entry, maps, clips, wh, preview)
    if problems:
        if preview:  # previews are for diagnosis: write them anyway, still fail
            write_outputs(entry, maps, clips, wh, preview)
        raise AssetError(f"{entry['key']}: " + "; ".join(problems))
    sizes = write_outputs(entry, maps, clips, wh, preview)
    mode = "PREVIEW" if preview else "OK"
    log_line(f"{mode} {entry['key']} | {', '.join(sizes)}{' | ' + seam if seam else ''} "
             f"| {time.time() - t0:.1f}s | peak {peak_mb()}MB")


def main(argv):
    ap = argparse.ArgumentParser(prog="render.py")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--asset")
    g.add_argument("--category")
    g.add_argument("--all", action="store_true")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args(argv)
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
        except Exception as e:  # noqa: BLE001 - any failure is one line + nonzero exit
            failed += 1
            traceback.print_exc()
            log_line(f"FAIL {entry['key']}: {type(e).__name__}: {e}")
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
