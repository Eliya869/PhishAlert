import pandas as pd
import os

"""
FEATURE VECTOR GENERATOR - This script aggregates all numerical features (X1, X2, X3) into a single matrix.
It removes raw text to prepare the dataset for Machine Learning training.
"""

# File paths configuration
data_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
input_file = os.path.join(data_path, "final_features_v2.csv")
output_file = os.path.join(data_path, "model_ready_data.csv")

if os.path.exists(input_file):
    print("Step 1: Loading dataset with all features...")
    df = pd.read_csv(input_file)

    # Selecting numerical features based on project specifications (X1, X2, X3)
    # X1: URL presence and Authentication
    # X2: Levenshtein structural similarity
    # X3: Suspicious urgency keywords
    base_features = ['has_urls', 'levenshtein_dist', 'auth_verify']
    keyword_features = [col for col in df.columns if col.startswith('word_')]

    # Creating the final column list (Features + Target Label)
    final_columns = base_features + keyword_features + ['label']

    print(f"Step 2: Extracting {len(final_columns) - 1} numerical features...")

    # Filter only the required columns and drop any rows with missing values
    model_ready_df = df[final_columns].dropna()

    # Save the cleaned numerical matrix
    model_ready_df.to_csv(output_file, index=False)

    print(f"\n--- Week 3 Milestone Complete ---")
    print(f"Final training file created: {output_file}")
    print(f"Total processed samples: {len(model_ready_df)}")
    print("\nPreview of the feature vector:")
    print(model_ready_df.head())
else:
    print(f"Error: Could not find {input_file}. Please run auth_check.py first.")