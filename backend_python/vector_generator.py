import pandas as pd
import os

# Configuration
data_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
input_file = os.path.join(data_path, "final_features_v2.csv")
output_file = os.path.join(data_path, "model_ready_data.csv")

if os.path.exists(input_file):
    df = pd.read_csv(input_file)

    # Identify basic features and all keyword columns
    base_features = ['has_urls', 'levenshtein_dist', 'auth_verify', 'keyword_count']
    keyword_features = [col for col in df.columns if col.startswith('word_')]

    # Combine everything into the final feature list
    final_columns = base_features + keyword_features + ['label']

    # Filter and save to the final training file
    model_ready_df = df[final_columns].dropna()
    model_ready_df.to_csv(output_file, index=False)

    print(f"Success! model_ready_data.csv created with {len(keyword_features)} keyword features.")
else:
    print(f"Error: {input_file} not found.")