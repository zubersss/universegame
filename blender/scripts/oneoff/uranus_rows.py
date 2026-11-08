"""B-166 export readiness: the Uranus v3 manifest rows. Replaces the v2 rows under the same keys where they exist
(creatures/uranus/*, props/uranus/*) and adds the new ones next to their Saturn siblings; validates the manifest."""
import json
import sys

sys.path.insert(0, r"C:\dev\universegame\blender\scripts")
import build_creatures_uranus_v3 as CU  # noqa: E402
import build_props_uranus_v3 as PU  # noqa: E402

P = r"C:\dev\universegame\blender\manifest.json"
text = open(P, encoding="utf-8").read()
if '"backgrounds/uranus/deck1_sun_left"' in text:
    sys.exit("already written")
lines = text.split("\n")

backs = []
for deck, seed in (("deck1", 15001), ("deck2", 15002), ("deck3", 15003), ("deep", 15004)):
    for light in ("sun_left", "sun_right", "night", "survey"):                 # survey LAST: render.py's URANUS-CHECK runs after it
        backs.append({"key": f"backgrounds/uranus/{deck}_{light}", "painted_bg": True, "generator": "scripts/build_backdrop_v3.py",
                      "numpy_only": True, "size": [2048, 1024], "seed": seed, "review_name": f"b158_uranus_{deck}_{light}",
                      "note": f"B-166 (D-142; study accepted under B-158; straight, D-147): Uranus {deck} lit {light}; one seed per deck so "
                              "the four lights share their geometry and alpha; export a deck's four lights in this order (survey last): "
                              "render.py then logs URANUS-CHECK <deck> PASS / FAIL"})
floes = {"key": "terrain/uranus/floe_strip_set", "ground_strip_set": True, "generator": "scripts/build_c2_uranus_floes.py", "size": [676, 152],
         "review_name": "b158_uranus_floes", "note": "B-166 (D-137): terrain/uranus/floe_strip_{ice,dark}, 10 frames 64x152 each (8 tiles + caps); "
         "UNITY tints them by the season (D-142)"}
rig = {"key": "flora/uranus/rigset", "style": "v3", "rigset": True, "source": "sources/flora/uranus_rigset_c2.blend", "build": "scripts/build_c2_uranus_rigs.py",
       "build_fn": "build", "collection": "parts", "planet": "uranus", "seed": 5, "review_name": "b158_uranus_rigset",
       "review_script": "scripts/build_c2_uranus_rigs.py", "self_check": {"face": "no face parts on any plant (D-101)"},
       "note": "B-166 (designs accepted under B-158): the Uranus rig set; plants + biomes from the builder (scene rig_plants)"}
colossus = {"key": "creatures/uranus/diamondback_colossus", "style": "v3", "rigset": True, "source": "sources/creatures/uranus_diamondback_rigset.blend",
            "build": "scripts/build_diamondback_v3.py", "build_fn": "build", "collection": "parts", "planet": "uranus", "seed": 5,
            "review_name": "b158_diamondback", "review_script": "scripts/build_diamondback_v3.py",
            "self_check": {"face": "the apex (D-087 friendly-neutral): pie eyes, a closed smile, no teeth"},
            "note": "B-166 (D-140): the Diamondback Colossus as a Grand rig set (7 bones, grand true); only its joints take damage"}
props = []
for name, spec in PU.PROPS.items():
    fw, fh = spec[1], spec[2]
    px, py = PU.pivot_of(name)
    props.append({"key": f"props/uranus/{name}", "style": "v3", "prop_sheet": True, "generator": "scripts/build_props_uranus_v3.py",
                  "planet": "uranus", "frame": [fw, fh], "pivot": [round(px, 6), round(py, 6)], "clips": [],
                  "note": "B-166: a Uranus prop (one static frame); replaces the v2 model under this key"})
props_set = {"key": "props/uranus/props_set", "style": "v3", "prop_sheet_set": True, "generator": "scripts/build_props_uranus_v3.py",
             "planet": "uranus", "review_name": "b158_uranus_props", "props": [p["key"] for p in props],
             "note": "B-166: exports every Uranus prop + the stamped review (build_props_uranus_v3.main)"}
creatures = {n: CU.entry_for(n) for n in CU.SPECIES}

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
    if s.startswith('{"key": "backgrounds/saturn/hexagon",'):
        out += [indent + json.dumps(b) + "," for b in backs]
    if s.startswith('{"key": "terrain/saturn/floe_strip_set",'):
        out.append(indent + json.dumps(floes) + ",")
    if s.startswith('{"key": "flora/saturn/rigset",'):
        out.append(indent + json.dumps(rig) + ",")
    if s.startswith('{"key": "creatures/saturn/polar_hydra",'):
        new_c = [c for c in creatures.values() if '"%s"' % c["key"] not in text]
        out += [indent + json.dumps(c) + "," for c in new_c] + [indent + json.dumps(colossus) + ","]
        used.update(c["key"] for c in new_c)
    if s.startswith('{"key": "props/saturn/props_set",'):
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
open(P, "w", encoding="utf-8", newline="").write(new)
print("rows", len(keys), "| uranus v3:", len([e for e in a if "uranus" in e["key"] and (e.get("style") == "v3" or e.get("painted_bg") or e.get("ground_strip_set"))]))
