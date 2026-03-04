import pandas as pd
import re
import os

"""
feature_extractor(X3) - extracted all features from every email.
FIX: Expanded keyword list from 8 to 28 words based on real phishing patterns.
     Added keyword_count column (total suspicious words per email).
"""

def extract_basic_features(df):
    # Ensure there are no null values in the email body
    df['body'] = df['body'].fillna('')

    #Expanded suspicious keywords (X3-Text_Keywords)
    suspicious_words = [
        # Original keywords
        'urgent', 'verify', 'account', 'update', 'password', 'bank', 'pay', 'immediately',
        # Phishing action words
        'click', 'confirm', 'suspend', 'suspended', 'restricted', 'unusual',
        'limited', 'expire', 'expired', 'login', 'signin',
        # Financial phishing
        'credit', 'debit', 'transfer', 'billing', 'invoice', 'payment',
        # Threat/urgency words
        'alert', 'warning', 'unauthorized', 'blocked', 'locked',
    ]

    print(f"Extracting text features (X3) - {len(suspicious_words)} keywords...")
    for word in suspicious_words:
        # Create a binary column for each keyword: 1 if present, 0 otherwise
        df[f'word_{word}'] = df['body'].str.contains(word, case=False, regex=False).astype(int)

    # Total suspicious keyword count per email (stronger signal than individual words)
    keyword_cols = [f'word_{w}' for w in suspicious_words]
    df['keyword_count'] = df[keyword_cols].sum(axis=1)

    # Check for presence of URLs
    print("Checking for URL presence...")
    df['has_urls'] = df['body'].str.contains(r'http[s]?://', regex=True).astype(int)

    return df


#File paths
data_path   = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
input_file  = os.path.join(data_path, "phishing_data.csv")
output_file = os.path.join(data_path, "processed_data.csv")

if not os.path.exists(input_file):
    print(f"Error: Input file not found at {input_file}")
else:
    print(f"Loading data from: {input_file}")
    df = pd.read_csv(input_file, low_memory=False)

    # Execute feature extraction process
    df_processed = extract_basic_features(df)

    # Save to a new file for model training
    df_processed.to_csv(output_file, index=False)

    new_cols = [col for col in df_processed.columns if 'word_' in col or col in ['has_urls', 'keyword_count']]
    print(f"\nSuccess! Processed file created: {output_file}")
    print(f"New columns added ({len(new_cols)}): {new_cols}")
    print(f"\nKeyword count distribution:")
    print(df_processed['keyword_count'].describe().round(2).to_string())