import sqlite3
from functools import wraps
from flask import current_app, session, redirect, url_for

def get_db():
    conn = sqlite3.connect(current_app.config["DB_PATH"])
    conn.row_factory = sqlite3.Row
    return conn

def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("main.login_page"))
        return view(*args, **kwargs)
    return wrapper

def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if session.get("username") != "admin":
            return redirect(url_for("main.home"))
        return view(*args, **kwargs)
    return wrapper
