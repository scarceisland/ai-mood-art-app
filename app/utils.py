import os
import psycopg2
from psycopg2.extras import DictCursor
from functools import wraps
from flask import session, redirect, url_for, flash, current_app


def get_db():
    """Establishes a connection to the PostgreSQL database on Supabase."""
    # The connection string is read from an environment variable for security.
    db_url = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE URL is not set. Set SUPABASE_DB_URL or DATABASE_URL environment variable.")

    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        # Fallback to SQLite or handle error
        raise


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

