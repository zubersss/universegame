"""B-215: the D1 key audit (read-only). Usage: python -I d1_key_audit.py <repo root> <out.json>
Collects every art key the D1 code and tables request (with the requester), checks it on disk under Art/ (png + json),
validates the json fields the importer reads against the png, and lists present D1-category keys nobody requests."""
import json
import os
import re
import struct
import sys
import zlib

ROOT = sys.argv[1]
ART = os.path.join(ROOT, "Assets", "_Game", "Art")
PH = os.path.join(ROOT, "Assets", "_Game", "Placeholders")
CODE = os.path.join(ROOT, "Assets", "_Game", "Code")
D1 = os.path.join(ROOT, "Assets", "_Game", "Settings", "Resources", "D1")


def png_size(p):
    with open(p, "rb") as f:
        h = f.read(24)
    return struct.unpack(">II", h[16:24])


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


# ---------------------------------------------------------------- the code's lines
code_lines = {}
for dp, _dn, fns in os.walk(CODE):
    for fn in fns:
        if fn.endswith(".cs"):
            p = os.path.join(dp, fn)
            with open(p, encoding="utf-8-sig", errors="replace") as f:
                code_lines[rel(p)] = f.read().split("\n")


def where(pattern):
    """First code line (file:line) matching the regex, skipping comment-only lines."""
    rx = re.compile(pattern)
    for f, lines in sorted(code_lines.items()):
        for i, ln in enumerate(lines):
            s = ln.strip()
            if s.startswith("//") or s.startswith("///"):
                continue
            if rx.search(ln):
                return f"{f.replace('Assets/_Game/Code/', '')}:{i + 1}"
    return None


req = {}     # key -> {"by": [...], "area": str}


def want(key, by, area):
    e = req.setdefault(key, {"by": [], "area": area})
    if by and by not in e["by"]:
        e["by"].append(by)


# ---------------------------------------------------------------- the D1 tables
tables = json.load(open(os.path.join(D1, "D1Tables.json"), encoding="utf-8-sig"))
tree = json.load(open(os.path.join(D1, "SkillTree.json"), encoding="utf-8-sig"))
d1_planets = [p["id"].lower() for p in tables["planets"]]
items = set()
for p in tables["planets"]:
    for t in p["tiers"]:
        for r in t["rows"]:
            items.add(r["item"])
            if r.get("elseItem"):
                items.add(r["elseItem"])
for n in tree["nodes"]:
    for it in n.get("items", []):
        items.add(it["item"] if isinstance(it, dict) else it)
icon_by = where(r'icon = \$"icons/\{key\}/base"') or where(r'icons/\{name\}/base')
for it in sorted(items):
    want(f"icons/{it}/base", f"D1Tables.json / SkillTree.json item '{it}' → ItemIcons ({icon_by})", "items")
nodes_by = where(r'Want\("icons/nodes/" \+ n\.id\)')
for n in tree["nodes"]:
    want(f"icons/nodes/{n['id']}", f"SkillTree.json node '{n['id']}' → {nodes_by}", "tree")

# ---------------------------------------------------------------- the code's requests (D1 areas)
st = where(r'foreach \(var s in new\[\] \{ "chart", "hub"')
for s in ("chart", "hub", "node_bought", "node_available", "node_locked", "node_cap_bought", "node_cap_available", "node_cap_locked",
          "link_bought", "link_open", "link_locked", "select"):
    want(f"ui/skilltree/{s}", st, "tree")
eb = where(r'"ui/skilltree/emblem_" \+ b')
for b in ("dig", "haul", "ascent", "survey", "endurance", "voyage"):
    want(f"ui/skilltree/emblem_{b}", eb, "tree")
want("ui/skilltree/cost_tag", where(r'"ui/skilltree/cost_tag"'), "tree")
for k, pat in (("ui/hud/gauges", r"HudGauges\)"), ("ui/hud/escape_line", r"ArtKeys\.Ui\.EscapeLine"), ("ui/hud/escape_sign", r"ArtKeys\.Ui\.EscapeSign"),
               ("ui/hud/film_switch", r"ArtKeys\.Ui\.FilmSwitch"), ("ui/panels/pause", r"ArtKeys\.Ui\.PanelPause"),
               ("ui/panels/settings", r"ArtKeys\.Ui\.PanelSettings"), ("ui/panels/inventory", r"ArtKeys\.Ui\.PanelInventory"),
               ("ui/panels/scroll", r"ArtKeys\.Ui\.PanelScroll"), ("ui/panels/sign", r"PanelSign")):
    want(k, where(pat + r"(?!.*const)") or where(pat), "hud")
for k in ("ui/map/sun", "ui/map/name_tag", "ui/map/minimap_chart", "ui/map/orbit_dot", "ui/map/well_dash", "ui/map/landed", "ui/map/ship",
          "ui/map/minimap_frame", "ui/map/rim_arrow", "ui/map/system_panel", "ui/map/title_cartouche", "ui/map/station"):
    want(k, where(re.escape(f'"{k}"')), "map")
disc = where(r'"ui/map/planet_" \+ b\.name')
for b in ("mercury", "venus", "earth", "luna", "mars", "jupiter", "saturn", "uranus", "neptune"):
    want(f"ui/map/planet_{b}", disc, "map")
for k, pat in (("fx/dig_sparks/base", r"ArtKeys\.Fx\.DigSparks\)"), ("fx/dust/base", r"ArtKeys\.Fx\.Dust\)"), ("fx/beam_ray/base", r"ArtKeys\.Fx\.BeamRay(?!\s*=)"),
               ("fx/survey_scan/base", r"ArtKeys\.Fx\.SurveyScan(?!\s*=)"), ("fx/builder_ghost/base", r"ArtKeys\.Fx\.BuilderGhost(?!\s*=)")):
    want(k, where(pat), "fx")
for m, k in (("Beam", "beam"), ("Grapple", "grapple"), ("Survey", "survey"), ("_", "builder")):
    want(f"props/rig/{k}", where(re.escape(f'"props/rig/{k}"')), "tools")
want("props/rig/shovel", where(r'ShovelKey = "props/rig/shovel"'), "tools")                          # B-226 (D-182) for U-193
want("fx/shovel_flick/base", where(r'ArtKeys\.Fx\.ShovelFlick(?!\s*=)'), "fx")
for t in ("shovel", "beam", "grapple", "survey", "builder"):                                          # B-226 / B-227: U-193's HudToolSlot
    want(f"icons/tools/{t}", where(re.escape(f'"icons/tools/{t}"')), "tools")
want("icons/thruster_mk2/base", where(r'R\("fab_thruster_mk2"'), "items (crafting)")                 # B-222
want("characters/surveyor/side", where(r'SurveyorKey = "characters/surveyor/side"'), "characters")
want("characters/surveyor/side_b", where(r'SurveyorSideB'), "characters")
sh = where(r'"characters/surveyor/mk" \+')
for t in (1, 2, 3):
    want(f"characters/surveyor/mk{t}", sh, "characters")
fill = where(r'ground_fill_t\{k \+ 2\}')
sl = where(r'surface_line"')
for p in d1_planets:
    for t in (2, 3, 4, 5):
        want(f"terrain/{p}/ground_fill_t{t}", fill, "terrain")
    want(f"terrain/{p}/surface_line", sl, "terrain")
BANDS = {"earth": ["ground_band", "ground_band_sand", "ground_band_stone", "ground_band_snow"],
         "mars": ["ground_band", "ground_band_basalt", "ground_band_frost", "ground_band_talus"],
         "mercury": ["ground_band", "ground_band_ice"], "venus": ["ground_band", "ground_band_tessera", "ground_band_vent"]}
ALT = {"earth": "sand", "mars": "basalt"}
band_by = where(r'Probe\(\$"terrain/\{planet\}/\{variantKey\[i\]\}"')
dec_by = where(r'fill_decor_t\{set\}_\{n\}')
for p in d1_planets:
    for b in BANDS.get(p, ["ground_band"]):
        want(f"terrain/{p}/{b}", band_by, "terrain")
    want(f"terrain/{p}/ground_fill", where(r'/ground_fill", s =>'), "terrain")
    if p in ALT:
        want(f"terrain/{p}/ground_fill_{ALT[p]}", where(r'Probe\(\$"terrain/\{planet\}/\{altFill\}"'), "terrain")
    want(f"terrain/{p}/dig_rim", where(r'/dig_rim"'), "terrain")
    want(f"terrain/{p}/dig_puff", where(r'/dig_puff" : null'), "terrain")
    for n in range(1, 5):
        want(f"terrain/{p}/fill_decor_{n}", dec_by, "decor")
        if p in ALT:
            want(f"terrain/{p}/fill_decor_{ALT[p]}_{n}", dec_by, "decor")
        for t in (2, 3, 4, 5):
            want(f"terrain/{p}/fill_decor_t{t}_{n}", dec_by, "decor")
for f, lines in code_lines.items():                                        # non-D1 terrain paths (strips, tile sheets, backwall)
    if not (f.endswith("GroundStrip.cs") or f.endswith("ArtKeys.cs")):
        continue
    for i, ln in enumerate(lines):
        if ln.strip().startswith("//"):
            continue
        for m in re.finditer(r'"(terrain/[a-z]+/[a-z0-9_]+)"', ln):
            if m.group(1).split("/")[1] in d1_planets:
                want(m.group(1), f"{f.replace('Assets/_Game/Code/', '')}:{i + 1}", "terrain (strip / tile path)")
bw = where(r'FindBlock\(p, "backwall"')
for p in d1_planets:
    want(f"terrain/{p}/backwall", bw, "terrain (strip / tile path)")
for k in ("props/earth/data_cache", "props/mars/lander_beacon", "props/mercury/sunshade_probe", "props/venus/pressure_capsule", "props/earth/vault_door"):
    want(k, where(re.escape(f'"{k}"')), "finds")


# ---------------------------------------------------------------- presence + json fields
def check(key):
    base = os.path.join(ART, *key.split("/"))
    png, js = base + "_color.png", base + ".json"
    out = {"png": os.path.isfile(png), "json": os.path.isfile(js), "placeholder": False, "fields": "", "size": ""}
    if not out["png"]:
        pb = os.path.join(PH, *key.split("/"))
        out["placeholder"] = os.path.isfile(pb + "_color.png")
        return out
    w, h = png_size(png)
    out["size"] = f"{w}x{h}"
    if not out["json"]:
        out["fields"] = "no json"
        return out
    try:
        m = json.load(open(js, encoding="utf-8-sig"))
    except Exception as e:  # noqa: BLE001
        out["fields"] = f"json unreadable: {e}"
        return out
    probs = []
    if m.get("key") not in (None, key):
        probs.append(f"key '{m.get('key')}'")
    pv = m.get("pivot")
    if pv is not None and not (len(pv) == 2 and all(-0.01 <= v <= 1.01 for v in pv)):
        probs.append(f"pivot {pv}")
    if m.get("frames"):
        fw, fh, cols, n, g = m.get("frame_width", 0), m.get("frame_height", 0), m.get("columns", 0), m["frames"], m.get("gutter", 4)
        if not (fw and fh and cols):
            probs.append("sheet without frame_width / frame_height / columns")
        else:
            rows = -(-n // cols)
            ew, eh = cols * fw + (cols - 1) * g, rows * fh + (rows - 1) * g
            if (ew, eh) != (w, h):
                probs.append(f"grid {ew}x{eh} != png {w}x{h}")
        for a in m.get("animations") or []:
            if a.get("start", 0) + a.get("length", 0) > n:
                probs.append(f"clip {a.get('name')} past frame {n}")
    if m.get("parts"):
        for p in m["parts"]:
            r = p.get("rect", [])
            if len(r) != 4 or r[0] < 0 or r[1] < 0 or r[0] + r[2] > w or r[1] + r[3] > h:
                probs.append(f"part {p.get('name')} rect {r} outside {w}x{h}")
    if m.get("slice") is not None:
        s = m["slice"]
        if len(s) != 4 or s[0] + s[2] >= w or s[1] + s[3] >= h:
            probs.append(f"slice {s} leaves no centre in {w}x{h}")
    if m.get("style") != "v3":
        probs.append(f"style {m.get('style')!r}")
    out["fields"] = "; ".join(probs) if probs else "OK"
    return out


rows = []
for key in sorted(req):
    c = check(key)
    rows.append({"key": key, **req[key], **c})

# ---------------------------------------------------------------- present but unrequested (the D1 categories)
D1_DIRS = ["ui/hud", "ui/hints", "ui/rank", "ui/skilltree", "ui/map", "ui/panels", "fx/rare", "fx/ui", "fx/beam_ray", "props/rig", "props/dig",
           "icons/nodes", "characters/surveyor"] + [f"terrain/{p}" for p in d1_planets]
unreq = []
for d in D1_DIRS:
    full = os.path.join(ART, *d.split("/"))
    if not os.path.isdir(full):
        continue
    for fn in sorted(os.listdir(full)):
        if fn.endswith("_color.png"):
            key = f"{d}/{fn[:-len('_color.png')]}"
            if key not in req:
                unreq.append(key)
json.dump({"rows": rows, "unrequested": unreq, "d1_planets": d1_planets, "n_nodes": len(tree["nodes"]), "n_items": len(items)},
          open(sys.argv[2], "w", encoding="utf-8"), indent=1)
miss = [r for r in rows if not r["png"]]
bad = [r for r in rows if r["png"] and r["fields"] != "OK"]
print(f"requested {len(rows)}; missing {len(miss)}; json issues {len(bad)}; unrequested {len(unreq)}")

# ---------------------------------------------------------------- the report's generated part (argv[3]: a markdown fragment)
if len(sys.argv) > 3:
    def status(r):
        if r["png"]:
            return "yes"
        return "probe, empty by design" if r["area"] == "decor" else ("placeholder only" if r["placeholder"] else "**MISSING**")

    def fields(r):
        if not r["png"]:
            return ""
        f = r["fields"]
        if f == "style None":
            return "legacy v2 (no `style`): see Findings"
        if f == "no json" and r["area"].startswith("terrain (strip"):
            return "tile sheet: routed by path (ArtRules.cs:43), no json by design"
        if f == "no json":
            return "**no json** (legacy v2 colour / normal / emission): see Findings"
        return f
    L = []
    L.append(f"| Area | Key | Requested by | Present | json (importer fields vs the png) |")
    L.append("|---|---|---|---|---|")
    for r in sorted(rows, key=lambda r: (r["area"], r["key"])):
        by = "; ".join(b for b in r["by"] if b) or "?"
        L.append(f"| {r['area']} | `{r['key']}` | {by} | {status(r)} | {fields(r)} |")
    L.append("")
    L.append("### Present in the D1 folders, requested by nothing")
    L.append("")
    groups = {}
    for k in unreq:
        groups.setdefault("/".join(k.split("/")[:2]), []).append(k.split("/", 2)[2])
    L.append("| Folder | Keys | Count |")
    L.append("|---|---|---|")
    for g, ks in groups.items():
        L.append(f"| `{g}/` | {', '.join(ks)} | {len(ks)} |")
    with open(sys.argv[3], "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
for r in miss:
    print("MISSING", r["key"], "| placeholder" if r["placeholder"] else "", "|", r["by"][0] if r["by"] else "?")
for r in bad:
    print("JSON", r["key"], "|", r["fields"])
