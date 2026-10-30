"""Builds coarse land-cover (biome) fractions on the 0.25-degree Earth grid.

Source: ESA WorldCover 10 m 2021 v200 (CC BY 4.0), public S3 bucket
https://esa-worldcover.s3.eu-central-1.amazonaws.com/ , prefix v200/2021/map/
(3 x 3 degree Cloud-Optimized GeoTIFF tiles, EPSG:4326, uint8 class codes).
Only the coarsest internal overview of each tile (factor 64: 562 x 562 px,
about 590 m pixels) is read, through GDAL /vsicurl/. Nothing is stored on
disk except the outputs, unless --cache-dir is given (per-tile overview
arrays, keyed by S3 ETag, so a re-run does not download again).

Every overview pixel is binned by its pixel-centre lat/lon into the node grid
of earth_grid.py (res 0.25 deg, H 721, W 1441):
  i = round((90 - lat) / 0.25),  j = round((lon + 180) / 0.25) mod 1440,
then column 0 is copied into column 1440 (enforce_seam).

Outputs in <out_dir>:
  biome_frac_15m.npy     uint8 (5, H, W): share of land-class pixels per channel
                         (tree, lowveg, bare, ice, tundra), 0..255; all 0 = no land
  biome_land_px_15m.npy  float32 (H, W): land-class overview pixels per cell
  biome_water_15m.npy    uint8 (H, W): class-80 pixels / valid (non-nodata)
                         pixels, 0..255; 0 where the cell has no valid pixel
  biome_frac_15m.json    provenance, class mapping, global statistics, samples
  biome_preview.png      RGB preview, 720 x 360, north up, west left

Run (from meridian/):
  python3 -I scripts/data/worldcover_fractions.py <out_dir> [--cache-dir DIR]
Exit status 0 = every listed tile was read, 3 = outputs written but some
tiles failed (named in the JSON), 1 = aborted, nothing written.
"""
import argparse
import concurrent.futures as cf
import datetime
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True    # leave no __pycache__ in the repo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import earth_grid as eg  # noqa: E402

GDAL_ENV = {
    'GDAL_DISABLE_READDIR_ON_OPEN': 'EMPTY_DIR',
    'CPL_VSIL_CURL_ALLOWED_EXTENSIONS': '.tif',
    'GDAL_HTTP_TIMEOUT': '60',
    'GDAL_HTTP_CONNECTTIMEOUT': '20',
    'GDAL_HTTP_MAX_RETRY': '2',
    'GDAL_HTTP_RETRY_DELAY': '1',
}
for _k, _v in GDAL_ENV.items():
    os.environ.setdefault(_k, _v)

import numpy as np  # noqa: E402
import rasterio  # noqa: E402
import rasterio.cache  # noqa: E402
from PIL import Image  # noqa: E402

BUCKET_URL = 'https://esa-worldcover.s3.eu-central-1.amazonaws.com/'
PREFIX = 'v200/2021/map/'
PRODUCT = 'ESA WorldCover 10 m 2021 v200'
LICENSE = 'CC BY 4.0'
LICENSE_URL = 'https://creativecommons.org/licenses/by/4.0/'
ATTRIBUTION = ('© ESA WorldCover project 2021 / Contains modified Copernicus '
               'Sentinel data (2021) processed by ESA WorldCover consortium')
CITATION = ('Zanaga, D. et al. (2022). ESA WorldCover 10 m 2021 v200. Zenodo. '
            'https://doi.org/10.5281/zenodo.7254221')
TILE_RE = re.compile(r'^v200/2021/map/(ESA_WorldCover_10m_2021_v200_([NS])(\d{2})([EW])(\d{3})_Map\.tif)$')
OVERVIEW_FACTOR = 64
TILE_DEG = 3.0
S3_NS = '{http://s3.amazonaws.com/doc/2006-03-01/}'

RES = 0.25
H, W = eg.grid_shape(RES)          # 721, 1441
NCOL = W - 1                       # unique longitudes; column W-1 is the seam copy

CODE_NAMES = {0: 'no data', 10: 'tree cover', 20: 'shrubland', 30: 'grassland',
              40: 'cropland', 50: 'built-up', 60: 'bare / sparse vegetation',
              70: 'snow and ice', 80: 'permanent water bodies', 90: 'herbaceous wetland',
              95: 'mangroves', 100: 'moss and lichen'}
CODES = tuple(sorted(CODE_NAMES))
SLOT = {c: s for s, c in enumerate(CODES)}
OTHER = len(CODES)                 # slot for any code outside the legend
NSLOT = OTHER + 1
LUT = np.full(256, OTHER, np.uint8)
for _c, _s in SLOT.items():
    LUT[_c] = _s
CHANNELS = (('tree', (10, 95)), ('lowveg', (20, 30, 40, 50, 90)), ('bare', (60,)),
            ('ice', (70,)), ('tundra', (100,)))
WATER, NODATA = 80, 0

PREVIEW_RGB = {'tree': (22, 88, 36), 'lowveg': (150, 200, 92), 'bare': (214, 188, 140),
               'ice': (246, 247, 251), 'tundra': (140, 124, 104)}
WATER_RGB = (40, 96, 176)          # valid pixels, all class 80
NO_DATA_RGB = (14, 30, 72)         # no valid WorldCover pixel in the cell

SAMPLES = (('amazon', -3, -60, 'tree'), ('sahara', 23, 10, 'bare'),
           ('greenland_interior', 72, -40, 'ice'), ('siberian_taiga', 62, 100, 'tree'),
           ('great_plains', 40, -100, 'lowveg'), ('arctic_canada', 68, -100, 'tundra|lowveg|bare'),
           ('australia_interior', -25, 133, 'bare|lowveg'))
EARTH_RADIUS_KM = 6371.0088        # IUGG mean radius, for the approximate areas


def http_get(url, retries, max_bytes=16 << 20):
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                body = r.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise ValueError('response too large')
            return body
        except Exception as e:
            if attempt == retries:
                raise RuntimeError('GET %s failed: %s' % (url, e)) from e
            time.sleep(2 ** attempt)


def list_tiles(retries):
    """S3 ListObjectsV2 of the map prefix -> sorted [(name, key, size, etag)], skipped keys."""
    tiles, skipped, token = [], [], None
    while True:
        q = {'list-type': '2', 'prefix': PREFIX}
        if token:
            q['continuation-token'] = token
        root = ET.fromstring(http_get(BUCKET_URL + '?' + urllib.parse.urlencode(q), retries))
        for c in root.findall(S3_NS + 'Contents'):
            key = c.findtext(S3_NS + 'Key')
            m = TILE_RE.match(key or '')
            if not m:
                skipped.append(key)
                continue
            tiles.append((m.group(1), key, int(c.findtext(S3_NS + 'Size')),
                          (c.findtext(S3_NS + 'ETag') or '').strip('"')))
        if root.findtext(S3_NS + 'IsTruncated') != 'true':
            break
        token = root.findtext(S3_NS + 'NextContinuationToken')
        if not token:
            raise RuntimeError('truncated listing without continuation token')
    tiles.sort()
    return tiles, skipped


def tile_origin(name):
    """(west lon, north lat) of a tile from its name (name = SW corner)."""
    m = re.search(r'_([NS])(\d{2})([EW])(\d{3})_Map', name)
    lat0 = int(m.group(2)) * (1 if m.group(1) == 'N' else -1)
    lon0 = int(m.group(4)) * (1 if m.group(3) == 'E' else -1)
    return float(lon0), float(lat0) + TILE_DEG


def cache_path(cache_dir, name, etag):
    tag = etag if re.fullmatch(r'[0-9a-fA-F]{32}(-\d+)?', etag) else hashlib.sha256(etag.encode()).hexdigest()
    return os.path.join(cache_dir, name[:-4] + '.' + tag + '.npz')


def load_cached(path):
    try:
        with np.load(path, allow_pickle=False) as z:
            a, tf, meta = z['a'], z['tf'], z['meta']
        if a.dtype == np.uint8 and a.ndim == 2 and tf.shape == (6,) and meta.shape == (3,):
            return a, tuple(float(v) for v in tf), [str(v) for v in meta]
    except Exception:
        pass
    return None


def read_overview(key):
    """Coarsest-overview array of one tile, its affine (a, b, c, d, e, f), [version, tile, base size]."""
    url = '/vsicurl/' + BUCKET_URL + key
    with rasterio.open(url) as ds:
        factors = ds.overviews(1)
        tags = ds.tags()
        meta = [tags.get('product_version', ''), tags.get('product_tile', ''),
                '%dx%d' % (ds.width, ds.height)]
        if ds.crs is None or ds.crs.to_epsg() != 4326 or ds.dtypes[0] != 'uint8':
            raise ValueError('unexpected CRS/dtype %s %s' % (ds.crs, ds.dtypes))
    if OVERVIEW_FACTOR not in factors:
        raise ValueError('no factor-%d overview (have %s)' % (OVERVIEW_FACTOR, factors))
    with rasterio.open(url, overview_level=factors.index(OVERVIEW_FACTOR)) as ov:
        a = ov.read(1)
        t = ov.transform
    return a, (t.a, t.b, t.c, t.d, t.e, t.f), meta


def fetch_tile(tile, cache_dir, retries):
    name, key, _size, etag = tile
    cp = cache_path(cache_dir, name, etag) if cache_dir else None
    if cp and os.path.exists(cp):
        got = load_cached(cp)
        if got:
            return got + ('cache',)
    for attempt in range(retries + 1):
        if attempt:
            time.sleep(2 ** (attempt - 1))
            rasterio.cache.invalidate(BUCKET_URL + key)
        try:
            a, tf, meta = read_overview(key)
            break
        except Exception as e:
            err = '%s: %s' % (type(e).__name__, e)
    else:
        raise RuntimeError('%d attempts failed, last: %s' % (retries + 1, err))
    if cp:
        tmp = cp + '.tmp'
        with open(tmp, 'wb') as fh:
            np.savez_compressed(fh, a=a, tf=np.array(tf, np.float64), meta=np.array(meta))
        os.replace(tmp, cp)
    return a, tf, meta, 'network'


def bin_tile(a, tf):
    """Per-cell class-slot counts of one tile: (i0, j0, counts[ni, nj, NSLOT], min tie distance)."""
    ta, tb, tc, td, te, tfy = tf
    if tb != 0 or td != 0 or not ta > 0 or not te < 0:
        raise ValueError('unexpected transform %s' % (tf,))
    h, w = a.shape
    x = (tc + ta * (np.arange(w) + 0.5) + 180.0) / RES     # pixel-centre lon in cells
    y = (90.0 - (tfy + te * (np.arange(h) + 0.5))) / RES    # pixel-centre colatitude in cells
    tie = min(float(np.abs(np.abs(v - np.floor(v)) - 0.5).min()) for v in (x, y))
    jj = np.rint(x).astype(np.int64)                         # unwrapped; mod NCOL on accumulate
    ii = np.rint(y).astype(np.int64)
    if ii.min() < 0 or ii.max() > H - 1 or jj.min() < 0 or jj.max() > NCOL:
        raise ValueError('pixel centres outside the grid')
    i0, j0 = int(ii.min()), int(jj.min())
    ni, nj = int(ii.max()) - i0 + 1, int(jj.max()) - j0 + 1
    cell = (ii - i0)[:, None] * nj + (jj - j0)[None, :]
    flat = (cell * NSLOT + LUT[a]).ravel()
    counts = np.bincount(flat, minlength=ni * nj * NSLOT).reshape(ni, nj, NSLOT)
    return i0, j0, counts, tie


def process_tile(tile, cache_dir, retries):
    a, tf, meta, src = fetch_tile(tile, cache_dir, retries)
    i0, j0, counts, tie = bin_tile(a, tf)
    lon0, lat_top = tile_origin(tile[0])
    geo_ok = (abs(tf[2] - lon0) < 1e-9 and abs(tf[5] - lat_top) < 1e-9
              and abs(tf[0] * a.shape[1] - TILE_DEG) < 1e-9 and abs(-tf[4] * a.shape[0] - TILE_DEG) < 1e-9)
    tile_id = re.search(r'_([NS]\d{2}[EW]\d{3})_Map', tile[0]).group(1)
    info = {'shape': a.shape, 'pix_deg': (round(tf[0], 15), round(-tf[4], 15)), 'version': meta[0],
            'tag_ok': meta[1] == tile_id, 'base': meta[2], 'geo_ok': geo_ok, 'src': src, 'tie': tie}
    return i0, j0, counts, info


def scale255(num, den):
    """round(255 * num / den), ties up, exact integer arithmetic; 0 where den == 0."""
    d = np.maximum(den, 1)
    return np.where(den > 0, (510 * num + d) // (2 * d), 0).astype(np.uint8)


def with_seam(a):
    """(..., H, NCOL) -> (..., H, W) with the last column copied from column 0."""
    out = np.concatenate([a, a[..., :1]], axis=-1)
    return np.ascontiguousarray(eg.enforce_seam(out))


def node_index(lat, lon):
    return round((90.0 - lat) / RES), round((lon + 180.0) / RES) % NCOL


def preview(frac, water, land, valid):
    cols = np.array([PREVIEW_RGB[n] for n, _ in CHANNELS], np.float64)
    f = frac[:, :, :NCOL].astype(np.float64)
    s = f.sum(axis=0)
    landrgb = np.einsum('khw,kc->hwc', f / np.maximum(s, 1)[None], cols)
    wf = (water[:, :NCOL].astype(np.float64) / 255.0)[..., None]
    rgb = (1 - wf) * landrgb + wf * np.array(WATER_RGB, np.float64)
    rgb[valid == 0] = NO_DATA_RGB
    rgb = rgb[:H - 1]                                          # 720 rows x 1440 cols
    rgb = rgb.reshape((H - 1) // 2, 2, NCOL // 2, 2, 3).mean(axis=(1, 3))
    return Image.fromarray(np.rint(rgb).astype(np.uint8), 'RGB')


def sha256_file(path):
    with open(path, 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description='ESA WorldCover 2021 -> 0.25-degree biome fractions')
    ap.add_argument('out_dir')
    ap.add_argument('--cache-dir', help='optional directory for per-tile overview arrays (.npz)')
    ap.add_argument('--workers', type=int, default=12)
    ap.add_argument('--retries', type=int, default=4, help='retries per tile after the first attempt')
    ap.add_argument('--max-failures', type=int, default=50, help='abort (write nothing) beyond this')
    ap.add_argument('--access-date', default=datetime.datetime.now(datetime.timezone.utc).date().isoformat())
    ap.add_argument('--limit', type=int, default=0, help='debug: only the first N tiles (partial output)')
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    if args.cache_dir:
        os.makedirs(args.cache_dir, exist_ok=True)

    t0 = time.time()
    tiles, skipped = list_tiles(args.retries)
    n_listed = len(tiles)
    if args.limit:
        tiles = tiles[:args.limit]
    print('listed %d tiles under %s%s (%d other keys skipped)' % (n_listed, BUCKET_URL, PREFIX, len(skipped)),
          file=sys.stderr)

    counts = np.zeros((H, NCOL, NSLOT), np.int64)
    infos, failed = {}, []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(process_tile, t, args.cache_dir, args.retries): t[0] for t in tiles}
        for n, fut in enumerate(cf.as_completed(futs), 1):
            name = futs[fut]
            try:
                i0, j0, c, info = fut.result()
            except Exception as e:
                failed.append({'name': name, 'error': str(e)[:300]})
                print('FAILED %s: %s' % (name, e), file=sys.stderr)
                if len(failed) > args.max_failures:
                    for f in futs:
                        f.cancel()
                    print('aborting: more than %d failed tiles; nothing written' % args.max_failures,
                          file=sys.stderr)
                    return 1
                continue
            rows = np.arange(i0, i0 + c.shape[0])
            cols = np.arange(j0, j0 + c.shape[1]) % NCOL
            counts[np.ix_(rows, cols)] += c
            infos[name] = info
            if n % 250 == 0 or n == len(tiles):
                print('  %d/%d tiles (%.0f s)' % (n, len(tiles), time.time() - t0), file=sys.stderr)
    failed.sort(key=lambda d: d['name'])

    slot_tot = counts.sum(axis=(0, 1))
    chan = np.stack([counts[:, :, [SLOT[c] for c in codes]].sum(axis=2) for _, codes in CHANNELS])
    land = chan.sum(axis=0)
    water = counts[:, :, SLOT[WATER]]
    valid = land + water

    frac_u8 = with_seam(scale255(chan, land[None]))
    water_u8 = with_seam(scale255(water, valid))
    land_px = with_seam(land.astype(np.float32))
    assert frac_u8.shape == (5, H, W) and water_u8.shape == (H, W) and land_px.shape == (H, W)

    out = {'biome_frac_15m.npy': frac_u8, 'biome_land_px_15m.npy': land_px, 'biome_water_15m.npy': water_u8}
    files = {}
    for fn, arr in out.items():
        p = os.path.join(args.out_dir, fn)
        np.save(p, arr)
        files[fn] = {'dtype': str(arr.dtype), 'shape': list(arr.shape), 'sha256': sha256_file(p)}
    img = preview(frac_u8, water_u8, land, valid)
    img.save(os.path.join(args.out_dir, 'biome_preview.png'))
    files['biome_preview.png'] = {'size': list(img.size)}

    # Statistics (unique columns only; each overview pixel weighted by its cell's area).
    wts = eg.node_area_weights(RES)                                  # (H, 1)
    land_w = float((land * wts).sum())
    shares = {n: (float((chan[k] * wts).sum()) / land_w if land_w else None)
              for k, (n, _) in enumerate(CHANNELS)}
    pix = sorted({v['pix_deg'] for v in infos.values()})
    shapes = sorted({tuple(v['shape']) for v in infos.values()})
    area_km2 = None
    if len(pix) == 1 and pix[0][0] == pix[0][1]:
        cosl = np.cos(np.radians(eg.node_lats(RES)))[:, None]
        px_km2 = (EARTH_RADIUS_KM * np.radians(pix[0][0])) ** 2 * cosl   # (H, 1)
        area_km2 = {'land_class': float((land * px_km2).sum()), 'water_class80': float((water * px_km2).sum())}
        area_km2.update({n: float((chan[k] * px_km2).sum()) for k, (n, _) in enumerate(CHANNELS)})
    lat = eg.node_lats(RES)

    def region(mask_rows, lon_lo=-180.0, lon_hi=180.0):
        lon = eg.node_lons(RES)[:NCOL]
        m = mask_rows[:, None] & ((lon >= lon_lo) & (lon <= lon_hi))[None, :]
        lw = float((land * wts * m).sum())
        return {'cells_with_land': int(((land > 0) & m).sum()),
                'land_px': int((land * m).sum()),
                'ice_share': (float((chan[3] * wts * m).sum()) / lw) if lw else None}

    samples = {}
    for nm, la, lo, expect in SAMPLES:
        i, j = node_index(la, lo)
        fr = [int(v) for v in frac_u8[:, i, j]]
        dom = CHANNELS[int(np.argmax(fr))][0] if land[i, j] else None
        nb = chan[:, i - 2:i + 3, [(j + d) % NCOL for d in range(-2, 3)]].sum(axis=(1, 2))   # 5 x 5 nodes
        nb_dom = CHANNELS[int(np.argmax(nb))][0] if nb.sum() else None
        samples[nm] = {'lat': la, 'lon': lo, 'node': [i, j], 'land_px': int(land[i, j]),
                       'water': round(int(water_u8[i, j]) / 255.0, 3),
                       'frac': {CHANNELS[k][0]: round(fr[k] / 255.0, 3) for k in range(5)},
                       'dominant': dom, 'expected': expect, 'ok': dom in expect.split('|'),
                       'nbhd_5x5_frac': {CHANNELS[k][0]: round(float(nb[k]) / max(int(nb.sum()), 1), 3)
                                         for k in range(5)},
                       'nbhd_5x5_dominant': nb_dom}
    land_rows = np.where(land.any(axis=1))[0]
    sw_lats = [tile_origin(t[0])[1] - TILE_DEG for t in tiles]
    n_cache = sum(1 for v in infos.values() if v['src'] == 'cache')
    sums = frac_u8[:, :, :NCOL].astype(np.int64).sum(axis=0)[land > 0]

    meta = {
        'layer': 'biome_frac_15m',
        'description': 'Coarse land-cover (biome) fractions on the 0.25-degree node grid, from the '
                       'factor-%d overviews of ESA WorldCover 10 m 2021 v200.' % OVERVIEW_FACTOR,
        'script': 'scripts/data/worldcover_fractions.py',
        'source': {'product': PRODUCT, 'product_version_tags': sorted({v['version'] for v in infos.values()}),
                   'bucket_url': BUCKET_URL, 'prefix': PREFIX, 'listing': 'S3 ListObjectsV2',
                   'access_date': args.access_date, 'license': LICENSE, 'license_url': LICENSE_URL,
                   'attribution': ATTRIBUTION, 'citation': CITATION},
        'overview': {'factor': OVERVIEW_FACTOR, 'tile_overview_shapes': [list(s) for s in shapes],
                     'base_sizes': sorted({v['base'] for v in infos.values()}),
                     'pixel_deg': [list(p) for p in pix],
                     'resampling_note': 'The overviews behave like majority (mode) resampling: on test tile '
                                        'N48E009, 97% of factor-64 pixels equal the mode of their 64x64 source '
                                        'block. Fractions are therefore shares of ~590 m majority-class pixels, '
                                        'not true 10 m area shares. Against the factor-8 overview on tiles '
                                        'N48E009, S03W060, N39W102 and N60E099, per-cell channel fractions '
                                        'differed by 0.6-2.5 percentage points on average, the locally dominant '
                                        'class being inflated and rare classes (scattered built-up, narrow '
                                        'rivers, small lakes) under-represented.'},
        'tiles': {'listed': n_listed, 'processed': len(tiles), 'read': len(infos), 'failed': len(failed),
                  'failed_tiles': failed, 'from_cache': n_cache, 'from_network': len(infos) - n_cache,
                  'skipped_keys': skipped[:50], 'partial_run_limit': args.limit or None,
                  'geometry_mismatch': sorted(n for n, v in infos.items() if not v['geo_ok']),
                  'tile_tag_mismatch': sorted(n for n, v in infos.items() if not v['tag_ok'])},
        'grid': {'res_deg': RES, 'H': H, 'W': W, 'registration': 'node: row i -> lat 90 - i*res, '
                 'column j -> lon -180 + j*res, column W-1 duplicates column 0',
                 'binning': 'each overview pixel to node i=round((90-lat)/res), j=round((lon+180)/res) mod %d '
                            'by its pixel-centre lat/lon' % NCOL,
                 'min_centre_distance_to_cell_edge_cells': min((v['tie'] for v in infos.values()), default=None)},
        'channels': [n for n, _ in CHANNELS],
        'class_mapping': {n: {str(c): CODE_NAMES[c] for c in codes} for n, codes in CHANNELS},
        'excluded_from_land': {str(WATER): CODE_NAMES[WATER] + ' (counted in biome_water_15m)',
                               str(NODATA): CODE_NAMES[NODATA]},
        'files': files,
        'encoding': {'biome_frac_15m.npy': 'round(255 * channel_px / land_px) per cell, ties up; all channels 0 '
                                           'where land_px == 0',
                     'biome_land_px_15m.npy': 'count of land-class overview pixels (codes 10..70, 90, 95, 100)',
                     'biome_water_15m.npy': 'round(255 * class80_px / (land_px + class80_px)); 0 where that '
                                            'denominator is 0 (no WorldCover data: e.g. open ocean outside '
                                            'tiles, south of 60S). land_px == 0 and water == 255 means all water. '
                                            'Class 80 includes sea near coasts inside the tile footprints; '
                                            'farther offshore WorldCover pixels are no data.'},
        'stats': {
            'pixel_counts_by_code': {str(c): int(slot_tot[SLOT[c]]) for c in CODES},
            'pixels_outside_legend': int(slot_tot[OTHER]),
            'land_share_area_weighted': shares,
            'approx_area_km2': area_km2,
            'cells_with_land': int((land > 0).sum()),
            'cells_with_valid_data': int((valid > 0).sum()),
            'cells_total_unique': H * NCOL,
            'frac_sum_min_max': [int(sums.min()), int(sums.max())] if sums.size else None,
            'land_px_per_cell_max': int(land.max()),
            'tile_lat_extent': [min(sw_lats), max(sw_lats) + TILE_DEG] if sw_lats else None,
            'land_node_lat_range': [float(lat[land_rows[-1]]), float(lat[land_rows[0]])] if land_rows.size else None,
            'south_of_60S': region(lat < -60),
            'greenland_box_65_80N_50_30W': region((lat >= 65) & (lat <= 80), -50, -30),
        },
        'samples': samples,
    }
    with open(os.path.join(args.out_dir, 'biome_frac_15m.json'), 'w') as fh:
        json.dump(meta, fh, indent=1, ensure_ascii=False)
        fh.write('\n')

    print('%s, %s%s, overview factor %d, accessed %s' % (PRODUCT, BUCKET_URL, PREFIX, OVERVIEW_FACTOR,
                                                       args.access_date))
    print('tiles listed %d, read %d (cache %d), failed %d%s' % (
        n_listed, len(infos), n_cache, len(failed),
        (': ' + ', '.join(f['name'] for f in failed)) if failed else ''))
    print('land share (area-weighted): ' + ', '.join('%s %.4f' % (n, s or 0) for n, s in shares.items()))
    for fn, d in files.items():
        print('  %s %s' % (fn, ' '.join('%s=%s' % kv for kv in d.items())))
    print('license %s; %s; %s' % (LICENSE, ATTRIBUTION, CITATION))
    print('done in %.0f s' % (time.time() - t0), file=sys.stderr)
    return 3 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
