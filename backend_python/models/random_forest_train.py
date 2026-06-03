import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline

print("\n=== STARTING RANDOM FOREST TRAINING ===")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "model_ready_data.csv")
MODEL_OUTPUT = os.path.join(BASE_DIR, "random_forest_model.pkl")
METRICS_OUTPUT = os.path.join(BASE_DIR, "random_forest_model_metrics.json")
RANDOM_STATE = 42


def split_data(X, y):
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.4, random_state=RANDOM_STATE, stratify=y
    )
    X_valid, X_test, y_valid, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=RANDOM_STATE, stratify=y_temp
    )
    return X_train, X_valid, X_test, y_train, y_valid, y_test


def find_best_threshold(y_true, y_prob, min_recall=0.70):
    best_threshold = 0.50
    best_accuracy = -1.0

    for threshold in np.arange(0.05, 0.96, 0.01):
        y_pred = (y_prob >= threshold).astype(int)
        recall = recall_score(y_true, y_pred, zero_division=0)
        accuracy = accuracy_score(y_true, y_pred)

        if recall >= min_recall and accuracy > best_accuracy:
            best_threshold = float(threshold)
            best_accuracy = accuracy

    if best_accuracy >= 0:
        return best_threshold

    for threshold in np.arange(0.05, 0.96, 0.01):
        y_pred = (y_prob >= threshold).astype(int)
        accuracy = accuracy_score(y_true, y_pred)
        if accuracy > best_accuracy:
            best_threshold = float(threshold)
            best_accuracy = accuracy

    return best_threshold


def evaluate_model(model, X, y, threshold):
    y_prob = model.predict_proba(X)[:, 1]
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, y_pred).ravel()

    return {
        "threshold": round(float(threshold), 2),
        "accuracy": round(accuracy_score(y, y_pred), 4),
        "precision": round(precision_score(y, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y, y_prob), 4),
        "pr_auc": round(average_precision_score(y, y_prob), 4),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
        "classification_report": classification_report(y, y_pred, output_dict=True, zero_division=0),
    }


def feature_importance(model, feature_names):
    rf = model.named_steps["model"]
    pairs = sorted(zip(feature_names, rf.feature_importances_), key=lambda item: item[1], reverse=True)
    return [{"feature": name, "importance": round(float(value), 5)} for name, value in pairs[:15]]


def print_results(metrics):
    print("\n" + "=" * 60)
    print("--- Random Forest Final Results ---")
    print(f"Threshold : {metrics['threshold']:.2f}")
    print(f"Accuracy  : {metrics['accuracy'] * 100:.2f}%")
    print(f"Precision : {metrics['precision'] * 100:.2f}%")
    print(f"Recall    : {metrics['recall'] * 100:.2f}%")
    print(f"F1 Score  : {metrics['f1'] * 100:.2f}%")
    print(f"ROC-AUC   : {metrics['roc_auc']:.4f}")
    print(f"PR-AUC    : {metrics['pr_auc']:.4f}")
    print(f"Confusion : {metrics['confusion_matrix']}")
    print("=" * 60)


def train_rf():
    if not os.path.exists(DATA_PATH):
        print(f"[-] Error: Data file not found at {DATA_PATH}")
        return

    print("[*] Loading dataset...")
    df = pd.read_csv(DATA_PATH).dropna(subset=["label"])
    X = df.drop("label", axis=1)
    y = df["label"].astype(int)

    print(f"[*] Dataset size: {len(df)}")
    print(f"[*] Class distribution: {y.value_counts().to_dict()}")

    X_train, X_valid, X_test, y_train, y_valid, y_test = split_data(X, y)

    pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("model", RandomForestClassifier(random_state=RANDOM_STATE, n_jobs=-1)),
        ]
    )

    param_distributions = {
        "model__n_estimators": [200, 300, 500],
        "model__max_depth": [8, 12, 16, 24, None],
        "model__min_samples_split": [2, 5, 10, 20],
        "model__min_samples_leaf": [1, 2, 4, 8],
        "model__max_features": ["sqrt", "log2", None],
        "model__class_weight": [None, "balanced", "balanced_subsample"],
    }

    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
    search = RandomizedSearchCV(
        pipeline,
        param_distributions=param_distributions,
        n_iter=24,
        cv=cv,
        scoring="roc_auc",
        n_jobs=-1,
        random_state=RANDOM_STATE,
        verbose=1,
    )

    print("[*] Searching best Random Forest parameters...")
    search.fit(X_train, y_train)
    best_model = search.best_estimator_
    print(f"[+] Best parameters: {search.best_params_}")

    valid_prob = best_model.predict_proba(X_valid)[:, 1]
    threshold = find_best_threshold(y_valid, valid_prob, min_recall=0.70)
    metrics = evaluate_model(best_model, X_test, y_test, threshold)
    metrics["best_params"] = search.best_params_
    metrics["feature_names"] = list(X.columns)
    metrics["feature_importance"] = feature_importance(best_model, list(X.columns))

    print_results(metrics)

    artifact = {
        "model": best_model,
        "threshold": threshold,
        "feature_names": list(X.columns),
        "metrics": metrics,
    }

    joblib.dump(artifact, MODEL_OUTPUT)
    with open(METRICS_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"[+] Model saved to: {MODEL_OUTPUT}")
    print(f"[+] Metrics saved to: {METRICS_OUTPUT}")


if __name__ == "__main__":
    train_rf()
