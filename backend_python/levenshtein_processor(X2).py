import pandas as pd
import os
import re
from difflib import SequenceMatcher

"""
PHISHALERT - ADVANCED LEVENSHTEIN PROCESSOR (X2)
Improvements: Brand isolation, Homoglyph mapping, and Weighted Danger Scoring.
Fulfills Agile Milestone: Precision Engineering for Phishing Detection.
"""

# File paths
data_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
input_file = os.path.join(data_path, "processed_data.csv")
output_file = os.path.join(data_path, "final_features.csv")

# Known legitimate brands (Isolated from TLDs for better matching)
TOP_BRANDS = ['paypal', 'google', 'microsoft', 'amazon', 'apple', 'facebook', 'linkedin', 'netflix', 'bankofamerica']


def normalize_homoglyphs(text):
    """
    Standardizes look-alike characters to catch visual deception.
    e.g., 'paypa1' becomes 'paypal', 'amaz0n' becomes 'amazon'.
    """
    replacements = {
        '0': 'o', '1': 'l', '8': 'b', 'vv': 'w', 'rn': 'm',
        'i': 'l', '!': 'l', '@': 'a', '5': 's', '3': 'e'
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text


def get_brand_part(domain):
    """Extracts the primary brand name from a domain (e.g., 'paypa1' from 'paypa1.com')"""
    if not domain: return ""
    return domain.split('.')[0].lower()


def calculate_smart_score(extracted_domain):
    """
    Calculates a weighted danger score.
    Returns: 1.0 (Identical to brand - Safe),
             0.0 (Typosquatting detected - Danger),
             0.5 (Neutral).
    """
    if not extracted_domain:
        return 0.5

    current_brand = get_brand_part(extracted_domain)
    normalized_brand = normalize_homoglyphs(current_brand)

    max_risk = 0.5  # Default neutral

    for target in TOP_BRANDS:
        # Case A: Homoglyph Attack (e.g., 'amaz0n' becomes 'amazon' after normalization)
        if normalized_brand == target and current_brand != target:
            return 0.0  # Extreme Danger

        # Case B: Exact Match (Safe)
        if current_brand == target:
            return 1.0

        # Case C: Structural Similarity (Typosquatting)
        # We calculate the ratio on the brand parts only
        similarity = SequenceMatcher(None, current_brand, target).ratio()

        # In phishing, a similarity between 0.7 and 0.9 is the "Danger Zone"
        # (e.g., 'paypa1' vs 'paypal')
        if 0.7 < similarity < 1.0:
            return 0.1  # Very Suspicious

    return max_risk


# ── Main processing ────────────────────────────────────────────────────────────

def process_levenshtein():
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    print("--- PhishAlert Smart Levenshtein Processor ---")
    df = pd.read_csv(input_file, low_memory=False)

    # Using the extraction logic from your original script
    def extract_best_domain(row):
        sender = str(row.get('sender', ''))
        sender_domain = re.search(r'@([\w.\-]+)', sender)
        if sender_domain:
            return sender_domain.group(1).lower()

        text = str(row.get('text_combined', ''))
        text_domain = re.search(r'@([\w.\-]+)', text) or re.search(r'https?://([\w.\-]+)', text)
        return text_domain.group(1).lower() if text_domain else ""

    print("Extracting domains and calculating danger scores...")
    df['extracted_domain'] = df.apply(extract_best_domain, axis=1)


    df['levenshtein_dist'] = df['extracted_domain'].apply(calculate_smart_score)

    # Show results
    print("\nSmart Levenshtein Score Distribution:")
    print(df['levenshtein_dist'].value_counts().head(5))

    df.drop(columns=['extracted_domain'], inplace=True)
    df.to_csv(output_file, index=False)
    print(f"\nSuccess! Features saved to: {output_file}")


if __name__ == "__main__":
    process_levenshtein()