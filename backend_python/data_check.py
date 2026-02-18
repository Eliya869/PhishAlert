import pandas as pd

"""
data_check - made sure that the combined file of emails actually worked
"""

# Path to the unified dataset created in the previous step
file_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data\phishing_data.csv"

# Load the dataset into a Pandas DataFrame
df = pd.read_csv(file_path)

# Initial data inspection
print(f"Total rows in dataset: {len(df)}")
print("\n--- First five rows of the unified dataset ---")
print(df.head())

# Inspection of column names to identify 'body', 'label', and 'urls'
print("\n--- Detected column names ---")
print(df.columns.tolist())