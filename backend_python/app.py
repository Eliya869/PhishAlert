import sqlite3
import os
import re
import json
import joblib
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from difflib import SequenceMatcher
from urllib.parse import urlparse

app = Flask(__name__)

# --- Configuration & Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_PATH = os.path.join(BASE_DIR, "models")
DATA_PATH = os.path.join(BASE_DIR, "data")
FEEDBACK_FILE = os.path.join(DATA_PATH, "user_feedback.csv")
DB_PATH = os.path.join(DATA_PATH, "phishalert.db")

# External Configuration Files
BRANDS_FILE = os.path.join(DATA_PATH, "trusted_brands.txt")
KEYWORDS_FILE = os.path.join(DATA_PATH, "suspicious_keywords.txt")
TLDS_FILE = os.path.join(DATA_PATH, "suspicious_tlds.txt")

os.makedirs(DATA_PATH, exist_ok=True)

# --- Regex Patterns ---
URL_REGEX = re.compile(r"(https?://[^\s\"'<>]+|www\.[^\s\"'<>]+)", re.IGNORECASE)
IP_REGEX = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")


# --- Dynamic File Loading Functions ---
def load_config_file(filepath):
    """Loads a list of strings from an external text file."""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip().lower() for line in f if line.strip()]
    except Exception as e:
        print(f"[-] Error loading {filepath}: {e}")
        return []


# --- Load Models & Expected Features ---
print("[*] Booting Machine Learning Pipelines...")

# Load Logistic Regression Model
raw_log = joblib.load(os.path.join(MODELS_PATH, "logistic_model.pkl"))
logistic_model = raw_log["model"] if isinstance(raw_log, dict) else raw_log
LOGISTIC_FEATURES = raw_log.get("feature_names", []) if isinstance(raw_log, dict) else []

# Load Random Forest Model
raw_rf = joblib.load(os.path.join(MODELS_PATH, "random_forest_model.pkl"))
rf_model = raw_rf["model"] if isinstance(raw_rf, dict) else raw_rf
RF_TEXT_MODEL = raw_rf.get("text_model") if isinstance(raw_rf, dict) else None

# Load Feature Names for Random Forest
MODEL_FEATURES = []
rf_metrics_path = os.path.join(MODELS_PATH, "random_forest_model_metrics.json")
if os.path.exists(rf_metrics_path):
    try:
        with open(rf_metrics_path, "r", encoding="utf-8") as f:
            metrics_data = json.load(f)
            MODEL_FEATURES = metrics_data.get("feature_names", [])
    except Exception:
        pass

if not MODEL_FEATURES:
    if isinstance(raw_rf, dict) and "feature_names" in raw_rf:
        MODEL_FEATURES = raw_rf["feature_names"]
    else:
        print("[-] WARNING: Could not load feature names. App may crash during scan.")

if not LOGISTIC_FEATURES:
    try:
        LOGISTIC_FEATURES = list(logistic_model.feature_names_in_)
    except Exception:
        LOGISTIC_FEATURES = MODEL_FEATURES


# --- Feature Extraction Helpers ---
def normalize_url(url):
    """Ensures URL has a standard scheme for accurate parsing."""
    if url.lower().startswith("www."):
        return "http://" + url
    return url


def get_domain(url):
    """Extracts the network location (domain) from a URL."""
    try:
        parsed = urlparse(normalize_url(url))
        return parsed.netloc.lower()
    except Exception:
        return ""


def get_tld(domain):
    """Extracts the Top-Level Domain (TLD)."""
    domain = domain.split(":")[0]
    parts = [part for part in domain.split(".") if part]
    return parts[-1] if len(parts) >= 2 else ""


def extract_live_features(body, sender, subject=""):
    """Transforms raw email text into an aligned feature vector for the ML models."""
    features = {}

    # 1. Text & Structural Analysis
    body_words = re.findall(r"\b\w+\b", body)
    word_count = len(body_words)
    text_combined = f"{body} {subject}"

    features['body_length'] = len(body)
    features['subject_length'] = len(subject)
    features['word_count'] = word_count
    features['avg_word_length'] = float(np.mean([len(w) for w in body_words])) if body_words else 0.0
    features['uppercase_ratio'] = sum(1 for c in body if c.isupper()) / max(1, len(body))
    features['digit_count'] = sum(1 for c in body if c.isdigit())
    features['exclamation_count'] = body.count('!')
    features['question_count'] = body.count('?')
    features['special_char_count'] = len(re.findall(r'[^A-Za-z0-9\s]', body))
    features['body_has_html'] = 1 if re.search(r'<html|<a\s+href|</', body, re.IGNORECASE) else 0
    features['subject_has_re'] = 1 if re.search(r'^\s*re:', subject, re.IGNORECASE) else 0
    features['subject_has_fwd'] = 1 if re.search(r'^\s*(?:fwd|fw):', subject, re.IGNORECASE) else 0

    # 2. Dynamic Keyword Analysis
    suspicious_words = load_config_file(KEYWORDS_FILE)
    keyword_count = 0
    for word in suspicious_words:
        val = 1 if word in body.lower() else 0
        features[f'word_{word}'] = val
        keyword_count += val

    features['keyword_count'] = keyword_count
    features['keyword_density'] = keyword_count / max(1, word_count)

    # 3. Dynamic URL Analysis
    urls = URL_REGEX.findall(text_combined)
    features['has_urls'] = 1 if urls else 0
    suspicious_tlds = set(load_config_file(TLDS_FILE))

    if urls:
        domains = [get_domain(u) for u in urls]
        lengths = [len(u) for u in urls]
        all_urls_text = " ".join(urls)

        features['url_count'] = len(urls)
        features['has_https_url'] = 1 if any(u.lower().startswith("https://") for u in urls) else 0
        features['has_ip_url'] = 1 if any(IP_REGEX.match(d.split(":")[0]) for d in domains) else 0
        features['has_at_symbol_url'] = 1 if any("@" in u for u in urls) else 0
        features['has_suspicious_tld'] = 1 if any(get_tld(d) in suspicious_tlds for d in domains) else 0
        features['url_avg_length'] = float(np.mean(lengths))
        features['url_max_length'] = int(max(lengths))
        features['url_dot_count'] = all_urls_text.count('.')
        features['url_dash_count'] = all_urls_text.count('-')
        features['url_digit_count'] = sum(1 for c in all_urls_text if c.isdigit())
    else:
        for k in ['url_count', 'has_https_url', 'has_ip_url', 'has_at_symbol_url', 'has_suspicious_tld',
                  'url_avg_length', 'url_max_length', 'url_dot_count', 'url_dash_count', 'url_digit_count']:
            features[k] = 0

    # 4. Sender & Dynamic Brand Analysis
    sender_domain_match = re.search(r'@([\w.\-]+)', sender.lower())
    domain = sender_domain_match.group(1) if sender_domain_match else ""

    features['sender_domain_length'] = len(domain)
    features['sender_has_digits'] = 1 if re.search(r'\d', domain) else 0
    features['sender_has_dash'] = 1 if '-' in domain else 0
    features['sender_subdomain_count'] = max(0, domain.count('.') - 1)

    trusted_brands = load_config_file(BRANDS_FILE)
    brand_in_sender = 0
    brand_in_subject = 0
    brand_in_body = 0

    if trusted_brands:
        brand_pattern = "|".join(re.escape(b) for b in trusted_brands)
        if re.search(brand_pattern, domain, re.IGNORECASE): brand_in_sender = 1
        if re.search(brand_pattern, subject, re.IGNORECASE): brand_in_subject = 1
        if re.search(brand_pattern, text_combined, re.IGNORECASE): brand_in_body = 1

    features['brand_in_sender'] = brand_in_sender
    features['brand_in_subject'] = brand_in_subject
    features['brand_in_body'] = brand_in_body
    features['brand_mismatch'] = 1 if (brand_in_body == 1 and brand_in_sender == 0) else 0

    # 5. Distance & Authentication Check
    lev_score = 0.5
    if domain:
        scores = []
        for d in trusted_brands:
            if d in domain or any(SequenceMatcher(None, sub, d).ratio() > 0.75 for sub in domain.split('-')):
                scores.append(0.95)
            else:
                scores.append(1 - SequenceMatcher(None, domain, d).ratio())
        lev_score = max(scores) if scores else 0.5

    features['levenshtein_dist'] = lev_score
    features['auth_verify'] = 1 if re.search(r'spf=pass|dkim=pass', body.lower()) else 0

    # 6. Feature Alignment & Text Model Evaluation
    features['text_for_model'] = f"{sender} {subject} {body}"
    if RF_TEXT_MODEL is not None:
        features['text_phish_score'] = RF_TEXT_MODEL.predict_proba(pd.Series([features['text_for_model']]))[0][1]

    df_features = pd.DataFrame([features])
    df_rf = df_features.reindex(columns=MODEL_FEATURES, fill_value=0)
    df_logistic = df_features.reindex(columns=LOGISTIC_FEATURES, fill_value=0)

    return df_rf, df_logistic, domain, lev_score, keyword_count, features['has_urls'], features['auth_verify']


def get_feedback_adjustment(sender):
    """Adjusts predictions based on historical SOC analyst feedback."""
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


# --- API Endpoints ---
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        body = data.get('body', '')
        sender = data.get('sender', '')
        subject = data.get('subject', '')

        if not body:
            return jsonify({"status": "error", "error": "Email body is missing"}), 400

        # Feature Extraction
        df_rf_vector, df_logistic_vector, domain, lev_dist, key_count, has_urls, auth_verify = extract_live_features(
            body, sender, subject)

        # Multi-Model Evaluation
        p_log = logistic_model.predict_proba(df_logistic_vector)[0][1]
        p_rf = rf_model.predict_proba(df_rf_vector)[0][1]

        # Ensemble Weighted Scoring
        base_score = (p_log * 0.8 + p_rf * 0.2) * 100
        adjustment = get_feedback_adjustment(sender)
        final_score = max(0, min(100, base_score + adjustment))

        # Categorical Classification
        classification = "Dangerous" if final_score >= 75 else ("Suspicious" if final_score >= 45 else "Safe")

        # Telemetry Logging
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scan_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scan_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        sender_email TEXT,
                        sender_domain TEXT,
                        phish_score REAL,
                        classification TEXT,
                        levenshtein_dist REAL,
                        keyword_count INTEGER,
                        has_urls INTEGER
                    )
                """)
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
            "lev_score": round(lev_dist, 2),
            "ai_prob": round(p_rf * 100, 2),
            "keyword_count": key_count,
            "auth_check": "VERIFIED" if auth_verify == 1 else "UNVERIFIED"
        })

    except Exception as e:
        print(f"Prediction Crash: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/history', methods=['GET'])
def get_history():
    """Retrieves recent scan telemetry for the dashboard."""
    try:
        if not os.path.exists(DB_PATH):
            return jsonify([])
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT scan_date, sender_email, phish_score, classification FROM scan_history ORDER BY id DESC LIMIT 100")
            return jsonify([dict(row) for row in cursor.fetchall()])
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/feedback', methods=['POST'])
def save_feedback():
    try:
        data = request.get_json()
        sender = data.get('sender', '')
        correct_label = data.get('correct_label', '')

        if not sender or not correct_label:
            return jsonify({"status": "error", "error": "Invalid feedback data"}), 400

        new_row = pd.DataFrame([[sender, correct_label]], columns=['sender', 'correct_label'])
        if not os.path.isfile(FEEDBACK_FILE):
            new_row.to_csv(FEEDBACK_FILE, index=False)
        else:
            new_row.to_csv(FEEDBACK_FILE, mode='a', header=False, index=False)
        return jsonify({"status": "success", "message": "Feedback recorded."})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == '__main__':
    print("--- PhishAlert Advanced Network API Online ---")
    app.run(host='127.0.0.1', port=5000, debug=True)