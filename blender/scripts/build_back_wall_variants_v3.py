"""B-242: the manifest row's generator for the two surface-variant back walls (terrain/earth/back_wall_sand,
terrain/mars/back_wall_basalt). The drawing lives in build_back_wall_v3 beside the tiers' walls (draw_tier with a variant's
name); this module only gives render.py's kit path its export / keys / preview, so the variants export on their own row and
the tiers' twenty exported tiles are never rewritten by it.

  python -I build_back_wall_v3.py --variants <review png>     the sheet (or this module's preview)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_back_wall_v3 as BW  # noqa: E402


def export(art):
    return BW.export_variants(art)


def keys():
    return BW.variant_keys()


def preview(out, footnote=None):
    BW.preview_variants(out, footnote=footnote)


if __name__ == "__main__":                       # python -I build_back_wall_variants_v3.py <review png>
    preview(sys.argv[1])
