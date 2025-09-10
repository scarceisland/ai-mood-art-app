from functools import wraps
from flask import session, redirect, url_for, flash

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
        # Assumes ADMIN_USERNAME is globally accessible or configured
        from .routes import ADMIN_USERNAME
        if session.get("username") != ADMIN_USERNAME:
            flash("Admin access required for this page.", "danger")
            return redirect(url_for("main.home"))
        return view(*args, **kwargs)

    return wrapped
