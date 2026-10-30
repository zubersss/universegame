"""Heliocentric position vectors at EPOCH from JPL DE421 (task W1, interim).

Reads the JPL DE421 Chebyshev series distributed on PyPI as the `de421`
package (2008.1, MIT packaging by Brandon Rhodes; data: JPL, Folkner,
Williams & Boggs 2009, IPN Progress Report 42-178) with jplephem's legacy
reader. The package does not build on current setuptools, so download and
unpack it, then pass its data directory:
  pip download de421==2008.1 --no-deps --no-binary :all: -d /tmp/de421
  tar -xzf /tmp/de421/de421-2008.1.tar.gz -C /tmp/de421
  python3 -I scripts/data/sol_positions_de421.py /tmp/de421/de421-2008.1/de421 > /tmp/de421-vectors.json
DE421 has no satellite ephemerides other than the Moon; Europa and Titan are
absent (build_sol.py marks their direction fictional). Outer planets are
system barycenters (offset from the planet center by < 0.01 of the game scale).
Output frame: J2000 mean ecliptic (obliquity 84381.448"), heliocentric, km.
"""
import json
import math
import sys
import types

from jplephem.ephem import Ephemeris

EPS = math.radians(84381.448 / 3600.0)
JD = 2461041.5  # 2026-01-01 00:00:00 TDB


def ecl(v):
    x, y, z = (float(c) for c in v)
    c, s = math.cos(EPS), math.sin(EPS)
    return [x, c * y + s * z, -s * y + c * z]


def main():
    data_dir = sys.argv[1]
    mod = types.SimpleNamespace(__name__='de421', __file__=data_dir.rstrip('/') + '/__init__.py')
    eph = Ephemeris(mod)
    sun = eph.position('sun', JD).ravel()
    emb = eph.position('earthmoon', JD).ravel()
    moon_geo = eph.position('moon', JD).ravel()
    earth = emb - moon_geo * eph.earth_share
    moon = earth + moon_geo
    bodies = {'mercury': eph.position('mercury', JD).ravel(), 'venus': eph.position('venus', JD).ravel(), 'earth': earth, 'moon': moon,
              'mars': eph.position('mars', JD).ravel(), 'jupiter': eph.position('jupiter', JD).ravel(), 'saturn': eph.position('saturn', JD).ravel(),
              'uranus': eph.position('uranus', JD).ravel(), 'neptune': eph.position('neptune', JD).ravel()}
    vectors = {k: ecl(v - sun) for k, v in bodies.items()}
    print(json.dumps({'source': 'de421', 'jd_tdb': JD, 'frame': 'J2000 mean ecliptic, heliocentric, km', 'vectors': vectors}, indent=1))


if __name__ == '__main__':
    main()
