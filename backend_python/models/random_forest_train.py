import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, classification_report,
                             confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

print("\n=== STARTING TEXT-STACKED RANDOM FOREST TRAINING ===")

# --- Paths & Global Configurations ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
SOURCE_DATA_PATH = os.path.join(DATA_DIR, "final_features_v2.csv")
FALLBACK_DATA_PATH = os.path.join(DATA_DIR, "model_ready_data.csv")
MODEL_OUTPUT = os.path.join(BASE_DIR, "random_forest_model.pkl")
METRICS_OUTPUT = os.path.join(BASE_DIR, "random_forest_model_metrics.json")
RANDOM_STATE = 42


def split_data(X, y):
    """Splits dataset into 3 phases: Training, Validation (for Stacking), and Testing."""
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.4, random_state=RANDOM_STATE, stratify=y)
    X_valid, X_test, y_valid, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=RANDOM_STATE,
                                                        stratify=y_temp)
    return X_train, X_valid, X_test, y_train, y_valid, y_test


def find_best_threshold(y_true, y_prob):
    """Identifies the peak classification threshold."""
    best_threshold = 0.50
    best_accuracy = -1.0
    for threshold in np.arange(0.20, 0.85, 0.01):
        accuracy = accuracy_score(y_true, (y_prob >= threshold).astype(int))
        if accuracy > best_accuracy:
            best_threshold = float(threshold)
            best_accuracy = accuracy
    return best_threshold


def evaluate_model(model, X, y, threshold):
    """Generates a complete matrix of performance telemetry."""
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
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}
    }


def build_training_frame():
    """Builds the foundational NLP + Numeric matrix for the stacking architecture."""
    if os.path.exists(SOURCE_DATA_PATH):
        df = pd.read_csv(SOURCE_DATA_PATH, low_memory=False).dropna(subset=["label"])
        text_combined = df.get("text_combined", pd.Series("", index=df.index)).fillna("").astype(str)
        body = df.get("body", pd.Series("", index=df.index)).fillna("").astype(str)
        main_text = text_combined.mask(text_combined.str.strip().eq(""), body)

        df["text_for_model"] = (
                df.get("sender", pd.Series("", index=df.index)).fillna("").astype(str) + " " +
                df.get("subject", pd.Series("", index=df.index)).fillna("").astype(str) + " " +
                df.get("urls", pd.Series("", index=df.index)).fillna("").astype(str) + " " + main_text
        )

        numeric_features = [col for col in df.columns if col.startswith("word_") or col in {
            "keyword_count", "has_urls", "levenshtein_dist", "auth_verify"}]
        return df[["text_for_model"] + numeric_features + ["label"]], numeric_features
    raise FileNotFoundError("[-] Missing training data.")


def build_rf_frame(frame, numeric_features, text_model):
    """Enriches the standard numeric vector with the predictive score from the underlying NLP model."""
    X_numeric = frame[numeric_features].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(
        0)
    X_numeric["text_phish_score"] = text_model.predict_proba(frame["text_for_model"])[:, 1]
    return X_numeric


def train_rf():
    try:
        df, numeric_features = build_training_frame()
    except Exception as exc:
        print(exc);
        return

    y = df["label"].astype(int)
    X = df.drop("label", axis=1)

    X_train, X_valid, X_test, y_train, y_valid, y_test = split_data(X, y)

    # Base-Level NLP Model Configuration (Level-0 Stacking)
    text_model = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=200, ngram_range=(1, 1), min_df=10, max_df=0.75, sublinear_tf=True)),
        ("model", LogisticRegression(max_iter=2000, C=0.01, solver="liblinear", random_state=RANDOM_STATE))
    ])

    print("[*] Training Base-Level NLP signal model...")
    text_model.fit(X_train["text_for_model"], y_train)

    print("[*] Building Stacked Random Forest Meta-Matrix...")
    rf_features = numeric_features + ["text_phish_score"]
    X_train_rf = build_rf_frame(X_train, numeric_features, text_model)
    X_valid_rf = build_rf_frame(X_valid, numeric_features, text_model)
    X_test_rf = build_rf_frame(X_test, numeric_features, text_model)

    # Meta-Level Classification Model (Level-1 Stacking)
    rf_model = RandomForestClassifier(n_estimators=250, max_depth=10, min_samples_leaf=8, max_features="sqrt",
                                      n_jobs=-1, random_state=RANDOM_STATE)

    print("[*] Training Meta Random Forest Engine...")
    rf_model.fit(X_train_rf, y_train)

    valid_prob = rf_model.predict_proba(X_valid_rf)[:, 1]
    threshold = find_best_threshold(y_valid, valid_prob)
    metrics = evaluate_model(rf_model, X_test_rf, y_test, threshold)
    metrics["feature_names"] = rf_features
    metrics["numeric_features"] = numeric_features

    print("\n" + "=" * 60)
    print("--- Random Forest Final Results ---")
    print(f"Accuracy  : {metrics['accuracy'] * 100:.2f}%")
    print(f"Confusion : {metrics['confusion_matrix']}")
    print("=" * 60)

    artifact = {"model": rf_model, "text_model": text_model, "threshold": threshold,
                "feature_names": rf_features, "numeric_features": numeric_features, "metrics": metrics}

    joblib.dump(artifact, MODEL_OUTPUT)
    with open(METRICS_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    train_rf()