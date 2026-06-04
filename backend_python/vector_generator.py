import os
import re
from urllib.parse import urlparse
import numpy as np
import pandas as pd

# --- Configuration & Paths ---
DATA_PATH = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
INPUT_FILE = os.path.join(DATA_PATH, "final_features_v2.csv")
OUTPUT_FILE = os.path.join(DATA_PATH, "model_ready_data.csv")

BRANDS_FILE = os.path.join(DATA_PATH, "trusted_brands.txt")
TLDS_FILE = os.path.join(DATA_PATH, "suspicious_tlds.txt")

URL_REGEX = re.compile(r"(https?://[^\s\"'<>]+|www\.[^\s\"'<>]+)", re.IGNORECASE)
IP_REGEX = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")


# --- Dynamic Loaders ---
def load_config_list(filepath):
    """Loads plain-text configuration lists dynamically."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as file:
        return [line.strip().lower() for line in file if line.strip()]


def clean_text_series(series):
    """Forces standard string formatting and null handling."""
    return series.fillna("").astype(str)


def extract_urls(row):
    """Aggregates all URLs identified within the email corpus."""
    combined = f"{str(row.get('urls', ''))} {str(row.get('body', ''))}"
    return URL_REGEX.findall(combined)


def get_domain(url):
    """Isolates the domain layer from raw HTTP schemas."""
    try:
        url = "http://" + url if url.lower().startswith("www.") else url
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def get_tld(domain):
    """Extracts the Top-Level Domain mapping."""
    domain = domain.split(":")[0]
    parts = [part for part in domain.split(".") if part]
    return parts[-1] if len(parts) >= 2 else ""


def url_features(urls, suspicious_tlds):
    """Builds a technical telemetry vector evaluating URL structures."""
    if not urls:
        return pd.Series({"url_count": 0, "has_https_url": 0, "has_ip_url": 0,
                          "has_at_symbol_url": 0, "has_suspicious_tld": 0,
                          "url_avg_length": 0.0, "url_max_length": 0, "url_dot_count": 0,
                          "url_dash_count": 0, "url_digit_count": 0})

    domains = [get_domain(url) for url in urls]
    lengths = [len(url) for url in urls]
    all_urls_text = " ".join(urls)

    return pd.Series({
        "url_count": len(urls),
        "has_https_url": int(any(url.lower().startswith("https://") for url in urls)),
        "has_ip_url": int(any(IP_REGEX.match(d.split(":")[0]) for d in domains if d)),
        "has_at_symbol_url": int(any("@" in url for url in urls)),
        "has_suspicious_tld": int(any(get_tld(d) in suspicious_tlds for d in domains)),
        "url_avg_length": float(np.mean(lengths)),
        "url_max_length": int(max(lengths)),
        "url_dot_count": all_urls_text.count("."),
        "url_dash_count": all_urls_text.count("-"),
        "url_digit_count": sum(ch.isdigit() for ch in all_urls_text),
    })


def add_text_features(df):
    """Calculates NLP distributions, structural ratios, and brand impersonation vectors."""
    body = clean_text_series(df.get("body", pd.Series(index=df.index, dtype=str)))
    subject = clean_text_series(df.get("subject", pd.Series(index=df.index, dtype=str)))
    sender = clean_text_series(df.get("sender", pd.Series(index=df.index, dtype=str)))
    text_combined = clean_text_series(df.get("text_combined", body + " " + subject))

    body_words = body.str.findall(r"\b\w+\b")
    word_count = body_words.apply(len)

    df["body_length"] = body.str.len()
    df["subject_length"] = subject.str.len()
    df["word_count"] = word_count
    df["avg_word_length"] = body_words.apply(lambda words: float(np.mean([len(w) for w in words])) if words else 0.0)
    df["uppercase_ratio"] = body.apply(lambda text: sum(ch.isupper() for ch in text) / max(1, len(text)))
    df["digit_count"] = body.str.count(r"\d")
    df["exclamation_count"] = body.str.count("!")
    df["question_count"] = body.str.count(r"\?")
    df["special_char_count"] = body.str.count(r"[^A-Za-z0-9\s]")
    df["body_has_html"] = body.str.contains(r"<html|<a\s+href|</", case=False, regex=True).astype(int)
    df["subject_has_re"] = subject.str.contains(r"^\s*re:", case=False, regex=True).astype(int)
    df["subject_has_fwd"] = subject.str.contains(r"^\s*(?:fwd|fw):", case=False, regex=True).astype(int)

    df["keyword_density"] = df["keyword_count"] / word_count.replace(0, 1) if "keyword_count" in df.columns else 0.0

    domains = sender.apply(lambda s: re.search(r"@([\w.\-]+)", s.lower()).group(1) if "@" in s else "")
    df["sender_domain_length"] = domains.str.len()
    df["sender_has_digits"] = domains.str.contains(r"\d", regex=True).astype(int)
    df["sender_has_dash"] = domains.str.contains("-", regex=False).astype(int)
    df["sender_subdomain_count"] = domains.apply(lambda val: max(0, val.count(".") - 1))

    brands = load_config_list(BRANDS_FILE)
    if brands:
        brand_pattern = "|".join(re.escape(brand) for brand in brands)
        df["brand_in_sender"] = domains.str.contains(brand_pattern, case=False, regex=True).astype(int)
        df["brand_in_subject"] = subject.str.contains(brand_pattern, case=False, regex=True).astype(int)
        df["brand_in_body"] = text_combined.str.contains(brand_pattern, case=False, regex=True).astype(int)
        df["brand_mismatch"] = ((df["brand_in_body"] == 1) & (df["brand_in_sender"] == 0)).astype(int)
    else:
        df["brand_in_sender"] = 0;
        df["brand_in_subject"] = 0
        df["brand_in_body"] = 0;
        df["brand_mismatch"] = 0

    return df


def build_model_ready_data(df):
    """Executes the master assembly for the numeric model matrix."""
    df = add_text_features(df.copy())

    print("Extracting URL structure features...")
    url_lists = df.apply(extract_urls, axis=1)
    suspicious_tlds = set(load_config_list(TLDS_FILE))
    url_feature_df = url_lists.apply(lambda u: url_features(u, suspicious_tlds))

    cols_to_drop = [c for c in url_feature_df.columns if c in df.columns]
    if cols_to_drop: df = df.drop(columns=cols_to_drop)

    df = pd.concat([df, url_feature_df], axis=1)
    df = df.loc[:, ~df.columns.duplicated()]

    base_features = [
        "has_urls", "levenshtein_dist", "auth_verify", "keyword_count", "keyword_density",
        "body_length", "subject_length", "word_count", "avg_word_length", "uppercase_ratio",
        "digit_count", "exclamation_count", "question_count", "special_char_count",
        "body_has_html", "subject_has_re", "subject_has_fwd", "url_count", "has_https_url",
        "has_ip_url", "has_at_symbol_url", "has_suspicious_tld", "url_avg_length",
        "url_max_length", "url_dot_count", "url_dash_count", "url_digit_count",
        "sender_domain_length", "sender_has_digits", "sender_has_dash",
        "sender_subdomain_count", "brand_in_sender", "brand_in_subject",
        "brand_in_body", "brand_mismatch"
    ]

    keyword_features = [col for col in df.columns if col.startswith("word_") and col != "word_count"]
    final_columns = list(dict.fromkeys(base_features + keyword_features + ["label"]))

    missing = [col for col in final_columns if col not in df.columns]
    if missing: raise ValueError(f"[-] Critical Error: Missing required columns: {missing}")

    model_ready_df = df[final_columns].copy()
    model_ready_df = model_ready_df.replace([np.inf, -np.inf], np.nan).fillna(0)

    for col in model_ready_df.columns:
        model_ready_df[col] = pd.to_numeric(model_ready_df[col], errors="coerce").fillna(0)

    model_ready_df["label"] = model_ready_df["label"].astype(int)
    return model_ready_df


if __name__ == "__main__":
    if not os.path.exists(INPUT_FILE):
        print(f" Error: {INPUT_FILE} not found.")
    else:
        print("Loading enriched source data...")
        source_df = pd.read_csv(INPUT_FILE, low_memory=False)
        model_ready = build_model_ready_data(source_df)
        model_ready.to_csv(OUTPUT_FILE, index=False)

        feature_count = len(model_ready.columns) - 1
        print(f"Success! Dataset finalized with {feature_count} technical features.")