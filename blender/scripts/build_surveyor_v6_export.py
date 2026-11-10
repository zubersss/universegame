"""B-250 (D-200; LEAD's word 11-10 12:4x): the manifest row's generator for the v6 surveyor's frame sheets, slice 1:
characters/surveyor_v6/side (idle, walk, run), /side_air (jump, fall, land, stroll), /side_dig (the four dig clips, the
five aim holds). The drawings and the json live in build_surveyor_frames_v6; this module only gives render.py's kit path
its export / keys / preview.

  python -I build_surveyor_v6_export.py <review png>     the read-back sheet of what is in Assets/_Game/Art
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_surveyor_frames_v6 as FR  # noqa: E402


def export(art):
    return FR.export(art)


def keys():
    return FR.keys()


def preview(out, footnote=None):
    FR.readback(out, footnote=footnote)


if __name__ == "__main__":
    preview(sys.argv[1])
