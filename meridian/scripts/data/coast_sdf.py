"""Coastline signed-distance field + land/lake rasters from Natural Earth 1:10m.

Inputs (public domain, https://www.naturalearthdata.com/about/terms-of-use/) come
from the canonical repository github.com/nvkelso/natural-earth-vector (master):
ne_10m_land, ne_10m_minor_islands, ne_10m_antarctic_ice_shelves_polys, ne_10m_lakes
(GeoJSON) and VERSION. Missing files are fetched into <download_dir>; existing
files are reused, so re-runs on the same inputs give byte-identical .npy files.

Outputs in <output_dir> (node-registered grids, see earth_grid.py):
  coast_sdf_5m.npy  float32 (2161, 4321) signed distance to the coastline in km,
                    > 0 on land (incl. ice shelves, islands), < 0 on ocean and lakes
  lake_id_5m.npy    uint16 (2161, 4321) 1-based ne_10m_lakes feature index (0 = none)
  water_id_5m.npy   uint16 (2161, 4321) nearest water body (lake id, 0 = sea), at 1.25'

  lakes.json, coast_sdf_5m.json (provenance, stats), coast_preview[_med].png

Run (from meridian/):
  python3 -I scripts/data/coast_sdf.py <download_dir> <output_dir>
"""
import hashlib
import json
import math
import os
import shutil
import sys
import time
import urllib.error
import urllib.request

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.dont_write_bytecode = True   # keep the repository free of __pycache__
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import earth_grid as eg  # noqa: E402

BASE = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/'
LAND_LAYERS = ('ne_10m_land', 'ne_10m_minor_islands', 'ne_10m_antarctic_ice_shelves_polys')
LAKE_LAYER = 'ne_10m_lakes'
SKIP_FEATURECLA = ('Null island',)  # fictitious 0.009 deg square at 0N 0E in ne_10m_land
ACCESSED = '2026-10-30'
LICENSE = 'public domain (https://www.naturalearthdata.com/about/terms-of-use/)'

N_SUPER = 48           # super-grid nodes per degree (1.25 arc-minutes)
STEP = 4               # super-grid nodes per output node (5 arc-minutes)
SS = 4                 # Pillow canvas pixels per super-grid node (see raster_polygon)
TILES = 4              # longitude tiles for the distance transform (bounds memory)
PAD0 = 1536            # initial wrap-around padding (columns per side) of each tile
R_KM = 6371.0          # mean Earth radius
KM_PER_PX = R_KM * math.pi / 180.0 / N_SUPER   # meridional super-pixel, 2.31656 km

SANITY = [  # label, lat, lon (None = whole row), expected sign (+1 land, -1 water)
    ('Atlantic', 0.0, -30.0, -1), ('Central Africa', 0.0, 25.0, 1),
    ('Australia', -25.0, 135.0, 1), ('South Pacific', -25.0, -135.0, -1),
    ('Caspian Sea', 42.0, 50.5, -1), ('Lake Victoria', -1.0, 33.0, -1),
    ('Lake Superior', 47.7, -87.5, -1), ('Greenland', 72.0, -40.0, 1),
    ('South Pole row', -90.0, None, 1), ('North Pole row', 90.0, None, -1),
    ('Ross Ice Shelf', -81.0, 180.0, 1), ('Hawaii Big Island', 19.6, -155.5, 1),
    ('Sri Lanka', 7.9, 80.7, 1), ('Strait of Gibraltar', 35.95, -5.6, -1),
]


def fetch(url, path):
    """Download url to path unless it exists. Returns False on HTTP 404."""
    if os.path.exists(path):
        return True
    tmp = path + '.part'
    req = urllib.request.Request(url, headers={'User-Agent': 'meridian-coast-sdf'})
    try:
        with urllib.request.urlopen(req, timeout=300) as r, open(tmp, 'wb') as fh:
            shutil.copyfileobj(r, fh, 1 << 20)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        raise
    os.replace(tmp, path)
    return True


def file_record(url, path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return {'url': url, 'file': os.path.basename(path), 'bytes': os.path.getsize(path),
            'sha256': h.hexdigest()}


def load_polygons(path):
    """Features plus a list of (feature_index, [rings as (n, 2) lon/lat arrays])."""
    with open(path, encoding='utf-8') as fh:
        feats = json.load(fh)['features']
    polys, skipped = [], []
    for fi, f in enumerate(feats):
        g, props = f['geometry'], f['properties'] or {}
        if g is None or props.get('featurecla') in SKIP_FEATURECLA:
            skipped.append({'index': fi, 'featurecla': props.get('featurecla')})
            continue
        if g['type'] not in ('Polygon', 'MultiPolygon'):
            raise ValueError('unexpected geometry %s in %s' % (g['type'], path))
        parts = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
        for rings in parts:
            polys.append((fi, [np.asarray(r, dtype=np.float64)[:, :2] for r in rings]))
    return feats, polys, skipped


def raster_polygon(rings, shape):
    """Node mask of one polygon (exterior ring = 1, then its holes = 0) drawn with
    Pillow ImageDraw.polygon on the polygon's own bounding-box canvas.
    Returns (i0, j0, mask) with mask[a, b] = node (i0 + a, j0 + b) is inside.

    Node coordinates: u = (lon + 180) * 48 (column), v = (90 - lat) * 48 (row).
    Pillow truncates vertices to int and fills closed spans, so the canvas is SS
    times finer than the node grid: x_px = SS * (u - j0) + 0.5, y_px = SS * (v - i0)
    + 0.5. Canvas pixel (SS*a, SS*b) then has its centre exactly on node
    (i0 + a, j0 + b), vertices snap to the nearest 1/SS node, and snapping plus the
    closed-span rule can only flip nodes lying within about 1/SS node of an edge.
    """
    h, w = shape
    u = (rings[0][:, 0] + 180.0) * N_SUPER
    v = (90.0 - rings[0][:, 1]) * N_SUPER
    j0, j1 = max(0, int(np.floor(u.min()))), min(w - 1, int(np.ceil(u.max())))
    i0, i1 = max(0, int(np.floor(v.min()))), min(h - 1, int(np.ceil(v.max())))
    im = Image.new('L', (SS * (j1 - j0) + 1, SS * (i1 - i0) + 1), 0)
    draw = ImageDraw.Draw(im)
    for k, ring in enumerate(rings):
        xy = np.empty((len(ring), 2))
        xy[:, 0] = SS * ((ring[:, 0] + 180.0) * N_SUPER - j0) + 0.5
        xy[:, 1] = SS * ((90.0 - ring[:, 1]) * N_SUPER - i0) + 0.5
        draw.polygon(xy.ravel().tolist(), fill=0 if k else 1)
    return i0, j0, np.asarray(im)[::SS, ::SS] > 0


def exact_nodes(rings_uv, i0, j0, mh, mw):
    """Reference for the self-test: exact even-odd node-in-polygon test and each
    node's distance (in nodes) to the polygon boundary."""
    vv, uu = np.mgrid[i0:i0 + mh, j0:j0 + mw].astype(np.float64)
    inside = np.zeros(vv.shape, bool)
    dist = np.full(vv.shape, np.inf)
    for u, v in rings_uv:
        for a in range(len(u) - 1):
            ua, va, du, dv = u[a], v[a], u[a + 1] - u[a], v[a + 1] - v[a]
            if dv != 0:
                cross = (va > vv) != (v[a + 1] > vv)
                inside ^= cross & (uu < ua + (vv - va) * du / dv)
            t = np.clip(((uu - ua) * du + (vv - va) * dv) / (du * du + dv * dv), 0, 1)
            dist = np.minimum(dist, np.hypot(uu - ua - t * du, vv - va - t * dv))
    return inside, dist


def self_test(shape):
    """Synthetic polygons near node (10N, 20E): Pillow nodes vs the exact test."""
    uc, vc = 200.0 * N_SUPER, 80.0 * N_SUPER

    def square(cu, cv, half, deg):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        pts = [(cu + half * (c * x - s * y), cv + half * (s * x + c * y))
               for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1))]
        return np.array(pts)

    cases = {
        'tiny square +-0.3 node around node (10N, 20E)': [square(uc, vc, 0.3, 0)],
        'axis-aligned rectangle, edges 0.3-0.7 node off the nodes':
            [np.array([(uc + .3, vc + .6), (uc + 7.7, vc + .6), (uc + 7.7, vc + 5.4),
                       (uc + .3, vc + 5.4), (uc + .3, vc + .6)])],
        'rotated 30 deg square with a rotated hole':
            [square(uc + .37, vc + .21, 9.3, 30), square(uc + .9, vc - .4, 3.1, 75)[::-1]],
    }
    out = {}
    for name, rings_uv in cases.items():
        rings = [np.column_stack((r[:, 0] / N_SUPER - 180.0, 90.0 - r[:, 1] / N_SUPER))
                 for r in rings_uv]
        i0, j0, m = raster_polygon(rings, shape)
        inside, dist = exact_nodes([(r[:, 0], r[:, 1]) for r in rings_uv], i0, j0, *m.shape)
        bad = m != inside
        out[name] = {'nodes_inside_exact': int(inside.sum()), 'nodes_filled': int(m.sum()),
                     'mismatches': int(bad.sum()),
                     'max_boundary_dist_of_mismatch_nodes':
                         round(float(dist[bad].max()), 4) if bad.any() else None}
        if name.startswith('tiny'):
            ii, jj = np.nonzero(m)
            out[name]['filled_nodes_latlon'] = [
                [float(90.0 - (i0 + a) / N_SUPER), float(-180.0 + (j0 + b) / N_SUPER)]
                for a, b in zip(ii, jj)]
        if (not name.startswith('rotated') and bad.any()) or (dist[bad] > 1.0 / SS).any():
            raise SystemExit('rasterization self-test failed: %s %s' % (name, out[name]))
    return out


def seam_or(a):
    """lon -180 and +180 columns := first column OR last column."""
    a[:, 0] |= a[:, -1]
    a[:, -1] = a[:, 0]


def signed_distance_px(land, lake):
    """Signed distance (super-grid pixels) to the land/water boundary at every
    STEP-th node, > 0 on land: edt_land - 0.5 on land, -(edt_water - 0.5) on water,
    and the water body each node belongs to or is nearest to: the lake id of the
    nearest water super-pixel (0 = sea, including water that is a hole in the land
    polygons such as the Caspian). Measuring both on the same super-grid keeps the
    distance and the water body consistent, so a small lake is its own shore.
    The EDT runs on TILES longitude tiles, each wrap-padded by `pad` columns per
    side. The padding doubles until every distance is < pad, which guarantees no
    nearer feature lay outside a tile's window, i.e. the result equals one EDT of
    the whole periodic grid."""
    h, w = land.shape
    n = w - 1                      # unique columns; column n duplicates column 0
    tw = n // TILES
    assert n % TILES == 0 and tw % STEP == 0 and (h - 1) % STEP == 0
    out = np.empty(((h - 1) // STEP + 1, n // STEP + 1), np.float32)
    wid = np.empty(out.shape, np.uint16)
    pick = np.s_[::STEP, ::STEP]
    pad = PAD0
    while True:
        dmax = 0.0
        for c0 in range(0, n, tw):
            cols = np.arange(c0 - pad, c0 + tw + pad) % n
            sub = land[:, cols]
            core = np.s_[:, pad:pad + tw]
            # For land pixels: distance to, and position of, the nearest water pixel.
            d_land, (ir, ic) = ndimage.distance_transform_edt(sub, return_indices=True)
            d_land = d_land[core]
            d_water = ndimage.distance_transform_edt(~sub)[core]
            dmax = max(dmax, float(d_land.max()), float(d_water.max()))
            out[:, c0 // STEP:(c0 + tw) // STEP] = np.where(
                sub[core][pick], d_land[pick].astype(np.float32) - 0.5,
                0.5 - d_water[pick].astype(np.float32))
            # Water nodes keep their own id (the EDT index of a zero pixel is itself).
            nr = ir[core][pick]
            nc = cols[ic[core][pick]]
            wid[:, c0 // STEP:(c0 + tw) // STEP] = lake[nr, nc]
            del sub, d_land, d_water, ir, ic
        if dmax < pad or pad >= n // 2:
            break
        pad = min(2 * pad, n // 2)
    out[:, -1] = out[:, 0]
    wid[:, -1] = wid[:, 0]
    return out, wid, pad, dmax


def node_index(lat, lon, res):
    return int(round((90.0 - lat) / res)), int(round((lon + 180.0) / res))


def bilinear(a, lat, lon, res):
    y, x = (90.0 - lat) / res, (lon + 180.0) / res
    i, j = min(int(y), a.shape[0] - 2), min(int(x), a.shape[1] - 2)
    fy, fx = y - i, x - j
    return float((1 - fy) * ((1 - fx) * a[i, j] + fx * a[i, j + 1])
                 + fy * ((1 - fx) * a[i + 1, j] + fx * a[i + 1, j + 1]))


def sanity_checks(sdf, lake, lakes_meta, res):
    rows = []
    for label, lat, lon, want in SANITY:
        if lon is None:
            i = node_index(lat, 0.0, res)[0]
            vals = sdf[i]
            ok = bool((np.sign(vals) == want).all())
            rows.append({'check': label, 'lat': lat, 'row': i, 'expect': 'land' if want > 0 else 'water',
                         'min_km': round(float(vals.min()), 2), 'max_km': round(float(vals.max()), 2),
                         'pass': ok})
            continue
        i, j = node_index(lat, lon, res)
        val = float(sdf[i, j])
        lid = int(lake[i, j])
        rows.append({'check': label, 'lat': lat, 'lon': lon,
                     'node_latlon': [90.0 - i * res, -180.0 + j * res],
                     'expect': 'land' if want > 0 else 'water', 'sdf_km': round(val, 2),
                     'bilinear_sdf_km': round(bilinear(sdf, lat, lon, res), 2),
                     'lake': lakes_meta[lid - 1]['name'] if lid else None,
                     'pass': bool(np.sign(val) == want)})
    return rows


def preview(sdf, lake, out_dir, res):
    t_land = np.clip(sdf / 600.0, 0, 1)[..., None]
    t_sea = np.clip(-sdf / 1500.0, 0, 1)[..., None]
    land_rgb = (1 - t_land) * np.array([168, 178, 98]) + t_land * np.array([116, 82, 52])
    sea_rgb = (1 - t_sea) * np.array([96, 156, 214]) + t_sea * np.array([12, 32, 92])
    rgb = np.where(sdf[..., None] > 0, land_rgb, sea_rgb)
    rgb[lake > 0] = (40, 205, 235)
    img = Image.fromarray(np.round(rgb).astype(np.uint8))
    h, w = sdf.shape
    img.crop((0, 0, w - 1, h - 1)).resize(((w - 1) // 4, (h - 1) // 4), Image.Resampling.BOX) \
        .save(os.path.join(out_dir, 'coast_preview.png'))
    # Mediterranean at full 5' resolution: lon -10..40, lat 28..48
    (i0, j0), (i1, j1) = node_index(48, -10, res), node_index(28, 40, res)
    img.crop((j0, i0, j1 + 1, i1 + 1)).save(os.path.join(out_dir, 'coast_preview_med.png'))


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    dl_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(dl_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.perf_counter()
    timing = {}

    sources = []
    for name in LAND_LAYERS + (LAKE_LAYER,):
        url = BASE + 'geojson/' + name + '.geojson'
        path = os.path.join(dl_dir, name + '.geojson')
        if not fetch(url, path):
            sys.exit('missing upstream file: ' + url)
        sources.append(file_record(url, path))
    version = None
    vpath = os.path.join(dl_dir, 'VERSION')
    if fetch(BASE + 'VERSION', vpath):
        sources.append(file_record(BASE + 'VERSION', vpath))
        with open(vpath, encoding='utf-8', errors='replace') as fh:
            version = fh.read(64).strip()
    timing['fetch_hash_s'] = time.perf_counter() - t0

    res, res_out = 1.0 / N_SUPER, 1.0 / (N_SUPER // STEP)
    shape = eg.grid_shape(res)
    tests = self_test(shape)

    # 1. land = land U minor islands U ice shelves, minus lakes, at 1.25'
    t = time.perf_counter()
    land = np.zeros(shape, bool)
    counts, skipped = {}, {}
    for name in LAND_LAYERS:
        _, polys, skip = load_polygons(os.path.join(dl_dir, name + '.geojson'))
        counts[name] = len(polys)
        if skip:
            skipped[name] = skip
        for _, rings in polys:
            i0, j0, m = raster_polygon(rings, shape)
            land[i0:i0 + m.shape[0], j0:j0 + m.shape[1]] |= m
    seam_or(land)
    lake_feats, lake_polys, _ = load_polygons(os.path.join(dl_dir, LAKE_LAYER + '.geojson'))
    counts[LAKE_LAYER] = len(lake_polys)
    if len(lake_feats) >= 65535:
        raise ValueError('too many lakes for uint16')
    lake = np.zeros(shape, np.uint16)
    overlap = 0
    for fi, rings in lake_polys:
        i0, j0, m = raster_polygon(rings, shape)
        ids = lake[i0:i0 + m.shape[0], j0:j0 + m.shape[1]]
        overlap += int(np.count_nonzero(m & (ids > 0) & (ids != fi + 1)))
        ids[m & (ids == 0)] = fi + 1          # lowest feature index wins on overlap
    col = np.where(lake[:, 0] > 0, lake[:, 0], lake[:, -1])
    lake[:, 0] = col
    lake[:, -1] = col
    land &= lake == 0
    land_frac_super = eg.area_fraction(land, res)
    lake_nodes_super = int(np.count_nonzero(lake[:, :-1]))
    lake5 = eg.enforce_seam(lake[::STEP, ::STEP].copy())   # every 4th node = 5' grid
    timing['rasterize_s'] = time.perf_counter() - t

    # 2. signed distance and nearest water body on the super-grid, 3. kept at every 4th node (5' grid)
    t = time.perf_counter()
    sdf_px, water5, pad, dmax = signed_distance_px(land, lake)
    del land, lake
    sdf = eg.enforce_seam((sdf_px.astype(np.float64) * KM_PER_PX).astype(np.float32))
    timing['distance_transform_s'] = time.perf_counter() - t
    assert sdf.shape == lake5.shape == eg.grid_shape(res_out)
    np.save(os.path.join(out_dir, 'coast_sdf_5m.npy'), sdf)
    np.save(os.path.join(out_dir, 'lake_id_5m.npy'), lake5)
    np.save(os.path.join(out_dir, 'water_id_5m.npy'), eg.enforce_seam(water5))

    node_counts = np.bincount(lake5[:, :-1].ravel(), minlength=len(lake_feats) + 1)
    lakes_meta = []
    for fi, f in enumerate(lake_feats):
        p = f['properties'] or {}
        g = f['geometry']
        parts = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
        ext = np.concatenate([np.asarray(rings[0], dtype=np.float64)[:, :2] for rings in parts])
        lakes_meta.append({'id': fi + 1, 'name': p.get('name'), 'scalerank': p.get('scalerank'),
                           'featurecla': p.get('featurecla'), 'ne_id': p.get('ne_id'),
                           'bbox_lon_lat': [round(float(x), 6) for x in (
                               ext[:, 0].min(), ext[:, 1].min(), ext[:, 0].max(), ext[:, 1].max())],
                           'nodes_5m': int(node_counts[fi + 1])})
    with open(os.path.join(out_dir, 'lakes.json'), 'w', encoding='utf-8') as fh:
        json.dump({'source': BASE + 'geojson/' + LAKE_LAYER + '.geojson',
                   'raster': 'lake_id_5m.npy', 'id': '1-based index of the feature in the GeoJSON',
                   'nodes_5m': "nodes per lake on the 5' grid, seam column counted once",
                   'lakes': lakes_meta}, fh, indent=1, ensure_ascii=False)
        fh.write('\n')

    sanity = sanity_checks(sdf, lake5, lakes_meta, res_out)
    seam_ok = bool(np.array_equal(sdf[:, 0], sdf[:, -1]) and np.array_equal(lake5[:, 0], lake5[:, -1]))
    stats = {
        'land_fraction_area_weighted_5m': round(eg.area_fraction(sdf > 0, res_out), 6),
        'land_fraction_area_weighted_1p25m': round(land_frac_super, 6),
        'lake_nodes_5m': int(np.count_nonzero(lake5[:, :-1])),
        'lake_nodes_1p25m': lake_nodes_super,
        'lakes_with_nodes_5m': int(np.count_nonzero(node_counts[1:])),
        'lake_overlap_nodes_1p25m': overlap,
        'sdf_min_km': round(float(sdf.min()), 3), 'sdf_max_km': round(float(sdf.max()), 3),
        'lake_nodes_all_water': bool((sdf[lake5 > 0] < 0).all()),
        'seam_col0_equals_col4320': seam_ok,
        'edt_wrap_pad_columns': pad, 'edt_max_distance_px': round(dmax, 3),
    }
    prov = {
        'layer': 'coast_sdf_5m',
        'outputs': {
            'coast_sdf_5m.npy': 'float32 (2161, 4321) signed distance to the coastline in km; '
                                '> 0 land (incl. ice shelves, islands), < 0 ocean and lakes',
            'lake_id_5m.npy': 'uint16 (2161, 4321) 1-based ne_10m_lakes feature index, 0 = not a lake '
                              '(see lakes.json)',
            'water_id_5m.npy': "uint16 (2161, 4321) water body each node is in or nearest to, found on the "
                               "1.25' super-grid: lake id, 0 = sea (incl. holes in the land polygons)"},
        'grid': {'registration': 'node', 'res_deg': res_out, 'shape': list(sdf.shape),
                 'row_i_lat': '90 - i/12', 'col_j_lon': '-180 + j/12',
                 'seam': 'column 4320 (lon +180) duplicates column 0'},
        'source': {'name': 'Natural Earth 1:10m physical vectors (GeoJSON)',
                   'repository': 'https://github.com/nvkelso/natural-earth-vector (master)',
                   'version': version, 'license': LICENSE, 'accessed': ACCESSED, 'files': sources,
                   'polygon_parts': counts, 'excluded_features': skipped},
        'method': [
            "Super-grid 1/48 deg (1.25'), node-registered, H=8641 W=17281.",
            'Land = ne_10m_land OR ne_10m_minor_islands OR ne_10m_antarctic_ice_shelves_polys, '
            'then AND-NOT ne_10m_lakes (holes of lake polygons stay land). Each polygon part is '
            'drawn with Pillow ImageDraw.polygon on its own bounding-box canvas (exterior ring = 1, '
            'then its holes = 0) and ORed (lakes: AND-NOT) into the global layer.',
            'Pixel transform: u = (lon+180)*48, v = (90-lat)*48 (node units); canvas '
            'x_px = %d*(u-j0)+0.5, y_px = %d*(v-i0)+0.5, sampled at every %dth pixel, so canvas pixel '
            '(%d*a, %d*b) is centred on node (i0+a, j0+b). Pillow truncates vertices to int and '
            'fills closed spans; the %dx canvas confines that to nodes within ~1/%d node of an edge '
            '(self_test).' % (SS, SS, SS, SS, SS, SS, SS),
            'Seam: column 0 and column W-1 := column 0 OR column W-1 (lake ids: first non-zero).',
            'Lake ids: same rasterization; lowest feature index wins where lake polygons overlap '
            '(mostly Great Lakes bay features such as Georgian Bay inside Lake Huron, which thus '
            'keep few or no nodes).',
            'SDF: land raster wrap-padded by %d columns per side (in %d longitude tiles; padding '
            'grown until every distance < pad, so the wrap is exact), '
            'scipy.ndimage.distance_transform_edt on land and on water, sdf_px = edt_land - 0.5 on '
            'land, -(edt_water - 0.5) on water, cropped, times %.6f km (meridional 1/48 deg, '
            'R = 6371.0 km).' % (pad, TILES, KM_PER_PX),
            "5' grid: every 4th super-grid node (exact node correspondence), enforce_seam."],
        'approximations': [
            'Distances are measured in the lat/lon pixel grid: east-west distances are '
            'overestimated by 1/cos(latitude) (no wrap over the poles).',
            "Quantised to the 1.25' super-grid: the coastline sits midway between land and water "
            'nodes, so |sdf| >= 0.5 super-pixel (1.16 km) and errors up to about one super-pixel.',
            'Vertices snap to 1/%d super-node and spans are closed, so nodes within ~1/%d '
            'super-node (~0.6 km) of an edge may differ from an exact point-in-polygon test; '
            'boundary nodes on lat -90 and lon +-180 edges count as inside.' % (SS, SS),
            "Features narrower than the 5' node spacing can be missed by the node sampling.",
            'The Caspian Sea is a hole of the ne_10m_land polygon, not an ne_10m_lakes feature, '
            'so it is water with lake_id 0.',
            "ne_10m_land feature 'Null island' (fictitious 0.009 deg square at 0N 0E) excluded."],
        'self_test': tests,
        'stats': stats,
        'sanity': sanity,
    }
    with open(os.path.join(out_dir, 'coast_sdf_5m.json'), 'w', encoding='utf-8') as fh:
        json.dump(prov, fh, indent=1, ensure_ascii=False)
        fh.write('\n')
    preview(sdf, lake5, out_dir, res_out)
    timing['total_s'] = time.perf_counter() - t0

    print('Natural Earth %s (accessed %s, %s)' % (version, ACCESSED, LICENSE))
    for s in sources:
        print('  %-45s %9d B  sha256 %s' % (s['file'], s['bytes'], s['sha256']))
    print('  polygon parts:', counts, ' excluded:', prov['source']['excluded_features'])
    for name, r in tests.items():
        print('self-test %s: %s' % (name, r))
    print('stats:', json.dumps(stats))
    for r in sanity:
        print('  %-20s %-5s %s %s' % (r['check'], r['expect'], 'PASS' if r['pass'] else 'FAIL',
                                     {k: r[k] for k in r if k.endswith('km') or k == 'lake'}))
    print('timing:', {k: round(v, 1) for k, v in timing.items()})
    print('wrote coast_sdf_5m.npy, lake_id_5m.npy, lakes.json, coast_sdf_5m.json, '
          'coast_preview.png, coast_preview_med.png in', out_dir)


if __name__ == '__main__':
    main()
