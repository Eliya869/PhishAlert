import pandas as pd
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, recall_score, classification_report

"""
PHISHALERT - MODEL 1 TRAINING (Logistic Regression)
Week 5 Task: Train the model, scale features, and evaluate Accuracy/Recall.
Fulfills Agile Milestone: Implementation and Testing.
"""

# Dynamic path configuration (Handles running from the 'models' folder)
base_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(base_dir, "..", "data")
input_file = os.path.join(data_path, "model_ready_data.csv")
model_output = os.path.join(base_dir, "logistic_model.pkl")


def train_logistic_model():
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Ensure Week 3 processing is complete.")
        return

    # 1. Load the processed feature vectors
    print("Step 1: Loading feature vectors...")
    df = pd.read_csv(input_file)

    X = df.drop('label', axis=1)
    y = df['label']

    # 2. Split into Training (80%) and Testing (20%) sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 3. Feature Scaling (CRITICAL for Logistic Regression)
    # This normalizes the data to help the model converge better.
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("Step 2: Training Logistic Regression (Balanced Weights)...")

    # 4. Initialize and train the model
    # 'class_weight=balanced' helps if there's an uneven number of phishing vs safe emails.
    model = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
    model.fit(X_train_scaled, y_train)

    # 5. Evaluation (Accuracy and Recall as per Week 5 requirements)
    y_pred = model.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)

    print(f"\n--- Week 5 Training Results ---")
    print(f"Accuracy: {acc:.4f} (Percentage of correct predictions)")
    print(f"Recall:   {recall:.4f} (Ability to catch actual phishing emails)")

    print("\nDetailed Classification Report:")
    print(classification_report(y_test, y_pred))

    # 6. Save the Model AND the Scaler (We need both for the API later)
    # We save them as a dictionary to keep them together.
    joblib.dump({'model': model, 'scaler': scaler}, model_output)
    print(f"\nSuccess! Logistic brain and scaler saved at: {model_output}")


if __name__ == "__main__":
    train_logistic_model()