"""Dataset smoke test: is the training dataset learnable and leak-free?

NOT the real Phase 3 training. Trains a default-ish XGBoost on a strict
chronological split and compares against the always-pick-home baseline.
A result wildly above ~0.70 AUC would suggest leakage; a result at or
below the baseline would suggest broken features.

Usage:
    uv run python -m feature_engineering.smoke_test
"""

import sys

import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score
from xgboost import XGBClassifier

from .build_dataset import DATASET_PATH, ID_COLUMNS, LABEL_COLUMN

TRAIN_MAX_SEASON = 2023  # train 2015-2023, test 2024-2026


def main() -> int:
    df = pd.read_parquet(DATASET_PATH)
    feature_cols = [c for c in df.columns if c not in ID_COLUMNS + [LABEL_COLUMN]]
    df["ctx_weather"] = df["ctx_weather"].astype("category")

    train = df[df["season"] <= TRAIN_MAX_SEASON]
    test = df[df["season"] > TRAIN_MAX_SEASON]
    print(f"Train: {len(train)} matches (2015-{TRAIN_MAX_SEASON}), "
          f"Test: {len(test)} matches ({TRAIN_MAX_SEASON + 1}-2026)")

    model = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        enable_categorical=True,
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(train[feature_cols], train[LABEL_COLUMN])

    proba = model.predict_proba(test[feature_cols])[:, 1]
    pred = (proba >= 0.5).astype(int)
    auc = roc_auc_score(test[LABEL_COLUMN], proba)
    acc = accuracy_score(test[LABEL_COLUMN], pred)
    baseline = test[LABEL_COLUMN].mean()  # accuracy of always picking home

    print(f"\nAUC:              {auc:.4f}")
    print(f"Accuracy:         {acc:.4f}")
    print(f"Home baseline:    {baseline:.4f} (always pick home win)")
    print(f"Edge vs baseline: {acc - baseline:+.4f}")

    importances = pd.Series(
        model.feature_importances_, index=feature_cols
    ).sort_values(ascending=False)
    print("\nTop 15 features by importance:")
    for name, value in importances.head(15).items():
        print(f"  {name:<42} {value:.4f}")

    if auc > 0.72:
        print("\nWARNING: AUC suspiciously high - investigate for leakage.")
    elif auc < 0.55:
        print("\nWARNING: AUC barely above random - features may be broken.")
    else:
        print("\nSmoke test OK: dataset is learnable and in the expected range.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
