#!/usr/bin/env python3
"""
Keep/remove HOOK for curating the taste set (CLI, NO UI).

Johnny looks at a render and decides: does this match my taste or not?
  --keep   -> copy render into data/private/taste/liked/    (reinforce taste)
  --remove -> copy render into data/private/taste/disliked/ (record off-taste)

Optionally re-fit the taste centroid afterward with --refit.

Usage:
    python tools/classify.py --render path/to/render.png --keep
    python tools/classify.py --render path/to/render.png --remove --refit
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
TASK_DIR = TOOLS_DIR.parent
LIKED_DIR = TASK_DIR / "data" / "private" / "taste" / "liked"
DISLIKED_DIR = TASK_DIR / "data" / "private" / "taste" / "disliked"
FIT_SCRIPT = TOOLS_DIR / "fit_taste.py"


def main() -> None:
    parser = argparse.ArgumentParser(description="Keep/remove hook for taste curation")
    parser.add_argument("--render", type=Path, required=True, help="Render PNG to classify")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--keep", action="store_true", help="Copy into liked/")
    group.add_argument("--remove", action="store_true", help="Copy into disliked/")
    parser.add_argument("--refit", action="store_true", help="Re-run fit_taste.py after copying")
    args = parser.parse_args()

    if not args.render.exists():
        print(f"ERROR: render not found: {args.render}", file=sys.stderr)
        sys.exit(1)

    dest_dir = LIKED_DIR if args.keep else DISLIKED_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)

    stem = args.render.stem
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = dest_dir / f"{stem}_{ts}.png"
    shutil.copy2(args.render, dest)
    verdict = "KEEP" if args.keep else "REMOVE"
    print(f"{verdict}: copied {args.render} -> {dest}")

    if args.refit:
        if args.remove and not args.keep:
            print("note: --refit re-fits from liked/ only; disliked set is recorded but not used by fit_taste.py")
        print("Re-fitting taste centroid...")
        rc = subprocess.call([sys.executable, str(FIT_SCRIPT)])
        if rc != 0:
            print(f"ERROR: fit_taste.py exited with code {rc}", file=sys.stderr)
            sys.exit(rc)


if __name__ == "__main__":
    main()
