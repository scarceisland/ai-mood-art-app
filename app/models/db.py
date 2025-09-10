# models/db.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Establish connection to Supabase
def get_supabase_conn():
    conn = psycopg2.connect(
        host=os.getenv("SUPABASE_HOST"),
        database=os.getenv("SUPABASE_DB"),  # Usually 'postgres'
        user=os.getenv("SUPABASE_USER"),    # Usually 'postgres'
        password=os.getenv("SUPABASE_PASSWORD"),
        port=5432
    )
    return conn

# Function to insert feedback
def insert_feedback_supabase(username, emotion, prompt, image_url, advice, predicted_correct, advice_ok, comments):
    conn = get_supabase_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO feedback (username, emotion, prompt, image_url, advice, predicted_correct, advice_ok, comments, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (username, emotion, prompt, image_url, advice, predicted_correct, advice_ok, comments)
        )
        conn.commit()
    conn.close()