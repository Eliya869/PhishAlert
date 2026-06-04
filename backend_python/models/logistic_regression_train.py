import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, classification_report,
                             confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

print("\n=== STARTING LOGISTIC REGRESSION MODEL ===")

# --- Paths & Global Configurations ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
SOURCE_DATA_PATH = os.path.join(DATA_DIR, "final_features_v2.csv")
FALLBACK_DATA_PATH = os.path.join(DATA_DIR, "model_ready_data.csv")
MODEL_OUTPUT = os.path.join(BASE_DIR, "logistic_model.pkl")
METRICS_OUTPUT = os.path.join(BASE_DIR, "logistic_model_metrics.json")
RANDOM_STATE = 42


def find_best_threshold(y_true, y_prob):
    """Calculates the optimal discrimination threshold prioritizing overall accuracy."""
    best_threshold = 0.50
    best_score = -1.0
    for threshold in np.arange(0.20, 0.85, 0.01):
        score = accuracy_score(y_true, (y_prob >= threshold).astype(int))
        if score > best_score:
            best_threshold = float(threshold)
            best_score = score
    return best_threshold


def evaluate_model(model, X_test, y_test, threshold):
    """Runs a full suite of classification metrics based on the optimal threshold."""
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
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}
    }


def build_training_frame():
    """Assembles the multimodal dataset combining raw NLP text fields with engineered numeric columns."""
    if os.path.exists(SOURCE_DATA_PATH):
        print(f"Loading source NLP dataset: {SOURCE_DATA_PATH}")
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

    if os.path.exists(FALLBACK_DATA_PATH):
        print(f"Loading numeric fallback dataset: {FALLBACK_DATA_PATH}")
        df = pd.read_csv(FALLBACK_DATA_PATH, low_memory=False).dropna(subset=["label"])
        df["text_for_model"] = ""
        numeric_features = [col for col in df.columns if col != "label"]
        return df[["text_for_model"] + numeric_features + ["label"]], numeric_features

    raise FileNotFoundError("Error: Training data not located in expected paths.")


def train_logistic():
    try:
        df, numeric_features = build_training_frame()
    except Exception as exc:
        print(exc)
        return

    X = df.drop("label", axis=1)
    y = df["label"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y)

    # NLP Pipeline Configuration (Restrained TF-IDF to prevent Data Leakage)
    preprocessor = ColumnTransformer(transformers=[
        ("text", TfidfVectorizer(max_features=200, ngram_range=(1, 1), min_df=10,
                                 max_df=0.75, sublinear_tf=True, strip_accents="unicode"), "text_for_model"),
        ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")),
                              ("scaler", StandardScaler(with_mean=False))]), numeric_features)
    ])

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", LogisticRegression(max_iter=2000, solver="liblinear", C=0.01, random_state=RANDOM_STATE))
    ])

    print("Training Natural Language (NLP) aware logistic model...")
    pipeline.fit(X_train, y_train)

    train_prob = pipeline.predict_proba(X_train)[:, 1]
    best_threshold = find_best_threshold(y_train, train_prob)
    metrics = evaluate_model(pipeline, X_test, y_test, best_threshold)

    metrics["feature_names"] = ["text_for_model"] + numeric_features
    metrics["numeric_features"] = numeric_features

    print("\n" + "=" * 60)
    print("--- Logistic Regression Final Results ---")
    print(f"Accuracy  : {metrics['accuracy'] * 100:.2f}%")
    print(f"Confusion : {metrics['confusion_matrix']}")
    print("=" * 60)

    artifact = {"model": pipeline, "threshold": best_threshold,
                "feature_names": metrics["feature_names"], "numeric_features": numeric_features, "metrics": metrics}

    joblib.dump(artifact, MODEL_OUTPUT)
    with open(METRICS_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    train_logistic()