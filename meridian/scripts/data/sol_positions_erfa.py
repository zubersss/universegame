"""Interim heliocentric position vectors for src/data/sol.json (task W1).

Stand-in for JPL Horizons while ssd.jpl.nasa.gov is not reachable from the
build environment. Uses the IAU SOFA algorithms through pyerfa:
  - erfa.epv00  Earth heliocentric position (accuracy ~ few km over 1900-2100)
  - erfa.plan94 planets Mercury..Neptune (Simon et al. 1994; arcsecond-class
                for the inner planets, up to ~10 arcsec for the outer ones)
  - erfa.moon98 geocentric Moon (Meeus 1998 simplified ELP; ~10 arcsec)
Output: J2000 mean ecliptic & equinox, km, heliocentric (Sun center), printed
as JSON. Run:  python3 -I scripts/data/sol_positions_erfa.py 2461041.5
Replace with scripts/data/horizons.mjs output when Horizons is reachable.
"""
import json
import math
import sys

import erfa

AU_KM = 149597870.7
# IAU 1976 obliquity of J2000 (the value Horizons uses for its ecliptic frame).
EPS = math.radians(84381.448 / 3600.0)


def ecl(v):
    x, y, z = v
    c, s = math.cos(EPS), math.sin(EPS)
    return [x * AU_KM, (c * y + s * z) * AU_KM, (-s * y + c * z) * AU_KM]


def main():
    jd = float(sys.argv[1]) if len(sys.argv) > 1 else 2461041.5  # 2026-01-01 00:00 TDB
    d1, d2 = 2400000.5, jd - 2400000.5
    out = {}
    names = {1: 'mercury', 2: 'venus', 4: 'mars', 5: 'jupiter', 6: 'saturn', 7: 'uranus', 8: 'neptune'}
    for n, name in names.items():
        pv = erfa.plan94(d1, d2, n)
        out[name] = ecl(pv[0])
    pvh, _pvb = erfa.epv00(d1, d2)
    earth = ecl(pvh[0])
    out['earth'] = earth
    moon_geo = ecl(erfa.moon98(d1, d2)[0])
    out['moon'] = [earth[i] + moon_geo[i] for i in range(3)]
    print(json.dumps({'jd_tdb': jd, 'frame': 'J2000 mean ecliptic, heliocentric, km', 'vectors': out}, indent=1))


if __name__ == '__main__':
    main()
