from __future__ import annotations

import json

import numpy as np
import pandas as pd
from pathlib import Path


BENCHMARK_SPEC = {
    "name": "simple-sine-regression",
    "description": "Fixed 1D regression benchmark with train/validation/test splits.",
    "n_samples": 300,
    "x_min": -3.0,
    "x_max": 3.0,
    "noise_std": 0.01,
    "seed": 42,
    "train_size": 180,
    "validation_size": 60,
    "test_size": 60,
}

DATA_DIR = Path(__file__).parent.parent / "public" / "data"


def _target_function(x: np.ndarray) -> np.ndarray:
    return np.sin(x)


def build_dataset() -> dict[str, object]:
    rng = np.random.default_rng(BENCHMARK_SPEC["seed"])
    n_samples = BENCHMARK_SPEC["n_samples"]

    x = np.linspace(
        BENCHMARK_SPEC["x_min"],
        BENCHMARK_SPEC["x_max"],
        n_samples,
    ).reshape(-1, 1)
    y = _target_function(x) + BENCHMARK_SPEC["noise_std"] * rng.standard_normal(
        (n_samples, 1)
    )

    permutation = rng.permutation(n_samples)
    train_end = BENCHMARK_SPEC["train_size"]
    validation_end = train_end + BENCHMARK_SPEC["validation_size"]

    return {
        "train": {
            "x": x[permutation[:train_end]],
            "y": y[permutation[:train_end]],
        },
        "validation": {
            "x": x[permutation[train_end:validation_end]],
            "y": y[permutation[train_end:validation_end]],
        },
        "test": {
            "x": x[permutation[validation_end:]],
            "y": y[permutation[validation_end:]],
        },
        "spec": dict(BENCHMARK_SPEC),
    }


def prepare(force: bool = False) -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    
    # Check if all three CSV files exist
    train_csv = DATA_DIR / "train.csv"
    validation_csv = DATA_DIR / "validation.csv"
    test_csv = DATA_DIR / "test.csv"
    
    if force or not (train_csv.exists() and validation_csv.exists() and test_csv.exists()):
        dataset = build_dataset()
        
        # Save each split as CSV
        for split in ["train", "validation", "test"]:
            split_data = dataset[split]
            df = pd.DataFrame({
                "x": split_data["x"].squeeze(),
                "y": split_data["y"].squeeze(),
            })
            csv_path = DATA_DIR / f"{split}.csv"
            df.to_csv(csv_path, index=False)
    return DATA_DIR


def load_prepared_data() -> dict[str, object]:
    prepare()
    
    dataset = {}
    for split in ["train", "validation", "test"]:
        csv_path = DATA_DIR / f"{split}.csv"
        df = pd.read_csv(csv_path)
        dataset[split] = {
            "x": df["x"].values.reshape(-1, 1).astype(np.float32),
            "y": df["y"].values.reshape(-1, 1).astype(np.float32),
        }
    
    dataset["spec"] = dict(BENCHMARK_SPEC)
    
    return dataset


def main() -> None:
    output_path = prepare(force=True)
    dataset = load_prepared_data()
    print(f"Prepared benchmark data at: {output_path}")
    print(f"Train samples: {dataset['train']['x'].shape[0]}")
    print(f"Validation samples: {dataset['validation']['x'].shape[0]}")
    print(f"Test samples: {dataset['test']['x'].shape[0]}")


if __name__ == "__main__":
    main()
