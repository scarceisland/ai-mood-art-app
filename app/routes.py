import os
from datetime import datetime, timedelta
from io import BytesIO
from collections import Counter

import pandas as pd
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
    current_app,
    Response,
    flash,
)
from sqlalchemy import text, func, or_

<<<<<<< HEAD
from app.db import db
from .image_generator import build_image_url
from .logger import log_event
from .models.user import User, verify_credentials, get_user, delete_user
from .models.app_models import Feedback, Log, Settings
from .mood_detector import EMOTIONS, advice_for
from .utils import login_required, admin_required

bp = Blueprint("main", __name__)

# Define Admin username from environment variable, for use in routes
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin").lower()

=======
# Local imports
from .image_generator import build_image_url
from .logger import log_event
from .models.user import (
    verify_credentials,
    ADMIN_USERNAME,
    refresh_users_cache,
    delete_user_data,
)
from .mood_detector import EMOTIONS, advice_for
from .utils import (
    get_db,
    login_required,
    admin_required,
    is_sqlite,
)


bp = Blueprint("main", __name__)

# ------------------------------
# NEW FUNCTION: Supabase Connection
# ------------------------------
def get_supabase_db():
    """Creates and returns a connection to the Supabase PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("SUPABASE_HOST"),
            database=os.getenv("SUPABASE_DB"),  # Usually 'postgres'
            user=os.getenv("SUPABASE_USER"),    # Usually 'postgres'
            password=os.getenv("SUPABASE_PASSWORD"),
            port=5432
        )
        return conn
    except Exception as e:
        current_app.logger.error(f"Failed to connect to Supabase: {e}")
        raise e  # Re-raise the exception to handle it in the route
>>>>>>> 07fab75bfb58c355c4d78f7afa95984138d98e83

# ------------------------------
# Dashboard Helper Functions (Refactored for SQLAlchemy)
# ------------------------------
def get_dashboard_stats():
    """Get statistics for the admin dashboard using SQLAlchemy."""
    total_users = db.session.query(func.count(User.id)).filter(User.username != ADMIN_USERNAME).scalar()
    total_images = db.session.query(func.count(Feedback.id)).filter(Feedback.image_url.isnot(None)).scalar()
    total_feedback = db.session.query(func.count(Feedback.id)).scalar()

    thirty_mins_ago = datetime.utcnow() - timedelta(minutes=30)
    active_sessions = db.session.query(func.count(func.distinct(Log.username))).filter(
        Log.timestamp > thirty_mins_ago).scalar()

    return {
        'total_users': total_users,
        'total_images': total_images,
        'total_feedback': total_feedback,
        'active_sessions': active_sessions
    }


def get_recent_activities():
    """Get recent user activities using SQLAlchemy."""
    activities = Feedback.query.filter(Feedback.username != ADMIN_USERNAME) \
        .order_by(Feedback.created_at.desc()) \
        .limit(10).all()

    processed_activities = []
    for activity in activities:
        processed_activities.append({
            'username': activity.username,
            'date': activity.created_at,
            'action': 'Feedback submitted',
            'status': 'submitted'
        })
    return processed_activities


def get_user_activities():
<<<<<<< HEAD
    """Get user activity data using SQLAlchemy."""
    users = User.query.filter(User.username != ADMIN_USERNAME).all()
=======
    """Get user activity data, checking logs first and falling back to feedback."""
    db = get_db()
    processed_users = []
    try:
        users = db.execute("""
            SELECT username, MAX(timestamp) as last_login,
                   CASE WHEN MAX(timestamp) > NOW() - INTERVAL '7 days' THEN 1 ELSE 0 END as active
            FROM logs WHERE username != 'admin' AND event = 'login_success' GROUP BY username ORDER BY last_login DESC
        """).fetchall()
    except Exception:
        # Fallback to feedback table if logs table fails or doesn't have the user
        users = db.execute("""
            SELECT username, MAX(created_at) as last_login,
                   CASE WHEN MAX(created_at) > datetime('now', '-7 days') THEN 1 ELSE 0 END as active
            FROM feedback WHERE username != 'admin'
            GROUP BY username ORDER BY last_login DESC
        """).fetchall()
>>>>>>> 07fab75bfb58c355c4d78f7afa95984138d98e83

    processed_users = []
    for user in users:
        last_log = Log.query.filter_by(username=user.username, event='login_success') \
            .order_by(Log.timestamp.desc()) \
            .first()

        last_login_time = last_log.timestamp if last_log else None
        is_active = last_login_time > (datetime.utcnow() - timedelta(days=7)) if last_login_time else False

        processed_users.append({
            'username': user.username,
            'last_login': last_login_time,
            'active': is_active
        })

    # Sort users by last login, descending (newest first)
    processed_users.sort(key=lambda x: x['last_login'] or datetime.min, reverse=True)
    return processed_users


# ------------------------------
# Main App Routes
# ------------------------------

@bp.route("/", methods=["GET"])
def entry():
    """Renders the main landing/consent page."""
    if session.get("username"):
        return redirect(url_for("main.home"))
    return render_template("entry.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Handles user login."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password") or request.form.get("password_select")

        if verify_credentials(username, password):
            session["username"] = username
            log_event("login_success", user=username)
            return redirect(url_for("main.home"))
        else:
            log_event("login_fail", user=username)
            return render_template("login.html", error="Invalid username or password.")

    return render_template("login.html")


@bp.route("/logout")
@login_required
def logout():
    """Logs the current user out."""
    user = session.pop("username", "(unknown)")
    log_event("logout", user=user)
    return redirect(url_for("main.entry"))


@bp.route("/home", methods=["GET"])
@login_required
def home():
    """Renders the main art generation page."""
    return render_template("home.html", emotions=EMOTIONS)


@bp.route("/generate", methods=["POST"])
@login_required
def generate():
    """Handles the AI art generation request."""
    emotion = (request.form.get("emotion") or "").strip().lower()
    prompt = (request.form.get("prompt") or "").strip()

    if emotion not in EMOTIONS:
        return render_template("_result_card.html", error=f"Invalid emotion: {emotion}")

    log_event(
        "generate",
        user=session.get("username"),
        data={"emotion": emotion, "prompt": prompt}
    )

    image_url = build_image_url(prompt, emotion)
    advice = advice_for(emotion)

    return render_template(
        "_result_card.html",
        image_url=image_url,
        prompt=prompt,
        emotion=emotion,
        advice=advice
    )


@bp.route("/feedback", methods=["POST"])
@login_required
def feedback():
    """Handles user feedback submission."""
<<<<<<< HEAD
    try:
        new_feedback = Feedback(
            username=session.get("username"),
            emotion=request.form.get("emotion"),
            prompt=request.form.get("prompt"),
            image_url=request.form.get("image_url"),
            advice=request.form.get("advice"),
            predicted_correct=int(request.form.get("predicted_correct", 0)),
            advice_ok=int(request.form.get("advice_ok", 0)),
            comments=request.form.get("comments", "").strip(),
            created_at=datetime.utcnow()
        )
        db.session.add(new_feedback)
        db.session.commit()

        log_event(
            "feedback_submit",
            user=session.get("username"),
            data={
                "emotion": new_feedback.emotion,
                "predicted_correct": new_feedback.predicted_correct,
                "advice_ok": new_feedback.advice_ok,
            }
        )
        return "<p class='muted success'>Thank you for your feedback!</p>"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"DB insert failed: {e}")
=======
    username = session.get("username")
    form_data = {
        "emotion": request.form.get("emotion"),
        "prompt": request.form.get("prompt"),
        "image_url": request.form.get("image_url"),
        "advice": request.form.get("advice"),
        "predicted_correct": int(request.form.get("predicted_correct", 0)),
        "advice_ok": int(request.form.get("advice_ok", 0)),
        "comments": request.form.get("comments", "").strip(),
        "created_at": datetime.now().isoformat()
    }

    log_event(
        "feedback_submit",
        user=username,
        data={
            "emotion": form_data["emotion"],
            "predicted_correct": form_data["predicted_correct"],
            "advice_ok": form_data["advice_ok"],
        }
    )

    # MODIFIED SECTION: Using Supabase instead of SQLite
    try:
        # Get a connection to the Supabase database
        conn = get_supabase_db()
        cur = conn.cursor()
        # Execute the INSERT command on Supabase
        cur.execute(
            """
            INSERT INTO feedback (username, emotion, prompt, image_url, advice,
                                  predicted_correct, advice_ok, comments, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (username, form_data["emotion"], form_data["prompt"], form_data["image_url"],
             form_data["advice"], form_data["predicted_correct"], form_data["advice_ok"],
             form_data["comments"], form_data["created_at"])
        )
        conn.commit()
        cur.close()
        conn.close() # Close the Supabase connection
    except Exception as e:
        current_app.logger.error(f"Supabase DB insert failed: {e}")
>>>>>>> 07fab75bfb58c355c4d78f7afa95984138d98e83
        return "<p class='error'>Sorry, there was a problem saving your feedback.</p>"


# ------------------------------
# Admin Login and Reset
# ------------------------------

@bp.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    """Handles admin login."""
    if request.method == "POST":
        password = request.form.get("password")
        if verify_credentials(ADMIN_USERNAME, password):
            session["username"] = ADMIN_USERNAME
            log_event("admin_login_success", user=ADMIN_USERNAME)
            return redirect(url_for("main.admin_dashboard"))
        else:
            log_event("admin_login_fail", user=ADMIN_USERNAME)
            return render_template("admin_login.html", admin_username=ADMIN_USERNAME, error="Invalid password.")
    return render_template("admin_login.html", admin_username=ADMIN_USERNAME)


@bp.route("/admin-reset", methods=["GET", "POST"])
def admin_reset():
    """Handles the admin password reset functionality using the database."""
    if 'username' in session and session.get('username') != ADMIN_USERNAME:
        return redirect(url_for('main.home'))

    if request.method == "POST":
        code = request.form.get("code")
        pw1 = request.form.get("pw1")
        pw2 = request.form.get("pw2")
        reset_code_env = current_app.config.get("ADMIN_RESET_CODE")

        if not reset_code_env:
            return render_template("admin_reset.html", error="Password reset feature is not configured.")
        if not code or code != reset_code_env:
            log_event("admin_password_reset_fail", data={"reason": "invalid_code"})
            return render_template("admin_reset.html", error="Invalid reset code.")
        if not pw1 or not pw2 or pw1 != pw2:
            return render_template("admin_reset.html", error="Passwords do not match or are empty.")

        try:
            admin_user = get_user(ADMIN_USERNAME)
            if admin_user:
                admin_user.set_password(pw1)
                db.session.commit()
                log_event("admin_password_reset", user=ADMIN_USERNAME)
                return render_template("admin_reset.html", msg="Password has been reset successfully.")
            else:
                return render_template("admin_reset.html", error="Admin user not found in the database.")
        except Exception as e:
            db.session.rollback()
            log_event("admin_password_reset_fail", user=ADMIN_USERNAME, data={"error": str(e)})
            return render_template("admin_reset.html", error="An error occurred during password reset.")

    return render_template("admin_reset.html")


# ------------------------------
# Admin Pages (Refactored for SQLAlchemy)
# ------------------------------

@bp.route("/admin")
@admin_required
def admin():
    """Main admin page, redirects to the dashboard."""
    return redirect(url_for("main.admin_dashboard"))


@bp.route("/admin/feedback")
@admin_required
def admin_feedback():
    """Displays all user feedback with charts and data."""
<<<<<<< HEAD
    feedback_data = Feedback.query.order_by(Feedback.created_at.desc()).all()
=======
    # NOTE: This still uses the local SQLite DB for reading.
    # You might want to change this to get_supabase_db() later for consistency.
    db = get_db()
    feedback_rows = db.execute("SELECT * FROM feedback ORDER BY created_at DESC").fetchall()

    feedback_data = []
    for row in feedback_rows:
        processed_row = dict(row)
        if processed_row.get('created_at'):
            processed_row['created_at'] = datetime.fromisoformat(processed_row['created_at'])
        feedback_data.append(processed_row)
>>>>>>> 07fab75bfb58c355c4d78f7afa95984138d98e83

    # Chart data aggregation
    emotion_counts = db.session.query(Feedback.emotion, func.count(Feedback.id)).group_by(Feedback.emotion).all()
    mood_yes = Feedback.query.filter_by(predicted_correct=1).count()
    mood_no = Feedback.query.filter_by(predicted_correct=0).count()
    advice_yes = Feedback.query.filter_by(advice_ok=1).count()
    advice_no = Feedback.query.filter_by(advice_ok=0).count()

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_activity_raw = db.session.query(func.date(Feedback.created_at).label('activity_date'),
                                          func.count(Feedback.id).label('count')) \
        .filter(Feedback.created_at >= seven_days_ago) \
        .group_by('activity_date') \
        .order_by('activity_date').all()

    emotion_data = {'labels': [e[0].capitalize() for e in emotion_counts], 'values': [e[1] for e in emotion_counts]}
    rating_data = {'mood_yes': mood_yes, 'mood_no': mood_no, 'advice_yes': advice_yes, 'advice_no': advice_no}

    # --- DATE FORMAT CHANGE (YMD to DMY) ---
    # Create a list of the last 7 dates as date objects for the activity chart
    date_objects = [(datetime.utcnow().date() - timedelta(days=i)) for i in range(6, -1, -1)]

    # Initialize counts for each date
    activity_counts = {d: 0 for d in date_objects}

    # Populate counts from the database query result
    for activity in daily_activity_raw:
        if activity.activity_date in activity_counts:
            activity_counts[activity.activity_date] = activity.count

    # Create labels in DD/MM format and their corresponding values
    activity_data = {
        'labels': [d.strftime('%d/%m') for d in date_objects],
        'values': [activity_counts[d] for d in date_objects]
    }

    return render_template(
        "admin_feedback.html",
        feedback_data=feedback_data,
        emotion_data=emotion_data,
        rating_data=rating_data,
        activity_data=activity_data
    )


@bp.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Displays the main admin dashboard with stats and activity lists."""
    stats = get_dashboard_stats()
    recent_activities = get_recent_activities()
    user_activities = get_user_activities()
    return render_template(
        "admin_dashboard.html",
        total_users=stats['total_users'],
        total_images=stats['total_images'],
        total_feedback=stats['total_feedback'],
        active_sessions=stats['active_sessions'],
        recent_activities=recent_activities,
        user_activities=user_activities
    )


@bp.route("/admin/logs")
@admin_required
def admin_logs():
    """Displays system logs with filtering and chart visualizations."""
    query = Log.query

    filter_event = request.args.get('event', '')
    filter_user = request.args.get('user', '')
    filter_start = request.args.get('start', '')
    filter_end = request.args.get('end', '')
    limit_rows = int(request.args.get('rows', 500))

    if filter_event:
        query = query.filter(Log.event.ilike(f"%{filter_event}%"))
    if filter_user:
        query = query.filter(Log.username.ilike(f"%{filter_user}%"))
    if filter_start:
        query = query.filter(Log.timestamp >= filter_start)
    if filter_end:
        query = query.filter(Log.timestamp <= filter_end)

    log_rows = query.order_by(Log.timestamp.desc()).limit(limit_rows).all()

    return render_template(
        "logs.html",
        rows=log_rows,
        applied_filters=request.args
    )


@bp.route("/admin/user/<username>")
@admin_required
def admin_view_user(username):
    """Displays a detailed view of a single user's activity."""
    user = get_user(username)
    if not user:
        flash(f"User '{username}' not found.", "error")
        return redirect(url_for("main.admin_dashboard"))

    feedback = Feedback.query.filter_by(username=username).order_by(Feedback.created_at.desc()).all()
    logs = Log.query.filter_by(username=username).order_by(Log.timestamp.desc()).all()
    last_login_log = Log.query.filter_by(username=username, event='login_success').order_by(
        Log.timestamp.desc()).first()

    user_data = {
        "username": username,
        "feedback_count": len(feedback),
        "log_count": len(logs),
        "last_login": last_login_log.timestamp if last_login_log else None,
        "feedback": feedback,
        "logs": logs
    }
    return render_template("admin_user_view.html", user_data=user_data)


@bp.route("/admin/user/delete/<username>", methods=["POST"])
@admin_required
def admin_delete_user(username):
    """Deletes a user and all their associated data."""
    if username.lower() == ADMIN_USERNAME:
        flash(f"Failed to delete user '{username}'. Admins cannot be deleted.", "error")
        return redirect(url_for("main.admin_dashboard"))

    try:
        # Delete associated data first
        Feedback.query.filter_by(username=username).delete()
        Log.query.filter_by(username=username).delete()

        # Now delete the user
        if delete_user(username):
            log_event("user_deleted", user=session.get("username"), data={"deleted_user": username})
            flash(f"User '{username}' and all their data have been successfully deleted.", "success")
        else:
            flash(f"Could not find user '{username}' to delete.", "error")

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user {username}: {e}")
        flash(f"An error occurred while deleting user '{username}'.", "error")

    return redirect(url_for("main.admin_dashboard"))


def get_setting(key):
<<<<<<< HEAD
    """Fetches a setting value from the database."""
    setting = Settings.query.get(key)
    return setting.value if setting else None


def set_setting(key, value):
    """Saves a setting value to the database (upsert)."""
    setting = Settings.query.get(key)
    if setting:
        setting.value = value
    else:
        setting = Settings(key=key, value=value)
        db.session.add(setting)
    db.session.commit()
=======
    """Fetches a setting value from the database (SQLite or Postgres)."""
    db = get_db()
    if is_sqlite(db):
        row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    else:
        row = db.execute("SELECT value FROM settings WHERE key = %s", (key,)).fetchone()
    return row['value'] if row else None


def set_setting(key, value):
    """Saves a setting value to the database (SQLite or Postgres)."""
    db = get_db()
    if is_sqlite(db):
        db.execute("""
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """, (key, value))
    else:
        db.execute("""
            INSERT INTO settings (key, value)
            VALUES (%s, %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """, (key, value))
    db.commit()
>>>>>>> 07fab75bfb58c355c4d78f7afa95984138d98e83


@bp.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    """Admin settings page to manage API keys and other configurations."""
    success_message = None
    if request.method == "POST":
        new_api_key = request.form.get("api_key", "").strip()
        set_setting("CLIPDROP_API_KEY", new_api_key)
        log_event("settings_update", user=session.get("username"), data={"setting": "CLIPDROP_API_KEY"})
        success_message = "Settings have been saved successfully!"

    current_api_key = get_setting("CLIPDROP_API_KEY")
    return render_template(
        "admin_settings.html",
        clipdrop_api_key=current_api_key,
        success_message=success_message
    )


@bp.route('/admin/export/<export_format>', methods=["GET"])
@admin_required
def export_data(export_format):
    """Handles exporting feedback data to CSV or Excel."""
    emotion_filter = request.args.get('emotion')
    query = Feedback.query
    if emotion_filter:
        query = query.filter_by(emotion=emotion_filter)

    df = pd.read_sql(query.statement, db.engine)

    # --- DATE FORMAT CHANGE (YMD to DMY) ---
    # Format the 'created_at' column to DD/MM/YYYY HH:MM:SS for the export
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%d/%m/%Y %H:%M:%S')

    if export_format == 'csv':
        return Response(df.to_csv(index=False), mimetype='text/csv',
                        headers={'Content-Disposition': 'attachment;filename=mood_app_data.csv'})
    elif export_format == 'excel':
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Feedback')
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name='mood_app_data.xlsx')

    return "Invalid format", 400

