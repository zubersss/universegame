"""B-246: one lock, one process - the surveyor stroke proof (proof_surveyor_strokes), then sheet 1 (build_surveyor_side_dig's
preview) only if every shipped drawing is stroke-identical. A turn beside UNITY is one job (D-037), so the two run together.

  python -I b246_run.py <review png> [rev]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import proof_surveyor_strokes as PROOF  # noqa: E402
import build_surveyor_side_dig as SD  # noqa: E402

if __name__ == "__main__":
    rc = PROOF.main(sys.argv[2] if len(sys.argv) > 2 else PROOF.DEFAULT_REV)
    if rc:
        sys.exit(rc)
    SD.preview(sys.argv[1])
