import pandas as pd
import re
import os

"""
feature_extractor(X3) - extracted all features from every email(suspicious words,url's,etc)
"""

def extract_basic_features(df):
    # Ensure there are no null values in the email body
    df['body'] = df['body'].fillna('')

    # List of suspicious keywords (X3-Text_Keywords)
    suspicious_words = ['urgent', 'verify', 'account', 'update', 'password', 'bank', 'pay', 'immediately']

    print("Extracting text features (X3)...")
    for word in suspicious_words:
        # Create a binary column for each keyword: 1 if present, 0 otherwise
        df[f'word_{word}'] = df['body'].str.contains(word, case=False).astype(int)

    # Check for presence of URLs (X1 feature)
    print("Checking for URL presence...")
    df['has_urls'] = df['body'].str.contains(r'http[s]?://', regex=True).astype(int)

    return df

# Define paths for the data folder and files
data_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
input_file = os.path.join(data_path, "phishing_data.csv")
output_file = os.path.join(data_path, "processed_data.csv")

if os.path.exists(input_file):
    print(f"Loading data from: {input_file}")
    df = pd.read_csv(input_file)

    # Execute feature extraction process
    df_processed = extract_basic_features(df)

    # Save to a new file for model training (Logistic Regression & Random Forest)
    df_processed.to_csv(output_file, index=False)
    print(f"\nSuccess! Processed file with features created: {output_file}")
    print(f"New columns added: {[col for col in df_processed.columns if 'word_' in col or col == 'has_urls']}")
else:
    print(f"Error: Input file not found at {input_file}")