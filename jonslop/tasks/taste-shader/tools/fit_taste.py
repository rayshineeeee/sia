#!/usr/bin/env python3
"""
Fit Johnny's taste DIRECTION from the liked set vs a trivial/generic negative set.

The old proxy was a LENIENT centroid of the liked images only — near-black/sparse
and generic glossy renders still scored high because everything is "kind of close"
to a single blob in CLIP space. The fix: fit a preference DIRECTION.

    w  = normalize( mean(liked_emb) - mean(neg_emb) )

`w` points from "trivial/generic shader" toward "on-taste". We then calibrate the
score band on PROJECTIONS onto w:

    lo = 5th  percentile of NEGATIVE projections (trivial -> lands near 0)
    hi = 95th percentile of LIKED    projections (strong on-taste -> lands near 1)

CLIP-embeds every image in data/private/taste/liked/ and every trivial render in
data/private/taste/negatives/ (produced by tools/make_negatives.py), L2-normalizes
each embed. Saves data/private/taste_proxy.npz.

Schema (taste_proxy.npz):
    w               : float32[D]  L2-normalized taste direction (liked-mean - neg-mean)
    lo              : float        5th pct of negative projections onto w
    hi              : float        95th pct of liked projections onto w
    model           : "ViT-B-32"
    pretrained      : "laion2b_s34b_b79k"
    liked_centroid  : float32[D]  mean of L2-normalized liked embeds (kept for reference)

Prints: n liked, n negatives, lo/hi, and the separation between the liked vs
negative projection distributions (means + a simple AUC-style separability).

Self-contained. Usage (run make_negatives.py FIRST):
    python tools/fit_taste.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

MODEL_NAME = "ViT-B-32"
PRETRAINED = "laion2b_s34b_b79k"

TOOLS_DIR = Path(__file__).resolve().parent
TASK_DIR = TOOLS_DIR.parent
LIKED_DIR = TASK_DIR / "data" / "private" / "taste" / "liked"
NEG_DIR = TASK_DIR / "data" / "private" / "taste" / "negatives"
OUT_PATH = TASK_DIR / "data" / "private" / "taste_proxy.npz"

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def _load_clip():
    import open_clip
    import torch

    model, _, preprocess = open_clip.create_model_and_transforms(
        MODEL_NAME, pretrained=PRETRAINED
    )
    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    return model, preprocess, device


def embed_dir(dir_path: Path, model, preprocess, device) -> tuple[np.ndarray, list[str]]:
    import torch

    paths = sorted(p for p in dir_path.iterdir() if p.suffix.lower() in IMG_EXTS)
    if not paths:
        raise SystemExit(f"No images found in {dir_path}")

    embeds = []
    names = []
    with torch.no_grad():
        for p in paths:
            try:
                img = Image.open(p).convert("RGB")
            except Exception as e:
                print(f"  skip {p.name}: {e}")
                continue
            x = preprocess(img).unsqueeze(0).to(device)
            feat = model.encode_image(x)
            feat = feat / feat.norm(dim=-1, keepdim=True)
            embeds.append(feat.cpu().numpy().astype(np.float32)[0])
            names.append(p.name)
    return np.stack(embeds, axis=0), names


def main() -> None:
    if not NEG_DIR.exists() or not any(
        p.suffix.lower() in IMG_EXTS for p in NEG_DIR.iterdir()
    ):
        raise SystemExit(
            f"Negative set empty at {NEG_DIR}.\n"
            f"Run tools/make_negatives.py first."
        )

    model, preprocess, device = _load_clip()

    print(f"Embedding liked set:     {LIKED_DIR}")
    liked, liked_names = embed_dir(LIKED_DIR, model, preprocess, device)  # (NL, D)
    print(f"Embedding negative set:  {NEG_DIR}")
    neg, neg_names = embed_dir(NEG_DIR, model, preprocess, device)  # (NN, D)

    nl, d = liked.shape
    nn = neg.shape[0]
    print(f"  n liked = {nl}, n negatives = {nn}, dim = {d}, model = {MODEL_NAME}/{PRETRAINED}")

    liked_mean = liked.mean(axis=0)
    neg_mean = neg.mean(axis=0)

    # Preference direction: from trivial/generic toward on-taste.
    w = (liked_mean - neg_mean).astype(np.float32)
    w = w / (np.linalg.norm(w) + 1e-8)

    # Projections onto the direction.
    liked_proj = liked @ w  # (NL,)
    neg_proj = neg @ w      # (NN,)

    # Calibration band: trivial renders land near 0, strong on-taste near 1.
    lo = float(np.percentile(neg_proj, 5))
    hi = float(np.percentile(liked_proj, 95))
    if hi - lo < 1e-3:
        # Degenerate guard: widen around the midpoint of the two means.
        mid = 0.5 * (float(liked_proj.mean()) + float(neg_proj.mean()))
        lo, hi = mid - 0.05, mid + 0.05

    # Liked centroid kept for reference (unit-mean of liked embeds).
    liked_centroid = liked_mean.astype(np.float32)

    np.savez(
        OUT_PATH,
        w=w,
        lo=np.float32(lo),
        hi=np.float32(hi),
        model=MODEL_NAME,
        pretrained=PRETRAINED,
        liked_centroid=liked_centroid,
    )

    # Separability: fraction of (liked, neg) pairs where liked_proj > neg_proj.
    # 1.0 = perfectly separated; 0.5 = no separation.
    gt = (liked_proj[:, None] > neg_proj[None, :]).mean()

    print("")
    print(f"  liked proj  mean/min/max : {liked_proj.mean():.4f} / {liked_proj.min():.4f} / {liked_proj.max():.4f}")
    print(f"  neg   proj  mean/min/max : {neg_proj.mean():.4f} / {neg_proj.min():.4f} / {neg_proj.max():.4f}")
    print(f"  separation (liked - neg) : {float(liked_proj.mean() - neg_proj.mean()):.4f} (mean gap)")
    print(f"  rank separability (AUC)  : {float(gt):.4f}  (1.0 = perfect, 0.5 = none)")
    print(f"  calibration band lo / hi : {lo:.4f} / {hi:.4f}")
    print(f"  saved -> {OUT_PATH}")


if __name__ == "__main__":
    main()
