import pandas as pd
import os
import re
from difflib import SequenceMatcher

"""
levenshtein_processor(X2) - measures domain similarity against known legitimate domains.
FIX: When sender is missing (int this case: 115K+ rows), extracts domain from text_combined instead.
     This prevents 73% of rows returning 1.0 (uninformative default).
"""

#File paths
data_path   = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
input_file  = os.path.join(data_path, "processed_data.csv")
output_file = os.path.join(data_path, "final_features.csv")

# Known legitimate domains for comparison (X2 feature)
top_legal_domains = ['paypal.com', 'google.com', 'microsoft.com',
                     'bankofamerica.com', 'gov.il', 'amazon.com',
                     'apple.com', 'facebook.com', 'linkedin.com']


#Helper functions
def get_levenshtein_distance(s1, s2):
    """Returns distance score: 0.0 = identical, 1.0 = completely different."""
    m = SequenceMatcher(None, s1, s2)
    return 1 - m.ratio()


def extract_domain_from_sender(sender):
    """Extracts domain from standard email: 'Name <user@domain.com>' or 'user@domain.com'"""
    sender = str(sender)
    match = re.search(r'@([\w.\-]+)', sender)
    return match.group(1).strip().lower() if match else ""


def extract_domain_from_text(text):
    """
    Fallback: scans text_combined for the first email address or URL domain.
    Used when sender column is empty.
    """
    text = str(text)

    # Try to find an email address in the text first
    email_match = re.search(r'@([\w.\-]+)', text)
    if email_match:
        return email_match.group(1).strip().lower()

    # Try to find a URL domain (http://domain.com or https://domain)
    url_match = re.search(r'https?://([\w.\-]+)', text)
    if url_match:
        return url_match.group(1).strip().lower()

    return ""


def min_levenshtein(domain):
    """Returns the minimum distance to any known legitimate domain."""
    if not domain:
        return 0.5  # Neutral value — no domain found, not safe not dangerous
    return min([get_levenshtein_distance(domain, legal) for legal in top_legal_domains])


# ── Main processing ────────────────────────────────────────────────────────────
if not os.path.exists(input_file):
    print(f"Error: Input file {input_file} not found.")
else:
    print("--- Levenshtein Processor (X2) - Fixed Version ---")
    print("\nStep 1: Loading processed_data.csv...")
    df = pd.read_csv(input_file, low_memory=False)
    print(f"Total rows loaded: {len(df)}")

    # ── Step 2: Extract domain (sender first, text_combined as fallback) ───────
    print("\nStep 2: Extracting domains...")

    sender_col       = 'sender'       if 'sender'       in df.columns else None
    text_combined_col = 'text_combined' if 'text_combined' in df.columns else None

    domains = []
    source_counts = {'sender': 0, 'text_combined': 0, 'none': 0}

    for _, row in df.iterrows():
        domain = ""

        # Try sender first
        if sender_col and pd.notna(row[sender_col]) and str(row[sender_col]).strip():
            domain = extract_domain_from_sender(row[sender_col])

        # Fallback to text_combined
        if not domain and text_combined_col and pd.notna(row[text_combined_col]):
            domain = extract_domain_from_text(row[text_combined_col])
            if domain:
                source_counts['text_combined'] += 1
            else:
                source_counts['none'] += 1
        elif domain:
            source_counts['sender'] += 1
        else:
            source_counts['none'] += 1

        domains.append(domain)

    df['extracted_domain'] = domains

    print(f"  Domains from sender       : {source_counts['sender']:,}")
    print(f"  Domains from text_combined: {source_counts['text_combined']:,}")
    print(f"  No domain found           : {source_counts['none']:,}")

    # ── Step 3: Calculate Levenshtein distance ─────────────────────────────────
    print("\nStep 3: Calculating Levenshtein Distance (X2)...")
    df['levenshtein_dist'] = df['extracted_domain'].apply(min_levenshtein)

    # ── Step 4: Show distribution (should be much more varied now) ────────────
    print("\nLevenshtein distance distribution (fixed):")
    print(df['levenshtein_dist'].describe().round(4).to_string())
    print("\nTop value counts:")
    print(df['levenshtein_dist'].value_counts().head(5).to_string())

    # ── Step 5: Drop helper column and save ───────────────────────────────────
    df.drop(columns=['extracted_domain'], inplace=True)
    df.to_csv(output_file, index=False)

    print(f"\n--- Process Complete ---")
    print(f"Fixed features saved to: {output_file}")
    print(f"Next step: run auth_check(X1).py → then vector_generator.py")