# app/routes.py
import os
import io
import json
import csv
import datetime as dt
from collections import Counter
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import requests

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, send_file, current_app, Response
)
from werkzeug.security import generate_password_hash

from .utils import get_db, login_required, admin_required
from .mood_detector import EMOTIONS, advice_for
from .image_generator import build_image_url
from .logger import log_event
from .models.user import verify_credentials, ADMIN_USERNAME, refresh_users_cache
from urllib.parse import quote_plus, urlparse

bp = Blueprint("main", __name__)

# Hosts we are willing to proxy images from (prevents open proxy abuse)
ALLOWED_IMAGE_HOSTS = {"image.pollinations.ai"}


# ------------------------------
# Dashboard Helper Functions
# ------------------------------
def get_dashboard_stats():
    """Get statistics for the admin dashboard"""
    db = get_db()

    # Total users (excluding admin)
    total_users = db.execute(
        "SELECT COUNT(DISTINCT username) FROM feedback WHERE username != 'admin'"
    ).fetchone()[0] or 0

    # Total images generated (approximate)
    total_images = db.execute(
        "SELECT COUNT(*) FROM feedback WHERE image_url IS NOT NULL"
    ).fetchone()[0] or 0

    # Total feedback submissions
    total_feedback = db.execute("SELECT COUNT(*) FROM feedback").fetchone()[0] or 0

    # Active sessions (last 30 minutes) - fallback if session_log doesn't exist
    try:
        active_sessions = db.execute(
            "SELECT COUNT(DISTINCT user) FROM session_log WHERE ts > datetime('now', '-30 minutes')"
        ).fetchone()[0] or 0
    except:
        active_sessions = 0  # Fallback if table doesn't exist

    return {
        'total_users': total_users,
        'total_images': total_images,
        'total_feedback': total_feedback,
        'active_sessions': active_sessions
    }


def get_recent_activities():
    """Get recent user activities, converting date strings to datetime objects."""
    db = get_db()
    processed_activities = []
    try:
        activities = db.execute("""
            SELECT username, created_at as date, 'Feedback submitted' as action, 'submitted' as status
            FROM feedback
            WHERE username != 'admin'
            ORDER BY created_at DESC
            LIMIT 10
        """).fetchall()

        for activity in activities:
            activity_dict = dict(activity)
            # **FIX**: Parse the date string into a datetime object
            if activity_dict.get('date'):
                activity_dict['date'] = datetime.fromisoformat(activity_dict['date'])
            processed_activities.append(activity_dict)

    except Exception as e:
        current_app.logger.error(f"Error fetching recent activities: {e}")
        # Return an empty list on error
        return []

    return processed_activities


def get_user_activities():
    """Get user activity data, converting timestamp strings to datetime objects."""
    db = get_db()
    processed_users = []
    try:
        # Try fetching from session_log first
        users = db.execute("""
            SELECT username, MAX(ts) as last_login,
                   CASE WHEN MAX(ts) > datetime('now', '-7 days') THEN 1 ELSE 0 END as active
            FROM session_log
            WHERE user != 'admin' AND event = 'login_success'
            GROUP BY username
            ORDER BY last_login DESC
        """).fetchall()
    except:
        # Fallback to feedback table if session_log fails or doesn't exist
        users = db.execute("""
            SELECT username, MAX(created_at) as last_login,
                   CASE WHEN MAX(created_at) > datetime('now', '-7 days') THEN 1 ELSE 0 END as active
            FROM feedback
            WHERE username != 'admin'
            GROUP BY username
            ORDER BY last_login DESC
        """).fetchall()

    for user in users:
        user_dict = dict(user)
        # **FIX**: Parse the last_login string into a datetime object
        if user_dict.get('last_login'):
            try:
                # Handle timestamps that might have timezone info or different formats
                user_dict['last_login'] = datetime.fromisoformat(user_dict['last_login'].replace('Z', '+00:00'))
            except ValueError:
                # Fallback for other common formats, like 'YYYY-MM-DD HH:MM:SS'
                user_dict['last_login'] = datetime.strptime(user_dict['last_login'], '%Y-%m-%d %H:%M:%S')
        processed_users.append(user_dict)

    return processed_users


# ------------------------------
# Landing (Admin / Users chooser)
# ------------------------------
@bp.route("/", methods=["GET"])
def entry():
    # If already logged in, go to app
    if session.get("username"):
        return redirect(url_for("main.home"))
    return render_template("entry.html")


# ------------------------------
# Users login (demo users only)
# ------------------------------
@bp.route("/login", methods=["GET"])
def login_page():
    # Admin is not exposed here; use /admin-login for admin
    return render_template("login.html")


@bp.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    # Accept either 'password' or 'password_select' field
    password = request.form.get("password") or request.form.get("password_select")

    if verify_credentials(username, password):
        session["username"] = username
        log_event("login_success", user=username)
        return redirect(url_for("main.home"))
    else:
        log_event("login_fail", user=username)
        return render_template("login.html", error="Invalid username or password.")


@bp.route("/logout", methods=["GET"])
def logout():
    user = session.pop("username", "(unknown)")
    log_event("logout", user=user)
    return redirect(url_for("main.entry"))


# ------------------------------
# Admin Login
# ------------------------------
@bp.route("/admin-login", methods=["GET"])
def admin_login_page():
    return render_template("admin_login.html", admin_username=ADMIN_USERNAME)


@bp.route("/admin-login", methods=["POST"])
def admin_login():
    password = request.form.get("password")

    if verify_credentials(ADMIN_USERNAME, password):
        session["username"] = ADMIN_USERNAME
        log_event("admin_login_success", user=ADMIN_USERNAME)
        return redirect(url_for("main.admin_dashboard"))
    else:
        log_event("admin_login_fail", user=ADMIN_USERNAME)
        return render_template("admin_login.html", admin_username=ADMIN_USERNAME, error="Invalid password.")


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

        if not pw1 or not pw2:
            return render_template("admin_reset.html", error="Both password fields are required.")

        if pw1 != pw2:
            return render_template("admin_reset.html", error="New passwords do not match.")

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
            return render_template("admin_reset.html", error="An error occurred while saving the new password.")

    return render_template("admin_reset.html")


# ------------------------------
# Core app (image generation)
# ------------------------------
@bp.route("/home", methods=["GET"])
@login_required
def home():
    return render_template("home.html", emotions=EMOTIONS)


@bp.route("/generate", methods=["POST"])
@login_required
def generate():
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


# ------------------------------
# Feedback form submission
# ------------------------------
@bp.route("/feedback", methods=["POST"])
@login_required
def feedback():
    emotion = request.form.get("emotion")
    prompt = request.form.get("prompt")
    image_url = request.form.get("image_url")
    advice = request.form.get("advice")
    predicted_correct = int(request.form.get("predicted_correct", 0))
    advice_ok = int(request.form.get("advice_ok", 0))
    comments = request.form.get("comments", "").strip()
    username = session.get("username")

    log_event(
        "feedback_submit",
        user=username,
        data={
            "emotion": emotion,
            "predicted_correct": predicted_correct,
            "advice_ok": advice_ok,
        }
    )

    try:
        db = get_db()
        db.execute(
            """
            INSERT INTO feedback (username, emotion, prompt, image_url, advice,
                                  predicted_correct, advice_ok, comments, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username, emotion, prompt, image_url, advice,
                predicted_correct, advice_ok, comments,
                dt.datetime.now().isoformat()  # Use ISO format for consistency
            )
        )
        db.commit()
    except Exception as e:
        current_app.logger.error(f"DB insert failed: {e}")
        return "<p class='error'>Sorry, there was a problem saving your feedback.</p>"

    return "<p class='muted success'>Thank you for your feedback!</p>"


# ------------------------------
# Admin pages
# ------------------------------
@bp.route("/admin", methods=["GET"])
@admin_required
def admin():
    """Feedback management page with date conversion fix."""
    db = get_db()

    # Get all feedback data from the database
    feedback_rows = db.execute("""
        SELECT username, emotion, prompt, advice, predicted_correct, 
               advice_ok, comments, created_at
        FROM feedback 
        ORDER BY created_at DESC
    """).fetchall()

    # --- FIX START ---
    # Process the feedback data to convert date strings into datetime objects
    # before sending them to the template.
    feedback_data = []
    for row in feedback_rows:
        processed_row = dict(row)  # Convert row to a mutable dictionary
        if processed_row.get('created_at'):
            processed_row['created_at'] = datetime.fromisoformat(processed_row['created_at'])
        feedback_data.append(processed_row)
    # --- FIX END ---

    # The rest of the function remains the same
    emotion_counts = db.execute("""
        SELECT emotion, COUNT(*) as count 
        FROM feedback 
        WHERE emotion IS NOT NULL 
        GROUP BY emotion
    """).fetchall()

    mood_yes = db.execute("SELECT COUNT(*) FROM feedback WHERE predicted_correct = 1").fetchone()[0] or 0
    mood_no = db.execute("SELECT COUNT(*) FROM feedback WHERE predicted_correct = 0").fetchone()[0] or 0
    advice_yes = db.execute("SELECT COUNT(*) FROM feedback WHERE advice_ok = 1").fetchone()[0] or 0
    advice_no = db.execute("SELECT COUNT(*) FROM feedback WHERE advice_ok = 0").fetchone()[0] or 0

    daily_activity = db.execute("""
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM feedback 
        WHERE created_at >= date('now', '-7 days')
        GROUP BY DATE(created_at)
        ORDER BY date
    """).fetchall()

    emotion_data = {
        'labels': [e['emotion'].capitalize() for e in emotion_counts],
        'values': [e['count'] for e in emotion_counts]
    }
    rating_data = {
        'mood_yes': mood_yes,
        'mood_no': mood_no,
        'advice_yes': advice_yes,
        'advice_no': advice_no
    }

    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    activity_counts = {d: 0 for d in dates}
    for activity in daily_activity:
        activity_counts[activity['date']] = activity['count']

    activity_data = {
        'labels': [datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m') for d in dates],
        'values': [activity_counts[d] for d in dates]
    }

    return render_template(
        "admin_feedback.html",
        feedback_data=feedback_data,  # Pass the newly processed data
        emotion_data=emotion_data,
        rating_data=rating_data,
        activity_data=activity_data
    )


@bp.route("/admin/dashboard", methods=["GET"])
@admin_required
def admin_dashboard():
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


@bp.route("/admin/logs", methods=["GET"])
@admin_required
def admin_logs():
    return render_template("logs.html")


@bp.route("/admin/export/csv", methods=["POST"])
@admin_required
def export_feedback_csv():
    db = get_db()
    rows = db.execute("SELECT * FROM feedback ORDER BY created_at DESC").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    if rows:
        writer.writerow(rows[0].keys())
        for row in rows:
            writer.writerow(row)
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=feedback.csv"}
    )


@bp.route("/admin/seed/users", methods=["POST"])
@admin_required
def admin_seed_users():
    return redirect(url_for("main.admin"))


@bp.route('/admin/export/<export_format>', methods=["GET"])
@admin_required
def export_data(export_format):
    db = get_db()
    emotion_filter = request.args.get('emotion')
    query = "SELECT * FROM feedback"
    if emotion_filter:
        query += f" WHERE emotion = '{emotion_filter}'"

    df = pd.read_sql(query, db)

    if export_format == 'csv':
        return Response(
            df.to_csv(index=False),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment;filename=mood_app_data.csv'}
        )
    elif export_format == 'excel':
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Feedback')
            summary_data = [{'Emotion': emotion, 'Count': count} for emotion, count in Counter(df['emotion']).items()]
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, index=False, sheet_name='Summary')
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='mood_app_data.xlsx'
        )
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
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='mood_app_data.pdf'
        )
    return "Invalid format", 400