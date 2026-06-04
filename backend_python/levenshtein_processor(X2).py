import pandas as pd
import os
import re
import json
from difflib import SequenceMatcher

"""
PhishAlert - Homoglyph & Typosquatting Detection
------------------------------------------------
Calculates Levenshtein distances against dynamically loaded trusted brands
to detect visual deception attacks. Uses dynamic JSON for homoglyph mapping.
"""

# --- Configuration & File Paths ---
DATA_PATH = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
INPUT_FILE = os.path.join(DATA_PATH, "processed_data.csv")
OUTPUT_FILE = os.path.join(DATA_PATH, "final_features.csv")
BRANDS_FILE = os.path.join(DATA_PATH, "trusted_brands.txt")
HOMOGLYPHS_FILE = os.path.join(DATA_PATH, "homoglyphs.json")


def load_trusted_brands():
    """Loads target protection brands dynamically from a text file."""
    if not os.path.exists(BRANDS_FILE):
        return []
    with open(BRANDS_FILE, "r", encoding="utf-8") as file:
        return [line.strip().lower() for line in file if line.strip()]


def load_homoglyphs():
    """Loads homoglyph mapping dictionaries dynamically from a JSON file."""
    if not os.path.exists(HOMOGLYPHS_FILE):
        print(f"[-] Warning: {HOMOGLYPHS_FILE} not found. Using empty mapping.")
        return {"multi_chars": {}, "single_chars": {}}
    with open(HOMOGLYPHS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_homoglyphs(text, homoglyphs_data):
    """
    Standardizes look-alike characters to expose spoofing attempts
    using dynamically loaded translation tables.
    """
    text = text.lower()

    # 1. Multi-character replacements (e.g., 'rn' -> 'm')
    multi_map = homoglyphs_data.get("multi_chars", {})
    for key, val in multi_map.items():
        text = text.replace(key, val)

    # 2. Single-character replacements (e.g., '0' -> 'o') using translation table
    single_map = homoglyphs_data.get("single_chars", {})
    if single_map:
        trans_table = str.maketrans(single_map)
        text = text.translate(trans_table)

    return text


def get_brand_part(domain):
    """Isolates the primary SLD (Second-Level Domain) from a domain string."""
    if not domain: return ""
    return domain.split('.')[0].lower()


def calculate_smart_score(extracted_domain, trusted_brands, homoglyphs_data):
    """Evaluates brand impersonation risks based on external logic layers."""
    if not extracted_domain or not trusted_brands:
        return 0.5

    current_brand = get_brand_part(extracted_domain)
    normalized_brand = normalize_homoglyphs(current_brand, homoglyphs_data)

    for target in trusted_brands:
        # Homoglyph Attack Detection
        if normalized_brand == target and current_brand != target:
            return 0.0
        # Legitimate Authentication
        if current_brand == target:
            return 1.0
        # Typosquatting Detection (High similarity but not identical)
        similarity = SequenceMatcher(None, current_brand, target).ratio()
        if 0.85 <= similarity < 1.0:
            return 0.1

    return 0.5


def process_levenshtein():
    """Batch-processes the dataset to calculate deception matrices."""
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    print("Starting Levenshtein Processor...")
    df = pd.read_csv(INPUT_FILE, low_memory=False)

    # Load external dynamic settings
    trusted_brands = load_trusted_brands()
    homoglyphs_data = load_homoglyphs()

    def extract_best_domain(row):
        """Extracts the operational domain from the sender or text bodies."""
        sender = str(row.get('sender', ''))
        match = re.search(r'@([\w.\-]+)', sender)
        if match: return match.group(1).lower()

        text = str(row.get('text_combined', ''))
        url_match = re.search(r'https?://([\w.\-]+)', text)
        return url_match.group(1).lower() if url_match else ""

    print("Calculating structural similarity and homoglyph thresholds...")
    df['extracted_domain'] = df.apply(extract_best_domain, axis=1)

    # Apply calculation using the loaded dynamic configurations
    df['levenshtein_dist'] = df['extracted_domain'].apply(
        lambda d: calculate_smart_score(d, trusted_brands, homoglyphs_data)
    )

    # Cleanup
    df.drop(columns=['extracted_domain'], inplace=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Success! Features finalized and saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    process_levenshtein()