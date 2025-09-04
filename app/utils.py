import os
import sqlite3
from functools import wraps
from flask import session, redirect, url_for, flash, current_app


def get_db():
    """Establishes a connection to the SQLite database."""
    db_path = current_app.config.get("DATABASE_PATH")

    if not db_path:
        # Fallback to a default path in the instance folder if not configured.
        instance_path = current_app.instance_path
        db_path = os.path.join(instance_path, "mood_app.db")

    # Ensure the directory for the database file exists.
    dirpath = os.path.dirname(db_path) or "."
    os.makedirs(dirpath, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


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
