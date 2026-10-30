"""Builds src/data/sol.json (task W1).

Physical constants below are the reference values of the IAU 2015 nominal
solar values and the NASA/NSSDCA Planetary and Satellite Fact Sheets, entered
WITHOUT a live fetch (nasa.gov is unreachable from the build environment).
Until they are checked against a fetched source they are tagged 'estimated',
verified=false, source 'pending', and are never shown as measured.

Positions: a vectors JSON from sol_positions_de421.py (JPL DE421, interim),
horizons.mjs (target source) or sol_positions_erfa.py (fallback).
Run:  python3 -I scripts/data/build_sol.py <vectors.json> > src/data/sol.json
"""
import json
import math
import sys
EPOCH_JD = 2461041.5  # 2026-01-01 00:00:00 TDB
FACT = 'https://nssdc.gsfc.nasa.gov/planetary/factsheet/'
SATS = 'https://ssd.jpl.nasa.gov/sats/phys_par/'
IAU = 'IAU 2015 Resolution B3 (nominal solar values)'

M = 'measured'
E = 'estimated'
F = 'fictional'


def earth_orientation(jd_tdb):
    """Earth's north pole and prime-meridian directions at the epoch, J2000 ecliptic unit vectors.

    IAU 2006/2000A celestial-to-terrestrial matrix (erfa.c2t06a), polar motion 0,
    UT1 = TT - 69.2 s (TAI-UTC 37 s, UT1-UTC ~ 0)."""
    import erfa
    eps = math.radians(84381.448 / 3600.0)
    c, s = math.cos(eps), math.sin(eps)
    m = erfa.c2t06a(jd_tdb, 0.0, jd_tdb, -69.2 / 86400.0, 0.0, 0.0)

    def ecl(v):
        return [round(float(v[0]), 12), round(float(c * v[1] + s * v[2]), 12), round(float(-s * v[1] + c * v[2]), 12)]

    return {
        'north': ecl(m[2]), 'primeMeridian': ecl(m[0]), 'tag': 'measured',
        'source': 'IAU 2006/2000A precession-nutation and Earth rotation angle (SOFA/ERFA c2t06a), polar motion neglected',
    }


def f(v, tag=M, unit=None):
    d = {'value': v, 'tag': tag}
    if unit:
        d['unit'] = unit
    return d


# id, name, kind, parent, radiusKm, gravity m/s^2, massKg, sidereal rotation h
# (negative = retrograde), semi-major axis about parent km (moons), atmosphere,
# physical-value source.
BODIES = [
    ('sun', 'Sun', 'star', None, 695700, 274.0, 1.9885e30, 609.12, None, True, IAU + '; ' + FACT + 'sunfact.html'),
    ('mercury', 'Mercury', 'planet', 'sun', 2439.7, 3.70, 3.3011e23, 1407.6, None, False, FACT + 'mercuryfact.html'),
    ('venus', 'Venus', 'planet', 'sun', 6051.8, 8.87, 4.8675e24, -5832.6, None, True, FACT + 'venusfact.html'),
    ('earth', 'Earth', 'planet', 'sun', 6371.0, 9.80, 5.9722e24, 23.9345, None, True, FACT + 'earthfact.html'),
    ('moon', 'Moon', 'moon', 'earth', 1737.4, 1.62, 7.346e22, 655.72, 384400, False, FACT + 'moonfact.html'),
    ('mars', 'Mars', 'planet', 'sun', 3389.5, 3.71, 6.4171e23, 24.6229, None, True, FACT + 'marsfact.html'),
    ('jupiter', 'Jupiter', 'planet', 'sun', 69911, 24.79, 1.89819e27, 9.925, None, True, FACT + 'jupiterfact.html'),
    ('europa', 'Europa', 'moon', 'jupiter', 1560.8, 1.315, 4.7998e22, 85.228, 671034, False, SATS + ' ; ' + FACT + 'joviansatfact.html'),
    ('saturn', 'Saturn', 'planet', 'sun', 58232, 10.44, 5.6834e26, 10.656, None, True, FACT + 'saturnfact.html'),
    ('titan', 'Titan', 'moon', 'saturn', 2574.7, 1.352, 1.3452e23, 382.69, 1221870, True, SATS + ' ; ' + FACT + 'saturniansatfact.html'),
    ('uranus', 'Uranus', 'planet', 'sun', 25362, 8.87, 8.6813e25, -17.24, None, True, FACT + 'uranusfact.html'),
    ('neptune', 'Neptune', 'planet', 'sun', 24622, 11.15, 1.02413e26, 16.11, None, True, FACT + 'neptunefact.html'),
]


def main():
    with open(sys.argv[1]) as fh:
        pos = json.load(fh)
    src_kind = pos.get('source', 'erfa')
    vec = pos['vectors']
    phys_verified = bool(pos.get('physicalVerified', False))
    pt = M if phys_verified else E
    bodies = []
    for (bid, name, kind, parent, r, g, m, rot, a, atm, src) in BODIES:
        b = {
            'id': bid,
            'name': name,
            'kind': kind,
            'parent': parent,
            'radiusKm': f(r, pt, 'km'),
            'gravity': f(g, pt, 'm/s^2'),
            'massKg': f(m, pt, 'kg'),
            'rotationHours': f(rot, pt, 'h'),
            'hasAtmosphere': f(atm, M),
            'source': src if phys_verified else 'pending (reference: ' + src + ')',
            'verified': phys_verified,
        }
        if a is not None:
            b['semiMajorAxisKm'] = f(a, pt, 'km')
        if bid == 'earth':
            b['orientation'] = earth_orientation(EPOCH_JD)
        if bid == 'sun':
            b['positionKm'] = f([0.0, 0.0, 0.0], M, 'km')
            b['luminosityW'] = f(3.828e26, pt, 'W')
            b['effectiveTempK'] = f(5772, pt, 'K')
        elif bid in vec:
            b['positionKm'] = f([round(c, 1) for c in vec[bid]], E if src_kind == 'erfa' else M, 'km')
        else:
            # No satellite ephemeris in DE421/ERFA: the moon sits at its real mean
            # distance in the parent's ecliptic plane, 90 degrees ahead of the
            # parent along its orbit. The DIRECTION is invented until Horizons.
            p = vec[parent]
            ang = math.atan2(p[1], p[0]) + math.pi / 2
            b['positionKm'] = f([round(p[0] + a * math.cos(ang), 1), round(p[1] + a * math.sin(ang), 1), round(p[2], 1)], F, 'km')
        bodies.append(b)
    POS = {
        'horizons': {'url': 'https://ssd.jpl.nasa.gov/horizons/', 'accessed': pos.get('accessed'),
                     'note': 'JPL Horizons vector tables, CENTER=500@10, REF_PLANE=ECLIPTIC, OUT_UNITS=KM-S.',
                     'license': 'US Government work (NASA/JPL)'},
        'de421': {'url': 'https://pypi.org/project/de421/ (JPL DE421, Folkner, Williams & Boggs 2009, IPN Progress Report 42-178)', 'accessed': '2026-10-29',
                  'note': 'INTERIM until Horizons is reachable: JPL DE421 read locally with jplephem (scripts/data/sol_positions_de421.py); outer planets are system barycenters; '
                          'cross-checked against IAU SOFA plan94/moon98 (agreement 0.0-14 arcsec). Europa and Titan directions are fictional (not in DE421).',
                  'license': 'Ephemeris data: JPL (US Government work); packaging MIT'},
        'erfa': {'url': 'https://github.com/liberfa/pyerfa (IAU SOFA epv00, plan94, moon98)', 'accessed': '2026-10-29',
                 'note': 'FALLBACK: analytic theories, ~10 arcsec; Europa and Titan directions are fictional.',
                 'license': 'SOFA/ERFA BSD-3-Clause (algorithm); output values are facts'},
    }
    doc = {
        'catalog': 'sol',
        'description': 'Scientific values for the Sol system. Gameplay values derive from these through src/world/scale.ts.',
        'epoch': {'iso': '2026-01-01T00:00:00 TDB', 'jdTdb': EPOCH_JD},
        'frame': 'Heliocentric (Sun center), J2000 mean ecliptic and equinox; x toward the vernal equinox, z toward the north ecliptic pole; km',
        'tags': {'measured': 'published measurement or ephemeris value', 'estimated': 'computed, conventional or not yet verified against a fetched source', 'fictional': 'invented for gameplay'},
        'sources': {
            'physical': {
                'url': FACT,
                'accessed': pos.get('accessed') if phys_verified else None,
                'note': 'Verified against fetched Horizons object data.' if phys_verified else
                        'PENDING: reference values entered without a live fetch (nasa.gov unreachable from the build environment, 2026-10-29); tagged estimated until verified.',
                'license': 'US Government work (NASA), public domain in the US',
            },
            'positions': POS[src_kind],
        },
        'bodies': bodies,
        'belts': [
            {'id': 'asteroid-belt', 'name': 'Main asteroid belt', 'innerAu': f(2.1, E, 'au'), 'outerAu': f(3.3, E, 'au'),
             'note': 'Conventional extent of the main belt (between the 4:1 and 2:1 Kirkwood gaps).'},
            {'id': 'kuiper-belt', 'name': 'Kuiper belt', 'innerAu': f(30.0, E, 'au'), 'outerAu': f(50.0, E, 'au'),
             'note': 'Conventional extent from Neptune\'s orbit to the 1:2 resonance edge.'},
        ],
    }
    print(json.dumps(doc, indent=1))


if __name__ == '__main__':
    main()
