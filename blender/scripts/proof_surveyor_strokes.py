"""B-246: the proof that build_surveyor_v3's new pose key (front_arm, default True) leaves every shipped drawing as it was.
For every pose of characters/surveyor/side (98) and side_b (72) the strokes drawn by the builder as committed at <rev>
(git show <rev>:blender/scripts/build_surveyor_v3.py) and by the working file are compared value for value (points, radii,
materials, order). Nothing under Assets/ is read or written; the old source goes to blender/preview/b246/.

  python -I proof_surveyor_strokes.py [rev]        rev: a commit that holds the builder before the change (default below)
"""
import importlib.util
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from meridian import fakegp  # noqa: E402

fakegp.install()                        # build_surveyor_v3 imports bpy at its top: the stub must be in place first
import build_surveyor_v3 as NEW  # noqa: E402
import build_surveyor_side_b as SB  # noqa: E402

DEFAULT_REV = "3ff5e37e"                # B-243's export commit: the last one before B-246 touched build_surveyor_v3


def load_old(rev):
    src = subprocess.run(["git", "show", f"{rev}:blender/scripts/build_surveyor_v3.py"], cwd=REPO, capture_output=True, text=True,
                         check=True).stdout
    dd = os.path.join(REPO, "blender", "preview", "b246")
    os.makedirs(dd, exist_ok=True)
    path = os.path.join(dd, "build_surveyor_v3_old.py")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(src)
    spec = importlib.util.spec_from_file_location("build_surveyor_v3_old", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, src


def side_poses(SV):
    out = ([SV.idle_pose(i) for i in range(10)] + [SV.walk_pose(i) for i in range(12)] + list(SV.JUMP) + list(SV.LAND)
           + [SV.look_pose(i) for i in range(12)] + list(SV.BUMP) + list(SV.CONK) + [SV.run_pose(i) for i in range(12)]
           + [SV.fall_pose(i) for i in range(8)] + list(SV.DASH))
    want = sum(n for _c, n in SV.CLIPS)
    if len(out) != want:
        raise SystemExit(f"side: {len(out)} poses built, the sheet has {want}")
    return out


def strokes(draw, materials, pose, seed):
    gp = fakegp.FakeGP()
    M = materials(gp)
    d = fakegp.FakeDrawing()
    draw(d, M, pose, seed)
    return fakegp.strokes_of(d, gp)


def same(a, b):
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        return np.array_equal(np.asarray(a), np.asarray(b))
    if isinstance(a, (list, tuple)):
        return isinstance(b, (list, tuple)) and len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def main(rev):
    OLD, src = load_old(rev)
    if "front_arm" in src:
        raise SystemExit(f"{rev} already holds the front_arm key: name an earlier commit")
    bad = 0
    n_strokes = 0
    po, pn = side_poses(OLD), side_poses(NEW)
    for f, (a, b) in enumerate(zip(po, pn)):
        so = strokes(lambda d, M, p, s: OLD.draw_surveyor(d, M, p, seed=s), OLD.materials, a, 7 * f)
        sn = strokes(lambda d, M, p, s: NEW.draw_surveyor(d, M, p, seed=s), NEW.materials, b, 7 * f)
        n_strokes += len(sn)
        if not same(so, sn):
            bad += 1
            print(f"side frame {f}: DIFFERS ({len(so)} strokes before, {len(sn)} now)")
    print(f"side: {len(pn)} poses, {n_strokes} strokes compared")
    n_strokes = 0
    poses = SB.all_poses()
    for f, pose in enumerate(poses):
        SB.SV = OLD
        try:
            so = strokes(lambda d, M, p, s: SB.draw_side_b(d, M, p, seed=s), SB.materials, pose, 7 * f)
        finally:
            SB.SV = NEW
        sn = strokes(lambda d, M, p, s: SB.draw_side_b(d, M, p, seed=s), SB.materials, pose, 7 * f)
        n_strokes += len(sn)
        if not same(so, sn):
            bad += 1
            print(f"side_b frame {f}: DIFFERS ({len(so)} strokes before, {len(sn)} now)")
    print(f"side_b: {len(poses)} poses, {n_strokes} strokes compared")
    print(f"RESULT: {'every stroke identical' if not bad else str(bad) + ' drawings differ'} (old = {rev})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_REV))
