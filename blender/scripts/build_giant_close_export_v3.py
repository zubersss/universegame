"""B-243: the manifest row's generator for the giants' close view (planets/common/close_view). The drawing lives in
build_giant_close_v3 (the functions the accepted B-240 / B-241 sheets used); this module only gives render.py's kit path
its export / keys / preview, so the close view's files export on a row of their own and no far-disc row is re-run by it.

  writes   planets/common/{limb_band, belt_edge_0, belt_edge_1, spot_rim, close_grain}_color.png + .json
           planets/saturn/ring_edge_color.png + .json
           planets/{jupiter,saturn,uranus,neptune}/close_pigment_color.png + .json
           planets/{jupiter,saturn,uranus,neptune}/close.json            (json-only keys: no png)
  review   the exported files read back on one stamped sheet (build_giant_close_v3.export_review)

  python -I build_giant_close_export_v3.py <review png>     the read-back sheet of what is in Assets/_Game/Art
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_giant_close_v3 as GC  # noqa: E402


def export(art):
    return GC.export(art)


def keys():
    return GC.keys()


def preview(out, footnote=None):
    GC.export_review(out, footnote=footnote)


if __name__ == "__main__":                       # python -I build_giant_close_export_v3.py <review png>
    preview(sys.argv[1])
