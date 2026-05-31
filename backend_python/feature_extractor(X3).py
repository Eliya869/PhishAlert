import pandas as pd
import re
import os

"""
PHISHALERT - DYNAMIC TEXTUAL FEATURE EXTRACTOR (X3)
----------------------------------------------------
Performs Natural Language Processing (NLP) and Feature Engineering.
Converts raw email text into a sanitized mathematical matrix for ML models.
Fully decoupled from hardcoded constants to implement Black-Box compliance.
"""

# Dynamic directory routing based on your exact folder structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
KEYWORDS_FILE = os.path.join(DATA_DIR, "suspicious_keywords.txt")


def load_suspicious_keywords():
    """
    Dynamically imports target signature terms from external text file.
    Ensures absolute alignment between Training and Live Inference vectors.
    """
    if not os.path.exists(KEYWORDS_FILE):
        raise FileNotFoundError(
            f"Deployment Error: Centralized key ledger not found at: {KEYWORDS_FILE}"
        )

    with open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
        return [line.strip().lower() for line in f if line.strip()]


def extract_basic_features(df):
    """
    Transforms raw unstructured text series into vectorized input dimensions.
    """
    # Sanitize null values to prevent dynamic loop breaks
    df['body'] = df['body'].fillna('')

    # Load keyword vectors dynamically (Runtime Signature Mapping)
    suspicious_words = load_suspicious_keywords()
    print(f"[*] Extracting Features: Processing {len(suspicious_words)} dynamic signatures...")

    # Vectorization Matrix Boundary: Map individual word flags
    for word in suspicious_words:
        # Case-insensitive substring matching converted to binary constraints
        df[f'word_{word}'] = df['body'].str.contains(word, case=False, regex=False).astype(int)

    # Engineering Feature: Aggregate density score (Total keyword frequency)
    keyword_cols = [f'word_{w}' for w in suspicious_words]
    df['keyword_count'] = df[keyword_cols].sum(axis=1)

    # Engineering Feature: Regular Expression URL structural analysis
    df['has_urls'] = df['body'].str.contains(r'http[s]?://', regex=True).astype(int)

    return df


if __name__ == "__main__":
    """
    Automated Batch Engineering Pipeline Entrypoint.
    Loads, processes, and persists data schema records.
    """
    print("\n=== STARTING FEATURE ENGINEERING PIPELINE (X3) ===")

    # Matched exactly to your 'phishing_data.csv' file found in the data folder
    raw_data_path = os.path.join(DATA_DIR, "phishing_data.csv")
    output_data_path = os.path.join(DATA_DIR, "model_ready_data.csv")

    if os.path.exists(raw_data_path):
        print(f"[*] Input Data Source Identified: {raw_data_path}")

        # 1. Read static raw corpus records
        raw_df = pd.read_csv(raw_data_path)

        # 2. Map mathematical vectors dynamically
        processed_df = extract_basic_features(raw_df)

        # 3. Export structural records to secondary model storage layer
        processed_df.to_csv(output_data_path, index=False)
        print(f"[+] Success! Compiled vectors persisted to storage: {output_data_path}")
        print("=== PIPELINE COMPLETION CLEAN: READY FOR MODEL TRAINING ===\n")
    else:
        print(f"[-] Evaluation Error: Could not find dataset at '{raw_data_path}'")
        print("[-] Please ensure the script file runs from the 'backend_python' root directory.\n")