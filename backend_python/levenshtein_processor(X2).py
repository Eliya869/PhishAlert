import pandas as pd
import os
from difflib import SequenceMatcher


# חישוב מרחק לווינשטיין מבוסס דמיון תווים
def get_levenshtein_distance(s1, s2):
    m = SequenceMatcher(None, s1, s2)
    return 1 - m.ratio()


# נתיבי קבצים
data_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
input_file = os.path.join(data_path, "processed_data.csv")
output_file = os.path.join(data_path, "final_features.csv")

# דומיינים לגיטימיים להשוואה
top_legal_domains = ['paypal.com', 'google.com', 'microsoft.com', 'bankofamerica.com', 'gov.il']

if os.path.exists(input_file):
    print("טוען נתונים...")
    df = pd.read_csv(input_file)


    # חילוץ דומיין מכתובת השולח
    def extract_domain(sender):
        parts = str(sender).split('@')
        return parts[-1].strip() if len(parts) > 1 else ""


    # חישוב המרחק המינימלי (X2)
    def min_levenshtein(sender_email):
        domain = extract_domain(sender_email)
        if not domain: return 1.0
        return min([get_levenshtein_distance(domain, legal) for legal in top_legal_domains])


    print("מחשב מרחק לווינשטיין (X2)...")
    df['levenshtein_dist'] = df['sender'].apply(min_levenshtein)

    # שמירת קובץ סופי לאימון מודלים
    df.to_csv(output_file, index=False)
    print(f"הסתיים: {output_file}")
else:
    print("קובץ קלט לא נמצא.")