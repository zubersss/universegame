"""Packages the Earth dataset for the game (task W3): src/data/earth/*.bin + earth.json.

Layers (all NODE-registered, see earth_grid.py):
  elevation  int16 metres above mean sea level, 10 arc-minute grid (2161 x 1081)
  coast      int8 signed distance to the coastline, 0.5 km steps, + on land, 5' grid
  water      int16 metres, surface level of the nearest water body (ocean 0, lakes
             their estimated level), 10' grid
  biome      uint8 x 5 land-cover fractions (tree, lowveg, bare, ice, tundra), 0.25 deg grid
Pole rows are constant (their mean) in every layer, so a pole has one value.

Elevation sources (one of):
  --elevation-fatiando <earth-topography-10arcmin.nc>   ETOPO1 ice surface at 10' (interim)
  --elevation-etopo2022 <ETOPO_2022_v1_60s_N90W180_surface.nc|.tif>   area-averaged to 10'
The coast and biome layers come from coast_sdf.py and worldcover_fractions.py
outputs in --build (coast_sdf_5m.npy, biome_frac_15m.npy and their .json).

File format (LSR1, little-endian, the whole file gzip-compressed):
  bytes 0-3 'LSR1'; u32 width; u32 height; u8 dtype (1 int8, 2 uint8, 3 int16);
  u8 channels; u8 predictor (1 = gradient); u8 reserved; then per channel the
  residuals r = (v - (left + up - upleft)) mod 2^bits in row-major order
  (left/up only on the first row/column, 0 for the first sample), zigzag
  coded; 16-bit residuals are stored as a plane of low bytes then a plane of
  high bytes. Decoding is exact (src/world/earthData.ts decodeLsr).

Run (from meridian/):
  python3 -I scripts/data/build_earth.py --elevation-fatiando <nc> --build <dir> --out src/data/earth
"""
import argparse
import gzip
import hashlib
import json
import os
import struct
import sys

import numpy as np

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import earth_grid  # noqa: E402

ELEV_RES = 1.0 / 6.0
COAST_RES = 1.0 / 12.0
BIOME_RES = 0.25
COAST_STEP_KM = 0.5
DTYPES = {'int8': 1, 'uint8': 2, 'int16': 3}


def zigzag(r, bits):
    """Signed residuals (already wrapped to `bits`) -> unsigned zigzag codes."""
    r = r.astype(np.int64)
    return ((r << 1) ^ (r >> (bits - 1))) & ((1 << bits) - 1)


def gradient_residuals(v, bits):
    """Residual of each sample against left + up - upleft, wrapped to `bits` (two's complement)."""
    v = v.astype(np.int64)
    p = np.zeros_like(v)
    p[0, 1:] = v[0, :-1]
    p[1:, 0] = v[:-1, 0]
    p[1:, 1:] = v[1:, :-1] + v[:-1, 1:] - v[:-1, :-1]
    m = 1 << bits
    r = (v - p) % m
    r[r >= m // 2] -= m
    return r


def encode_lsr(arr, dtype):
    """arr: (H, W) or (C, H, W) integer array already in the target dtype's range."""
    a = arr if arr.ndim == 3 else arr[None]
    c, h, w = a.shape
    bits = 16 if dtype == 'int16' else 8
    body = []
    for ch in range(c):
        vals = a[ch].astype(np.int64)
        if dtype == 'uint8':
            vals = vals.astype(np.int64)  # residuals mod 256 work on any 8-bit pattern
        z = zigzag(gradient_residuals(vals, bits), bits)
        if bits == 16:
            body.append((z & 0xFF).astype(np.uint8).tobytes())
            body.append((z >> 8).astype(np.uint8).tobytes())
        else:
            body.append(z.astype(np.uint8).tobytes())
    header = b'LSR1' + struct.pack('<IIBBBB', w, h, DTYPES[dtype], c, 1, 0)
    return gzip.compress(header + b''.join(body), 9, mtime=0)


def raw_sha256(arr, dtype):
    np_t = {'int8': '<i1', 'uint8': '<u1', 'int16': '<i2'}[dtype]
    return hashlib.sha256(np.ascontiguousarray(arr.astype(np_t)).tobytes()).hexdigest()


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- elevation

def read_fatiando(path):
    import h5py
    with h5py.File(path, 'r') as f:
        lat = f['latitude'][:]
        lon = f['longitude'][:]
        z = f['topography'][:].astype(np.float64)
        fill = f['topography'].attrs.get('_FillValue', [None])[0]
    if fill is not None:
        z[z == fill] = np.nan
    if lat[0] < lat[-1]:
        lat = lat[::-1]
        z = z[::-1]
    return z, lat, lon


def read_etopo2022(path):
    """ETOPO 2022 global 60s/30s grid (cell-centred) as netCDF (lat, lon, z) or GeoTIFF."""
    if path.endswith('.tif') or path.endswith('.tiff'):
        import rasterio
        with rasterio.open(path) as ds:
            z = ds.read(1).astype(np.float64)
            if ds.nodata is not None:
                z[z == ds.nodata] = np.nan
            t = ds.transform
            lon = t.c + (np.arange(ds.width) + 0.5) * t.a
            lat = t.f + (np.arange(ds.height) + 0.5) * t.e
    else:
        import h5py
        with h5py.File(path, 'r') as f:
            lat = f['lat'][:]
            lon = f['lon'][:]
            z = f['z'][:].astype(np.float64)
            fill = f['z'].attrs.get('_FillValue', [None])[0]
        if fill is not None:
            z[z == fill] = np.nan
    if lat[0] < lat[-1]:
        lat = lat[::-1]
        z = z[::-1]
    return z, lat, lon


def bin_to_nodes(z, lat, lon, res):
    """Area-average source cells (by centre) into node cells [lat +- res/2] x [lon +- res/2]."""
    h, w = earth_grid.grid_shape(res)
    sums = np.zeros((h, w - 1))
    cnt = np.zeros((h, w - 1))
    wts = np.cos(np.radians(lat))
    ii = np.clip(np.rint((90.0 - lat) / res).astype(np.int64), 0, h - 1)
    jj = np.rint((lon + 180.0) / res).astype(np.int64) % (w - 1)
    for r in range(z.shape[0]):
        row = z[r]
        ok = np.isfinite(row)
        np.add.at(sums[ii[r]], jj[ok], row[ok] * wts[r])
        np.add.at(cnt[ii[r]], jj[ok], wts[r])
    out = np.full((h, w), np.nan)
    with np.errstate(invalid='ignore', divide='ignore'):
        out[:, :-1] = sums / cnt
    return earth_grid.enforce_seam(out)


def fill_nodata(z):
    """Replace NaN nodes by the mean of their valid 8-neighbours, repeatedly (longitude wraps)."""
    z = z.copy()
    filled = 0
    for _ in range(1000):
        bad = ~np.isfinite(z)
        if not bad.any():
            break
        core = z[:, :-1]
        pad = np.pad(core, ((1, 1), (0, 0)), mode='edge')
        pad = np.concatenate([pad[:, -1:], pad, pad[:, :1]], axis=1)
        acc = np.zeros_like(core)
        n = np.zeros_like(core)
        for dy in (0, 1, 2):
            for dx in (0, 1, 2):
                v = pad[dy:dy + core.shape[0], dx:dx + core.shape[1]]
                ok = np.isfinite(v)
                acc[ok] += v[ok]
                n += ok
        fix = bad[:, :-1] & (n > 0)
        core[fix] = acc[fix] / n[fix]
        filled += int(fix.sum())
        earth_grid.enforce_seam(z)
    return z, filled


def build_elevation(args):
    if args.elevation_fatiando:
        z, lat, lon = read_fatiando(args.elevation_fatiando)
        src = args.elevation_fatiando
        expect_h, expect_w = earth_grid.grid_shape(ELEV_RES)
        assert z.shape == (expect_h, expect_w), z.shape
        assert abs(lat[0] - 90) < 1e-9 and abs(lat[-1] + 90) < 1e-9 and abs(lon[0] + 180) < 1e-9 and abs(lon[-1] - 180) < 1e-9
        source = {
            'name': 'ETOPO1 Ice Surface (NOAA NGDC, Amante & Eakins 2009) at 10 arc-minutes, as distributed by Fatiando a Terra',
            'url': 'https://github.com/fatiando-data/earth-topography-10arcmin/releases/download/v1/earth-topography-10arcmin.nc',
            'doi': ['https://doi.org/10.7289/V5C8276M', 'https://doi.org/10.5281/zenodo.5882203'],
            'license': 'ETOPO1: public domain (US Government work); this 10\' grid: CC BY 4.0 (Fatiando a Terra)',
            'note': 'INTERIM: evaluated from the ETOPO1 spherical-harmonic model (degree 720, taper 540-720) by the ICGEM service, so relief is smoothed (Everest region about 5.9 km). Replace with ETOPO 2022 60s (--elevation-etopo2022) when www.ncei.noaa.gov is reachable.',
            'accessed': '2026-10-30',
            'sha256': file_sha256(src),
        }
    else:
        z, lat, lon = read_etopo2022(args.elevation_etopo2022)
        src = args.elevation_etopo2022
        z = bin_to_nodes(z, lat, lon, ELEV_RES)
        source = {
            'name': 'ETOPO 2022 v1 60 arc-second global relief (surface), NOAA NCEI, area-averaged to 10 arc-minute nodes',
            'url': 'https://www.ncei.noaa.gov/products/etopo-global-relief-model',
            'doi': ['https://doi.org/10.25921/fd45-gt74'],
            'license': 'Public domain (US Government work, NOAA NCEI)',
            'accessed': args.accessed,
            'sha256': file_sha256(src),
        }
    z, filled = fill_nodata(z)
    z = earth_grid.enforce_seam(constant_poles(z))
    zi = np.clip(np.rint(z), -32767, 32767).astype(np.int16)
    return zi, source, filled


# -------------------------------------------------------------------- main

def constant_poles(a):
    """Set the first and last rows (the poles) to their mean along longitude, per channel."""
    a = a.astype(np.float64)
    a[..., 0, :] = a[..., 0, :-1].mean(axis=-1, keepdims=True)
    a[..., -1, :] = a[..., -1, :-1].mean(axis=-1, keepdims=True)
    return a


def wrap_edt_indices(water):
    """Nearest water node (row, col) for every node of a 5' grid, wrapping in longitude."""
    from scipy import ndimage
    core = water[:, :-1]
    pad = 256
    wrapped = np.concatenate([core[:, -pad:], core, core[:, :pad]], axis=1)
    _, idx = ndimage.distance_transform_edt(~wrapped, return_indices=True)
    rows = idx[0][:, pad:-pad]
    cols = (idx[1][:, pad:-pad] - pad) % core.shape[1]
    rows = np.concatenate([rows, rows[:, :1]], axis=1)
    cols = np.concatenate([cols, cols[:, :1]], axis=1)
    return rows, cols


def lake_levels(elev, sdf, lake_id, lakes_meta):
    """Estimated surface level per lake: 5th percentile of the DEM on land within 1-6 nodes (5-30 km at 5') of the lake, at least +1 m.

    Chosen over wider/higher-percentile rings by comparison with commonly cited
    surface elevations of 18 large lakes (median error 7 m; worst +194 m for
    rift lakes in narrow valleys, -318 m for Lake Victoria, where the interim
    DEM has a spurious depression). Erring low is benign: the shore then slopes
    down to the water instead of being lifted to it."""
    from scipy import ndimage
    h5, w5 = sdf.shape
    # DEM (10' nodes) at every 5' node by bilinear interpolation.
    rr, cc = np.meshgrid(np.arange(h5) / 2.0, np.arange(w5) / 2.0, indexing='ij')
    dem5 = ndimage.map_coordinates(elev.astype(np.float64), [rr, cc], order=1, mode='nearest')
    land = sdf > 0
    levels = {}
    objs = ndimage.find_objects(lake_id)
    st = ndimage.generate_binary_structure(2, 2)
    for k, sl in enumerate(objs, start=1):
        if sl is None:
            continue
        r0, r1 = max(sl[0].start - 8, 0), min(sl[0].stop + 8, h5)
        c0, c1 = max(sl[1].start - 8, 0), min(sl[1].stop + 8, w5)
        m = lake_id[r0:r1, c0:c1] == k
        far = ndimage.binary_dilation(m, st, iterations=6)
        vals = dem5[r0:r1, c0:c1][far & ~m & land[r0:r1, c0:c1]]
        if vals.size == 0:
            continue
        levels[k] = max(1.0, float(np.percentile(vals, 5)))
    return levels


def build_water(elev, sdf, lake_id, lakes_meta):
    water = sdf <= 0
    levels = lake_levels(elev, sdf, lake_id, lakes_meta)
    level_at = np.zeros(sdf.shape)
    for k, v in levels.items():
        level_at[lake_id == k] = v
    level_at[~water] = 0
    rows, cols = wrap_edt_indices(water)
    nearest = level_at[rows, cols]
    nearest[water] = level_at[water]
    w10 = nearest[::2, ::2]
    assert w10.shape == earth_grid.grid_shape(ELEV_RES)
    w10 = earth_grid.enforce_seam(constant_poles(w10))
    table = []
    for k, v in sorted(levels.items()):
        info = lakes_meta.get(str(k), {}) if isinstance(lakes_meta, dict) else {}
        table.append({'id': k, 'name': info.get('name'), 'level': round(v, 1), 'nodes5m': int((lake_id == k).sum())})
    return np.clip(np.rint(w10), -32767, 32767).astype(np.int16), table


def write_layer(out_dir, name, arr, dtype):
    path = os.path.join(out_dir, f'earth-{name}.bin')
    data = encode_lsr(arr, dtype)
    with open(path, 'wb') as fh:
        fh.write(data)
    return {'file': os.path.basename(path), 'bytes': len(data), 'sha256Decoded': raw_sha256(arr, dtype)}


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--elevation-fatiando')
    g.add_argument('--elevation-etopo2022')
    ap.add_argument('--accessed', default='2026-10-30')
    ap.add_argument('--build', required=True, help='directory with coast_sdf_5m.npy and biome_frac_15m.npy (+ .json)')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    elev, elev_src, filled = build_elevation(args)
    h, w = elev.shape
    layers = {}
    m = write_layer(args.out, 'elevation', elev, 'int16')
    layers['elevation'] = {
        **m, 'dtype': 'int16', 'width': w, 'height': h, 'channels': 1, 'res': ELEV_RES, 'scale': 1, 'offset': 0,
        'units': 'm', 'datum': 'mean sea level', 'nodata': None, 'nodataFilled': filled,
        'min': int(elev.min()), 'max': int(elev.max()), 'source': elev_src,
    }

    sdf = np.load(os.path.join(args.build, 'coast_sdf_5m.npy'))
    with open(os.path.join(args.build, 'coast_sdf_5m.json')) as fh:
        coast_meta = json.load(fh)
    assert sdf.shape == earth_grid.grid_shape(COAST_RES), sdf.shape
    sdf = earth_grid.enforce_seam(constant_poles(sdf))
    q = np.clip(np.rint(sdf / COAST_STEP_KM), -127, 127).astype(np.int8)
    # Keep the sign exact: a node on land never quantizes to 0 or below, water never to 0 or above.
    q[(sdf > 0) & (q <= 0)] = 1
    q[(sdf <= 0) & (q >= 0)] = -1
    earth_grid.enforce_seam(q)
    m = write_layer(args.out, 'coast', q, 'int8')
    layers['coast'] = {
        **m, 'dtype': 'int8', 'width': q.shape[1], 'height': q.shape[0], 'channels': 1, 'res': COAST_RES,
        'scale': COAST_STEP_KM, 'offset': 0, 'units': 'km', 'meaning': 'signed distance to the coastline, positive on land (incl. ice shelves), negative on ocean and lakes, clamped to +-63.5 km',
        'landFraction': earth_grid.area_fraction(q > 0, COAST_RES),
        'source': {k: coast_meta[k] for k in ('source', 'method', 'approximations') if k in coast_meta},
    }

    lake_id = np.load(os.path.join(args.build, 'lake_id_5m.npy'))
    with open(os.path.join(args.build, 'lakes.json')) as fh:
        lakes_meta = json.load(fh)
    lake_list = lakes_meta['lakes'] if isinstance(lakes_meta, dict) else lakes_meta
    lakes_meta = {str(x.get('id', x.get('index', i + 1))): x for i, x in enumerate(lake_list)}
    water, lake_table = build_water(elev, sdf, lake_id, lakes_meta)
    m = write_layer(args.out, 'water', water, 'int16')
    layers['water'] = {
        **m, 'dtype': 'int16', 'width': water.shape[1], 'height': water.shape[0], 'channels': 1, 'res': ELEV_RES,
        'scale': 1, 'offset': 0, 'units': 'm',
        'meaning': 'surface level of the nearest water body: 0 for the ocean, an estimated level for lakes (5th percentile of the DEM on land within 5-30 km of the shore, at least +1 m)',
        'tag': 'estimated', 'lakes': [t for t in lake_table if t['nodes5m'] >= 20],
        'notes': ['The Caspian Sea is part of the sea in Natural Earth (a hole in the land polygons), so it takes the ocean level 0 m (real -28 m).',
                  'Lakes below sea level (Dead Sea) are raised to +1 m so no land or lake sits below the ocean surface.'],
    }

    frac = np.load(os.path.join(args.build, 'biome_frac_15m.npy'))
    with open(os.path.join(args.build, 'biome_frac_15m.json')) as fh:
        biome_meta = json.load(fh)
    assert frac.shape == (5,) + earth_grid.grid_shape(BIOME_RES), frac.shape
    # WorldCover does not cover Antarctica: land cells south of 60 S without
    # WorldCover land pixels (land per the coastline layer) become snow/ice (estimated).
    step = int(round(BIOME_RES / COAST_RES))
    land_b = sdf[::step, ::step] > 0
    lat_b = earth_grid.node_lats(BIOME_RES)[:, None]
    empty = frac.sum(axis=0) == 0
    fill = empty & land_b & (lat_b < -60)
    frac = frac.copy()
    frac[:, fill] = 0
    frac[3, fill] = 255
    filled_ice = int(fill.sum())
    frac = np.clip(np.rint(constant_poles(frac)), 0, 255).astype(np.uint8)
    earth_grid.enforce_seam(frac)
    m = write_layer(args.out, 'biome', frac, 'uint8')
    layers['biome'] = {
        **m, 'dtype': 'uint8', 'width': frac.shape[2], 'height': frac.shape[1], 'channels': 5, 'res': BIOME_RES,
        'scale': 1 / 255, 'offset': 0, 'channelNames': ['tree', 'lowveg', 'bare', 'ice', 'tundra'],
        'meaning': 'fraction of land-cover pixels per class in the node cell (0 where the cell has no land pixels)',
        'antarcticIceFill': {'cells': filled_ice, 'tag': 'estimated', 'note': 'WorldCover has no Antarctic tiles; land cells south of 60 S (per the coastline layer) are set to snow/ice'},
        'source': {k: biome_meta[k] for k in ('source', 'overview', 'class_mapping', 'excluded_from_land') if k in biome_meta},
        'tiles': {k: biome_meta.get('tiles', {}).get(k) for k in ('listed', 'read', 'failed')},
    }

    doc = {
        'dataset': 'earth',
        'format': 'LSR1 (see scripts/data/build_earth.py)',
        'grid': 'node-registered latitude/longitude: row 0 = 90N, last row = 90S, column 0 = 180W, last column = 180E (duplicate of column 0)',
        'built': args.accessed,
        'tool': 'scripts/data/build_earth.py',
        'totalBytes': sum(l['bytes'] for l in layers.values()),
        'credits': [
            'Topography: ETOPO1 (NOAA NGDC, public domain), 10\' grid by Fatiando a Terra (CC BY 4.0)'
            if args.elevation_fatiando else 'Topography: ETOPO 2022 (NOAA NCEI, public domain)',
            'Coastlines and lakes: Natural Earth (public domain)',
            'Land cover: \u00a9 ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium (CC BY 4.0)',
        ],
        'layers': layers,
    }
    with open(os.path.join(args.out, 'earth.json'), 'w') as fh:
        json.dump(doc, fh, indent=1)
        fh.write('\n')
    print(json.dumps({k: {kk: v[kk] for kk in ('file', 'bytes')} for k, v in layers.items()}, indent=1), 'total', doc['totalBytes'])


if __name__ == '__main__':
    main()
