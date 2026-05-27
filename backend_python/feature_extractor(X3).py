import pandas as pd
import re
import os

"""
PHISHALERT - TEXTUAL FEATURE EXTRACTOR (X3)
----------------------------------------------------
This module performs Natural Language Processing (NLP) to convert 
raw email text into numerical features for the ML models.
"""


def extract_basic_features(df):
    # Handling missing values to prevent processing errors during the scan
    df['body'] = df['body'].fillna('')

    # Includes triggers for urgency, financial action, and account security
    suspicious_words = [
        'urgent', 'verify', 'account', 'update', 'password', 'bank', 'pay', 'immediately',
        'click', 'confirm', 'suspend', 'suspended', 'reastricted', 'unusual',
        'limited', 'expire', 'expired', 'login', 'signin', 'credit', 'debit',
        'transfer', 'billing', 'invoice', 'payment', 'alert', 'warning',
        'unauthorized', 'blocked', 'locked'
    ]

    print(f"Executing NLP Scan: Mapping {len(suspicious_words)} critical keywords...")

    # Iterate through the dictionary to find matches in the email body
    for word in suspicious_words:
        # Create a binary column: 1 if the keyword is present, 0 otherwise
        # Optimized with case-insensitive search for higher accuracy
        df[f'word_{word}'] = df['body'].str.contains(word, case=False, regex=False).astype(int)

    # Calculate 'keyword_count' - Represents the density of suspicious words
    # This aggregate feature is a strong signal for the Machine Learning models
    keyword_cols = [f'word_{w}' for w in suspicious_words]
    df['keyword_count'] = df[keyword_cols].sum(axis=1)

    # Structural check: Detecting URLs using Regular Expressions (Regex)
    # Most phishing attempts rely on a malicious link to steal credentials
    print("Analyzing structural indicators: Checking for URL presence...")
    df['has_urls'] = df['body'].str.contains(r'http[s]?://', regex=True).astype(int)

    return df