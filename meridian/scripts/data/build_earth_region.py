"""Regional high-resolution elevation overlay for the Earth dataset (task W5).

The global elevation layer is a 10' grid; where the game needs real relief at
walking scale (the First Light route over the Southern Alps) a small regional
grid overrides it. Source: AWS Terrain Tiles ("terrarium" PNG, zoom 9, about
225 m per pixel at 43 S), which at zooms 7-9 are composited from SRTM and
GMTED2010 on land (U.S. Geological Survey, public domain) and ETOPO1 in the
ocean (NOAA, public domain); each tile's x-amz-meta-x-imagery-sources header
names the images it was built from and is recorded in the metadata.

Output: src/data/earth/earth-region-<name>.bin (LSR1, int16 metres, node-registered
lat/lon grid: row 0 = north edge, column 0 = west edge, no wrap) and an entry in
earth.json "regions" (bounds, resolution, provenance). Terrarium decoding:
metres = R * 256 + G + B / 256 - 32768; the grid is sampled bilinearly from the
Web Mercator mosaic at each node.

Run (from meridian/):
  python3 -I scripts/data/build_earth_region.py --tiles <dir with z9_X_Y.png + headers.txt> \
      --name southern-alps --north -42.2 --south -44.2 --west 169.2 --east 171.8 --res-arcsec 10 \
      --out src/data/earth
"""
import argparse
import hashlib
import json
import math
import os
import sys

import numpy as np
from PIL import Image

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_earth import encode_lsr, raw_sha256  # noqa: E402

TILE = 256
URL = 'https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{z}/{x}/{y}.png'


def merc_px(lat, lon, z):
    """Global Web Mercator pixel coordinates (continuous; pixel i spans [i, i + 1))."""
    n = TILE * 2 ** z
    x = (lon + 180.0) / 360.0 * n
    phi = np.radians(lat)
    y = (1.0 - np.log(np.tan(phi) + 1.0 / np.cos(phi)) / math.pi) / 2.0 * n
    return x, y


def decode_terrarium(path):
    a = np.asarray(Image.open(path).convert('RGB'), dtype=np.float64)
    return a[..., 0] * 256.0 + a[..., 1] + a[..., 2] / 256.0 - 32768.0


def sha256(path):
    with open(path, 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tiles', required=True)
    ap.add_argument('--zoom', type=int, default=9)
    ap.add_argument('--name', required=True)
    ap.add_argument('--north', type=float, required=True)
    ap.add_argument('--south', type=float, required=True)
    ap.add_argument('--west', type=float, required=True)
    ap.add_argument('--east', type=float, required=True)
    ap.add_argument('--res-arcsec', type=float, default=10)
    ap.add_argument('--accessed', default='2026-10-30')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    z = args.zoom
    res = args.res_arcsec / 3600.0

    # Node grid.
    h = int(round((args.north - args.south) / res)) + 1
    w = int(round((args.east - args.west) / res)) + 1
    lats = args.north - np.arange(h) * res
    lons = args.west + np.arange(w) * res
    lat2, lon2 = np.meshgrid(lats, lons, indexing='ij')
    px, py = merc_px(lat2, lon2, z)

    # Mosaic of the tiles that cover the grid (one pixel of margin for bilinear).
    tx0, tx1 = int(math.floor((px.min() - 1) / TILE)), int(math.floor((px.max() + 1) / TILE))
    ty0, ty1 = int(math.floor((py.min() - 1) / TILE)), int(math.floor((py.max() + 1) / TILE))
    headers = {}
    with open(os.path.join(args.tiles, 'headers.txt')) as fh:
        for line in fh:
            key, _, src = line.rstrip('\n').partition('\t')
            headers[key] = [s.strip() for s in src.split(',') if s.strip()]
    mosaic = np.zeros(((ty1 - ty0 + 1) * TILE, (tx1 - tx0 + 1) * TILE))
    tiles = []
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            path = os.path.join(args.tiles, f'z{z}_{tx}_{ty}.png')
            if not os.path.exists(path):
                sys.exit(f'missing tile {path}')
            mosaic[(ty - ty0) * TILE:(ty - ty0 + 1) * TILE, (tx - tx0) * TILE:(tx - tx0 + 1) * TILE] = decode_terrarium(path)
            key = f'{z}/{tx}/{ty}'
            tiles.append({'tile': key, 'sha256': sha256(path), 'imagerySources': headers.get(key, [])})

    # Bilinear at pixel centres (pixel i is centred on i + 0.5).
    fx = px - tx0 * TILE - 0.5
    fy = py - ty0 * TILE - 0.5
    x0 = np.floor(fx).astype(int)
    y0 = np.floor(fy).astype(int)
    ax = fx - x0
    ay = fy - y0
    assert x0.min() >= 0 and y0.min() >= 0 and x0.max() + 1 < mosaic.shape[1] and y0.max() + 1 < mosaic.shape[0]
    v = (mosaic[y0, x0] * (1 - ax) * (1 - ay) + mosaic[y0, x0 + 1] * ax * (1 - ay)
         + mosaic[y0 + 1, x0] * (1 - ax) * ay + mosaic[y0 + 1, x0 + 1] * ax * ay)
    elev = np.clip(np.rint(v), -32767, 32767).astype(np.int16)

    os.makedirs(args.out, exist_ok=True)
    fname = f'earth-region-{args.name}.bin'
    data = encode_lsr(elev, 'int16')
    with open(os.path.join(args.out, fname), 'wb') as fh:
        fh.write(data)
    sources = sorted({s.split('/')[0] for t in tiles for s in t['imagerySources']})
    entry = {
        'name': args.name, 'file': fname, 'bytes': len(data), 'sha256Decoded': raw_sha256(elev, 'int16'),
        'dtype': 'int16', 'width': w, 'height': h, 'channels': 1, 'res': res, 'scale': 1, 'offset': 0,
        'north': args.north, 'south': args.south, 'west': args.west, 'east': args.east,
        'units': 'm', 'datum': 'mean sea level', 'min': int(elev.min()), 'max': int(elev.max()), 'tag': 'measured',
        'grid': 'node-registered latitude/longitude: row 0 = north edge, column 0 = west edge (no wrap)',
        'source': {
            'name': 'AWS Terrain Tiles (Mapzen/Tilezen joerd), terrarium encoding',
            'url': URL.replace('{z}', str(z)), 'zoom': z, 'accessed': args.accessed,
            'composition': 'zooms 7-9: SRTM and GMTED2010 on land (U.S. Geological Survey), ETOPO1 in the ocean (NOAA)',
            'imagerySources': sources,
            'license': 'public domain (U.S. Government works: SRTM, GMTED2010, ETOPO1)',
            'credit': 'SRTM and GMTED2010 data courtesy of the U.S. Geological Survey; ETOPO1: NOAA National Centers for Environmental Information',
            'docs': ['https://github.com/tilezen/joerd/blob/master/docs/data-sources.md', 'https://github.com/tilezen/joerd/blob/master/docs/attribution.md'],
            'tiles': tiles,
        },
        'method': 'Web Mercator mosaic of the zoom tiles, sampled bilinearly at each node (pixel centres), rounded to whole metres.',
    }
    assert set(sources) <= {'srtm', 'gmted', 'etopo1'}, f'unexpected imagery sources {sources}'

    meta_path = os.path.join(args.out, 'earth.json')
    with open(meta_path) as fh:
        doc = json.load(fh)
    regions = [r for r in doc.get('regions', []) if r['name'] != args.name] + [entry]
    doc['regions'] = regions
    doc['totalBytes'] = sum(l['bytes'] for l in doc['layers'].values()) + sum(r['bytes'] for r in regions)
    credit = 'Regional topography (Southern Alps): SRTM and GMTED2010 courtesy of the U.S. Geological Survey, ETOPO1 (NOAA), via AWS Terrain Tiles (public domain)'
    if credit not in doc['credits']:
        doc['credits'].append(credit)
    with open(meta_path, 'w') as fh:
        json.dump(doc, fh, indent=1)
        fh.write('\n')
    print(json.dumps({k: entry[k] for k in ('file', 'bytes', 'width', 'height', 'min', 'max')}), 'total', doc['totalBytes'], 'sources', sources)


if __name__ == '__main__':
    main()
