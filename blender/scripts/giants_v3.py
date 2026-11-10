"""B-239 (LEAD 11-09 22:0x; the design: coordination/reports/blender/b237_limb_band_design.md): the four giants' faces as
ONE table. No drawing here, no numpy, no imports: only the facts both builders read.

  build_discs_v3   paints the far discs (planets/<giant>/disc) from it: paint(), BAND_EDGES, the night crescent, the
                   shadow tone and Saturn's rings. B-239's proof: the far discs and the ring parts rebuilt from this
                   table are byte-identical to the exported files (build_discs_v3.py --b239).
  the close view   (D-128's painted close-up band, not yet carded as art) will draw from planets/<giant>/close.json,
                   which close_json() below fills from the same numbers, so the two views cannot drift apart.

Coordinates are the far disc's own: u to the right, v up, both in disc radii (the limb is u^2 + v^2 = 1); a belt is
(v_top, tone) from the north down, the last one running to the south pole. A tone is a recipe in the palette's slot
names: (name,) or (a, b, t) = a mixed t of the way to b. Every disc is painted in the EARTH palette (build_discs_v3.PAL).
"""

NIGHT = {"centre": (0.30, 0.30), "radius": 1.06}      # the night crescent: the part of the face outside this circle
SHADE = ("brown", 0.3)                                 # the one shadow tone: a colour mixed 0.3 of the way to the palette's brown

GIANTS = {
    "jupiter": {
        "belts": [(1.1, ("offwhite", "mustard", 0.3)), (0.62, ("brown", "mustard", 0.45)), (0.42, ("offwhite",)),
                  (0.18, ("mustard", "red", 0.25)), (-0.05, ("offwhite",)), (-0.25, ("brown", "red", 0.35)),
                  (-0.52, ("offwhite", "mustard", 0.4)), (-0.75, ("brown", "mustard", 0.5))],
        "wob": 0.045, "freq": 4.0,                     # an edge wobbles as wob * sin(freq * pi * u + phase) * (1 - v^2)
        "storms": [{"name": "red_spot", "lon": 0.25, "lat": -0.38, "rad": 0.13, "tone": ("red",), "drift": 0.35}],
        "band_edges": (0.62, 0.42, 0.18, -0.05, -0.25, -0.52),     # the edges that carry short ink dashes
    },
    "saturn": {
        "belts": [(1.1, ("mustard", "offwhite", 0.6)), (0.5, ("mustard", "offwhite", 0.3)), (0.15, ("mustard", "offwhite", 0.55)),
                  (-0.2, ("mustard", "brown", 0.15)), (-0.6, ("mustard", "offwhite", 0.5))],
        "wob": 0.025, "freq": 3.0,
        "storms": [],
        "band_edges": (0.5, 0.15, -0.2),
        # the rings, in body radii: bands (r_in, r_out, tone) with the Cassini gap between the second and the third; ink on
        # the outer edge (the outline's weight) and the inner edge (the interior weight); drawn flattened by tilt
        "rings": {"tilt": 0.30, "inner": 1.24, "outer": 2.27, "gap": (1.95, 2.03),
                  "bands": [(1.24, 1.55, ("mustard", "offwhite", 0.55)), (1.55, 1.95, ("mustard", "offwhite", 0.25)),
                            (2.03, 2.27, ("brown", "mustard", 0.5))]},
    },
    "uranus": {
        "belts": [(1.1, ("sky", "teal", 0.2)), (0.3, ("sky", "offwhite", 0.3)), (-0.3, ("sky", "teal", 0.3))],
        "wob": 0.02, "freq": 3.0,
        "storms": [],
        "band_edges": (0.3, -0.3),
    },
    "neptune": {
        "belts": [(1.1, ("teal",)), (0.35, ("teal", "sky", 0.4)), (-0.1, ("teal",)), (-0.5, ("teal", "brown", 0.25))],
        "wob": 0.03, "freq": 3.0,
        # no face (D-101): the dark storm, then a bright companion cloud trailing it (a chain of small blobs); both drift
        "storms": [{"name": "dark_storm", "lon": 0.22, "lat": -0.25, "rad": 0.12, "tone": ("teal", "brown", 0.3), "drift": 0.4},
                   {"name": "companion_cloud", "chain": {"lon0": 0.30, "dlon": 0.011, "lat0": -0.12, "dlat": 0.004, "rad": 0.032,
                                                         "j0": -8, "j1": 9},
                    "tone": ("offwhite", "sky", 0.3), "drift": 0.4}],
        "band_edges": (0.35, -0.1),
    },
}


def tone(recipe, pal):
    """A recipe -> the colour, with the far disc's own arithmetic (build_discs_v3.mix): a * (1 - t) + b * t."""
    if len(recipe) == 1:
        return pal[recipe[0]]
    a, b, t = recipe
    return pal[a] * (1 - t) + pal[b] * t


def storm_blobs(s):
    """A storm's blobs as build_discs_v3.blobs takes them: [(lon, lat, rad)], lon in turns, lat and rad in disc radii."""
    c = s.get("chain")
    if c:
        return [(c["lon0"] + c["dlon"] * j, c["lat0"] + c["dlat"] * j, c["rad"]) for j in range(c["j0"], c["j1"])]
    return [(s["lon"], s["lat"], s["rad"])]


def close_json(name, pal, to_hex, radius_u, loop_frames, fps):
    """The DRAFT of planets/<giant>/close.json (B-239: into blender/preview only; the close view is not carded as art).
    pal: slot -> colour (0..1); to_hex(colour) -> '#RRGGBB'."""
    g = GIANTS[name]

    def h(recipe):
        return to_hex(tone(recipe, pal))

    def night(recipe):
        c = tone(recipe, pal)
        return to_hex(c * (1 - SHADE[1]) + pal[SHADE[0]] * SHADE[1])
    out = {
        "key": f"planets/{name}/close", "style": "v3", "draft": True,
        "note": "B-239 draft, not exported: the far disc's own facts for the close view (b237_limb_band_design.md). u right, "
                "v up, in disc radii; tones are the far disc's flat tones (the Earth palette, as every disc)",
        "radius_u": radius_u, "loop_frames": loop_frames, "fps": fps,
        "belts": [{"v_top": vt, "tone_hex": h(r), "night_hex": night(r)} for vt, r in g["belts"]],
        "edge_wobble": {"amp": g["wob"], "freq": g["freq"],
                        "formula": "edge y(x) = v_top - amp * sin(freq * pi * x + phase) * (1 - v_top^2); "
                                   "phase = 2 * pi * frame / loop_frames"},
        "ink_dash_edges": list(g["band_edges"]),
        "night": {"centre": list(NIGHT["centre"]), "radius": NIGHT["radius"], "toward_hex": to_hex(pal[SHADE[0]]), "t": SHADE[1],
                  "note": "the face outside this circle is the night crescent: each tone mixed t of the way to toward_hex "
                          "(night_hex per belt)"},
        "storms": [],
        "swap": {"above_px_per_far_texel": 6, "below_px_per_far_texel": 5, "note": "DiscSprite.NearAbove / NearBelow"},
    }
    for s in g["storms"]:
        row = {"name": s["name"], "tone_hex": h(s["tone"]), "night_hex": night(s["tone"]), "drift_turns_per_loop": s["drift"],
               "blobs": [{"lon_turns": round(a, 4), "v": round(b, 4), "radius": c} for a, b, c in storm_blobs(s)],
               "note": "lon in turns of the body at frame 0 (it advances by drift_turns_per_loop * frame / loop_frames); "
                       "v and radius in disc radii"}
        out["storms"].append(row)
    rg = g.get("rings")
    if rg:
        out["rings"] = {"tilt": rg["tilt"], "inner": rg["inner"], "outer": rg["outer"], "gap": list(rg["gap"]),
                        "bands": [{"r_in": a, "r_out": b, "tone_hex": h(r)} for a, b, r in rg["bands"]],
                        "ink_px": {"outer_edge": 2.5, "inner_edge": 1.25},
                        "note": "in body radii; the upper half passes behind the body (rings_back), the lower in front "
                                "(rings_front); the wobble is disc_rig.json's"}
    return out
