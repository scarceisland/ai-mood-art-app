import csv
import io
import os
from collections import Counter
from datetime import datetime, timedelta
from io import BytesIO

import pandas as pd
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, send_file, current_app, Response, flash
)
from werkzeug.security import generate_password_hash

from .image_generator import build_image_url
from .logger import log_event
from .models.user import verify_credentials, ADMIN_USERNAME, refresh_users_cache, delete_user_data
from .mood_detector import EMOTIONS, advice_for
from .utils import get_db, login_required, admin_required

bp = Blueprint("main", __name__)


# ------------------------------
# Dashboard Helper Functions
# ------------------------------
def get_dashboard_stats():
    """Get statistics for the admin dashboard."""
    db = get_db()
    total_users = db.execute("SELECT COUNT(DISTINCT username) FROM feedback WHERE username != 'admin'").fetchone()[0] or 0
    total_images = db.execute("SELECT COUNT(*) FROM feedback WHERE image_url IS NOT NULL").fetchone()[0] or 0
    total_feedback = db.execute("SELECT COUNT(*) FROM feedback").fetchone()[0] or 0
    try:
        active_sessions = db.execute("SELECT COUNT(DISTINCT username) FROM logs WHERE timestamp > NOW() - INTERVAL '30 minutes'").fetchone()[0] or 0
    except Exception:
        active_sessions = 0
    return {'total_users': total_users, 'total_images': total_images, 'total_feedback': total_feedback, 'active_sessions': active_sessions}


def get_recent_activities():
    """Get recent user activities."""
    db = get_db()
    processed_activities = []
    try:
        activities = db.execute("""
            SELECT username, created_at as date, 'Feedback submitted' as action, 'submitted' as status
            FROM feedback WHERE username != 'admin' ORDER BY created_at DESC LIMIT 10
        """).fetchall()
        for activity in activities:
            activity_dict = dict(activity)
            if activity_dict.get('date'):
                activity_dict['date'] = datetime.fromisoformat(activity_dict['date'])
            processed_activities.append(activity_dict)
    except Exception as e:
        current_app.logger.error(f"Error fetching recent activities: {e}")
    return processed_activities


def get_user_activities():
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
                   CASE WHEN MAX(created_at) > NOW() - INTERVAL '7 days' THEN 1 ELSE 0 END as active
            FROM feedback WHERE username != 'admin' GROUP BY username ORDER BY last_login DESC
        """).fetchall()

    for user in users:
        user_dict = dict(user)
        if user_dict.get('last_login'):
            try:
                user_dict['last_login'] = datetime.fromisoformat(user_dict['last_login'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                # Fallback for other common formats
                try:
                    user_dict['last_login'] = datetime.strptime(user_dict['last_login'], '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    user_dict['last_login'] = None  # In case of parsing failure
        processed_users.append(user_dict)
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

    try:
        db = get_db()
        db.execute(
            """
            INSERT INTO feedback (username, emotion, prompt, image_url, advice,
                                  predicted_correct, advice_ok, comments, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (username, form_data["emotion"], form_data["prompt"], form_data["image_url"],
             form_data["advice"], form_data["predicted_correct"], form_data["advice_ok"],
             form_data["comments"], form_data["created_at"])
        )
        db.commit()
    except Exception as e:
        current_app.logger.error(f"DB insert failed: {e}")
        return "<p class='error'>Sorry, there was a problem saving your feedback.</p>"

    return "<p class='muted success'>Thank you for your feedback!</p>"


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
    """Handles the admin password reset functionality."""
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
            project_root = os.path.abspath(os.path.join(current_app.root_path, ".."))
            hash_file_path = os.path.join(project_root, "admin_pwd.hash")
            new_hash = generate_password_hash(pw1)
            with open(hash_file_path, "w", encoding="utf-8") as f:
                f.write(new_hash)

            refresh_users_cache()
            log_event("admin_password_reset", user=ADMIN_USERNAME)
            return render_template("admin_reset.html", msg="Password has been reset successfully.")
        except Exception as e:
            log_event("admin_password_reset_fail", user=ADMIN_USERNAME, data={"error": str(e)})
            return render_template("admin_reset.html", error="An error occurred.")

    return render_template("admin_reset.html")


# ------------------------------
# Admin Pages
# ------------------------------

@bp.route("/admin")
@admin_required
def admin():
    """Main admin page, redirects to the feedback view."""
    return redirect(url_for("main.admin_feedback"))


@bp.route("/admin/feedback")
@admin_required
def admin_feedback():
    """Displays all user feedback with charts and data."""
    db = get_db()
    feedback_rows = db.execute("SELECT * FROM feedback ORDER BY created_at DESC").fetchall()

    feedback_data = []
    for row in feedback_rows:
        processed_row = dict(row)
        if processed_row.get('created_at'):
            processed_row['created_at'] = datetime.fromisoformat(processed_row['created_at'])
        feedback_data.append(processed_row)

    # Chart data aggregation
    emotion_counts = db.execute("SELECT emotion, COUNT(*) as count FROM feedback WHERE emotion IS NOT NULL GROUP BY emotion").fetchall()
    mood_yes = db.execute("SELECT COUNT(*) FROM feedback WHERE predicted_correct = 1").fetchone()[0] or 0
    mood_no = db.execute("SELECT COUNT(*) FROM feedback WHERE predicted_correct = 0").fetchone()[0] or 0
    advice_yes = db.execute("SELECT COUNT(*) FROM feedback WHERE advice_ok = 1").fetchone()[0] or 0
    advice_no = db.execute("SELECT COUNT(*) FROM feedback WHERE advice_ok = 0").fetchone()[0] or 0
    daily_activity = db.execute("SELECT DATE(created_at) as date, COUNT(*) as count FROM feedback WHERE created_at >= CURRENT_DATE - INTERVAL '7 days' GROUP BY DATE(created_at) ORDER BY date").fetchall()

    emotion_data = {'labels': [e['emotion'].capitalize() for e in emotion_counts], 'values': [e['count'] for e in emotion_counts]}
    rating_data = {'mood_yes': mood_yes, 'mood_no': mood_no, 'advice_yes': advice_yes, 'advice_no': advice_no}
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    activity_counts = {d: 0 for d in dates}
    for activity in daily_activity:
        activity_counts[activity['date']] = activity['count']
    activity_data = {'labels': [datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m') for d in dates], 'values': [activity_counts[d] for d in dates]}

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
    filter_event = request.args.get('event', '')
    filter_user = request.args.get('user', '')
    filter_source = request.args.get('source', '')
    filter_start = request.args.get('start', '')
    filter_end = request.args.get('end', '')
    limit_rows = int(request.args.get('rows', 500))

    applied_filters = {
        'event': filter_event, 'user': filter_user, 'source': filter_source,
        'start': filter_start, 'end': filter_end, 'rows': limit_rows
    }

    query = "SELECT * FROM logs WHERE 1=1"
    params = []

    if filter_event:
        query += " AND event LIKE %s"
        params.append(f"%{filter_event}%")
    if filter_user:
        query += " AND username LIKE %s"
        params.append(f"%{filter_user}%")
    if filter_source:
        query += " AND source LIKE %s"
        params.append(f"%{filter_source}%")
    if filter_start:
        query += " AND (timestamp >= %s OR created_at >= %s)"
        params.extend([filter_start, filter_start])
    if filter_end:
        query += " AND (timestamp <= %s OR created_at <= %s)"
        params.extend([filter_end, filter_end])

    query += " ORDER BY COALESCE(created_at, timestamp) DESC LIMIT %s"
    params.append(limit_rows)

    db = get_db()
    log_rows = db.execute(query, params).fetchall()
    logs_as_dicts = [dict(row) for row in log_rows]

    return render_template(
        "logs.html",
        rows=logs_as_dicts,
        applied_filters=applied_filters
    )


@bp.route("/admin/user/<username>")
@admin_required
def admin_view_user(username):
    """Displays a detailed view of a single user's activity."""
    db = get_db()
    feedback = db.execute("SELECT * FROM feedback WHERE username = %s ORDER BY created_at DESC", (username,)).fetchall()
    logs = db.execute("SELECT * FROM logs WHERE username = %s ORDER BY timestamp DESC", (username,)).fetchall()
    last_login_row = db.execute("SELECT MAX(timestamp) as last_login FROM logs WHERE username = %s AND event = 'login_success'", (username,)).fetchone()
    last_login = datetime.fromisoformat(last_login_row['last_login']) if last_login_row and last_login_row['last_login'] else None

    # Process rows to convert date strings into datetime objects for the template
    processed_feedback = [dict(row, created_at=datetime.fromisoformat(row['created_at'])) for row in feedback]
    processed_logs = [dict(row, timestamp=datetime.fromisoformat(row['timestamp'])) for row in logs]

    user_data = {
        "username": username,
        "feedback_count": len(processed_feedback),
        "log_count": len(processed_logs),
        "last_login": last_login,
        "feedback": processed_feedback,
        "logs": processed_logs
    }
    return render_template("admin_user_view.html", user_data=user_data)


@bp.route("/admin/user/delete/<username>", methods=["POST"])
@admin_required
def admin_delete_user(username):
    """Deletes a user and all their associated data."""
    db = get_db()
    if delete_user_data(username, db):
        log_event("user_deleted", user=session.get("username"), data={"deleted_user": username})
        flash(f"User '{username}' and all their data have been successfully deleted.", "success")
    else:
        flash(f"Failed to delete user '{username}'. Admins cannot be deleted.", "error")
    return redirect(url_for("main.admin_dashboard"))


def get_setting(key):
    """Fetches a setting value from the database."""
    db = get_db()
    row = db.execute("SELECT value FROM settings WHERE key = %s", (key,)).fetchone()
    return row['value'] if row else None


def set_setting(key, value):
    """Saves a setting value to the database."""
    db = get_db()
    # Use PostgreSQL's UPSERT functionality
    db.execute("""
        INSERT INTO settings (key, value) 
        VALUES (%s, %s)
        ON CONFLICT (key) 
        DO UPDATE SET value = EXCLUDED.value
    """, (key, value))
    db.commit()


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


# ------------------------------
# Export Routes
# ------------------------------

@bp.route('/admin/export/<export_format>', methods=["GET"])
@admin_required
def export_data(export_format):
    """Handles exporting feedback data to CSV, Excel, or PDF."""
    db = get_db()
    emotion_filter = request.args.get('emotion')
    query = "SELECT * FROM feedback"
    if emotion_filter:
        query += f" WHERE emotion = '{emotion_filter}'"

    df = pd.read_sql(query, db)

    if export_format == 'csv':
        return Response(df.to_csv(index=False), mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=mood_app_data.csv'})
    elif export_format == 'excel':
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Feedback')
            summary_df = pd.DataFrame([{'Emotion': e, 'Count': c} for e, c in Counter(df['emotion']).items()])
            summary_df.to_excel(writer, index=False, sheet_name='Summary')
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='mood_app_data.xlsx')
    elif export_format == 'pdf':
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 750, "AI Art Mood App - Data Report")
        p.drawString(100, 730, f"Emotion Filter: {emotion_filter or 'All'}")
        p.drawString(100, 710, f"Total Records: {len(df)}")
        y = 690
        for _, row in df.iterrows():
            if y < 100:
                p.showPage()
                y = 750
            p.drawString(100, y, f"{row['created_at']} - {row['emotion']} - {row['prompt'][:50]}...")
            y -= 20
        p.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name='mood_app_data.pdf')

    return "Invalid format", 400