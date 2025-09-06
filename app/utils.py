import os
import sqlite3
import psycopg2
from psycopg2.extras import DictCursor
from functools import wraps
from flask import session, redirect, url_for, flash, current_app

def get_db():
    # Try to get Supabase database URL from environment variables
    db_url = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")

    if db_url:
        try:
            # Try to connect to Supabase PostgreSQL
            conn = psycopg2.connect(db_url)
            current_app.logger.info("Connected to Supabase database successfully")
            return conn
        except Exception as e:
            # Fallback to SQLite if Supabase connection fails
            current_app.logger.warning(f"Supabase connection failed: {e}. Falling back to SQLite.")
            return sqlite3.connect('mood_app.db')
    else:
        # Use SQLite if no database URL is set
        current_app.logger.warning("No database URL found. Using SQLite.")
        return sqlite3.connect('mood_app.db')


def login_required(view):
    """Decorator to ensure a user is logged in before accessing a view."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "username" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("main.entry"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    """Decorator to ensure a user has admin privileges."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("username") != "admin":
            flash("Admin access required for this page.", "danger")
            return redirect(url_for("main.home"))
        return view(*args, **kwargs)

    return wrapped

