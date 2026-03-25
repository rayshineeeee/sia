# Task Description

Your task is to train a model to predict `y` from `x`. It's important that you iterate on `train.py` over and over again to improve your test metrics.

# Data description

The public data is in `data/train.csv`, `data/validation.csv`, and `data/test.csv`.
Each file contains two columns: `x` and `y`. 

# Evaluation description

Predictions are evaluated with mean squared error (`loss`) and `r2`, as defined in `eval.py`.
Lower `loss` is better and higher `r2` is better.

Report your metrics like the following:
```
Validation samples: xx
Test samples: xx
validation: {'loss': xxx, 'r2': xxx}
test: {'loss': xxx, 'r2': xxx}
```

# Additional Rules
1. Create train.py if it doesn't exist and iterate on it. 
2. You are not allowed to go outside `task_1/public`. 
3. Activate virtual environment using `source .venv/bin/activate`.
