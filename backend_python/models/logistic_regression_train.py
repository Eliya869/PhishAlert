import pandas as pd
import os
import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, recall_score, classification_report, confusion_matrix

"""
PHISHALERT - MODEL 1 TRAINING (Logistic Regression)
Optimized for high Recall using customized decision thresholding.
Implements Gradient Descent optimization internally via 'lbfgs' solver.
"""

# Dynamic path configuration
base_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(base_dir, "..", "data")
input_file = os.path.join(data_path, "model_ready_data.csv")
model_output = os.path.join(base_dir, "logistic_model.pkl")


def train_logistic_model():
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Ensure preprocessing is complete.")
        return

    # 1. Load the processed feature vectors
    print("Step 1: Loading feature vectors...")
    df = pd.read_csv(input_file)

    X = df.drop('label', axis=1)
    y = df['label']

    # 2. Split into Training (80%) and Testing (20%) sets (FIXED KEYWORD HERE)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 3. Feature Scaling (CRITICAL for Gradient Descent Convergence)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("Step 2: Training Logistic Regression Engine...")

    # 4. Initialize and train the model
    # Uses 'class_weight=balanced' to mathematically punish False Negatives during Gradient Descent
    model = LogisticRegression(max_iter=2000, class_weight='balanced', random_state=42, solver='lbfgs')
    model.fit(X_train_scaled, y_train)

    # 5. Advanced Evaluation via Customized Threshold (Optimizing Recall)
    # Extract raw probabilities instead of hard binary predictions
    y_probabilities = model.predict_proba(X_test_scaled)[:, 1]

    # Lower threshold from 0.5 to 0.35 to catch more sophisticated phishing payloads
    y_pred_adjusted = (y_probabilities >= 0.35).astype(int)

    # 6. Performance Analytics Generation
    acc = accuracy_score(y_test, y_pred_adjusted)
    recall = recall_score(y_test, y_pred_adjusted)

    print(f"\n--- Optimized Logistic Regression Metrics ---")
    print(f"Accuracy: {acc * 100:.2f}% (Overall accuracy rate)")
    print(f"Recall:   {recall * 100:.2f}% (Catch sensitivity for explicit threats)")

    print("\n--- Confusion Matrix (Visual Proof for Examiners) ---")
    print(confusion_matrix(y_test, y_pred_adjusted))

    print("\nDetailed Classification Report:")
    print(classification_report(y_test, y_pred_adjusted))

    # 7. Serializing and saving both the model and the mathematical scaling parameters
    joblib.dump({'model': model, 'scaler': scaler, 'threshold': 0.35}, model_output)
    print(f"\nSuccess! Logistic brain and scaler saved at: {model_output}")


if __name__ == "__main__":
    train_logistic_model()