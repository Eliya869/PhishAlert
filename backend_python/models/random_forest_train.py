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
    fbeta_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline

print("\n=== STARTING FAST RANDOM FOREST TRAINING ===")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "model_ready_data.csv")
MODEL_OUTPUT = os.path.join(BASE_DIR, "random_forest_model.pkl")
METRICS_OUTPUT = os.path.join(BASE_DIR, "random_forest_model_metrics.json")
RANDOM_STATE = 42


def find_best_threshold(y_true, y_prob, min_recall=0.85):
    best_threshold = 0.50
    best_score = -1.0

    for threshold in np.arange(0.10, 0.91, 0.01):
        y_pred = (y_prob >= threshold).astype(int)
        recall = recall_score(y_true, y_pred, zero_division=0)
        score = fbeta_score(y_true, y_pred, beta=2, zero_division=0)

        if recall >= min_recall and score > best_score:
            best_threshold = float(threshold)
            best_score = score

    if best_score >= 0:
        return best_threshold

    for threshold in np.arange(0.10, 0.91, 0.01):
        y_pred = (y_prob >= threshold).astype(int)
        score = fbeta_score(y_true, y_pred, beta=2, zero_division=0)
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
        "f2": round(fbeta_score(y_test, y_pred, beta=2, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, y_prob), 4),
        "pr_auc": round(average_precision_score(y_test, y_prob), 4),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
        "classification_report": classification_report(y_test, y_pred, output_dict=True, zero_division=0),
    }


def get_feature_importance(model, feature_names):
    rf = model.named_steps["model"]
    importance = rf.feature_importances_
    pairs = sorted(zip(feature_names, importance), key=lambda item: item[1], reverse=True)
    return [{"feature": name, "importance": round(float(score), 5)} for name, score in pairs[:15]]


def train_rf():
    if not os.path.exists(DATA_PATH):
        print(f"[-] Error: Data file not found at {DATA_PATH}")
        return

    print("[*] Loading dataset...")
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["label"])

    X = df.drop("label", axis=1)
    y = df["label"].astype(int)

    print(f"[*] Dataset size: {len(df)} records")
    print(f"[*] Class distribution: {y.value_counts().to_dict()}")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            (
                "model",
                RandomForestClassifier(
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                    oob_score=True,
                ),
            ),
        ]
    )

    # --- THE OPTIMIZED, MUCH FASTER PARAMETERS ---
    param_distributions = {
        "model__n_estimators": [100, 150, 200],  # Less trees
        "model__max_depth": [8, 12, 16],  # Less depth
        "model__min_samples_split": [5, 10],
        "model__min_samples_leaf": [2, 4],
        "model__max_features": ["sqrt", "log2"],  # Removed the slow 'None'
        "model__class_weight": ["balanced"],
    }

    # Reduced folds to 3
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)

    # Reduced iterations to 10
    search = RandomizedSearchCV(
        pipeline,
        param_distributions=param_distributions,
        n_iter=10,
        cv=cv,
        scoring="recall",
        n_jobs=-1,
        random_state=RANDOM_STATE,
        verbose=2,  # You will now see live progress output!
    )

    print("[*] Running FAST randomized hyperparameter search (30 fits total)...")
    search.fit(X_train, y_train)
    best_rf = search.best_estimator_
    print(f"[+] Best parameters: {search.best_params_}")

    train_prob = best_rf.predict_proba(X_train)[:, 1]
    best_threshold = find_best_threshold(y_train, train_prob, min_recall=0.85)
    metrics = evaluate_model(best_rf, X_test, y_test, best_threshold)
    metrics["best_params"] = search.best_params_
    metrics["feature_names"] = list(X.columns)
    metrics["feature_importance"] = get_feature_importance(best_rf, list(X.columns))

    print("\n" + "=" * 60)
    print("--- Random Forest Final Results ---")
    print(f"Threshold : {metrics['threshold']:.2f}")
    print(f"Accuracy  : {metrics['accuracy'] * 100:.2f}%")
    print(f"Precision : {metrics['precision'] * 100:.2f}%")
    print(f"Recall    : {metrics['recall'] * 100:.2f}%")
    print(f"F1 Score  : {metrics['f1'] * 100:.2f}%")
    print(f"ROC-AUC   : {metrics['roc_auc']:.4f}")
    print(f"Confusion : {metrics['confusion_matrix']}")
    print("=" * 60)

    print("[*] Saving production model...")
    joblib.dump(best_rf, MODEL_OUTPUT)

    with open(METRICS_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"[+] Model saved to: {MODEL_OUTPUT}")
    print(f"[+] Metrics saved to: {METRICS_OUTPUT}\n")


if __name__ == "__main__":
    train_rf()