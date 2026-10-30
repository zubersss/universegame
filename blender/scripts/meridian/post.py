"""numpy post-processing for rendered passes (contract §2, §5, §7). Arrays are HxWx4, row 0 = top."""
import numpy as np

from . import contract as C

_N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def _shift(a, dy, dx):
    """Shift without wrap; vacated cells are zero."""
    out = np.zeros_like(a)
    h, w = a.shape[:2]
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = a[ys, xs]
    return out


def dilate(rgb, known, steps=C.DILATE):
    """Grow RGB values from `known` pixels outward `steps` px (average of known 8-neighbours).
    Returns (rgb, known_after)."""
    rgb = rgb.astype(np.float32).copy()
    known = known.copy()
    for _ in range(steps):
        acc = np.zeros_like(rgb)
        cnt = np.zeros(known.shape, np.float32)
        for dy, dx in _N8:
            k = _shift(known, dy, dx)
            acc += _shift(rgb, dy, dx) * k[..., None]
            cnt += k
        grow = (~known) & (cnt > 0)
        rgb[grow] = acc[grow] / cnt[grow][:, None]
        known = known | grow
    return rgb, known


# RGB is trusted only where coverage >= 50%: un-premultiplied values of faint anti-aliased
# edge pixels are noisy (and differ run to run). Edge pixels take their RGB from the solid
# interior by dilation, which also gives halo-free edges. EDGE_STEPS covers the AA band.
SOLID = 0.5
EDGE_STEPS = 2


def finish_color(px):
    """px: float 0..1 straight-alpha render. Returns uint8 RGBA, RGB dilated 8 px past the
    silhouette under alpha=0."""
    a = px[..., 3]
    rgb, _ = dilate(px[..., :3], a >= SOLID, C.DILATE + EDGE_STEPS)
    return _u8(np.dstack([rgb, a]))


def finish_normal(px, alpha):
    """px: float render of (n+1)/2 in linear. alpha: coverage 0..1 from the color pass.
    Edge normals dilated 8 px, the rest filled with (128,128,255); alpha 255."""
    rgb, grown = dilate(px[..., :3], alpha >= SOLID, C.DILATE + EDGE_STEPS)
    fill = np.array(C.NORMAL_FILL, np.float32) / 255.0
    rgb[~grown] = fill
    out = np.dstack([rgb, np.ones(alpha.shape, np.float32)])
    return _u8(out)


def finish_emission(px, alpha):
    """Emission RGB premultiplied by coverage (black outside the sprite); alpha 255."""
    rgb = px[..., :3] * px[..., 3:4]
    rgb = rgb * (alpha[..., None] > 0)
    return _u8(np.dstack([rgb, np.ones(alpha.shape, np.float32)]))


def finish_mask(px, alpha):
    """Linear mask, R rim, G AO, B metallic; dilated like color; alpha unused (255)."""
    rgb, _ = dilate(px[..., :3], alpha >= SOLID, C.DILATE + EDGE_STEPS)
    return _u8(np.dstack([rgb, np.ones(alpha.shape, np.float32)]))


def _u8(a):
    return np.clip(np.rint(a * 255.0), 0, 255).astype(np.uint8)


# ---------- checks ----------

def check_padding(color_u8, pad=C.PADDING):
    a = color_u8[..., 3]
    border = np.concatenate([a[:pad].ravel(), a[-pad:].ravel(), a[:, :pad].ravel(), a[:, -pad:].ravel()])
    n = int((border > 0).sum())
    return n == 0, f"{n} non-transparent px inside the {pad} px margin"


def seam_score(color_u8, axis):
    """Ratio of the wrap-seam difference to the mean neighbouring-line difference.
    axis 1 = horizontal tiling (compare last column with first)."""
    img = color_u8[..., :3].astype(np.float32)
    if axis == 0:
        img = img.transpose(1, 0, 2)
    interior = np.abs(np.diff(img, axis=1)).mean()
    seam = np.abs(img[:, -1] - img[:, 0]).mean()
    return float(seam / max(interior, 0.5))


def check_tileable(color_u8, mode, limit=2.0):
    """mode 'x' | 'y' | 'xy'. Passes when the wrap seam is no stronger than `limit` x the
    average interior step (a seam you can see is typically 4x+)."""
    msgs, ok = [], True
    for ax, name in ((1, "x"), (0, "y")):
        if name in mode:
            s = seam_score(color_u8, ax)
            msgs.append(f"seam_{name}={s:.2f}")
            ok &= s <= limit
    return ok, " ".join(msgs)


# ---------- frame sheets ----------

def pack_sheet(frames, columns, gutter=C.GUTTER, fill=(0, 0, 0, 0)):
    """frames: list of HxWx4 uint8 (same size). Row-major grid, `gutter` px between frames,
    no outer margin (each frame already holds its own 8 px padding)."""
    fh, fw = frames[0].shape[:2]
    rows = (len(frames) + columns - 1) // columns
    cols = min(columns, len(frames))
    sheet = np.empty((rows * fh + (rows - 1) * gutter, cols * fw + (cols - 1) * gutter, 4), np.uint8)
    sheet[:] = fill
    for i, f in enumerate(frames):
        r, c = divmod(i, columns)
        y, x = r * (fh + gutter), c * (fw + gutter)
        sheet[y:y + fh, x:x + fw] = f
    return sheet


# ---------- contact sheet ----------

def _checker(h, w, s=16):
    yy, xx = np.mgrid[0:h, 0:w]
    c = (((yy // s) + (xx // s)) % 2).astype(np.float32)
    return (0.55 + 0.2 * c)[..., None].repeat(3, axis=2)


def _over_checker(rgba):
    f = rgba.astype(np.float32) / 255.0
    a = f[..., 3:4]
    return f[..., :3] * a + _checker(*f.shape[:2]) * (1 - a)


def relight(color_u8, normal_u8, light=(1.0, 1.0, 1.0)):
    """Lambert relight from the upper-right-front: proves the normal convention.
    The upper-right of a sphere must come out brightest."""
    L = np.array(light, np.float32)
    L /= np.linalg.norm(L)
    n = normal_u8[..., :3].astype(np.float32) / 127.5 - 1.0
    ndl = np.clip((n * L).sum(axis=2), 0, 1)[..., None]
    col = color_u8.astype(np.float32) / 255.0
    lit = col[..., :3] * (0.2 + 0.8 * ndl)
    out = np.dstack([lit, col[..., 3:4]])
    return _u8(out)


def _fit(rgb, max_h):
    """Nearest-neighbour downscale so panels stay readable on screen."""
    h = rgb.shape[0]
    if h <= max_h:
        return rgb
    step = int(np.ceil(h / max_h))
    return rgb[::step, ::step]


def contact_sheet(maps, tile_mode=None, max_h=512, gap=8):
    """maps: dict name -> uint8 RGBA. Panels left to right: color (over checker), color RGB
    with alpha ignored (shows the dilation), normal, relit (upper-right light), emission, mask;
    second row: 2x tile of the color if tileable."""
    panels = []
    col = maps["color"]
    panels.append(_over_checker(col))
    panels.append(col[..., :3].astype(np.float32) / 255.0)
    if "normal" in maps:
        panels.append(maps["normal"][..., :3].astype(np.float32) / 255.0)
        panels.append(_over_checker(relight(col, maps["normal"])))
    for m in ("emission", "mask"):
        if m in maps:
            panels.append(maps[m][..., :3].astype(np.float32) / 255.0)
    panels = [_fit(p, max_h) for p in panels]
    rows = [panels]
    if tile_mode:
        reps = (2 if "y" in tile_mode else 1, 2 if "x" in tile_mode else 1, 1)
        tiled = _over_checker(np.tile(col, reps))
        rows.append([_fit(tiled, max_h)])
    lines = []
    for row in rows:
        h = max(p.shape[0] for p in row)
        parts = []
        for p in row:
            pad = np.full((h, p.shape[1], 3), 0.12, np.float32)
            pad[:p.shape[0]] = p
            parts += [pad, np.full((h, gap, 3), 0.12, np.float32)]
        lines.append(np.hstack(parts[:-1]))
    w = max(l.shape[1] for l in lines)
    out = []
    for l in lines:
        pad = np.full((l.shape[0], w, 3), 0.12, np.float32)
        pad[:, :l.shape[1]] = l
        out += [pad, np.full((gap, w, 3), 0.12, np.float32)]
    rgb = np.vstack(out[:-1])
    return _u8(np.dstack([rgb, np.ones(rgb.shape[:2], np.float32)]))
