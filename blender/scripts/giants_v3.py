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


RIM = (0.012, 3, 0.008, 5)                             # the far disc's lumpy limb: r(angle) = 1 + a3 * sin(3 angle + ph3)
#                                                         + a5 * sin(5 angle + ph5), the two phases drawn per body (Disc)

# The far disc's interior ink marks (build_discs_v3.interior_marks; 1.25 px), B-240: lifted here so the close view can place
# the same marks where the far disc has them (a mark on the strips' own rhythm would jump at the swap).
#   hatch: in the night crescent, `count` short diagonal strokes per group: stroke j runs from (u0 + step j - L/2, v0 + step
#          j - L/2) to (+ L/2, + L/2), L = max(length, 6 px on a small disc); skipped where u^2 + v^2 > limit
#   dash:  near each of a giant's band_edges (v = vb), one per u0: from u = uu to uu + length, uu = u0 + drift * sin(ph +
#          vb * drift_per_v), its height vb + wave_amp * sin(wave_freq * u + ph), ph = 2 pi frame / loop; skipped where
#          (|uu| + length)^2 + vb^2 > limit. (It rides NEAR the belt's edge, on its own gentler wave, not on the edge.)
MARKS = {"hatch": {"groups": ((-0.62, -0.42), (-0.30, -0.80)), "count": 3, "step": 0.06, "length": 0.10, "limit": 0.86},
         "dash": {"u0": (-0.35, 0.25), "length": 0.22, "drift": 0.05, "drift_per_v": 7, "wave_amp": 0.04, "wave_freq": 4.0,
                  "limit": 0.9, "points": 6}}


# The close view's strips (B-243, contract 11.5.1 / D-195). ONE scale, fixed to the planet: STRIP_SCALE strip texels per
# far-disc texel, so a strip texel is 6 / STRIP_SCALE screen px at the wheel's closest zoom (6 px per far texel) and
# 9 / STRIP_SCALE at the end of the entry's push-in (9); no zoom stepping. The strips' drawn widths are 2.5 texels (the
# limb's ink) and 1.25 (the thin line), each +-20 %. RULED 7.5 (LEAD 11-10 01:0x, on B-243's desk-check; the contract's
# first 7.3 gave 2.05-3.08 and 1.03-1.54 px): a strip texel is 0.80 px at 6 and 1.20 at 9, so the limb's mean runs
# 2.00-3.00 px and the thin line 1.00-1.50, contract 11.1's two ranges exactly. A change here changes close.json only,
# never a strip.
STRIP_SCALE = 7.5
EDGE_VARIANT = {"jupiter": 0, "saturn": 0, "uranus": 1, "neptune": 1}      # belt_edge: 0 firm, 1 faint and streaky


def strips_json(name):
    """close.json's "strips": which textures the close view lays, on which row each one's line sits, and the one scale."""
    out = {                                            # the field names are UNITY's (U-208, 11-10 01:1x: JsonUtility reads
        "scale": STRIP_SCALE,                          # fixed names, flat number arrays and arrays of objects only)
        "rows_from": "top",
        "limb_band": {"key": "planets/common/limb_band", "cut_row": 8},
        "belt_edge": {"key": f"planets/common/belt_edge_{EDGE_VARIANT[name]}", "cut_row": 12},
        "spot_rim": {"key": "planets/common/spot_rim", "cut_row": 12},
        "pigment": {"key": f"planets/{name}/close_pigment"},
        "grain": {"key": "planets/common/close_grain"},
        "note": "scale = strip texels per far-disc texel, ONE scale fixed to the planet at every zoom (no stepping); u runs "
                "along each curve from the body's own left, the limb with a whole number of repeats; cut_row is the row "
                "the strip's line or cut sits on, counted from the strip's top (limb_band: its ink's centre line; v = "
                "cut_row - the signed distance in strip texels); the pigment tile lies over the far sheet's frame "
                "(disc.json's frame_width x frame_height), value / 127.5; the grain is laid in screen space, value / 127.5",
    }
    if "rings" in GIANTS[name]:
        out["ring_edge"] = {"key": "planets/saturn/ring_edge", "cut_row": 8}
    return out


def close_json(name, pal, to_hex, radius_u, loop_frames, fps, rim_phases=None):
    """The DRAFT of planets/<giant>/close.json (B-239: into blender/preview only; the close view is not carded as art).
    pal: slot -> colour (0..1); to_hex(colour) -> '#RRGGBB'; rim_phases: the body's (ph3, ph5) from build_discs_v3
    (B-240: the far limb is not a circle, so the close view's limb must follow the same curve or it jumps at the swap)."""
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
        "ink_marks": {
            "width_px_far": 1.25,
            "dashes": dict(MARKS["dash"], u0=list(MARKS["dash"]["u0"]), edges=list(g["band_edges"]),
                           formula="per edge vb and per u0: uu = u0 + drift * sin(phase + vb * drift_per_v); the dash runs u = uu "
                                   "... uu + length at v(u) = vb + wave_amp * sin(wave_freq * u + phase); skipped where "
                                   "(|uu| + length)^2 + vb^2 > limit; phase = 2 * pi * frame / loop_frames"),
            "night_hatches": dict(MARKS["hatch"], groups=[{"u": p[0], "v": p[1]} for p in MARKS["hatch"]["groups"]],
                                  formula="stroke j (0 .. count - 1) of a group (u0, v0) = its u, v: from (u0 + step * j - length / 2, "
                                          "v0 + step * j - length / 2) to (+ length / 2, + length / 2); skipped where "
                                          "u^2 + v^2 > limit at its centre"),
            "note": "drawn over everything, storms included, as on the far disc",
        },
        "night": {"centre": list(NIGHT["centre"]), "radius": NIGHT["radius"], "toward_hex": to_hex(pal[SHADE[0]]), "t": SHADE[1],
                  "note": "the face outside this circle is the night crescent: each tone mixed t of the way to toward_hex "
                          "(night_hex per belt)"},
        "storms": [],
        "swap": {"above_px_per_far_texel": 6, "below_px_per_far_texel": 5, "note": "DiscSprite.NearAbove / NearBelow"},
        "strips": strips_json(name),
    }
    if rim_phases is not None:
        out["rim"] = {"a3": RIM[0], "ph3": round(float(rim_phases[0]), 6), "a5": RIM[2], "ph5": round(float(rim_phases[1]), 6),
                      "formula": "the limb, in disc radii: r(angle) = 1 + a3 * sin(3 * angle + ph3) + a5 * sin(5 * angle + ph5); "
                                 "angle = atan2(v, u)"}
    for s in g["storms"]:
        row = {"name": s["name"], "tone_hex": h(s["tone"]), "night_hex": night(s["tone"]), "drift_turns_per_loop": s["drift"],
               "blobs": [{"lon_turns": round(a, 4), "v": round(b, 4), "radius": c} for a, b, c in storm_blobs(s)],
               "note": "lon in turns of the body at frame 0 (it advances by drift_turns_per_loop * frame / loop_frames); "
                       "v and radius in disc radii"}
        c = s.get("chain")
        if c:                                          # B-241: up close a chain of blobs shows its scallops (a segmented
            j1 = c["j1"] - 1                           # grub); at the far disc's own size they are under a pixel, so the
            row["streak"] = {                          # close view draws ONE smooth streak from the first blob to the last
                "from": {"lon_turns": round(c["lon0"] + c["dlon"] * c["j0"], 4), "v": round(c["lat0"] + c["dlat"] * c["j0"], 4)},
                "to": {"lon_turns": round(c["lon0"] + c["dlon"] * j1, 4), "v": round(c["lat0"] + c["dlat"] * j1, 4)},
                "radius": c["rad"], "end_radius_share": 0.3,
                "note": "the close view draws this streak (in the blobs' own coordinates) instead of the blobs: along it "
                        "(t = 0 .. 1) its radius is radius * (s + (1 - s) * sin(pi * t) ^ 0.6), s = end_radius_share (tapered "
                        "ends: a cirrus streak, LEAD 23:4x), and its outline takes belt_edge's ragged cut"}
        out["storms"].append(row)
    rg = g.get("rings")
    if rg:
        out["rings"] = {"tilt": rg["tilt"], "inner": rg["inner"], "outer": rg["outer"], "gap": list(rg["gap"]),
                        "bands": [{"r_in": a, "r_out": b, "tone_hex": h(r)} for a, b, r in rg["bands"]],
                        "ink_px": {"outer_edge": 2.5, "inner_edge": 1.25},
                        "note": "in body radii; the upper half passes behind the body (rings_back), the lower in front "
                                "(rings_front); the wobble is disc_rig.json's"}
    return out
