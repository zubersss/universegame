"""Constants from coordination/ASSET_CONTRACT.md v1.0. Change only when the contract changes."""
import re

CONTRACT_VERSION = "1.0"
PPU = 128                      # 1 m = 128 px
PADDING = 8                    # transparent margin on every side (tight sprites)
DILATE = 8                     # edge dilation for color and normal
GUTTER = 4                     # frame-sheet gutter
MAX_FILE_BYTES = 4 * 1024 * 1024
NORMAL_FILL = (128, 128, 255)
MAPS = ("color", "normal", "emission", "mask")
KEY_RE = re.compile(r"^[a-z0-9_]+/[a-z0-9_]+/[a-z0-9_]+$")

# category -> rules. size = (max_w, max_h) of the written file; frame = max frame edge for sheets.
# exact = file must be exactly that size. padded = tight sprite needing the 8 px clear border.
CATEGORIES = {
    "planets":     {"size": (2048, 1024), "padded": False, "lit": False},
    "terrain":     {"size": (1024, 1024), "padded": False, "lit": True, "exact": True},
    "backgrounds": {"size": (2048, 1024), "padded": False, "lit": False, "exact": True},
    "ships":       {"size": (1536, 768),  "padded": True,  "lit": True},
    "characters":  {"size": (2048, 2048), "padded": True,  "lit": True, "frame": 256},
    "creatures":   {"size": (2048, 2048), "padded": True,  "lit": True, "frame": 512},
    "props":       {"size": (512, 512),   "padded": True,  "lit": True},
    "fx":          {"size": (1024, 1024), "padded": True,  "lit": False, "frame": 256},
    "icons":       {"size": (128, 128),   "padded": True,  "lit": False, "exact": True},
    "ui":          {"size": (1024, 1024), "padded": False, "lit": False},
}

# Per-variant overrides of the category caps (contract §4).
VARIANT_SIZE = {
    ("planets", "surface"): (2048, 1024),
    ("planets", "clouds"): (1024, 512),
    ("planets", "glow"): (512, 512),
    ("ships", "top"): (768, 768),     # 512 normal, 768 for large ships; manifest "large": true
    ("ships", "side"): (1536, 512),
}


def size_cap(key, entry):
    cat, _name, variant = key.split("/")
    rules = CATEGORIES[cat]
    cap = VARIANT_SIZE.get((cat, variant), rules["size"])
    if (cat, variant) == ("ships", "top") and not entry.get("large"):
        cap = (512, 512)
    return cap, rules
