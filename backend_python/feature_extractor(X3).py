import pandas as pd
import os

"""
PhishAlert - Dynamic Textual Feature Extractor (X3)
----------------------------------------------------
Performs NLP keyword density checks and URL structure identification.
Fully decoupled from hardcoded keywords.
"""

# --- Configuration & Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
KEYWORDS_FILE = os.path.join(DATA_DIR, "suspicious_keywords.txt")


def load_suspicious_keywords():
    """Imports signature terms dynamically from an external configuration file."""
    if not os.path.exists(KEYWORDS_FILE):
        raise FileNotFoundError(f"[-] Deployment Error: Keyword ledger not found at {KEYWORDS_FILE}")

    with open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
        return [line.strip().lower() for line in f if line.strip()]


def extract_basic_features(df):
    """Maps unstructured text to binary feature vectors based on keyword presence."""
    df['body'] = df['body'].fillna('')
    suspicious_words = load_suspicious_keywords()

    print(f"[*] Extracting Features: Processing {len(suspicious_words)} dynamic signatures...")

    # Construct individual binary columns per target keyword
    for word in suspicious_words:
        df[f'word_{word}'] = df['body'].str.contains(word, case=False, regex=False).astype(int)

    # Aggregate metric: Overall keyword density
    keyword_cols = [f'word_{w}' for w in suspicious_words]
    df['keyword_count'] = df[keyword_cols].sum(axis=1)

    # URL Identification Matrix
    df['has_urls'] = df['body'].str.contains(r'http[s]?://', regex=True).astype(int)

    return df


if __name__ == "__main__":
    print("\n=== STARTING FEATURE ENGINEERING PIPELINE (X3) ===")
    raw_data_path = os.path.join(DATA_DIR, "phishing_data.csv")
    output_data_path = os.path.join(DATA_DIR, "model_ready_data.csv")

    if os.path.exists(raw_data_path):
        print(f"[*] Input Data Source Identified: {raw_data_path}")
        raw_df = pd.read_csv(raw_data_path)
        processed_df = extract_basic_features(raw_df)
        processed_df.to_csv(output_data_path, index=False)
        print(f"[+] Success! Compiled vectors persisted to storage.")
    else:
        print(f"[-] Evaluation Error: Could not find dataset at '{raw_data_path}'")