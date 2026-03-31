"""
Prepared benchmark data at: /home/ubuntu/sia/task_1/public/data
Train samples: 180
Validation samples: 60
Test samples: 60
validation: {'loss': 0.1596197156718097, 'r2': 0.6158968830758148}
test: {'loss': 0.1643126395533773, 'r2': 0.7078601008285936}
"""

import pandas as pd
from pathlib import Path
from eval import score_predictions
from sklearn.linear_model import LinearRegression

SPLITS_DIR = Path(__file__).parent / "data" 

def load_split(name: str):
    df = pd.read_csv(SPLITS_DIR / f"{name}.csv")
    x = df[["x"]].to_numpy()
    y = df["y"].to_numpy()
    return x, y


def main() -> None:
    x_train, y_train = load_split("train")
    x_validation, y_validation = load_split("validation")
    x_test, y_test = load_split("test")

    model = LinearRegression()
    model.fit(x_train, y_train)

    validation_predictions = model.predict(x_validation)
    test_predictions = model.predict(x_test)

    print("validation:", score_predictions(validation_predictions, y_validation))
    print("test:", score_predictions(test_predictions, y_test))


if __name__ == "__main__":
    main()
