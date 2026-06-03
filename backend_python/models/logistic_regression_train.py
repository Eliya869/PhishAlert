import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    fbeta_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

print("\n=== STARTING LOGISTIC REGRESSION (MAX ACCURACY) ===")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "model_ready_data.csv")
MODEL_OUTPUT = os.path.join(BASE_DIR, "logistic_model.pkl")
METRICS_OUTPUT = os.path.join(BASE_DIR, "logistic_model_metrics.json")
RANDOM_STATE = 42


def find_best_threshold(y_true, y_prob):
    best_threshold = 0.50
    best_score = -1.0

    for threshold in np.arange(0.20, 0.85, 0.01):
        y_pred = (y_prob >= threshold).astype(int)
        score = accuracy_score(y_true, y_pred)

        if score > best_score:
            best_threshold = float(threshold)
            best_score = score

    return best_threshold


def evaluate_model(model, X_test, y_test, threshold):
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

    return {
        "threshold": round(float(threshold), 2),
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, y_prob), 4),
        "pr_auc": round(average_precision_score(y_test, y_prob), 4),
        "confusion_matrix": {
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        }
    }


def train_logistic():
    if not os.path.exists(DATA_PATH):
        print(f"[-] Error: Data file not found at {DATA_PATH}")
        return

    print("[*] Loading dataset...")
    df = pd.read_csv(DATA_PATH).dropna(subset=["label"])
    X = df.drop("label", axis=1)
    y = df["label"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)),
        ]
    )

    param_grid = {
        "model__C": [0.01, 0.1, 1.0, 10.0],
        "model__solver": ["lbfgs", "liblinear"],
        "model__class_weight": [None],
    }

    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)

    grid_search = GridSearchCV(
        pipeline, param_grid, cv=cv,
        scoring="accuracy",
        n_jobs=2,
        verbose=1
    )

    print("[*] Running optimization for highest Accuracy (Safe Memory Mode)...")
    grid_search.fit(X_train, y_train)
    best_model = grid_search.best_estimator_

    train_prob = best_model.predict_proba(X_train)[:, 1]
    best_threshold = find_best_threshold(y_train, train_prob)
    metrics = evaluate_model(best_model, X_test, y_test, best_threshold)

    print("\n" + "=" * 60)
    print("--- Logistic Regression Final Results ---")
    print(f"Threshold : {metrics['threshold']:.2f}")
    print(f"Accuracy  : {metrics['accuracy'] * 100:.2f}%")
    print(f"Precision : {metrics['precision'] * 100:.2f}%")
    print(f"Recall    : {metrics['recall'] * 100:.2f}%")
    print(f"Confusion : {metrics['confusion_matrix']}")
    print("=" * 60)

    print("[*] Saving production model...")
    joblib.dump(best_model, MODEL_OUTPUT)
    with open(METRICS_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"[+] Complete. Models ready.")


if __name__ == "__main__":
    train_logistic()