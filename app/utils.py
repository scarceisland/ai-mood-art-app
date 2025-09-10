from functools import wraps
from flask import session, redirect, url_for, flash
from .models.user import User

def login_required(view):
    """Decorator to ensure a user is logged in before accessing a view."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("main.entry"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    """Decorator to ensure a user has admin privileges."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("main.login"))

        user = User.query.get(session["user_id"])
        if not user or not user.is_admin:
            flash("Admin access required for this page.", "danger")
            return redirect(url_for("main.home"))
        return view(*args, **kwargs)

    return wrapped