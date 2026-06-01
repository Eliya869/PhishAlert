import sqlite3
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
FEEDBACK_FILE = os.path.join(BASE_DIR, "data", "user_feedback.csv")
DB_PATH = os.path.join(BASE_DIR, "data", "phishalert.db")
BRANDS_FILE = os.path.join(BASE_DIR, "data", "trusted_brands.txt")
KEYWORDS_FILE = os.path.join(BASE_DIR, "data", "suspicious_keywords.txt")  # Added Keywords File Path

os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)


# Dynamic loading of trusted brands from external database/file (Black-Box requirement)
def load_trusted_brands():
    if not os.path.exists(BRANDS_FILE):
        # Fallback if file is missing
        return ['paypal', 'google', 'amazon', 'microsoft', 'apple', 'netflix', 'facebook']
    with open(BRANDS_FILE, 'r', encoding='utf-8') as f:
        return [line.strip().lower() for line in f if line.strip()]


# Dynamic loading of suspicious keywords from external file (Black-Box requirement)
def load_suspicious_keywords():
    # Fallback default list in case the file is missing or corrupted
    default_keywords = [
        'urgent', 'verify', 'account', 'update', 'password', 'bank', 'pay', 'immediately',
        'click', 'confirm', 'suspend', 'suspended', 'restricted', 'unusual',
        'limited', 'expire', 'expired', 'login', 'signin', 'credit', 'debit',
        'transfer', 'billing', 'invoice', 'payment', 'alert', 'warning',
        'unauthorized', 'blocked', 'locked'
    ]

    if not os.path.exists(KEYWORDS_FILE):
        print(f"[-] Warning: {KEYWORDS_FILE} not found. Using safe default list.")
        return default_keywords

    try:
        with open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
            # Read line by line, strip whitespace, and convert to lowercase for exact matching
            words = [line.strip().lower() for line in f if line.strip()]

        if not words:
            print("[-] Warning: Keywords file is empty. Using default list.")
            return default_keywords

        return words

    except Exception as e:
        print(f"[-] Error reading keywords file: {e}")
        return default_keywords


# Load BOTH models for the Ensemble pipeline
logistic_data = joblib.load(os.path.join(MODELS_PATH, "logistic_model.pkl"))
rf_data = joblib.load(os.path.join(MODELS_PATH, "random_forest_model.pkl"))


def get_feedback_adjustment(sender):
    if not os.path.exists(FEEDBACK_FILE):
        return 0
    try:
        df = pd.read_csv(FEEDBACK_FILE)
        sender_feedback = df[df['sender'] == sender]
        if not sender_feedback.empty:
            latest_correction = sender_feedback.iloc[-1]['correct_label']
            if latest_correction == "Phishing":
                return 35.0
            elif latest_correction == "Safe":
                return -35.0
        return 0
    except Exception:
        return 0


def extract_live_features(body, sender):
    # Load keywords dynamically instead of using a hardcoded list
    suspicious_words = load_suspicious_keywords()

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

    # Dynamic calculation using external black-box brands file
    trusted_brands = load_trusted_brands()
    lev_score = 0.5
    if domain:
        scores = []
        for d in trusted_brands:
            # Check for hidden strings or partial matches inside structural components
            if d in domain or any(SequenceMatcher(None, sub, d).ratio() > 0.75 for sub in domain.split('-')):
                scores.append(0.95)
            else:
                scores.append(1 - SequenceMatcher(None, domain, d).ratio())
        lev_score = max(scores) if scores else 0.5

    features['levenshtein_dist'] = lev_score
    features['auth_verify'] = 1 if re.search(r'spf=pass|dkim=pass', body.lower()) else 0

    feature_order = ['has_urls', 'levenshtein_dist', 'auth_verify', 'keyword_count'] + [f'word_{w}' for w in
                                                                                        suspicious_words]
    vector = [features[col] for col in feature_order]

    return vector, domain, lev_score, keyword_count, features['has_urls'], features['auth_verify']


@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        body = data.get('body', '')
        sender = data.get('sender', '')

        if not body:
            return jsonify({"status": "error", "message": "Email body is missing"}), 400

        vector, domain, lev_dist, key_count, has_urls, auth_verify = extract_live_features(body, sender)

        # 1. Evaluate Model 1: Logistic Regression
        scaler = logistic_data['scaler']
        vector_scaled = scaler.transform([vector])
        p_log = logistic_data['model'].predict_proba(vector_scaled)[0][1]

        # 2. Evaluate Model 2: Random Forest
        p_rf = rf_data['model'].predict_proba([vector])[0][1]

        # Soft Voting Ensemble weight balance
        base_score = (p_rf * 0.7 + p_log * 0.3) * 100

        # Feedback loop modifier
        adjustment = get_feedback_adjustment(sender)
        final_score = max(0, min(100, base_score + adjustment))
        classification = "Dangerous" if final_score >= 75 else ("Suspicious" if final_score >= 45 else "Safe")

        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO scan_history (sender_email, sender_domain, phish_score, classification, levenshtein_dist, keyword_count, has_urls)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (sender, domain, round(final_score, 2), classification, lev_dist, key_count, has_urls))
                conn.commit()
        except Exception as db_e:
            print(f"Database Logging Error: {db_e}")

        return jsonify({
            "status": "success",
            "phish_score": round(final_score, 2),
            "base_ai_score": round(base_score, 2),
            "classification": classification,
            "was_adjusted": True if adjustment != 0 else False,
            "recommendation": "CRITICAL RISK: System Isolation Recommended!" if classification == "Dangerous" else "Legitimate Infrastructure.",
            "lev_score": round(lev_dist, 2),
            "ai_prob": round(p_rf * 100, 2),
            "auth_check": "VERIFIED (SPF/DKIM PASS)" if auth_verify == 1 else "UNVERIFIED INFRASTRUCTURE"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/history', methods=['GET'])
def get_history():
    try:
        if not os.path.exists(DB_PATH):
            return jsonify([])
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT scan_date, sender_email, phish_score, classification FROM scan_history ORDER BY id DESC")
            rows = cursor.fetchall()
            return jsonify([dict(row) for row in rows])
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/feedback', methods=['POST'])
def save_feedback():
    try:
        data = request.get_json()
        sender = data.get('sender', '')
        correct_label = data.get('correct_label', '')

        if not sender or not correct_label:
            return jsonify({"status": "error", "message": "Invalid feedback data"}), 400

        new_row = pd.DataFrame([[sender, correct_label]], columns=['sender', 'correct_label'])
        if not os.path.isfile(FEEDBACK_FILE):
            new_row.to_csv(FEEDBACK_FILE, index=False)
        else:
            new_row.to_csv(FEEDBACK_FILE, mode='a', header=False, index=False)
        return jsonify({"status": "success", "message": "Feedback recorded."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    print("--- PhishAlert Advanced Network API Online ---")
    # Using 127.0.0.1 as it successfully bypassed the firewall connection issues previously
    app.run(host='127.0.0.1', port=5000, debug=True)