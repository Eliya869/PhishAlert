import os
import re
import joblib
import pandas as pd
from flask import Flask, request, jsonify
from difflib import SequenceMatcher

app = Flask(__name__)

# --- Configuration & Model Loading ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_PATH = os.path.join(BASE_DIR, "models")
# Path for the feedback database
FEEDBACK_FILE = os.path.join(BASE_DIR, "data", "user_feedback.csv")

# Ensure the data directory exists
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

# Loading the system brains
logistic_data = joblib.load(os.path.join(MODELS_PATH, "logistic_model.pkl"))
rf_model = joblib.load(os.path.join(MODELS_PATH, "random_forest_model.pkl"))

TOP_LEGAL_DOMAINS = ['paypal', 'google', 'amazon', 'microsoft', 'apple', 'netflix', 'facebook', 'linkedin', 'icloud']


def get_feedback_adjustment(sender):
    """
    Checks if the sender has been manually reported by the user in the past.
    Returns: 30 (Boost for Phishing), -30 (Reduction for Safe), or 0 (No feedback)
    """
    if not os.path.exists(FEEDBACK_FILE):
        return 0

    try:
        df = pd.read_csv(FEEDBACK_FILE)
        # Get all feedback for this specific sender
        sender_feedback = df[df['sender'] == sender]

        if not sender_feedback.empty:
            # Get the latest report for this sender
            latest_correction = sender_feedback.iloc[-1]['correct_label']
            if latest_correction == "Phishing":
                return 35.0  # Significant boost if user said it's phishing
            elif latest_correction == "Safe":
                return -35.0  # Significant reduction if user said it's safe
        return 0
    except Exception:
        return 0


def extract_live_features(body, sender):
    suspicious_words = [
        'urgent', 'verify', 'account', 'update', 'password', 'bank', 'pay', 'immediately',
        'click', 'confirm', 'suspend', 'suspended', 'restricted', 'unusual',
        'limited', 'expire', 'expired', 'login', 'signin', 'credit', 'debit',
        'transfer', 'billing', 'invoice', 'payment', 'alert', 'warning',
        'unauthorized', 'blocked', 'locked'
    ]

    features = {}
    features['has_urls'] = 1 if re.search(r'http[s]?://', body) else 0
    keyword_count = 0
    for word in suspicious_words:
        val = 1 if word in body.lower() else 0
        features[f'word_{word}'] = val
        keyword_count += val
    features['keyword_count'] = keyword_count

    domain_match = re.search(r'@([\w.\-]+)', sender)
    domain = domain_match.group(1).lower() if domain_match else ""

    if not domain:
        url_match = re.search(r'https?://([\w.\-]+)', body)
        domain = url_match.group(1).lower() if url_match else ""

    lev_score = 0.5
    if domain:
        lev_score = min([1 - SequenceMatcher(None, domain, d).ratio() for d in TOP_LEGAL_DOMAINS])
    features['levenshtein_dist'] = lev_score
    features['auth_verify'] = 0

    feature_order = ['has_urls', 'levenshtein_dist', 'auth_verify', 'keyword_count'] + [f'word_{w}' for w in
                                                                                        suspicious_words]
    return [features[col] for col in feature_order]


# --- Main API Routes ---

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        body = data.get('body', '')
        sender = data.get('sender', '')

        if not body:
            return jsonify({"status": "error", "message": "Email body is missing"}), 400

        # 1. Standard AI Prediction
        vector = extract_live_features(body, sender)
        scaler = logistic_data['scaler']
        vector_scaled = scaler.transform([vector])

        p_log = logistic_data['model'].predict_proba(vector_scaled)[0][1]
        p_rf = rf_model.predict_proba([vector])[0][1]

        # Base Ensemble Score
        base_score = (p_rf * 0.7 + p_log * 0.3) * 100

        # 2. Feedback Loop Adjustment (Learning from History)
        adjustment = get_feedback_adjustment(sender)
        final_score = max(0, min(100, base_score + adjustment))

        classification = "Phishing" if final_score >= 50 else "Safe"

        return jsonify({
            "status": "success",
            "phish_score": round(final_score, 2),
            "base_ai_score": round(base_score, 2),
            "classification": classification,
            "was_adjusted": True if adjustment != 0 else False,
            "recommendation": "Danger! Highly suspicious." if classification == "Phishing" else "Looks legitimate."
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/feedback', methods=['POST'])
def save_feedback():
    """
    Endpoint for the Java UI to report if the AI was wrong.
    Expects: {"sender": "...", "correct_label": "Phishing" or "Safe"}
    """
    try:
        data = request.get_json()
        sender = data.get('sender', '')
        correct_label = data.get('correct_label', '')  # "Phishing" or "Safe"

        if not sender or not correct_label:
            return jsonify({"status": "error", "message": "Invalid feedback data"}), 400

        # Create/Append to feedback file
        new_row = pd.DataFrame([[sender, correct_label]], columns=['sender', 'correct_label'])
        if not os.path.isfile(FEEDBACK_FILE):
            new_row.to_csv(FEEDBACK_FILE, index=False)
        else:
            new_row.to_csv(FEEDBACK_FILE, mode='a', header=False, index=False)

        return jsonify(
            {"status": "success", "message": "Feedback recorded. The model will adjust future scores for this sender."})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    print("--- PhishAlert API Starting... ---")
    app.run(host='0.0.0.0', port=5000, debug=True)