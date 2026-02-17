import pandas as pd
import os

# הגדרת הנתיב לתיקיית הנתונים
data_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
output_file = os.path.join(data_path, "phishing_data.csv")

# רשימת הקבצים שראינו בתמונה שלך
files_to_combine = [
    'CEAS_08.csv', 'Enron.csv', 'Ling.csv',
    'Nazario.csv', 'Nigerian_Fraud.csv',
    'phishing_email.csv', 'SpamAssassin.csv'
]

all_dfs = []

print("--- מתחיל איחוד נתונים ---")

for file in files_to_combine:
    full_path = os.path.join(data_path, file)
    if os.path.exists(full_path):
        # טעינת הקובץ - אנחנו מניחים שיש עמודות טקסט ותווית
        df = pd.read_csv(full_path)
        all_dfs.append(df)
        print(f"נטען בהצלחה: {file} | שורות: {len(df)}")

# איחוד כל הטבלאות לאחת
final_df = pd.concat(all_dfs, ignore_index=True)

# שמירה לקובץ המאוחד שבו נשתמש לאימון המודלים
final_df.to_csv(output_file, index=False)

print(f"\nסיום! נוצר קובץ מאוחד: {output_file}")
print(f"סה\"כ שורות במאגר המאוחד: {len(final_df)}")