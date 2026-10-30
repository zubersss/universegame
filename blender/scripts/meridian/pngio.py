"""PNG I/O. The writer is pure Python + numpy: 8-bit RGBA, straight alpha, no iCCP/sRGB/gAMA
chunks (contract §2), no timestamps, so identical pixels always give identical bytes."""
import struct
import zlib

import numpy as np


def _chunk(tag, data):
    body = tag + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def _filter_rows(img):
    """Per-row adaptive filter (None/Sub/Up), chosen by minimum sum of absolute values."""
    h, w, c = img.shape
    rows = img.reshape(h, w * c).astype(np.int16)
    prev = np.vstack([np.zeros((1, w * c), np.int16), rows[:-1]])
    left = np.hstack([np.zeros((h, c), np.int16), rows[:, :-c]])
    cands = [rows, (rows - left) & 0xFF, (rows - prev) & 0xFF]
    cost = np.stack([np.where(x > 127, 256 - x, x).sum(axis=1) for x in cands])
    best = cost.argmin(axis=0)
    out = np.empty((h, w * c + 1), np.uint8)
    out[:, 0] = best
    for f in range(3):
        sel = best == f
        out[sel, 1:] = cands[f][sel].astype(np.uint8)
    return out.tobytes()


def write_png(path, img):
    """img: HxWx4 uint8, row 0 = top."""
    img = np.ascontiguousarray(img, dtype=np.uint8)
    assert img.ndim == 3 and img.shape[2] == 4, "write_png expects HxWx4 uint8"
    h, w, _ = img.shape
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(_filter_rows(img), 9)) + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


def read_png(path):
    """Read a PNG (e.g. a Blender render) via bpy as HxWx4 float32 0..1, row 0 = top, no
    color conversion (raw stored values, straight alpha)."""
    import bpy
    img = bpy.data.images.load(path, check_existing=False)
    try:
        img.colorspace_settings.name = "Non-Color"
        img.alpha_mode = "STRAIGHT"
        w, h = img.size
        buf = np.empty(w * h * 4, np.float32)
        img.pixels.foreach_get(buf)
        return buf.reshape(h, w, 4)[::-1].copy()
    finally:
        bpy.data.images.remove(img)


def to_u8(a):
    return np.clip(np.rint(a * 255.0), 0, 255).astype(np.uint8)
