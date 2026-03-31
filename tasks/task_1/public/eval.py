import numpy as np

def score_predictions(predictions: np.ndarray, targets: np.ndarray) -> dict[str, float]:
    predictions = np.asarray(predictions)
    targets = np.asarray(targets)

    mse = np.mean((predictions - targets) ** 2)
    ss_res = np.sum((predictions - targets) ** 2)
    ss_tot = np.sum((targets - targets.mean()) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {"loss": float(mse), "r2": float(r2)}