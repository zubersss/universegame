"""Review composites for exported art, stamped so nobody reviews a stale image (LEAD, B-026).

Every panel gets a stamp in its corner: the source PNG's modification time and the first 8 hex
of its SHA-256, plus a red STALE banner when render.py listed the key in preview/STALE.txt
(the latest render failed, so the file on disk is from an earlier one).

  blender --background --factory-startup --python blender/review.py -- stack <art dir> <out.png>
      parallax layers layer0..2 composited, 2x wrap, half size (backgrounds)
  blender --background --factory-startup --python blender/review.py -- frames <art dir> <variant> <out.png> 0,8,17,27
      chosen sheet frames: flat albedo row + relit row (creatures, fx)
"""
import hashlib
import json
import os
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))
import numpy as np  # noqa: E402

from meridian import pngio, post  # noqa: E402

STALE = os.path.join(HERE, "preview", "STALE.txt")
ART = os.path.normpath(os.path.join(HERE, "..", "Assets", "_Game", "Art"))

# 3x5 bitmap glyphs, rows top to bottom.
FONT = {
    "0": "111101101101111", "1": "010110010010111", "2": "111001111100111", "3": "111001111001111",
    "4": "101101111001001", "5": "111100111001111", "6": "111100111101111", "7": "111001001001001",
    "8": "111101111101111", "9": "111101111001111", "a": "010101111101101", "b": "110101110101110",
    "c": "111100100100111", "d": "110101101101110", "e": "111100110100111", "f": "111100110100100",
    ":": "000010000010000", "-": "000000111000000", " ": "000000000000000", "S": "111100111001111",
    "T": "111010010010010", "A": "010101111101101", "L": "100100100100111", "E": "111100110100111",
}


# v3 review sheets (§11.7) print words: the rest of the alphabet (case-insensitive) + punctuation.
FONT.update({
    "g": "011100101101011", "h": "101101111101101", "i": "111010010010111", "j": "001001001101010",
    "k": "101101110101101", "l": "100100100100111", "m": "101111111101101", "n": "110101101101101",
    "o": "010101101101010", "p": "110101110100100", "q": "010101101110011", "r": "110101110101101",
    "s": "011100010001110", "t": "111010010010010", "u": "101101101101111", "v": "101101101101010",
    "w": "101101111111101", "x": "101101010101101", "y": "101101010010010", "z": "111001010100111",
    ".": "000000000000010", ",": "000000000010100", "/": "001001010100100", "(": "010100100100010",
    ")": "010001001001010", "+": "000010111010000", "=": "000111000111000", "#": "101111101111101",
    "[": "110100100100110", "]": "011001001001011", "%": "101001010100101", "'": "010010000000000",
    "?": "111001010000010", "!": "010010010000010", "_": "000000000000111", ">": "100010001010100",
    "<": "001010100010001", "*": "101010101000000", '"': "101101000000000", ";": "000010000010100",
    "~": "000011110000000", "^": "010101000000000", "|": "010010010010010",
})


def glyph(ch):
    return FONT.get(ch) or FONT.get(ch.lower()) or FONT[" "]


def stale_keys():
    if not os.path.isfile(STALE):
        return set()
    with open(STALE, encoding="utf-8") as fh:
        return {ln.split(" | ")[0] for ln in fh.read().splitlines() if ln.strip()}


def key_of(path):
    """Art path -> manifest key (cat/name/variant)."""
    rel = os.path.relpath(path, ART).replace("\\", "/")
    cat, name, fname = rel.split("/")[:3]
    variant = fname.rsplit("_", 1)[0]
    return f"{cat}/{name}/{variant}"


def stamp_text(path):
    with open(path, "rb") as fh:
        h = hashlib.sha256(fh.read()).hexdigest()[:8]
    t = time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(path)))
    return f"{t} {h}"


def draw(img, text, x, y, color, scale=2):
    """Blit `text` into float RGB img at (x, y) top-left, on a dark backing box."""
    w = (len(text) * 4 + 1) * scale
    h = 7 * scale
    img[y:y + h, x:x + w] = img[y:y + h, x:x + w] * 0.25
    for i, ch in enumerate(text):
        g = glyph(ch)
        for r in range(5):
            for c in range(3):
                if g[r * 3 + c] == "1":
                    yy, xx = y + (r + 1) * scale, x + (i * 4 + c + 1) * scale
                    img[yy:yy + scale, xx:xx + scale] = color


def stamp(img, path, stale):
    """Stamp time + hash bottom-left; STALE banner top-left when the latest render failed."""
    H = img.shape[0]
    draw(img, stamp_text(path), 2, H - 16, (1.0, 1.0, 0.85))
    if key_of(path) in stale:
        draw(img, "STALE", 2, 2, (1.0, 0.15, 0.1), scale=4)


def write(out, rgb):
    pngio.write_png(out, np.dstack([pngio.to_u8(np.clip(rgb, 0, 1)), np.full(rgb.shape[:2], 255, np.uint8)]))


def stack(d, out):
    stale = stale_keys()
    acc, panels = None, []
    for i in range(3):
        p = os.path.join(d, f"layer{i}_color.png")
        img = pngio.read_png(p)
        acc = img[..., :3].copy() if acc is None else acc * (1 - img[..., 3:4]) + img[..., :3] * img[..., 3:4]
        panels.append(p)
    acc = np.hstack([acc, acc])[::2, ::2].copy()              # 2x wrap, half size
    for i, p in enumerate(panels):                              # one stamp per layer, stacked up
        sub = acc[: acc.shape[0] - 18 * (2 - i)]
        stamp(sub, p, stale)
    write(out, acc)
    print("REVIEW stack ok", out)


def frames(d, v, out, pick):
    stale = stale_keys()
    cpath = os.path.join(d, f"{v}_color.png")
    meta = json.load(open(os.path.join(d, f"{v}.json"), encoding="utf-8"))
    c = pngio.to_u8(pngio.read_png(cpath))
    n = pngio.to_u8(pngio.read_png(os.path.join(d, f"{v}_normal.png")))
    ep = os.path.join(d, f"{v}_emission.png")
    e = pngio.to_u8(pngio.read_png(ep)) if os.path.exists(ep) else np.zeros_like(c)
    fw, cols, g = meta["frame_width"], meta["columns"], meta["gutter"]
    bg = np.array([0.55, 0.62, 0.70], np.float32)
    rows = []
    for lit in (False, True):
        row = []
        for i in pick:
            r, cc = divmod(i, cols)
            sl = (slice(r * (fw + g), r * (fw + g) + fw), slice(cc * (fw + g), cc * (fw + g) + fw))
            img = post.relight(c[sl], n[sl]) if lit else c[sl]
            f = img.astype(np.float32) / 255
            a = f[..., 3:4]
            row.append(np.clip(f[..., :3] * a + bg * (1 - a) + e[sl][..., :3].astype(np.float32) / 255 * 0.8, 0, 1))
        rows.append(np.hstack(row))
    out_img = np.vstack(rows)
    stamp(out_img, cpath, stale)
    write(out, out_img)
    print("REVIEW frames ok", out)


def tiles(out, dirs):
    """Terrain atlases side by side at half size (over a dark ground), one stamp each."""
    stale = stale_keys()
    panels = []
    for p in dirs:                                     # colour PNG paths (terrain/<planet>/<set>_color.png)
        img = pngio.read_png(p)
        rgb = (img[..., :3] * img[..., 3:4] + 0.1 * (1 - img[..., 3:4]))[::2, ::2].copy()
        stamp(rgb, p, stale)
        panels.append(rgb)
    write(out, np.hstack(panels))
    print("REVIEW tiles ok", out)


def sprites(out, paths):
    """Prop sprites over a neutral backdrop, bottom-aligned side by side; emission added on
    top when present; one stamp per sprite."""
    stale = stale_keys()
    imgs = [pngio.read_png(p) for p in paths]
    H = max(i.shape[0] for i in imgs)
    bg = np.array([0.55, 0.62, 0.70], np.float32)
    panels = []
    for p, img in zip(paths, imgs):
        h, w = img.shape[:2]
        rgb = img[..., :3] * img[..., 3:4] + bg * (1 - img[..., 3:4])
        ep = p.replace("_color.png", "_emission.png")
        if os.path.exists(ep):
            rgb = np.clip(rgb + pngio.read_png(ep)[..., :3] * 0.8, 0, 1)
        panel = np.tile(bg, (H, w + 8, 1)).astype(np.float32)
        panel[H - h:, 4:4 + w] = rgb
        stamp(panel, p, stale)
        panels.append(panel)
    write(out, np.hstack(panels))
    print("REVIEW sprites ok", out)




# ---------------------------------------------------------------- v3 cartoon review (contract §11.7)

BOXES = [                     # Bible 4.1 §9.7, the ten-box list (D-100, D-101)
    ("ink", "ink 2-3 px outer / 1-1.5 px interior, jitter, interior detail + texture marks"),
    ("cel", "flat cel colour, up to two shadow tones, muted aged palette"),
    ("face", "faces only on people and animals (D-101)"),
    ("twos", "animated on twos (12 fps), within the frame caps"),
    ("motion", "squash + stretch, rubber-hose limbs, secondary motion"),
    ("idle", "has an idle loop (nothing sits still)"),
    ("original", "original design, not any existing character"),
    ("sheet", "sprite sheet + json per the contract"),
    ("budget", "fits the atlas + RAM budget after import"),
    ("style", "consistent with the approved style test"),
]
PAPER = np.array([0.91, 0.88, 0.81], np.float32)
DARK = (0.12, 0.10, 0.09)


def _hexf(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


def _read(path):
    """HxWx4 float 0..1: through bpy inside Blender; numpy only (our 8-bit RGBA writer's files) in the bundled
    python, so lock-free previews (fakegp) can build the same review without blender.exe."""
    try:
        import bpy
        if hasattr(bpy, "data"):
            return pngio.read_png(path)
    except ImportError:
        pass
    return pngio.read_png_np(path).astype(np.float32) / 255.0


def _over(dst, rgba_u8, x, y):
    f = rgba_u8.astype(np.float32) / 255.0
    h, w = f.shape[:2]
    a = f[..., 3:4]
    dst[y:y + h, x:x + w] = f[..., :3] * a + dst[y:y + h, x:x + w] * (1 - a)


def _label(img, text, x, y, scale=2, color=(1.0, 0.97, 0.85)):
    draw(img, text, x, y, color, scale)


def planet_background(planet, scene, W, H):
    """The planet's painted layers when B-114 has exported them (tiled to W), else a flat
    placeholder in the planet palette (sky over a ground band) so the asset can be judged."""
    from meridian import v3
    d = os.path.join(ART, "backgrounds", planet, scene)
    layers = sorted(f for f in os.listdir(d) if f.startswith("layer") and f.endswith("_color.png")) if os.path.isdir(d) else []
    pal = v3.PALETTES[planet]
    bg = np.empty((H, W, 3), np.float32)
    bg[:] = _hexf(pal["sky"])
    if not layers:
        bg[int(H * 0.72):] = _hexf(pal["green"])
        return bg, "placeholder (no painted layers yet)"
    for f in layers:
        img = _read(os.path.join(d, f))
        lh, lw = img.shape[:2]
        reps = -(-W // lw)
        img = np.tile(img, (1, reps, 1))[:, :W]
        if lh > H:
            img = img[lh - H:]
        y = H - img.shape[0]
        a = img[..., 3:4]
        bg[y:] = img[..., :3] * a + bg[y:] * (1 - a)
    return bg, f"{len(layers)} painted layers"


def rotate_about(img_u8, deg, pivot_xy):
    """Rotate an RGBA frame by deg (+ = clockwise on screen, i.e. leaning right) about a pixel
    point, nearest sampling, into a canvas large enough to hold it (review panels only)."""
    h, w = img_u8.shape[:2]
    a = np.radians(deg)
    ca, sa = np.cos(a), np.sin(a)
    D = int(np.ceil(np.hypot(h, w))) + 4
    yy, xx = np.mgrid[0:D, 0:D].astype(np.float32)
    cx, cy = D / 2.0, D / 2.0
    dx, dy = xx - cx, yy - cy
    sx = ca * dx + sa * dy + pivot_xy[0]
    sy = -sa * dx + ca * dy + pivot_xy[1]
    ok = (sx >= 0) & (sx < w) & (sy >= 0) & (sy < h)
    out = np.zeros((D, D, 4), np.uint8)
    out[ok] = img_u8[sy[ok].astype(int), sx[ok].astype(int)]
    ys, xs = np.nonzero(out[..., 3])
    if len(ys) == 0:
        return out[:1, :1]
    return out[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def ink_zoom(frame_u8, box=96):
    """2x nearest zoom of the box with the most line work in a frame (v3.1: the 2x detail crop).
    Dark pixels count, not exact ink, because 1-1.5 px lines are mostly anti-aliased."""
    lum = frame_u8[..., :3].astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32) / 255.0
    m = ((lum < 0.35) & (frame_u8[..., 3] > 128)).astype(np.int32)
    H, W = m.shape
    box = min(box, H, W)
    ii = np.pad(m.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    s = ii[box:, box:] - ii[:-box, box:] - ii[box:, :-box] + ii[:-box, :-box]
    y, x = np.unravel_index(int(s.argmax()), s.shape)
    crop = frame_u8[y:y + box, x:x + box]
    return np.repeat(np.repeat(crop, 2, 0), 2, 1)


def v3_sheet_review(entry, meta, frames, sheet_path, out, stats, stale=None):
    """frames: per-frame HxWx4 uint8 in sheet order. stats: ink widths, palette, problems.
    Returns {box: (mark, note)}; mark 'x' measured/checked, 's' BLENDER self-check, ' ' open."""
    from meridian import v3
    stale = stale_keys() if stale is None else stale
    planet = entry.get("planet", "earth")
    fw, fh = meta["frame_width"], meta["frame_height"]
    clips = meta["animations"]
    longest = max(c["length"] for c in clips)
    W = max(1400, 16 + longest * (fw + 8))
    rows = []

    # header
    head = np.tile(PAPER, (30, W, 1))
    _label(head, f"review {meta['key']}  style v3  ppu {meta['ppu']}  {meta['fps']} fps  "
                 f"sheet {stats['sheet_wh'][0]}x{stats['sheet_wh'][1]}  {stats['png_kb']} kb", 6, 6)
    rows.append(head)

    # on the planet background at 1x: first frame of each clip + mid walk/idle frames
    bh = fh + 48
    if entry.get("beside"):              # the panel must hold the frame stood beside (a 192 px surveyor next to a 128 px wolf)
        try:
            sk = entry["beside"]
            sm = json.load(open(os.path.join(ART, *sk.split("/")[:2], sk.split("/")[2] + ".json"), encoding="utf-8"))
            bh = max(bh, int(sm["frame_height"]) + 48)
        except (OSError, KeyError, ValueError):
            pass
    bg, bg_note = planet_background(planet, entry.get("bg_scene", "plains"), W, bh)
    x = 16
    for c in clips:
        for k in sorted({0, c["length"] // 2}):
            if x + fw > W:
                break
            _over(bg, frames[c["start"] + k], x, bh - fh - 8)
            x += fw + 8
    ground = bh - 8 - int(round(meta["pivot"][1] * fh))      # the pivot line of the frames above, in panel px
    if entry.get("review_tilt"):                             # the in-flight lean the game applies (D-102: +-35 deg)
        for deg in (-float(entry["review_tilt"]), float(entry["review_tilt"])):
            rot = rotate_about(frames[0], deg, (meta["pivot"][0] * fw, fh - meta["pivot"][1] * fh - 6.2 * meta["ppu"]))
            if x + rot.shape[1] <= W:
                _over(bg, rot, x, max(0, bh - rot.shape[0] - 8))
                x += rot.shape[1] + 8
    if entry.get("beside"):                                  # e.g. the surveyor at 1x on the same ground line
        try:
            sk = entry["beside"]
            sd = os.path.join(ART, *sk.split("/")[:2])
            sm = json.load(open(os.path.join(sd, sk.split("/")[2] + ".json"), encoding="utf-8"))
            sh = pngio.to_u8(_read(os.path.join(sd, sk.split("/")[2] + "_color.png")))
            sfw, sfh = sm["frame_width"], sm["frame_height"]
            fr = sh[:sfh, :sfw]
            _over(bg, fr, min(x, W - sfw - 8), ground - sfh + int(round(sm["pivot"][1] * sfh)))
            _label(bg, f"beside: {sk} frame 0 at 1x", min(x, W - sfw - 8), 22)
        except (OSError, KeyError, ValueError) as e:
            _label(bg, f"beside {entry['beside']} unavailable: {type(e).__name__}", 6, 22)
    _label(bg, f"at 1x on {planet} background: {bg_note}", 6, 4)
    rows.append(bg)

    # every clip as a numbered frame strip
    for c in clips:
        strip = np.tile(PAPER, (fh + 40, W, 1))
        _label(strip, f"{c['name']}  {c['length']} frames  {'loop' if c['loop'] else 'once'}  "
                      f"cap {v3.cap_of(c['name'])[0]}-{v3.cap_of(c['name'])[1]}", 6, 4)
        for k in range(c["length"]):
            xx = 8 + k * (fw + 8)
            if xx + fw > W:
                break
            strip[22:22 + fh, xx:xx + fw] = PAPER * 0.96
            _over(strip, frames[c["start"] + k], xx, 22)
            _label(strip, str(k), xx + 2, 24 + fh - 14)
        rows.append(strip)

    # bottom: ink zoom, palette strip, checklist
    bot_h = 430
    bot = np.tile(PAPER, (bot_h, W, 1))
    z = ink_zoom(frames[0])
    _over(bot, z, 8, 26)
    _label(bot, "detail 2x (most line work)", 8, 6)
    pal = v3.PALETTES[planet]
    px0 = 8 + z.shape[1] + 24
    _label(bot, f"palette {planet}: colour, mid shadow, deep shadow", px0, 6)
    for i, k in enumerate(v3.PALETTE_ORDER):
        xx = px0 + i * 46
        bot[26:62, xx:xx + 40] = _hexf(pal[k])
        if k != "ink":
            bot[64:80, xx:xx + 40] = _hexf(v3.shadow_of(pal[k], planet))
            bot[82:98, xx:xx + 40] = _hexf(v3.deep_of(pal[k], planet))
        _label(bot, pal[k][1:], xx, 102, scale=1)
    ow, iw = stats["outer_px"], stats["inner_px"]
    n_in = stats.get("inner_n", 0)
    lines = [
        f"outer ink {ow[0]:.1f}-{ow[1]:.1f} px ({v3.OUTER_PX[0]:g}-{v3.OUTER_PX[1]:g})  interior {iw[0]:.1f}-{iw[1]:.1f} px "
        f"({v3.INNER_PX[0]:g}-{v3.INNER_PX[1]:g})  jitter +-20%  interior strokes {n_in / max(len(frames), 1):.0f} per frame",
        f"palette hits {stats['palette'][0] * 100:.1f}% of solid pixels" + (f"  off: {' '.join(stats['palette'][1])}" if stats['palette'][1] else ""),
        f"json {'valid' if not stats['problems'] else 'INVALID: ' + '; '.join(stats['problems'])[:120]}",
    ]
    for i, ln in enumerate(lines):
        _label(bot, ln, px0, 118 + i * 18)

    sc = entry.get("self_check", {})
    ink_ok = v3.OUTER_PX[0] - 0.05 <= ow[0] and ow[1] <= v3.OUTER_PX[1] + 0.05 and \
        iw != (0, 0) and v3.INNER_PX[0] - 0.05 <= iw[0] and iw[1] <= v3.INNER_PX[1] + 0.05
    cat = entry["key"].split("/")[0]
    if cat in ("characters", "creatures"):
        face = ("x", "a person / animal: a face is allowed")
    elif "face" in sc:
        face = ("s", sc["face"])
    else:
        face = (" ", "BLENDER did not self-check (object, plant, ship or planet)")
    res = {
        "ink": ("x" if ink_ok else "!", "measured widths, interior detail present" + ("; " + sc["ink"] if "ink" in sc else "")
                if ink_ok else ("no interior detail" if iw == (0, 0) else "widths outside v3.1")),
        "cel": ("x" if stats["palette"][0] >= 0.98 else "!", f"{stats['palette'][0] * 100:.1f}% palette (+ mid, deep)"),
        "face": face,
        "twos": ("x" if not stats["problems"] else "!", "fps 12, caps"),
        "motion": ("s", sc["motion"]) if "motion" in sc else (" ", "BLENDER did not self-check"),
        "idle": ("x", "idle loops") if any(c["name"] == "idle" and c["loop"] for c in clips) else ("!", "no looping idle"),
        "original": ("s", sc["original"]) if "original" in sc else (" ", "LEAD (§9.8)"),
        "sheet": ("x" if not stats["problems"] else "!", "png + json written, validated"),
        "budget": ("x" if stats["sheet_wh"][0] <= 2048 and stats["sheet_wh"][1] <= 2048 else "!",
                   "sheet side; UNITY confirms after import"),
        "style": ("s", sc["style"]) if "style" in sc else (" ", "LEAD, against the C0 style test"),
    }
    _label(bot, "bible 4.1 9.7 ten-box checklist  (x checked  s self-check  ! fails  blank: not mine to tick)", px0, 180)
    for i, (k, text) in enumerate(BOXES):
        mark, note = res[k]
        _label(bot, f"[{mark}] {text}  -  {note}"[:135], px0, 198 + i * 16)
    ours = entry.get("ours")
    if ours:
        _label(bot, f"what makes it ours: {ours}"[:160], 8, bot_h - 40)
    zf = stats.get("zoom_frames")
    if zf:
        zh, zw = zf[0].shape[:2]
        per = max(1, (W - 16) // (zw + 8))
        labels = entry.get("labels", [])
        for r0 in range(0, len(zf), per):
            zrow = np.tile(PAPER, (zh + 30, W, 1))
            for j, im in enumerate(zf[r0:r0 + per]):
                xx = 8 + j * (zw + 8)
                _over(zrow, im, xx, 24)
                _label(zrow, labels[r0 + j] if r0 + j < len(labels) else str(r0 + j), xx + 2, 4)
            rows.insert(2 + r0 // per, zrow)

    rows.append(bot)

    img = np.vstack(rows)
    stamp(img, sheet_path, stale) if os.path.normpath(sheet_path).startswith(ART) else \
        draw(img, stamp_text(sheet_path) + " preview", 2, img.shape[0] - 16, (1.0, 1.0, 0.85))
    write(out, img)
    return res


def v3_rigset_review(entry, meta, sheet, sheet_path, out, part_imgs, stats):
    """Rig set: the packed sheet over paper, each part with its pivot marked, json validity."""
    stale = stale_keys()
    H, W = sheet.shape[:2]
    canvas = np.tile(PAPER, (H + 80, max(W + 16, 900), 1))
    _label(canvas, f"review {meta['key']}  rig set  {W}x{H}  {len(meta['parts'])} parts  "
                   f"{len(meta['plants'])} plants  {stats['png_kb']} kb", 6, 6)
    _over(canvas, sheet, 8, 30)
    for p in meta["parts"]:
        x, y, w, h = p["rect"]
        top = H - (y + h)
        cx, cy = int(8 + x + p["pivot"][0] * w), int(30 + top + (1 - p["pivot"][1]) * h)
        canvas[max(cy - 1, 0):cy + 2, max(cx - 4, 0):cx + 5] = (0.85, 0.1, 0.1)
        canvas[max(cy - 4, 0):cy + 5, max(cx - 1, 0):cx + 2] = (0.85, 0.1, 0.1)
    _label(canvas, f"json {'valid' if not stats['problems'] else 'INVALID: ' + '; '.join(stats['problems'])[:120]}",
           6, H + 38)
    loop = stats.get("loop")                          # §11.7 (B-118): the assembled preview loop, 1x and 2x
    if loop:
        fh, fw = loop[0].shape[:2]
        Wc = max(canvas.shape[1], 16 + len(loop) * (fw * 2 + 8))
        if Wc > canvas.shape[1]:
            canvas = np.hstack([canvas, np.tile(PAPER, (canvas.shape[0], Wc - canvas.shape[1], 1))])
        bg, note = planet_background(entry.get("planet", "earth"), entry.get("bg_scene", "plains"), Wc, fh + 40)
        for i, im in enumerate(loop):
            _over(bg, im, 8 + i * (fw + 8), 30)
        _label(bg, f"assembled loop at 1x ({len(loop)} frames, 12 fps) on {note}", 6, 4)
        big = np.tile(PAPER, (fh * 2 + 30, Wc, 1))
        for i, im in enumerate(loop):
            _over(big, np.repeat(np.repeat(im, 2, 0), 2, 1), 8 + i * (fw * 2 + 8), 24)
            _label(big, str(i), 10 + i * (fw * 2 + 8), 6)
        canvas = np.vstack([canvas, bg, big])
    if os.path.normpath(sheet_path).startswith(ART):
        stamp(canvas, sheet_path, stale)
    else:
        draw(canvas, stamp_text(sheet_path) + " preview", 2, canvas.shape[0] - 16, (1.0, 1.0, 0.85))
    write(out, canvas)

def film(out, paths):
    """Film overlays (§11.6): each tiled 2x2 and cropped so the four-tile seam crossing sits in
    the panel centre (crosshair ticks mark it); row 1 at game strength on paper, row 2 boosted
    x4 around mid-grey so seams and specks are easy to see. One stamp per overlay."""
    stale = stale_keys()
    top, bottom = [], []
    for p in paths:
        img = pngio.read_png(p)
        t = np.tile(img, (2, 2, 1))
        n = img.shape[0]
        c = t[n - 192:n + 192, n - 192:n + 192]
        rgb, a = c[..., :3], c[..., 3:4]
        if (a > 0.99).all():                        # grain: overlay around mid-grey
            game = np.clip(PAPER + (rgb - 0.5) * 0.35, 0, 1)
            boost = np.clip(0.5 + (rgb - 0.5) * 4.0, 0, 1)
        else:
            game = rgb * a * 0.6 + PAPER * (1 - a * 0.6)
            boost = rgb * np.clip(a * 4, 0, 1) + 0.5 * (1 - np.clip(a * 4, 0, 1))
        for im in (game, boost):
            im[0:6, 191:193] = (0.85, 0.1, 0.1)
            im[-6:, 191:193] = (0.85, 0.1, 0.1)
            im[191:193, 0:6] = (0.85, 0.1, 0.1)
            im[191:193, -6:] = (0.85, 0.1, 0.1)
        game = np.ascontiguousarray(game)
        _label(game, os.path.basename(p).replace("_color.png", "") + " at game strength", 4, 4)
        _label(boost, "x4 boost", 4, 4)
        stamp(game, p, stale)
        top.append(np.pad(game, ((0, 0), (0, 8), (0, 0)), constant_values=1.0))
        bottom.append(np.pad(boost, ((0, 0), (0, 8), (0, 0)), constant_values=1.0))
    write(out, np.vstack([np.hstack(top), np.full((8, sum(x.shape[1] for x in top), 3), 1.0), np.hstack(bottom)]))
    print("REVIEW film ok", out)


if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if a[0] == "film":
        film(a[1], a[2:])
    elif a[0] == "sprites":
        sprites(a[1], a[2:])
    elif a[0] == "tiles":
        tiles(a[1], a[2:])
    elif a[0] == "stack":
        stack(a[1], a[2])
    elif a[0] == "frames":
        frames(a[1], a[2], a[3], [int(x) for x in a[4].split(",")])
    else:
        raise SystemExit(__doc__)
