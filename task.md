## Objective

Train a model that predicts a noisy sine wave from a single scalar input. The benchmark uses fixed `train`, `validation`, and `test` splits so experiments are directly comparable.

## Fixed Benchmark Files

- `prepare.py` is the benchmark definition. It creates the dataset, applies the split, and exposes the metric helper functions.
- `prepare.py` must stay fixed across experiments so results remain comparable.
- `train.py` is the baseline training script. This is the file you improve.

## Data Protocol

Running `python prepare.py` creates one deterministic dataset with:

- 300 total samples
- `x` values from `-3` to `3`
- targets generated as `sin(x) + Gaussian noise`
- seed `42`
- a fixed split into `180` train samples, `60` validation samples, and `60` test samples

The split roles are:

- `train`: fit model parameters
- `validation`: model selection and iteration feedback
- `test`: held-out evaluation split

`prepare.py` writes the prepared tensors to `simple/data/prepared_data.pt` and stores the benchmark metadata in `simple/data/metadata.json`.

## Evaluation

Use `load_prepared_data()` from `prepare.py` instead of generating data inside `train.py`.

Use `score_predictions()` from `prepare.py` to compute the reported loss and R-squared values.

Required outputs:

- `FINAL_VAL_LOSS`: mean squared error on the validation split
- `FINAL_VAL_R2`: R-squared on the validation split
- `FINAL_TEST_LOSS`: mean squared error on the test split
- `FINAL_TEST_R2`: R-squared on the test split

Lower loss is better. Use the validation split for tuning and the test split for consistent held-out evaluation.

## Baseline Behavior

The current baseline `train.py`:

- loads the fixed prepared dataset from `prepare.py`
- trains a small MLP on the training split
- tracks the best model state by validation loss during training
- restores that best state before computing the final validation and test metrics
- prints the four required metric lines exactly

## Training Script Contract

Any updated `train.py` should:

- import the benchmark data from `prepare.py`
- trains a model using the fixed prepared splits
- use the validation split for model selection
- prints the required metric lines exactly
- does not change the benchmark definition in `prepare.py`

In short: `prepare.py` defines the fixed benchmark, and `train.py` is the part that can change between experiments.
