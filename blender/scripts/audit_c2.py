"""B-173: the C2 exit audit (Bible §12 C2: "§9.7 on every asset"). One stamped contact sheet per planet, read back from
Assets/_Game/Art/ at 1x with numpy only (every v3 file was written by meridian.pngio; no blender.exe, no export):

  sets          each painted set (backgrounds/<p>/<set>/<set>.json): its layers stacked bottom-aligned, at 0.25x
  strips        floe strips: cap_left + tiles 0-3 + cap_right; ground strips: their 8 tiles side by side (1x)
  flora         the rig set assembled at rest (bones chained, parts in bone order), plants side by side (1x)
  props         frame 0 (1x)
  creatures     the idle clip's first frame (1x); a Grand rig set assembled at rest at 0.25x
  ui            the palette strip (x24) and the title card (1x)

Each tile carries its measured ink widths (the export log's last measured line for the key when it has one, else a raster
estimate: the per-pixel min of the horizontal / vertical run of ink-coloured pixels, p25-p75) and its palette hit
(meridian.v3.palette_hits on the sheet; painted sets are watercolour and skip it). Then every key under the planet's
folders that is still v2 (a .glb, a _normal / _mask / _emission map, or a json without "style": "v3") and every colour
PNG with no json of its own.

  python -I audit_c2.py <planet> [<planet> ...]    -> blender/preview/audit_c2_<planet>.png (stamped) + one line per planet
                                                      in coordination/reports/blender/audit_c2.md (replacing that planet's)
"""
import glob
import json
import os
import re
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from meridian import pngio, v3  # noqa: E402
import review  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
ART = os.path.join(ROOT, "Assets", "_Game", "Art")
PREVIEW = os.path.join(ROOT, "blender", "preview")
REPORT = os.path.join(ROOT, "coordination", "reports", "blender", "audit_c2.md")
CATS = ("backgrounds", "terrain", "flora", "props", "creatures")
V2_MAPS = ("_normal.png", "_mask.png", "_emission.png")
W = 2100
PAPER = (np.asarray(review.PAPER) * 255).astype(np.uint8)
LABEL = (255, 247, 217)


# ---------------------------------------------------------------- scan

def planet_roots(p):
    roots = [os.path.join(ART, c, p) for c in CATS] + [d for c in CATS for d in glob.glob(os.path.join(ART, c, p + "_*"))]
    return [r for r in roots if os.path.isdir(r)]


def rel(path):
    return os.path.relpath(path, ART).replace("\\", "/")


def scan(p):
    """-> (v3 [(key, json path, meta)], v2 stems [rel], unpaired colour PNGs [rel])."""
    v3_keys, v2, unpaired = [], set(), []
    extra = [os.path.join(ART, "ui", "palettes", p, "strip.json"), os.path.join(ART, "ui", "titlecards", p + ".json")]
    for js in extra:
        if os.path.isfile(js):
            meta = json.load(open(js, encoding="utf-8"))
            v3_keys.append((meta.get("key", rel(js)[:-5]), js, meta))
    for root in planet_roots(p):
        for d, _subs, files in os.walk(root):
            files = [f for f in files if not f.endswith(".meta")]
            set_layers = False
            for f in files:
                path = os.path.join(d, f)
                if f.endswith(".json"):
                    try:
                        meta = json.load(open(path, encoding="utf-8"))
                    except ValueError:
                        v2.add(rel(path)[:-5])
                        continue
                    if meta.get("style") == "v3":
                        v3_keys.append((meta.get("key", rel(path)[:-5]), path, meta))
                        set_layers = set_layers or "layers" in meta
                    else:
                        v2.add(rel(path)[:-5])
                elif f.endswith(".glb"):
                    v2.add(rel(path)[:-4])
                elif f.endswith(V2_MAPS):
                    v2.add(re.sub(r"_(normal|mask|emission)\.png$", "", rel(path)))
            for f in files:
                if f.endswith("_color.png"):
                    stem = f[:-len("_color.png")]
                    if os.path.isfile(os.path.join(d, stem + ".json")) or (set_layers and re.fullmatch(r"layer\d", stem)):
                        continue
                    if rel(os.path.join(d, stem)) not in v2:
                        unpaired.append(rel(os.path.join(d, f)))
    v3_keys.sort(key=lambda t: t[0])
    return v3_keys, sorted(v2), sorted(unpaired)


# ---------------------------------------------------------------- measures

_LOG = None


def logged_ink():
    """{key: 'outer a-b / inner c-d'} from the newest OK line per key in logs/blender_*.log."""
    global _LOG
    if _LOG is None:
        _LOG = {}
        for lf in sorted(glob.glob(os.path.join(ROOT, "logs", "blender_*.log"))):
            for ln in open(lf, encoding="utf-8", errors="replace"):
                m = re.search(r" OK (\S+) \|.*?ink outer ([\d.]+)-([\d.]+)px inner ([\d.]+)-([\d.]+)px", ln)
                if m:
                    _LOG[m.group(1)] = f"{m.group(2)}-{m.group(3)} / {m.group(4)}-{m.group(5)} px (export log)"
    return _LOG


def _runs(M):
    """Per-pixel length of the horizontal run of True containing it."""
    H, Wd = M.shape
    p = np.zeros((H, Wd + 2), np.int8)
    p[:, 1:-1] = M
    d = np.diff(p, axis=1)
    s = np.argwhere(d == 1)
    e = np.argwhere(d == -1)
    lens = (e[:, 1] - s[:, 1]).astype(np.int32)
    acc = np.zeros((H, Wd + 1), np.int32)
    np.add.at(acc, (s[:, 0], s[:, 1]), lens)
    np.add.at(acc, (e[:, 0], e[:, 1]), -lens)
    return np.cumsum(acc, axis=1)[:, :Wd]


def raster_ink(rgba):
    ink = np.array(v3.hex_rgb(v3.INK), np.int16)
    M = (rgba[..., 3] == 255) & (np.abs(rgba[..., :3].astype(np.int16) - ink).max(-1) <= 24)
    if M.sum() < 20:
        return "no ink found"
    w = np.minimum(_runs(M), _runs(M.T).T)[M]
    return f"raster p25-p75 {np.percentile(w, 25):.0f}-{np.percentile(w, 75):.0f} px"


def palette(rgba, planet, tol=6):
    """meridian.v3.palette_hits' measure (solid interior pixels: alpha 255 and 3x3 uniform; a palette colour or one of its
    shadow tones within tol) on packed colours, comparing only the unique ones by count: v3's version builds a pixels x
    palette x 3 array (~0.5 GB on a 2040x1256 creature sheet), over the 300 MB lock-free cap."""
    a = rgba[..., 3] == 255
    c = (rgba[..., 0].astype(np.int32) << 16) | (rgba[..., 1].astype(np.int32) << 8) | rgba[..., 2].astype(np.int32)
    same = a.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                same &= (np.roll(np.roll(c, dy, 0), dx, 1) == c) & np.roll(np.roll(a, dy, 0), dx, 1)
    vals, counts = np.unique(c[same], return_counts=True)
    if len(vals) == 0:
        return 1.0, []
    rgb = np.stack([(vals >> 16) & 255, (vals >> 8) & 255, vals & 255], -1)
    pal = np.array([v3.hex_rgb(v) for v in v3.palette_with_shadows(planet).values()], np.int32)
    d = np.abs(rgb[:, None, :] - pal[None, :, :]).max(-1).min(-1)
    ok = d <= tol
    order = np.argsort(-counts[~ok])
    off = [v3.rgb_hex(rgb[~ok][i]) for i in order[:5]]
    return float(counts[ok].sum() / counts.sum()), off


# ---------------------------------------------------------------- tiles

def frame_of(sheet, meta, i):
    fw, fh, g, cols = meta["frame_width"], meta["frame_height"], meta.get("gutter", 4), meta["columns"]
    r, c = divmod(i, cols)
    return sheet[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw]


def hcat(frames, gap=2):
    h = max(f.shape[0] for f in frames)
    out = np.zeros((h, sum(f.shape[1] for f in frames) + gap * (len(frames) - 1), 4), np.uint8)
    x = 0
    for f in frames:
        out[h - f.shape[0]:, x:x + f.shape[1]] = f
        x += f.shape[1] + gap
    return out


def down(rgba, k):
    """Premultiplied box downscale by an integer k."""
    H, Wd = (rgba.shape[0] // k) * k, (rgba.shape[1] // k) * k
    f = rgba[:H, :Wd].astype(np.float32) / 255.0
    f[..., :3] *= f[..., 3:4]
    s = f.reshape(H // k, k, Wd // k, k, 4).mean(axis=(1, 3))
    a = s[..., 3:4]
    s[..., :3] = np.where(a > 1e-6, s[..., :3] / np.maximum(a, 1e-6), 0)
    return np.clip(np.rint(s * 255), 0, 255).astype(np.uint8)


def over_u8(dst, src, x, y):
    h, w = src.shape[:2]
    h, w = min(h, dst.shape[0] - y), min(w, dst.shape[1] - x)
    if h <= 0 or w <= 0:
        return
    s = src[:h, :w].astype(np.float32)
    a = s[..., 3:4] / 255.0
    d = dst[y:y + h, x:x + w].astype(np.float32)
    dst[y:y + h, x:x + w] = np.clip(np.rint(s[..., :3] * a + d * (1 - a)), 0, 255).astype(np.uint8)


def assemble_rig(sheet, meta, plant, scale=1):
    """A rig plant at rest from its raster parts: bone offsets chained from the root, each part's pivot on its bone,
    drawn in bone / slot order (a slot that replaces its bone's part draws its first swap instead)."""
    SH = sheet.shape[0]
    ppu = meta.get("ppu", 64)
    parts = {p_["name"]: p_ for p_ in meta["parts"]}
    world = {}
    for b in plant["bones"]:
        ox, oz = b.get("offset_m", [0.0, 0.0])
        px_, pz_ = world[b["parent"]] if b.get("parent") else (0.0, 0.0)
        world[b["name"]] = (px_ + ox, pz_ + oz)
    replaced = {s["bone"] for s in plant.get("slots", []) if s.get("replaces_part")}
    items = [(b["order"], b["part"], world[b["name"]]) for b in plant["bones"] if b["name"] not in replaced]
    for s in plant.get("slots", []):
        sw = plant.get("swaps", {}).get(s["slot"]) or []
        if sw:
            bx, bz = world[s["bone"]]
            ox, oz = s.get("offset_m", [0.0, 0.0])
            items.append((s["order"], sw[0], (bx + ox, bz + oz)))
    placed = []
    for _o, name, (wx, wz) in sorted(items, key=lambda t: t[0]):
        p_ = parts.get(name)
        if p_ is None:
            continue
        x, y, w, h = p_["rect"]
        img = sheet[SH - (y + h):SH - y, x:x + w]
        left = wx * ppu - p_["pivot"][0] * w
        top = -(wz * ppu) - (1 - p_["pivot"][1]) * h
        placed.append((img, left, top))
    if not placed:
        return np.zeros((8, 8, 4), np.uint8)
    x0 = min(l_ for _i, l_, _t in placed)
    y0 = min(t_ for _i, _l, t_ in placed)
    x1 = max(l_ + i.shape[1] for i, l_, _t in placed)
    y1 = max(t_ + i.shape[0] for i, _l, t_ in placed)
    canvas = np.zeros((int(np.ceil(y1 - y0)) + 2, int(np.ceil(x1 - x0)) + 2, 4), np.uint8)
    for img, l_, t_ in placed:
        xx, yy = int(round(l_ - x0)), int(round(t_ - y0))
        sub = canvas[yy:yy + img.shape[0], xx:xx + img.shape[1]]
        a = img[:sub.shape[0], :sub.shape[1], 3:4].astype(np.float32) / 255.0
        sub[..., :3] = np.clip(np.rint(img[:sub.shape[0], :sub.shape[1], :3] * a + sub[..., :3] * (1 - a)), 0, 255)
        sub[..., 3:] = np.maximum(sub[..., 3:], img[:sub.shape[0], :sub.shape[1], 3:])
    return down(canvas, scale) if scale > 1 else canvas


def tile_for(key, js, meta, planet):
    """-> (section, rgba uint8, caption)."""
    d = os.path.dirname(js)
    stem = os.path.basename(js)[:-5]
    png = os.path.join(d, stem + "_color.png")
    ink = logged_ink().get(key)
    if "layers" in meta:                                        # a painted set
        Wl = 2048
        H = max(l_["height_px"] for l_ in meta["layers"])
        canvas = np.zeros((H, Wl, 4), np.uint8)
        for l_ in meta["layers"]:
            img = pngio.read_png_np(os.path.join(d, f"layer{l_['n']}_color.png"))
            over = canvas[H - img.shape[0]:, :img.shape[1]]
            a = img[..., 3:4].astype(np.float32) / 255.0
            over[..., :3] = np.clip(np.rint(img[..., :3] * a + over[..., :3] * (1 - a)), 0, 255)
            over[..., 3:] = np.maximum(over[..., 3:], img[..., 3:])
            del img
        return "sets", down(canvas, 4), f"{len(meta['layers'])} layers at 0.25x; painted (no palette check)"
    if meta.get("palette") is True:                             # a strip (a title card says "palette": "<planet>")
        strip = pngio.read_png_np(png)
        big = np.repeat(np.repeat(strip, 24, axis=0), 24, axis=1)
        return "ui", big, f"palette strip x24 ({len(meta.get('colors', []))} colours)"
    sheet = pngio.read_png_np(png)
    hit, off = palette(sheet, planet)
    pal = f"palette {hit * 100:.1f}%" + (f" off {' '.join(off[:3])}" if hit < 0.98 and off else "")
    ink = ink or raster_ink(sheet)
    if "width" in meta and "lettering" in meta:                 # the title card
        return "ui", sheet, f"title card 1x; ink {ink}; {pal}"
    if "parts" in meta:                                         # a rig set
        plants = meta.get("plants", [])
        grand = any(p_.get("grand") for p_ in plants)
        k = 4 if grand else 1
        imgs = [assemble_rig(sheet, meta, p_, k) for p_ in plants]
        if grand and sum(i.shape[1] for i in imgs) > W - 40:          # a Grand rig wider than the sheet at 0.25x: 0.125x
            k = 8
            imgs = [assemble_rig(sheet, meta, p_, k) for p_ in plants]
        return ("creatures" if key.startswith("creatures/") else "flora"), hcat(imgs, 12), \
            f"{len(plants)} rig(s) at rest {('0.25x' if k == 4 else '0.125x') if grand else '1x'}, {len(meta['parts'])} parts; ink {ink}; {pal}"
    if "frame_width" in meta:
        n = meta["frames"]
        if meta.get("contract", "").startswith("v3.2 11.9"):         # B-175's ground band set: its own section
            fr = hcat([frame_of(sheet, meta, i) for i in range(n)], 4) if n > 1 else frame_of(sheet, meta, 0).copy()
            return "ground", (down(fr, 2) if fr.shape[1] > 600 else fr), f"{n} frame(s){' 0.5x' if fr.shape[1] > 600 else ' 1x'}; ink {ink}; {pal}"
        if meta.get("caps"):
            c = meta["caps"]
            img = hcat([frame_of(sheet, meta, c["cap_left"])] + [frame_of(sheet, meta, i) for i in range(4)] +
                       [frame_of(sheet, meta, c["cap_right"])], 0)
            return "strips", img, f"cap + 4 tiles + cap 1x; ink {ink}; {pal}"
        if meta.get("tile"):
            return "strips", hcat([frame_of(sheet, meta, i) for i in range(n)], 0), f"{n} tiles 1x; ink {ink}; {pal}"
        idle = next((a for a in meta.get("animations", []) if a["name"] == "idle"), None)
        i0 = idle["start"] if idle else 0
        sec = "creatures" if key.startswith("creatures/") else ("props" if key.startswith("props/") else "other")
        return sec, frame_of(sheet, meta, i0).copy(), f"{'idle' if idle else 'frame'} {i0} 1x of {n}; ink {ink}; {pal}"
    return "other", down(sheet, 2), f"unknown layout at 0.5x; {pal}"


# ---------------------------------------------------------------- the sheet

SECTIONS = [("sets", "painted sets"), ("ground", "ground band set (b-175, contract v3.2 11.9)"), ("strips", "ground / floe strips"), ("flora", "flora rig set"), ("props", "props"),
            ("creatures", "creatures (idle 1x; Grand rigs 0.25x)"), ("ui", "palette + title card"), ("other", "other")]


def audit(planet):
    t0 = time.time()
    keys, v2, unpaired = scan(planet)
    sky = np.array(v3.hex_rgb(v3.PALETTES[planet]["sky"]), np.uint8)
    tiles, outl = [], []
    for key, js, meta in keys:
        try:
            sec, img, cap = tile_for(key, js, meta, planet)
        except Exception as e:  # noqa: BLE001
            sec, img, cap = "other", np.zeros((24, 24, 4), np.uint8), f"UNREADABLE: {type(e).__name__}: {e}"[:120]
            outl.append(f"{key} unreadable")
        if "palette " in cap:
            m = re.search(r"palette ([\d.]+)%", cap)
            if m and float(m.group(1)) < 98.0:
                outl.append(f"{key} palette {m.group(1)}%")
        if "raster p25-p75" in cap and not key.startswith("ui/titlecards/"):   # the cards' lettering is solid ink, not line work
            m = re.search(r"raster p25-p75 (\d+)-(\d+) px", cap)
            if m and (int(m.group(2)) > 4 or int(m.group(1)) < 1):
                outl.append(f"{key} ink {m.group(1)}-{m.group(2)} px")
        tiles.append((sec, key, img, cap))
    # layout: sections in order, tiles flowing left to right
    rows, y = [], 40
    for sec, title in SECTIONS:
        st = [t for t in tiles if t[0] == sec]
        if not st:
            continue
        rows.append(("title", title, y))
        y += 26
        x, rh = 8, 0
        for _s, key, img, cap in st:
            h, w = img.shape[:2]
            cw = max(w, 8 * len(key.split("/", 1)[1]) + 8, 4 * min(len(cap), 120) + 8)
            cw = min(cw, W - 16)
            if x + cw > W - 8 and x > 8:
                x, y, rh = 8, y + rh, 0
            rows.append(("tile", (key, img, cap, x, y), 0))
            x += cw + 16
            rh = max(rh, h + 46)
        y += rh + 10
    foot = ["v2 keys left (" + str(len(v2)) + "): " + (", ".join(v2) if v2 else "none"),
            "colour PNGs with no json (" + str(len(unpaired)) + "): " + (", ".join(unpaired) if unpaired else "none"),
            "outliers: " + (", ".join(outl) if outl else "none")]
    wrapped = []
    for ln in foot:
        while len(ln) > 250:
            cut = ln.rfind(", ", 0, 250)
            cut = cut if cut > 0 else 250
            wrapped.append(ln[:cut + 1])
            ln = "    " + ln[cut + 2:]
        wrapped.append(ln)
    H = y + 30 + 16 * len(wrapped) + 30
    canvas = np.empty((H, W, 3), np.uint8)
    canvas[:] = PAPER
    review.draw(canvas, f"b-173 c2 audit: {planet}  ({len(keys)} v3 keys, {len(v2)} v2 keys left, {len(unpaired)} unpaired pngs) "
                        f"read back from assets/_game/art at 1x unless marked", 6, 8, LABEL)
    for kind, a, b in rows:
        if kind == "title":
            review.draw(canvas, a, 6, b, LABEL)
            continue
        key, img, cap, x, yy = a
        h, w = img.shape[:2]
        canvas[yy + 16:yy + 16 + h, x:x + min(w, W - x)] = sky
        over_u8(canvas, img, x, yy + 16)
        review.draw(canvas, key.split("/", 1)[1], x, yy, LABEL, scale=2)
        review.draw(canvas, cap[:120], x, yy + 16 + h + 4, LABEL, scale=1)
    for i, ln in enumerate(wrapped):
        review.draw(canvas, ln, 6, y + 16 + 16 * i, LABEL, scale=1)
    newest = max((os.path.getmtime(js) for _k, js, _m in keys), default=0)
    review.draw(canvas, time.strftime("%m-%d %H:%M") + " audit; newest v3 json " + time.strftime("%m-%d %H:%M", time.localtime(newest)),
                2, H - 16, LABEL)
    out = os.path.join(PREVIEW, f"audit_c2_{planet}.png")
    rgba = np.empty((H, W, 4), np.uint8)
    rgba[..., :3] = canvas
    rgba[..., 3] = 255
    pngio.write_png(out, rgba)
    line = (f"- {planet} ({time.strftime('%m-%d %H:%M')}): {len(keys)} v3 keys, {len(v2)} v2 keys left"
            f"{' (' + ', '.join(v2) + ')' if v2 else ''}, {len(unpaired)} colour PNGs with no json"
            f"{' (' + ', '.join(unpaired) + ')' if unpaired else ''}; outliers: {', '.join(outl) if outl else 'none'}; "
            f"sheet blender/preview/audit_c2_{planet}.png")
    print(f"{planet}: {len(keys)} v3, {len(v2)} v2, {len(unpaired)} unpaired, {len(outl)} outliers, {W}x{H}, {time.time() - t0:.1f}s")
    return line


def write_report(lines):
    head = ("# B-173: the C2 exit audit (one line per planet; the sheets are blender/preview/audit_c2_<planet>.png, "
            "built by blender/scripts/audit_c2.py from Assets/_Game/Art)\n\n")
    old = {}
    if os.path.isfile(REPORT):
        for ln in open(REPORT, encoding="utf-8"):
            m = re.match(r"- (\w+) \(", ln)
            if m:
                old[m.group(1)] = ln.rstrip("\n")
    for ln in lines:
        old[re.match(r"- (\w+) \(", ln).group(1)] = ln
    order = ["earth", "mars", "mercury", "venus", "jupiter", "saturn", "uranus", "neptune"]
    with open(REPORT, "w", encoding="utf-8", newline="\n") as f:
        f.write(head + "\n".join(old[p] for p in order if p in old) + "\n")


if __name__ == "__main__":
    write_report([audit(p) for p in sys.argv[1:]])
