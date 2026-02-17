import pandas as pd

# נתיב לקובץ המאוחד
file_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data\phishing_data.csv"

# טעינת הנתונים
df = pd.read_csv(file_path)

# בדיקה ראשונית
print(f"סה\"כ שורות במאגר: {len(df)}")
print("\n--- חמש השורות הראשונות במאגר המאוחד ---")
print(df.head())

# בדיקת שמות העמודות
print("\n--- שמות העמודות שמצאתי ---")
print(df.columns.tolist())