"""B-246 (D-196, LEAD 02:1x): the manifest row's generator for props/rig/grip_fist - the surveyor's front glove as a fist
round a shaft, one 32x32 sprite UNITY lays OVER the held tool at side_dig's hand socket. The drawing lives in
build_surveyor_side_dig (grip_frame: the glove's own strokes); this module only gives render.py's kit path its export /
keys / preview.

  python -I build_grip_fist_v3.py <review png>     the read-back sheet of what is in Assets/_Game/Art
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_surveyor_side_dig as SD  # noqa: E402


def export(art):
    return SD.fist_export(art)


def keys():
    return [SD.FIST_KEY]


def preview(out, footnote=None):
    SD.fist_review(out, footnote=footnote)


if __name__ == "__main__":
    preview(sys.argv[1])
