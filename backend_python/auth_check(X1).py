import pandas as pd
import os
import re

"""
auth_check(X1) - Implemented Sender authentication via SPF & DKIM.
Returns 1 for verified senders, 0 for potential spoofing.
This script builds upon the improved Levenshtein data (X2) from final_features.csv.
"""


def verify_authentication_headers(text):
    # Handle missing values (NaN) to prevent code from crashing
    if pd.isna(text):
        return 0

    text = str(text).lower()

    # Identify typical patterns for successful SPF/DKIM verification
    # These strings indicate that the sending server is authorized
    spf_pass = 1 if re.search(r'spf=pass|received-spf: pass', text) else 0
    dkim_pass = 1 if re.search(r'dkim=pass|dkim-signature', text) else 0

    # Return 1 if at least one authentication method passed
    return 1 if (spf_pass or dkim_pass) else 0


# Configuration of file paths
data_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
input_file = os.path.join(data_path, "final_features.csv")  # Updated Levenshtein data
output_file = os.path.join(data_path, "final_features_v2.csv")  # Final enriched dataset

if os.path.exists(input_file):
    print("Loading dataset for Authentication Check (SPF/DKIM)...")
    df = pd.read_csv(input_file)

    # Process headers found in 'text_combined' column
    # This ensures X1 is added alongside the improved X2 data
    print("Analyzing email headers for security signatures...")
    if 'text_combined' in df.columns:
        df['auth_verify'] = df['text_combined'].apply(verify_authentication_headers)

        # Save to V2 - This file now contains both X1 (Auth) and improved X2 (Levenshtein)
        df.to_csv(output_file, index=False)
        print(f"Success! X1 Authentication feature added: {output_file}")
    else:
        print("Error: 'text_combined' column not found in dataset.")
else:
    print(f"Error: {input_file} not found. Please run the Levenshtein processor first.")