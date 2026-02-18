import pandas as pd
import os
from difflib import SequenceMatcher

"""
levenshtein_processor(X2) - used difflib to create levenshtein algorithm(measure the difference between two domains)
"""

# Calculate Levenshtein-based distance using SequenceMatcher ratio
def get_levenshtein_distance(s1, s2):
    m = SequenceMatcher(None, s1, s2)
    # Distance is 1 minus the similarity ratio
    return 1 - m.ratio()

# Define file paths for input and output
data_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
input_file = os.path.join(data_path, "processed_data.csv")
output_file = os.path.join(data_path, "final_features.csv")

# Known legitimate domains for comparison (X2 feature)
top_legal_domains = ['paypal.com', 'google.com', 'microsoft.com', 'bankofamerica.com', 'gov.il']

if os.path.exists(input_file):
    print("Loading processed data for Levenshtein calculation...")
    df = pd.read_csv(input_file)


    # Helper function to isolate the domain from the sender's email address
    def extract_domain(sender):
        parts = str(sender).split('@')
        return parts[-1].strip() if len(parts) > 1 else ""


    # Calculate the minimum distance to any known legitimate domain (X2)
    def min_levenshtein(sender_email):
        domain = extract_domain(sender_email)
        if not domain:
            return 1.0 # Maximum distance if no domain found
        # Find the smallest distance among all legal domains
        return min([get_levenshtein_distance(domain, legal) for legal in top_legal_domains])

    print("Calculating Levenshtein Distance (X2) for all rows...")
    df['levenshtein_dist'] = df['sender'].apply(min_levenshtein)

    # Save the final feature set for model training (Logistic Regression & Random Forest)
    df.to_csv(output_file, index=False)
    print(f"Process complete! Final features saved to: {output_file}")
else:
    print(f"Error: Input file {input_file} not found.")