import sqlite3
import os

"""
Database Setup - Initializes the PhishAlert SQLite database.
"""

data_path = r"C:\Users\eliya\Desktop\PhishProject\backend_python\data"
db_path = os.path.join(data_path, "phishalert.db")


def setup_db():
    print("--- Starting Database Setup ---")

    # Using 'with' ensures the connection closes automatically
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Table 1: Scan History (Logs all X1, X2, X3 features)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_date        TEXT    DEFAULT (datetime('now')),
                sender_email     TEXT    NOT NULL,
                sender_domain    TEXT    NOT NULL,
                phish_score      REAL    NOT NULL,
                classification   TEXT    NOT NULL,
                spf_dkim_result  INTEGER,
                levenshtein_dist REAL,
                keyword_count    INTEGER,
                has_urls         INTEGER,
                blocked          INTEGER DEFAULT 0
            )
        """)

        # Table 2: Trusted Domains (X2 Reference list)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trusted_domains (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                domain   TEXT    NOT NULL UNIQUE,
                category TEXT    NOT NULL
            )
        """)

        # Table 3: System Settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key         TEXT PRIMARY KEY,
                value       TEXT NOT NULL,
                description TEXT
            )
        """)

        conn.commit()

    print(f"Success! Database initialized at: {db_path}")


if __name__ == "__main__":
    setup_db()