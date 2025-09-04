# init_db.py
import sqlite3

# This path should be correct based on your previous confirmation.
DATABASE = 'data/mood_app.db'

# SQL command to create the 'logs' table
create_logs_table_sql = """
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT (datetime('now','localtime')),
    timestamp TEXT,
    event TEXT NOT NULL,
    user TEXT,
    source TEXT,
    data TEXT
);
"""

# --- NEW ---
# SQL command to create the 'settings' table
create_settings_table_sql = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY NOT NULL,
    value TEXT
);
"""
# --- END NEW ---

try:
    # Connect to the database
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()

    # Execute the create command for the 'logs' table
    cur.execute(create_logs_table_sql)

    # --- NEW ---
    # Execute the create command for the 'settings' table
    cur.execute(create_settings_table_sql)
    # --- END NEW ---

    # Commit the changes and close the connection
    con.commit()
    con.close()

    print("✅ Success! The 'logs' and 'settings' tables were created or already exist.")

except sqlite3.Error as e:
    print(f"❌ An error occurred: {e}")