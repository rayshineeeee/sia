#!/usr/bin/env python3
"""Reward-faithfulness probe (Track 3 — research).

QUESTION: when a self-improving loop optimizes a PROXY reward (CLIP-cosine to a
reference) for a SUBJECTIVE target (taste), does the climb stay faithful — i.e.
does an INDEPENDENT judge that is NOT part of the reward agree the render is
getting closer? Where the optimized proxy rises but the independent judge does
NOT, the loop is Goodharting the proxy.

METHOD (read-only on a finished converge run; no edits to converge.py):
  for each best-so-far frame the loop kept:
    clip_sim = cosine(CLIP(frame), CLIP(reference))   # the OPTIMIZED reward
    vlm_sim  = an independent VLM's 0-1 similarity     # NEVER used as reward
  Report Pearson(clip_sim, vlm_sim) and plot both curves. High corr -> the proxy
  is a faithful stand-in for taste; low / late-diverging -> reward hacking.

This reuses converge.py's CLIP + VLM plumbing by import (so the metric is byte-
identical to what the loop optimized) — it does not modify it.

Usage:
    .venv/bin/python tools/faithfulness_probe.py --run demo/converge/run1 [--every 1]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from converge import (  # read-only reuse of the loop's exact metric + VLM client
    DEFAULT_VISION_MODEL,
    _image_data_url,
    clip_embed,
    cosine,
    discover_vision_model,
    make_client,
)


def vlm_similarity(client, model, ref_img: Image.Image, render_img: Image.Image):
    """Independent 0-1 similarity from a VLM. NOT used as a reward — a witness."""
    prompt = (
        "Compare two images.\n"
        "- IMAGE 1: the REFERENCE (the goal look).\n"
        "- IMAGE 2: a candidate RENDER.\n"
        "How visually similar is the render to the reference overall (structure, "
        "color, density, composition)? Reply with ONLY one line:\n"
        "SIMILARITY: N    (N is 0-10; 10 = looks identical, 0 = nothing alike)\n"
    )
    resp = client.chat.completions.create(
        model=model,
        temperature=0.0,
        max_tokens=1400,  # thinking model: budget for the reasoning trace + answer
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": _image_data_url(ref_img)}},
                {"type": "image_url", "image_url": {"url": _image_data_url(render_img)}},
            ],
        }],
    )
    txt = resp.choices[0].message.content or ""
    m = re.search(r"SIMILARITY:\s*([0-9]+(?:\.[0-9]+)?)", txt)
    if m:
        return round(min(10.0, float(m.group(1))) / 10.0, 4)
    nums = re.findall(r"\b(10(?:\.0)?|[0-9](?:\.[0-9])?)\b", txt)  # fallback: last 0-10
    return round(float(nums[-1]) / 10.0, 4) if nums else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Reward-faithfulness probe")
    ap.add_argument("--run", required=True, help="converge out dir (reference.png + frames/)")
    ap.add_argument("--every", type=int, default=1, help="sample every Nth frame")
    args = ap.parse_args()

    run = Path(args.run).resolve()
    ref_path = run / "reference.png"
    frames = sorted((run / "frames").glob("iter_*.png"))[:: args.every]
    if not ref_path.exists() or not frames:
        print(f"FATAL: need {ref_path} and {run}/frames/iter_*.png", file=sys.stderr)
        return 1

    ref = Image.open(ref_path).convert("RGB")
    ref_emb = clip_embed(ref)

    client = make_client()
    judge = discover_vision_model(client, DEFAULT_VISION_MODEL)
    if not judge:
        print("FATAL: no working independent VLM judge", file=sys.stderr)
        return 1
    print(f"[probe] independent judge = {judge}\n")

    rows = []
    for f in frames:
        it = int(f.stem.split("_")[1])
        img = Image.open(f).convert("RGB")
        clip_sim = round(cosine(clip_embed(img), ref_emb), 4)
        vlm_sim = vlm_similarity(client, judge, ref, img)
        rows.append({"iter": it, "clip_sim": clip_sim, "vlm_sim": vlm_sim})
        print(f"[iter {it:>2}] clip={clip_sim:.4f}  vlm={vlm_sim}")

    its = [r["iter"] for r in rows]
    clip = [r["clip_sim"] for r in rows]
    vlm = [r["vlm_sim"] for r in rows]
    pairs = [(c, v) for c, v in zip(clip, vlm) if v is not None]
    corr = (
        float(np.corrcoef([p[0] for p in pairs], [p[1] for p in pairs])[0, 1])
        if len(pairs) > 2
        else float("nan")
    )

    plt.figure(figsize=(9, 5))
    plt.plot(its, clip, color="crimson", lw=2.2, marker="o",
             label="CLIP proxy — the OPTIMIZED reward")
    plt.plot(its, [v if v is not None else np.nan for v in vlm], color="#2e5aa8",
             lw=2.0, marker="s", label="VLM independent judge — NOT optimized")
    plt.xlabel("iteration")
    plt.ylabel("similarity to reference")
    plt.title(f"Reward faithfulness: proxy vs independent judge  (Pearson r = {corr:.2f})")
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(run / "faithfulness.png", dpi=120)
    plt.close()

    out = {
        "run": str(run),
        "judge_model": judge,
        "pearson_clip_vs_vlm": round(corr, 4) if corr == corr else None,
        "clip_gain": round(clip[-1] - clip[0], 4),
        "vlm_gain": (round(vlm[-1] - vlm[0], 4) if vlm[0] is not None and vlm[-1] is not None else None),
        "rows": rows,
    }
    (run / "faithfulness.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("\n=== FAITHFULNESS ===")
    print(json.dumps({k: out[k] for k in
                      ("pearson_clip_vs_vlm", "clip_gain", "vlm_gain", "judge_model")}, indent=2))
    print(f"chart -> {run / 'faithfulness.png'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
