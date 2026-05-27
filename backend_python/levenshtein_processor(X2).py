import pandas as pd
import os
import re
from difflib import SequenceMatcher

"""
Refined logic for visual deception detection and structural similarity.
Full implementation with expanded brands and performance optimizations.
"""

# --- Configuration & File Paths ---
# Ensure these paths match your local project structure
DATA_PATH = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
INPUT_FILE = os.path.join(DATA_PATH, "processed_data.csv")
OUTPUT_FILE = os.path.join(DATA_PATH, "final_features.csv")

#list of legitimate brands (Targeted by phishers)
TOP_BRANDS = [
    'paypal', 'google', 'microsoft', 'amazon', 'apple', 'facebook', 'linkedin',
    'netflix', 'bankofamerica', 'ebay', 'instagram', 'whatsapp', 'gmail',
    'twitter', 'yahoo', 'dropbox', 'steam', 'discord', 'chase',
    'icloud', 'adobe', 'spotify', 'roblox', 'binance', 'coinbase', 'slack'
]


def normalize_homoglyphs(text):
    """
    Standardizes look-alike characters using an optimized translation table.
    Converts 'paypa1' -> 'paypal', 'amaz0n' -> 'amazon', etc.
    """
    # Create a translation table for single-character replacements
    homoglyph_map = str.maketrans({
        '0': 'o', '1': 'l', '8': 'b', 'i': 'l', '!': 'l',
        '@': 'a', '5': 's', '3': 'e'
    })

    # Handle common multi-character visual tricks first
    text = text.lower().replace('vv', 'w').replace('rn', 'm')

    # Apply the bulk translation for speed
    return text.translate(homoglyph_map)


def get_brand_part(domain):
    """Extracts the primary brand segment from a domain string (e.g., 'paypa1' from 'paypa1.com')"""
    if not domain: return ""
    return domain.split('.')[0].lower()


def calculate_smart_score(extracted_domain):
    """
    Logic:
    - 1.0: Safe (Identical to a protected brand)
    - 0.0: High Risk (Homoglyph spoofing detected)
    - 0.1: Suspicious (High structural similarity / Typosquatting)
    - 0.5: Neutral (No match in the brand protection list)
    """
    if not extracted_domain:
        return 0.5

    current_brand = get_brand_part(extracted_domain)
    normalized_brand = normalize_homoglyphs(current_brand)

    for target in TOP_BRANDS:
        # Check for visual deception (Homoglyph Attack)
        # If it matches after normalization but was different before, it's a spoof.
        if normalized_brand == target and current_brand != target:
            return 0.0

            # Legitimate brand verification
        if current_brand == target:
            return 1.0

        # Structural Similarity: SequenceMatcher provides the Levenshtein-based ratio
        similarity = SequenceMatcher(None, current_brand, target).ratio()

        # Threshold for Typosquatting: Similarity > 75% is usually a phishing attempt
        if 0.85 <= similarity < 1.0:
            return 0.1

    return 0.5

def process_levenshtein():
    """Main function to batch-process the phishing dataset."""
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Please check your data directory.")
        return

    print("--- Starting Levenshtein Processor ---")
    df = pd.read_csv(INPUT_FILE, low_memory=False)

    def extract_best_domain(row):
        """Helper to extract domain from sender email or body text."""
        sender = str(row.get('sender', ''))
        match = re.search(r'@([\w.\-]+)', sender)
        if match: return match.group(1).lower()

        # Fallback to URLs in the text if sender is missing
        text = str(row.get('text_combined', ''))
        url_match = re.search(r'https?://([\w.\-]+)', text)
        return url_match.group(1).lower() if url_match else ""

    print("Processing domains and calculating danger levels...")
    df['extracted_domain'] = df.apply(extract_best_domain, axis=1)
    df['levenshtein_dist'] = df['extracted_domain'].apply(calculate_smart_score)

    # Cleanup and Export
    df.drop(columns=['extracted_domain'], inplace=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Success! Features finalized and saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    process_levenshtein()