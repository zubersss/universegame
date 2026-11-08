"""B-169 export readiness: the Neptune v3 manifest rows (after the Uranus rows: run uranus_rows.py first). Replaces the
v2 rows under the same keys (creatures/neptune/*, props/neptune/*) and adds the new ones next to their Uranus siblings."""
import json
import sys

sys.path.insert(0, r"C:\dev\universegame\blender\scripts")
import build_creatures_neptune_v3 as CN  # noqa: E402
import build_props_neptune_v3 as PN  # noqa: E402

P = r"C:\dev\universegame\blender\manifest.json"
text = open(P, encoding="utf-8").read()
if '"backgrounds/neptune/deck1"' in text:
    sys.exit("already written")
if '"backgrounds/uranus/deep_survey"' not in text:
    sys.exit("run uranus_rows.py first (the Neptune rows go after the Uranus ones)")
lines = text.split("\n")

backs = []
for deck, seed in (("deck1", 15101), ("deck2", 15102), ("deck3", 15103), ("deep", 15104), ("storm", 15105), ("spot", 15105)):
    note = (f"B-169 (study accepted under B-161; straight, D-147): painted Neptune {deck}, layer0 2048x1024 / layer1 2048x640 / "
            f"layer2 2048x384 + {deck}.json")
    if deck in ("storm", "spot"):
        note += ("; layer1 the storm rim alone with its pulse block (D-148 / D-155: scale 0.97-1.03, alpha 0.85-1.0, 8 beats at "
                 "110 bpm, pivot_uv 0.5 / 0.5; a fixed wrap)")
    if deck == "spot":
        note += "; the storm's seed, so layers 1-2 are byte-identical to storm's (B-169 accept); layer0 the Meridian far off"
    backs.append({"key": f"backgrounds/neptune/{deck}", "painted_bg": True, "generator": "scripts/build_backdrop_v3.py", "numpy_only": True,
                  "size": [2048, 1024], "seed": seed, "review_name": f"b169_neptune_{deck}", "note": note})
floes = {"key": "terrain/neptune/floe_strip_set", "ground_strip_set": True, "generator": "scripts/build_c2_neptune_floes.py", "size": [676, 152],
         "review_name": "b169_neptune_floes", "note": "B-169 (D-137): terrain/neptune/floe_strip_{ice,superionic}, 10 frames 64x152 each (8 tiles + "
         "caps; a rounded windward cap, a ragged lee cap; json wind +x, mirrored for a -x wind)"}
rig = {"key": "flora/neptune/rigset", "style": "v3", "rigset": True, "source": "sources/flora/neptune_rigset_c2.blend", "build": "scripts/build_c2_neptune_rigs.py",
       "build_fn": "build", "collection": "parts", "planet": "neptune", "seed": 5, "review_name": "b169_neptune_rigset",
       "review_script": "scripts/build_c2_neptune_rigs.py", "self_check": {"face": "no face parts on any plant (D-101)"},
       "note": "B-169 (designs accepted under B-161): the Neptune rig set, 24 parts, 5 plants (kitebloom, gripweed, pipereed, stormlantern, rimecomb)"}
leviathan = {"key": "creatures/neptune/umbral_leviathan", "style": "v3", "rigset": True, "source": "sources/creatures/neptune_leviathan_rigset.blend",
             "build": "scripts/build_umbral_leviathan_v3.py", "build_fn": "build", "collection": "parts", "planet": "neptune", "seed": 5,
             "review_name": "b169_umbral_leviathan", "review_script": "scripts/build_umbral_leviathan_v3.py",
             "self_check": {"face": "the apex (D-087 friendly-neutral): a pie eye, a closed smile, no teeth"},
             "note": "B-169 (D-140): the Umbral Leviathan as a Grand rig set (8 bones, grand true; swaps dim / lit; actions survey, circle)"}
props = []
for name, spec in PN.PROPS.items():
    fw, fh = spec[1], spec[2]
    px, py = PN.pivot_of(name)
    props.append({"key": f"props/neptune/{name}", "style": "v3", "prop_sheet": True, "generator": "scripts/build_props_neptune_v3.py",
                  "planet": "neptune", "frame": [fw, fh], "pivot": [round(px, 6), round(py, 6)], "clips": [],
                  "note": "B-169: a Neptune prop (one static frame); replaces the v2 model under this key"})
props_set = {"key": "props/neptune/props_set", "style": "v3", "prop_sheet_set": True, "generator": "scripts/build_props_neptune_v3.py",
             "planet": "neptune", "review_name": "b169_neptune_props", "props": [p["key"] for p in props],
             "note": "B-169: exports the wind anchor + the three Meridian wreck segments + the stamped review (build_props_neptune_v3.main)"}
creatures = {n: CN.entry_for(n) for n in CN.SPECIES}

replace = {r["key"]: r for r in list(creatures.values()) + props}
used = set()
out = []
for ln in lines:
    s = ln.lstrip()
    hit = next((k for k in replace if s.startswith('{"key": "%s",' % k)), None)
    if hit:
        out.append(ln[:len(ln) - len(s)] + json.dumps(replace[hit]) + ",")
        used.add(hit)
        continue
    out.append(ln)
    indent = ln[:len(ln) - len(s)]
    if s.startswith('{"key": "backgrounds/uranus/deep_survey",'):
        out += [indent + json.dumps(b) + "," for b in backs]
    if s.startswith('{"key": "terrain/uranus/floe_strip_set",'):
        out.append(indent + json.dumps(floes) + ",")
    if s.startswith('{"key": "flora/uranus/rigset",'):
        out.append(indent + json.dumps(rig) + ",")
    if s.startswith('{"key": "creatures/uranus/diamondback_colossus",'):
        new_c = [c for c in creatures.values() if '"%s"' % c["key"] not in text]
        out += [indent + json.dumps(c) + "," for c in new_c] + [indent + json.dumps(leviathan) + ","]
        used.update(c["key"] for c in new_c)
    if s.startswith('{"key": "props/uranus/props_set",'):
        new_p = [p for p in props if '"%s"' % p["key"] not in text]
        out += [indent + json.dumps(p) + "," for p in new_p] + [indent + json.dumps(props_set) + ","]
        used.update(p["key"] for p in new_p)
missing = set(replace) - used
if missing:
    sys.exit(f"not placed: {sorted(missing)}")
new = "\n".join(out)
m = json.loads(new)
a = m["assets"] if isinstance(m, dict) else m
keys = [e["key"] for e in a]
assert len(keys) == len(set(keys)), "duplicate keys"
for k in ("backgrounds/neptune/deck1", "terrain/neptune/floe_strip_set", "flora/neptune/rigset", "creatures/neptune/umbral_leviathan", "props/neptune/props_set"):
    assert k in keys, f"{k} not placed"
open(P, "w", encoding="utf-8", newline="").write(new)
print("rows", len(keys), "| neptune v3:", len([e for e in a if "neptune" in e["key"] and (e.get("style") == "v3" or e.get("painted_bg") or e.get("ground_strip_set"))]))
