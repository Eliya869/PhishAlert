import pandas as pd
import re
import os


def extract_basic_features(df):
    # וידוא שאין ערכים ריקים בטקסט
    df['body'] = df['body'].fillna('')

    # רשימת מילות מפתח מחשידות
    suspicious_words = ['urgent', 'verify', 'account', 'update', 'password', 'bank', 'pay', 'immediately']

    print("מחלץ מאפייני טקסט (X3)...")
    for word in suspicious_words:
        # יצירת עמודה לכל מילה: 1 אם קיימת, 0 אם לא
        df[f'word_{word}'] = df['body'].str.contains(word, case=False).astype(int)

    # בדיקת נוכחות קישורים (X1)
    print("בודק נוכחות קישורים (URLs)...")
    df['has_urls'] = df['body'].str.contains(r'http[s]?://', regex=True).astype(int)

    return df


# נתיב לקובץ המאוחד לפי המבנה שראיתי בתמונה
data_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
input_file = os.path.join(data_path, "phishing_data.csv")
output_file = os.path.join(data_path, "processed_data.csv")

if os.path.exists(input_file):
    print(f"טוען נתונים מ: {input_file}")
    df = pd.read_csv(input_file)

    # הרצת החילוץ
    df_processed = extract_basic_features(df)

    # שמירה לקובץ חדש שישמש לאימון ה-Random Forest וה-Logistic Regression
    df_processed.to_csv(output_file, index=False)
    print(f"\nהצלחה! נוצר קובץ מעובד עם מאפיינים: {output_file}")
    print(f"עמודות חדשות שנוספו: {[col for col in df_processed.columns if 'word_' in col or col == 'has_urls']}")
else:
    print(f"שגיאה: לא נמצא הקובץ {input_file}")