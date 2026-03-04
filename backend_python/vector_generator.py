import pandas as pd
import os

"""
vector_generator - This script aggregates all numerical features (X1, X2, X3) into a single matrix.
It uses the improved final_features_v2 (with fixed Levenshtein and Auth data).
It removes raw text to prepare the dataset for Machine Learning training.
"""

# Configuration of file paths
data_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
input_file = os.path.join(data_path, "final_features_v2.csv")  # Updated data source
output_file = os.path.join(data_path, "model_ready_data.csv")  # Final ML input

if os.path.exists(input_file):
    print("Step 1: Loading enriched dataset (X1 + Improved X2)...")
    df = pd.read_csv(input_file)

    # Selecting numerical features:
    # X1: auth_verify (Authentication)
    # X2: levenshtein_dist (Improved domain similarity)
    # X3: word_xxx (Suspicious keywords)
    base_features = ['has_urls', 'levenshtein_dist', 'auth_verify']
    keyword_features = [col for col in df.columns if col.startswith('word_')]

    # Adding the target label
    final_columns = base_features + keyword_features + ['label']

    print(f"Step 2: Extracting {len(final_columns) - 1} numerical features for {len(df)} rows...")

    # Filter only numeric columns and drop incomplete rows
    model_ready_df = df[final_columns].dropna()

    # Save the cleaned numerical matrix
    model_ready_df.to_csv(output_file, index=False)

    print(f"\n--- Feature Engineering Complete ---")
    print(f"Final training file created: {output_file}")
    print(f"Ready for Model Training (Week 5).")
else:
    print(f"Error: {input_file} not found. Please run auth_check.py first.")