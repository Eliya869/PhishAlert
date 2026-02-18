import pandas as pd
import os
import re

"""
AUTHENTICATION CHECKER (X1)
This script scans email headers/text for SPF and DKIM authentication signatures.
It assigns a binary value (1 if verified, 0 otherwise) to help the model identify spoofed senders.
"""
def verify_authentication_headers(text):
    text = str(text).lower()

    # Identify typical patterns for successful SPF/DKIM verification
    spf_pass = 1 if re.search(r'spf=pass|received-spf: pass', text) else 0
    dkim_pass = 1 if re.search(r'dkim=pass|dkim-signature', text) else 0

    # Return 1 if at least one authentication method passed
    return 1 if (spf_pass or dkim_pass) else 0


# Configuration of file paths
data_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
input_file = os.path.join(data_path, "final_features.csv")
output_file = os.path.join(data_path, "final_features_v2.csv")

if os.path.exists(input_file):
    print("Loading dataset for Authentication Check (SPF/DKIM)...")
    df = pd.read_csv(input_file)

    # Process headers found in 'text_combined' column
    print("Analyzing email headers for security signatures...")
    df['auth_verify'] = df['text_combined'].apply(verify_authentication_headers)

    df.to_csv(output_file, index=False)
    print(f"Success! X1 Authentication feature added: {output_file}")
else:
    print(f"Error: {input_file} not found.")