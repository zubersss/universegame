"""Crop + nearest upscale of PNGs, numpy only: for looking at a review sheet or a smoke shot at 2x-6x before it is judged.
Reads 8-bit RGB or RGBA, non-interlaced (UNITY's captures are RGB; pngio.read_png_np reads RGBA only). Writes opaque RGBA.

  python -I blender/scripts/crop_png.py (<src> <x0> <y0> <x1> <y1> <k> <dst>)...      paths relative to the repo root

Run it under my lock (tools/blender_locked.ps1): ~50 MB, a few seconds. Crops go to blender/preview/ (gitignored).
"""
import os
import struct
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from meridian import pngio  # noqa: E402


def read_any(path, y_max=None):
    """HxWx4 uint8 (row 0 = top) of an 8-bit RGB / RGBA PNG; only the rows above y_max are decoded when it is given."""
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(path + ": not a PNG")
    pos, idat, w, h, bpp = 8, [], None, None, None
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos + 4])[0]
        tag, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + n]
        if tag == b"IHDR":
            w, h, bd, ct, _c, _f, il = struct.unpack(">IIBBBBB", body)
            if bd != 8 or ct not in (2, 6) or il != 0:
                raise ValueError(f"{path}: bit depth {bd}, colour type {ct}, interlace {il} not supported")
            bpp = 3 if ct == 2 else 4
        elif tag == b"IDAT":
            idat.append(body)
        pos += 12 + n
    raw = zlib.decompress(b"".join(idat))
    stride = w * bpp
    rows = h if y_max is None else min(h, y_max)
    out = np.zeros((rows, stride), np.uint8)
    prev = bytearray(stride)
    for y in range(rows):
        o = y * (stride + 1)
        f = raw[o]
        cur = bytearray(raw[o + 1:o + 1 + stride])
        if f == 1:                                                    # Sub: a running sum per channel
            a = np.frombuffer(bytes(cur), np.uint8).reshape(-1, bpp).astype(np.int64)
            cur = bytearray((np.cumsum(a, axis=0) & 255).astype(np.uint8).tobytes())
        elif f == 2:                                                  # Up
            s = (np.frombuffer(bytes(cur), np.uint8).astype(np.int32) + np.frombuffer(bytes(prev), np.uint8)) & 255
            cur = bytearray(s.astype(np.uint8).tobytes())
        elif f == 3:                                                  # Average
            for x in range(stride):
                a = cur[x - bpp] if x >= bpp else 0
                cur[x] = (cur[x] + ((a + prev[x]) >> 1)) & 255
        elif f == 4:                                                  # Paeth
            for x in range(stride):
                a = cur[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                cur[x] = (cur[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        out[y] = np.frombuffer(bytes(cur), np.uint8)
        prev = cur
    img = out.reshape(rows, w, bpp)
    if bpp == 3:
        img = np.dstack([img, np.full((rows, w), 255, np.uint8)])
    return img


def main(args):
    if not args or len(args) % 7:
        raise SystemExit(__doc__)
    cache = {}
    for i in range(0, len(args), 7):
        src, x0, y0, x1, y1, k, dst = args[i:i + 7]
        x0, y0, x1, y1, k = int(x0), int(y0), int(x1), int(y1), int(k)
        p = src if os.path.isabs(src) else os.path.join(REPO, src)
        if p not in cache or cache[p].shape[0] < y1:
            cache[p] = read_any(p, y1)
        c = np.repeat(np.repeat(cache[p][y0:y1, x0:x1], k, 0), k, 1).copy()
        c[..., 3] = 255
        d = dst if os.path.isabs(dst) else os.path.join(REPO, dst)
        pngio.write_png(d, c)
        print("crop", src, (x0, y0, x1, y1), f"x{k} ->", dst, c.shape[1], "x", c.shape[0])


if __name__ == "__main__":
    main(sys.argv[1:])
