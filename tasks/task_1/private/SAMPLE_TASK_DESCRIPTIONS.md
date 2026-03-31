# Task Description

Your task is to build a classifier that predicts whether `label` is `0` or `1` from the input features. You should improve `train.py` through multiple iterations and aim to maximize classification performance on the test set.

# Data description

The public data is in `data/train.csv`, `data/validation.csv`, and `data/test.csv`.

Each file contains several input feature columns and one target column: `label`.

# Evaluation description

Predictions are evaluated using accuracy and F1 score, as defined in `eval.py`.

Higher `accuracy` is better and higher `f1` is better.

Report your metrics like the following:

```text
Validation samples: xx
Test samples: xx
validation: {'accuracy': xxx, 'f1': xxx}
test: {'accuracy': xxx, 'f1': xxx}
```

# Additional Rules

1. Create `train.py` if it does not exist and iterate on it multiple times.
2. You are not allowed to go outside `task_3/public`.
3. Activate the virtual environment using `source .venv/bin/activate`.

---

# Task Description

Your task is to forecast `target` from the historical and contextual input columns in the dataset. You should keep refining `train.py` and make repeated improvements to achieve better forecasting performance.

# Data description

The public data is in `data/train.csv`, `data/validation.csv`, and `data/test.csv`.

Each file contains feature columns and one target column: `target`.

# Evaluation description

Predictions are evaluated with mean absolute error (`mae`) and root mean squared error (`rmse`), as defined in `eval.py`.

Lower `mae` is better and lower `rmse` is better.

Report your metrics like the following:

```text
Validation samples: xx
Test samples: xx
validation: {'mae': xxx, 'rmse': xxx}
test: {'mae': xxx, 'rmse': xxx}
```

# Additional Rules

1. Create `train.py` if it does not exist and iterate on it multiple times.
2. You are not allowed to go outside `task_4/public`.
3. Activate the virtual environment using `source .venv/bin/activate`.

---

# Task Description

Your task is to rank items for each query so that the most relevant items appear higher in the output. You should repeatedly update `train.py` to improve the ranking quality on the evaluation set.

# Data description

The public data is in `data/train.csv`, `data/validation.csv`, and `data/test.csv`.

Each file contains query-item pairs, feature columns, and a relevance label called `relevance`.

# Evaluation description

Predictions are evaluated with mean reciprocal rank (`mrr`) and normalized discounted cumulative gain (`ndcg`), as defined in `eval.py`.

Higher `mrr` is better and higher `ndcg` is better.

Report your metrics like the following:

```text
Validation samples: xx
Test samples: xx
validation: {'mrr': xxx, 'ndcg': xxx}
test: {'mrr': xxx, 'ndcg': xxx}
```

# Additional Rules

1. Create `train.py` if it does not exist and iterate on it multiple times.
2. You are not allowed to go outside `task_5/public`.
3. Activate the virtual environment using `source .venv/bin/activate`.

---

# Task Description

Your task is to predict the probability of a rare event from the provided features. It is important that you iterate on `train.py` multiple times, especially paying attention to class imbalance and calibration.

# Data description

The public data is in `data/train.csv`, `data/validation.csv`, and `data/test.csv`.

Each file contains feature columns and one binary target column: `target`.

# Evaluation description

Predictions are evaluated with AUROC and average precision (`ap`), as defined in `eval.py`.

Higher `auroc` is better and higher `ap` is better.

Report your metrics like the following:

```text
Validation samples: xx
Test samples: xx
validation: {'auroc': xxx, 'ap': xxx}
test: {'auroc': xxx, 'ap': xxx}
```

# Additional Rules

1. Create `train.py` if it does not exist and iterate on it multiple times.
2. You are not allowed to go outside `task_6/public`.
3. Activate the virtual environment using `source .venv/bin/activate`.

---

# Task Description

Your task is to predict one of several classes from the input features. You should improve `train.py` over multiple iterations and try to achieve strong multiclass performance on both validation and test sets.

# Data description

The public data is in `data/train.csv`, `data/validation.csv`, and `data/test.csv`.

Each file contains feature columns and one target column: `label`, which takes one of several class values.

# Evaluation description

Predictions are evaluated with accuracy and macro F1, as defined in `eval.py`.

Higher `accuracy` is better and higher `macro_f1` is better.

Report your metrics like the following:

```text
Validation samples: xx
Test samples: xx
validation: {'accuracy': xxx, 'macro_f1': xxx}
test: {'accuracy': xxx, 'macro_f1': xxx}
```

# Additional Rules

1. Create `train.py` if it does not exist and iterate on it multiple times.
2. You are not allowed to go outside `task_7/public`.
3. Activate the virtual environment using `source .venv/bin/activate`.