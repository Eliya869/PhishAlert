import pandas as pd
import os
import re
from difflib import SequenceMatcher

"""
PhishAlert - Homoglyph & Typosquatting Detection
------------------------------------------------
Calculates Levenshtein distances against dynamically loaded trusted brands
to detect visual deception attacks (e.g., amaz0n vs amazon).
"""

# --- Configuration & File Paths ---
DATA_PATH = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
INPUT_FILE = os.path.join(DATA_PATH, "processed_data.csv")
OUTPUT_FILE = os.path.join(DATA_PATH, "final_features.csv")
BRANDS_FILE = os.path.join(DATA_PATH, "trusted_brands.txt")

def load_trusted_brands():
    """Loads target protection brands dynamically from a text file."""
    if not os.path.exists(BRANDS_FILE):
        return []
    with open(BRANDS_FILE, "r", encoding="utf-8") as file:
        return [line.strip().lower() for line in file if line.strip()]

def normalize_homoglyphs(text):
    """Standardizes look-alike characters to expose spoofing attempts."""
    homoglyph_map = str.maketrans({
        '0': 'o', '1': 'l', '8': 'b', 'i': 'l', '!': 'l',
        '@': 'a', '5': 's', '3': 'e'
    })
    text = text.lower().replace('vv', 'w').replace('rn', 'm')
    return text.translate(homoglyph_map)

def get_brand_part(domain):
    """Isolates the primary SLD (Second-Level Domain) from a domain string."""
    if not domain: return ""
    return domain.split('.')[0].lower()

def calculate_smart_score(extracted_domain, trusted_brands):
    """
    Evaluates brand impersonation risks:
    1.0: Safe / Authentic
    0.0: High Risk (Homoglyph spoof)
    0.1: Suspicious (Typosquatting)
    0.5: Neutral
    """
    if not extracted_domain or not trusted_brands:
        return 0.5

    current_brand = get_brand_part(extracted_domain)
    normalized_brand = normalize_homoglyphs(current_brand)

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
        print(f"[-] Error: {INPUT_FILE} not found.")
        return

    print("[*] Starting Levenshtein Processor...")
    df = pd.read_csv(INPUT_FILE, low_memory=False)
    trusted_brands = load_trusted_brands()

    def extract_best_domain(row):
        """Extracts the operational domain from the sender or text bodies."""
        sender = str(row.get('sender', ''))
        match = re.search(r'@([\w.\-]+)', sender)
        if match: return match.group(1).lower()

        text = str(row.get('text_combined', ''))
        url_match = re.search(r'https?://([\w.\-]+)', text)
        return url_match.group(1).lower() if url_match else ""

    print("[*] Calculating structural similarity and homoglyph thresholds...")
    df['extracted_domain'] = df.apply(extract_best_domain, axis=1)
    df['levenshtein_dist'] = df['extracted_domain'].apply(lambda d: calculate_smart_score(d, trusted_brands))

    # Cleanup
    df.drop(columns=['extracted_domain'], inplace=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"[+] Success! Features finalized and saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    process_levenshtein()