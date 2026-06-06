#!/usr/bin/env python3
"""
Fit Johnny's taste centroid from the liked image set.

CLIP-embeds every image in data/private/taste/liked/, L2-normalizes each embed,
takes the mean -> centroid, and computes the lo/hi calibration band from the
distribution of per-image cosines to the centroid. Saves data/private/taste_proxy.npz.

Schema (taste_proxy.npz):
    centroid   : float32[D]  mean of L2-normalized CLIP image embeds of liked set
    model      : "ViT-B-32"
    pretrained : "laion2b_s34b_b79k"
    lo         : float  (low anchor: a typical "off-taste" cosine floor)
    hi         : float  (high anchor: a typical "on-taste" cosine ceiling)

Prints: n images, mean intra-liked cosine, and a held-out sanity number
(mean cosine of held-out liked images to a centroid fit on the rest).

Self-contained. Usage:
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
OUT_PATH = TASK_DIR / "data" / "private" / "taste_proxy.npz"

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def embed_dir(dir_path: Path) -> tuple[np.ndarray, list[str]]:
    import open_clip
    import torch

    model, _, preprocess = open_clip.create_model_and_transforms(
        MODEL_NAME, pretrained=PRETRAINED
    )
    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

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
    print(f"Embedding liked set: {LIKED_DIR}")
    embeds, names = embed_dir(LIKED_DIR)  # (N, D), each L2-normalized
    n, d = embeds.shape
    print(f"  n images = {n}, dim = {d}, model = {MODEL_NAME}/{PRETRAINED}")

    # Centroid = mean of unit embeds.
    centroid = embeds.mean(axis=0).astype(np.float32)
    cen_unit = centroid / (np.linalg.norm(centroid) + 1e-8)

    # Per-image cosine to centroid (the on-taste distribution).
    cos_to_centroid = embeds @ cen_unit  # (N,)
    mean_cos = float(cos_to_centroid.mean())

    # Mean intra-liked pairwise cosine (how tight the cluster is).
    gram = embeds @ embeds.T
    iu = np.triu_indices(n, k=1)
    mean_intra = float(gram[iu].mean()) if n > 1 else 1.0

    # Calibration band: lo = low percentile of on-taste cosines (so off-taste
    # renders land near/below 0), hi = high percentile (so the best on-taste
    # renders approach 1). Robust to outliers via percentiles.
    lo = float(np.percentile(cos_to_centroid, 5))
    hi = float(np.percentile(cos_to_centroid, 95))
    # Guard against degenerate band.
    if hi - lo < 1e-3:
        lo, hi = mean_cos - 0.05, mean_cos + 0.05

    # Held-out sanity: leave-one-out-ish on a 80/20 split.
    rng = np.random.default_rng(0)
    idx = rng.permutation(n)
    k = max(1, n // 5)
    held = idx[:k]
    rest = idx[k:]
    rest_centroid = embeds[rest].mean(axis=0)
    rest_centroid /= np.linalg.norm(rest_centroid) + 1e-8
    held_cos = float((embeds[held] @ rest_centroid).mean())

    np.savez(
        OUT_PATH,
        centroid=centroid,
        model=MODEL_NAME,
        pretrained=PRETRAINED,
        lo=np.float32(lo),
        hi=np.float32(hi),
    )

    print("")
    print(f"  mean intra-liked cosine   : {mean_intra:.4f}")
    print(f"  mean cosine to centroid   : {mean_cos:.4f}")
    print(f"  held-out sanity (mean cos): {held_cos:.4f}  (held {k}, fit on {len(rest)})")
    print(f"  calibration band lo / hi  : {lo:.4f} / {hi:.4f}")
    print(f"  saved -> {OUT_PATH}")


if __name__ == "__main__":
    main()
