import pandas as pd
import os

# Define the path to the data folder
data_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
output_file = os.path.join(data_path, "phishing_data.csv")

# List of dataset files to be merged
files_to_combine = [
    'CEAS_08.csv', 'Enron.csv', 'Ling.csv',
    'Nazario.csv', 'Nigerian_Fraud.csv',
    'phishing_email.csv', 'SpamAssassin.csv'
]

all_dfs = []

print("--- Starting Data Merging ---")

for file in files_to_combine:
    full_path = os.path.join(data_path, file)
    if os.path.exists(full_path):
        # Load the file - assuming it contains text and label columns
        df = pd.read_csv(full_path)
        all_dfs.append(df)
        print(f"Loaded successfully: {file} | Rows: {len(df)}")

# Concatenate all DataFrames into one
final_df = pd.concat(all_dfs, ignore_index=True)

# Save to a single unified file for model training (Logistic Regression & Random Forest)
final_df.to_csv(output_file, index=False)

print(f"\nDone! Unified file created: {output_file}")
print(f"Total rows in unified dataset: {len(final_df)}")