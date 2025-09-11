# models/db.py
import os
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

# --- SQLAlchemy ORM Setup ---
db = SQLAlchemy()  # this is what __init__.py expects


# --- psycopg2 (Direct Supabase Connection) ---
def get_supabase_conn():
    """Establish a raw psycopg2 connection to Supabase Postgres."""
    conn = psycopg2.connect(
        host=os.getenv("SUPABASE_HOST"),
        database=os.getenv("SUPABASE_DB", "postgres"),
        user=os.getenv("SUPABASE_USER", "postgres"),
        password=os.getenv("SUPABASE_PASSWORD"),
        port=os.getenv("SUPABASE_PORT", 5432)
    )
    return conn


def insert_feedback_supabase(username, emotion, prompt, image_url, advice,
                             predicted_correct, advice_ok, comments):
    """Insert feedback directly into the 'feedback' table in Supabase."""
    conn = get_supabase_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO feedback (
                username, emotion, prompt, image_url, advice,
                predicted_correct, advice_ok, comments, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (username, emotion, prompt, image_url, advice,
             predicted_correct, advice_ok, comments)
        )
        conn.commit()
    conn.close()
