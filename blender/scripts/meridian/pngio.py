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


def read_png_np(path):
    """Read an 8-bit RGBA PNG with numpy only (no bpy): HxWx4 uint8, row 0 = top. Handles all five
    PNG filter types (our writer uses None/Sub/Up). For lock-free reviews of exported sheets."""
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG")
    pos, idat, w, h = 8, b"", None, None
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos + 4])[0]
        tag, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + n]
        if tag == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", body[:10])
            if bd != 8 or ct != 6:
                raise ValueError(f"{path}: only 8-bit RGBA is supported (bit depth {bd}, colour type {ct})")
        elif tag == b"IDAT":
            idat += body
        pos += 12 + n
    raw = zlib.decompress(idat)
    stride = w * 4
    out = np.zeros((h, stride), np.uint8)
    prev = np.zeros(stride, np.int32)
    for y in range(h):
        f = raw[y * (stride + 1)]
        cur = np.frombuffer(raw, np.uint8, stride, y * (stride + 1) + 1).astype(np.int32)
        if f == 1:                                       # Sub = a running sum per channel (vectorised)
            cur = (np.cumsum(cur.reshape(-1, 4), axis=0) & 255).reshape(-1)
        elif f == 2:
            cur = (cur + prev) & 255
        elif f in (3, 4):
            cur = cur.copy()
            for x in range(stride):
                a = int(cur[x - 4]) if x >= 4 else 0
                b = int(prev[x])
                c = int(prev[x - 4]) if x >= 4 else 0
                if f == 3:
                    cur[x] = (cur[x] + (a + b) // 2) & 255
                else:
                    p = a + b - c
                    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                    cur[x] = (cur[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        out[y] = cur
        prev = cur
    return out.reshape(h, w, 4)


def to_u8(a):
    return np.clip(np.rint(a * 255.0), 0, 255).astype(np.uint8)
