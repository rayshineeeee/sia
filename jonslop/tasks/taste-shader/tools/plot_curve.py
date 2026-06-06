#!/usr/bin/env python3
"""
Plot the running-max accuracy curve across generations.

Scans runs/<run>/gen_<n>/results.json, reads the top-level 'accuracy' scalar per
generation, and plots both per-gen accuracy and the running-max (best-so-far)
curve to a PNG.

Usage:
    python tools/plot_curve.py                          # all runs under runs/
    python tools/plot_curve.py --run-dir runs/run_1     # single run
    python tools/plot_curve.py --out curve.png
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

TOOLS_DIR = Path(__file__).resolve().parent
TASK_DIR = TOOLS_DIR.parent
RUNS_DIR = TASK_DIR / "runs"


def gen_num(gen_dir: Path) -> int:
    m = re.search(r"gen_?(\d+)", gen_dir.name)
    return int(m.group(1)) if m else 0


def collect(run_dir: Path) -> tuple[list[int], list[float]]:
    gens = sorted(run_dir.glob("gen_*"), key=gen_num)
    xs, ys = [], []
    for g in gens:
        rj = g / "results.json"
        if not rj.exists():
            continue
        try:
            data = json.loads(rj.read_text(encoding="utf-8"))
            acc = float(data.get("accuracy", 0.0))
        except Exception:
            acc = 0.0
        xs.append(gen_num(g))
        ys.append(acc)
    return xs, ys


def running_max(ys: list[float]) -> list[float]:
    out, best = [], float("-inf")
    for y in ys:
        best = max(best, y)
        out.append(best)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=None, help="Single run dir; default = all runs/")
    parser.add_argument("--out", type=Path, default=None, help="Output PNG path")
    args = parser.parse_args()

    if args.run_dir:
        run_dirs = [args.run_dir]
    else:
        run_dirs = sorted(RUNS_DIR.glob("run_*")) or sorted(p for p in RUNS_DIR.iterdir() if p.is_dir()) if RUNS_DIR.exists() else []

    if not run_dirs:
        raise SystemExit(f"No run directories found under {RUNS_DIR}")

    plt.figure(figsize=(9, 5))
    plotted = False
    for run_dir in run_dirs:
        xs, ys = collect(run_dir)
        if not xs:
            continue
        plotted = True
        rmax = running_max(ys)
        plt.plot(xs, ys, marker="o", alpha=0.35, label=f"{run_dir.name} per-gen")
        plt.plot(xs, rmax, marker="", linewidth=2.0, label=f"{run_dir.name} running-max")

    if not plotted:
        raise SystemExit("No results.json found in any generation.")

    plt.xlabel("generation")
    plt.ylabel("accuracy (0-100, higher better)")
    plt.title("taste-shader: accuracy curve")
    plt.ylim(0, 100)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=8)
    plt.tight_layout()

    out = args.out or (TASK_DIR / "runs" / "accuracy_curve.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=120)
    print(f"Saved curve -> {out}")


if __name__ == "__main__":
    main()
