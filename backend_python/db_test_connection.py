import sqlite3
import os

"""
Database Connection Testing - Writing and Reading from DB.
"""

db_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data\phishalert.db"


def test_db_operations():
    print("--- Testing Database Connection ---")

    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()

        # 1. Test Writing (Insert a sample trusted domain)
        print("Writing sample data to 'trusted_domains'...")
        cursor.execute("INSERT OR IGNORE INTO trusted_domains (domain, category) VALUES (?, ?)",
                       ('paypal.com', 'Finance'))

        # 2. Test Reading (Select the data back)
        print("Reading data back from 'trusted_domains'...")
        cursor.execute("SELECT * FROM trusted_domains WHERE domain = 'paypal.com'")
        row = cursor.fetchone()

        if row:
            print(f"Connection Successful! Found: {row}")
        else:
            print("Error: Could not retrieve data.")


if __name__ == "__main__":
    if os.path.exists(db_path):
        test_db_operations()
    else:
        print("Error: Database file not found. Run db_setup.py first.")