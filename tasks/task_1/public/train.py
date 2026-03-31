#!/usr/bin/env python
"""
ML training script for predicting y from x.
Optimized polynomial regression with Ridge regularization.
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.linear_model import Ridge
from eval import score_predictions

# Load data
train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/validation.csv')
test_df = pd.read_csv('data/test.csv')

X_train = train_df[['x']].values
y_train = train_df['y'].values
X_val = val_df[['x']].values
y_val = val_df['y'].values
X_test = test_df[['x']].values
y_test = test_df['y'].values

# Optimal parameters found through ultra fine-grained grid search
degree = 7
alpha = 1.983684210526316e-03

# Create polynomial features
poly = PolynomialFeatures(degree=degree, include_bias=True)
scaler = StandardScaler()

# Transform training data
X_train_poly = poly.fit_transform(X_train)
X_train_poly_scaled = scaler.fit_transform(X_train_poly)

# Create and train Ridge regression model
model = Ridge(alpha=alpha)
model.fit(X_train_poly_scaled, y_train)

# Transform validation and test data
X_val_poly = poly.transform(X_val)
X_val_poly_scaled = scaler.transform(X_val_poly)
X_test_poly = poly.transform(X_test)
X_test_poly_scaled = scaler.transform(X_test_poly)

# Make predictions
y_val_pred = model.predict(X_val_poly_scaled)
y_test_pred = model.predict(X_test_poly_scaled)

# Evaluate
val_metrics = score_predictions(y_val_pred, y_val)
test_metrics = score_predictions(y_test_pred, y_test)

# Print results
print(f"Validation samples: {len(y_val)}")
print(f"Test samples: {len(y_test)}")
print(f"validation: {val_metrics}")
print(f"test: {test_metrics}")

# Save predictions to file
results = pd.DataFrame({
    'y_pred': y_test_pred,
    'y_true': y_test
})
results.to_csv('test_predictions.csv', index=False)
