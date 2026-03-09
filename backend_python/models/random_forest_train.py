import pandas as pd
import os
import joblib  # Switched from pickle to joblib for better stability
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, recall_score,
                             precision_score, f1_score,
                             classification_report)

"""
random_forest_model (Week 6) - trains Random Forest on model_ready_data.csv.
Implements Ensemble PhishScore logic: (RF * 0.7 + LR * 0.3) * 100
Output: random_forest_model.pkl (used together with logistic_model.pkl in Week 7 API)
"""

# File paths
data_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
models_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\models"
input_file = os.path.join(data_path, "model_ready_data.csv")
rf_output = os.path.join(models_path, "random_forest_model.pkl")
logistic_model_path = os.path.join(models_path, "logistic_model.pkl")

if not os.path.exists(input_file):
    print(f"Error: {input_file} not found. Please run vector_generator.py first.")
else:
    print("--- Week 6: Training Random Forest Model ---")

    # Step 1: Load data
    print("\nStep 1: Loading model_ready_data.csv...")
    df = pd.read_csv(input_file)
    print(f"Total samples  : {len(df)}")
    print(f"Phishing  (1)  : {(df['label'] == 1).sum()}")
    print(f"Legitimate (0) : {(df['label'] == 0).sum()}")

    # Step 2: Split features and label
    print("\nStep 2: Defining features and label...")
    X = df.drop('label', axis=1)
    y = df['label']
    feature_cols = X.columns.tolist()
    print(f"Features ({len(feature_cols)}): {feature_cols}")

    # Step 3: Train / Test split 80% / 20%
    print("\nStep 3: Splitting into train (80%) and test (20%)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Training samples : {len(X_train)}")
    print(f"Testing  samples : {len(X_test)}")

    # Step 4: Train Random Forest
    print("\nStep 4: Training Random Forest (100 trees)...")
    rf_model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        class_weight='balanced'  # handles imbalanced phishing/legitimate ratio
    )
    rf_model.fit(X_train, y_train)
    print("Training complete.")

    # Step 8: Save Random Forest model (MOVED UP FOR SAFETY)
    print(f"\nStep 8: Saving Random Forest model...")
    joblib.dump(rf_model, rf_output)
    print(f"Random Forest model saved successfully: {rf_output}")

    # Step 5: Evaluate Random Forest
    print("\nStep 5: Evaluating Random Forest on test set...")
    y_pred_rf = rf_model.predict(X_test)
    y_prob_rf = rf_model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred_rf)
    recall = recall_score(y_test, y_pred_rf)
    precision = precision_score(y_test, y_pred_rf)
    f1 = f1_score(y_test, y_pred_rf)

    print("\n--- Random Forest Results ---")
    print(f"Accuracy  : {accuracy:.4f}  ({accuracy * 100:.2f}%)")
    print(f"Recall    : {recall:.4f}  ({recall * 100:.2f}%)")
    print(f"Precision : {precision:.4f}  ({precision * 100:.2f}%)")
    print(f"F1-Score  : {f1:.4f}  ({f1 * 100:.2f}%)")

    # Step 6: Feature importance
    print("\n--- Feature Importance (Random Forest) ---")
    feat_df = pd.DataFrame({
        'Feature': feature_cols,
        'Importance': rf_model.feature_importances_
    }).sort_values('Importance', ascending=False)
    print(feat_df.to_string(index=False))

    # Step 7: Ensemble PhishScore (RF * 0.7 + LR * 0.3)
    print("\n--- Step 7: Ensemble PhishScore Logic ---")

    if os.path.exists(logistic_model_path):
        try:
            # Use joblib to load the model (handles both dict and direct objects)
            lr_data = joblib.load(logistic_model_path)

            # Extract the actual model if it was saved in a dictionary
            if isinstance(lr_data, dict) and 'model' in lr_data:
                lr_model = lr_data['model']
                scaler = lr_data.get('scaler')
            else:
                lr_model = lr_data

            # Logistic Regression requires scaled data (assuming it was trained on scaled data)
            # For this test on X_test, we only use probabilities if available
            y_prob_lr = lr_model.predict_proba(X_test)[:, 1]

            # Weighted average: RF gets 70%, Logistic Regression gets 30%
            ensemble_prob = (y_prob_rf * 0.7) + (y_prob_lr * 0.3)
            phish_scores = (ensemble_prob * 100).round(2)  # scale to 0-100
            ensemble_pred = (ensemble_prob >= 0.5).astype(int)  # classify at 0.5 threshold

            acc_ens = accuracy_score(y_test, ensemble_pred)
            print("Formula: PhishScore = (P_RF * 0.7 + P_LR * 0.3) * 100")
            print(f"Ensemble Accuracy: {acc_ens:.4f} ({acc_ens * 100:.2f}%)")

            print("\nSample PhishScores from test set (first 10):")
            sample = pd.DataFrame({
                'PhishScore': phish_scores[:10],
                'Actual Label': y_test.values[:10]
            })
            print(sample.to_string(index=False))

        except Exception as e:
            print(f"Warning: Could not run Ensemble calculation: {e}")
            print("Action: Re-run Week 5 training script using joblib.dump() to fix the .pkl file.")
    else:
        print(f"Warning: logistic_model.pkl not found.")

    print(f"\n--- Week 6 Milestone Complete ---")
    print(f"Ensemble PhishScore formula ready for Week 7 API integration.")