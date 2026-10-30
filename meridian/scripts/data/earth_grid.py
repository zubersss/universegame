"""Shared grid conventions for the Earth dataset (tasks W3-W5).

Every Earth raster is NODE-registered on a regular latitude/longitude grid:
  row i    -> latitude  90 - i * res   (row 0 = north pole, last row = south pole)
  column j -> longitude -180 + j * res (west to east; last column = +180,
              a duplicate of column 0, so bilinear sampling never wraps)
with res in degrees. W = 360 / res + 1, H = 180 / res + 1.
Imported by the build scripts in this directory (run them with python3 -I
from the meridian/ directory, or add this directory to sys.path).
"""
import numpy as np


def grid_shape(res_deg):
    w = int(round(360.0 / res_deg)) + 1
    h = int(round(180.0 / res_deg)) + 1
    return h, w


def node_lats(res_deg):
    h, _ = grid_shape(res_deg)
    return 90.0 - np.arange(h, dtype=np.float64) * res_deg


def node_lons(res_deg):
    _, w = grid_shape(res_deg)
    return -180.0 + np.arange(w, dtype=np.float64) * res_deg


def node_area_weights(res_deg):
    """Relative area of each node's cell (cos latitude; the pole rows get the
    area of their half-cell cap), shape (H, 1) for broadcasting."""
    lat = np.radians(node_lats(res_deg))
    half = np.radians(res_deg) / 2
    top = np.minimum(lat + half, np.pi / 2)
    bot = np.maximum(lat - half, -np.pi / 2)
    return (np.sin(top) - np.sin(bot))[:, None]


def enforce_seam(a):
    """Make the last column equal the first (lon +180 == -180) along the last axis."""
    a[..., -1] = a[..., 0]
    return a


def area_fraction(mask, res_deg):
    """Area-weighted fraction of True nodes, counting the duplicate seam column once."""
    w = node_area_weights(res_deg)
    m = mask[..., :-1]
    return float((m * w).sum() / (np.ones_like(m, dtype=np.float64) * w).sum())
