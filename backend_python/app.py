import os
import re
import joblib
from flask import Flask, request, jsonify
from difflib import SequenceMatcher

app = Flask(__name__)

# --- Configuration & Model Loading (Week 7) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_PATH = os.path.join(BASE_DIR, "models")

# Loading the system brains (Week 5 & 6 model files)
logistic_data = joblib.load(os.path.join(MODELS_PATH, "logistic_model.pkl"))
rf_model = joblib.load(os.path.join(MODELS_PATH, "random_forest_model.pkl"))

# Known legitimate domains for comparison (X2 - Levenshtein)
TOP_LEGAL_DOMAINS = ['paypal.com', 'google.com', 'microsoft.com', 'amazon.com', 'apple.com', 'bankofamerica.com']


def extract_live_features(body, sender):
    """
    Feature extraction function for real-time analysis.
    Converts raw email data into a numerical vector for the models.
    """
    suspicious_words = [
        'urgent', 'verify', 'account', 'update', 'password', 'bank', 'pay', 'immediately',
        'click', 'confirm', 'suspend', 'suspended', 'restricted', 'unusual',
        'limited', 'expire', 'expired', 'login', 'signin', 'credit', 'debit',
        'transfer', 'billing', 'invoice', 'payment', 'alert', 'warning',
        'unauthorized', 'blocked', 'locked'  # Added unauthorized and blocked
    ]

    features = {}

    # X3: Text and keyword analysis
    features['has_urls'] = 1 if re.search(r'http[s]?://', body) else 0
    keyword_count = 0
    for word in suspicious_words:
        val = 1 if word in body.lower() else 0
        features[f'word_{word}'] = val
        keyword_count += val
    features['keyword_count'] = keyword_count

    # X2: Levenshtein distance (Domain similarity)
    domain_match = re.search(r'@([\w.\-]+)', sender)
    domain = domain_match.group(1).lower() if domain_match else ""

    # Fallback: If sender is missing, extract domain from links within the text body
    if not domain:
        url_match = re.search(r'https?://([\w.\-]+)', body)
        domain = url_match.group(1).lower() if url_match else ""

    lev_score = 0.5  # Neutral default value
    if domain:
        lev_score = min([1 - SequenceMatcher(None, domain, d).ratio() for d in TOP_LEGAL_DOMAINS])
    features['levenshtein_dist'] = lev_score

    # X1: Authentication check (Defaulting to 0 for real-time simulation)
    features['auth_verify'] = 0

    # Constructing the feature vector in the exact training order
    feature_order = ['has_urls', 'levenshtein_dist', 'auth_verify', 'keyword_count'] + [f'word_{w}' for w in
                                                                                        suspicious_words]

    return [features[col] for col in feature_order]


# --- Main API Routes ---

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Endpoint that receives email details via JSON and returns PhishScore and classification.
    """
    try:
        data = request.get_json()
        body = data.get('body', '')
        sender = data.get('sender', '')

        if not body:
            return jsonify({"status": "error", "message": "Email body is missing"}), 400

        # 1. Extract features from the live input
        vector = extract_live_features(body, sender)

        # 2. Model prediction using Ensemble logic
        # Model 1: Logistic Regression (includes scaling)
        scaler = logistic_data['scaler']
        vector_scaled = scaler.transform([vector])
        p_log = logistic_data['model'].predict_proba(vector_scaled)[0][1]

        # Model 2: Random Forest
        p_rf = rf_model.predict_proba([vector])[0][1]

        # 3. Final PhishScore calculation (70% RF weight, 30% LogReg weight)
        final_score = (p_rf * 0.7 + p_log * 0.3) * 100
        classification = "Phishing" if final_score >= 50 else "Safe"

        # 4. Return the final JSON response
        return jsonify({
            "status": "success",
            "phish_score": round(final_score, 2),
            "classification": classification,
            "recommendation": "Danger! Highly suspicious." if classification == "Phishing" else "Looks legitimate."
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    print("--- PhishAlert API Server is Starting... ---")
    app.run(host='0.0.0.0', port=5000, debug=True)