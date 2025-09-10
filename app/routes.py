import os
from datetime import datetime, timedelta
from io import BytesIO
import pandas as pd
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, send_file, current_app, Response, flash
)
from sqlalchemy import func

from .db import db
from .image_generator import build_image_url
from .logger import log_event
from .models.user import User
from .models.app_models import Feedback, Log, Setting
from .mood_detector import EMOTIONS, advice_for
from .utils import login_required, admin_required

bp = Blueprint("main", __name__)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin").lower()


# ------------------------------
# Dashboard Helper Functions
# ------------------------------
def get_dashboard_stats():
    """Get statistics for the admin dashboard using SQLAlchemy."""
    total_users = db.session.query(func.count(User.id)).filter(User.is_admin == False).scalar() or 0
    total_images = db.session.query(func.count(Feedback.id)).filter(Feedback.image_url != None).scalar() or 0
    total_feedback = db.session.query(func.count(Feedback.id)).scalar() or 0
    thirty_minutes_ago = datetime.utcnow() - timedelta(minutes=30)
    active_sessions = db.session.query(func.count(func.distinct(Log.username))).filter(
        Log.timestamp > thirty_minutes_ago).scalar() or 0
    return {
        'total_users': total_users,
        'total_images': total_images,
        'total_feedback': total_feedback,
        'active_sessions': active_sessions
    }


def get_recent_activities():
    """Get recent user activities."""
    return Feedback.query.filter(Feedback.username != ADMIN_USERNAME).order_by(Feedback.created_at.desc()).limit(
        10).all()


def get_user_activities():
    """Get user activity data."""
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    users = User.query.filter(User.is_admin == False).all()
    user_activities = []
    for user in users:
        last_log = Log.query.filter_by(username=user.username, event='login_success').order_by(
            Log.timestamp.desc()).first()
        last_login_time = last_log.timestamp if last_log else None
        is_active = last_login_time and last_login_time > seven_days_ago
        user_activities.append({
            'username': user.username,
            'last_login': last_login_time,
            'active': is_active
        })
    # Sort by last login, descending, handling users who never logged in
    user_activities.sort(key=lambda x: x['last_login'] or datetime.min, reverse=True)
    return user_activities


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
        user = User.query.filter(func.lower(User.username) == func.lower(username)).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["username"] = user.username
            log_event("login_success", user=user.username)
            if user.is_admin:
                return redirect(url_for("main.admin_dashboard"))
            return redirect(url_for("main.home"))
        else:
            log_event("login_fail", user=username)
            flash("Invalid username or password.", "error")
            return redirect(url_for("main.login"))

    return render_template("login.html")


@bp.route("/logout")
@login_required
def logout():
    """Logs the current user out."""
    user = session.pop("username", "(unknown)")
    session.pop("user_id", None)
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

    log_event("generate", user=session.get("username"), data={"emotion": emotion, "prompt": prompt})
    api_key_setting = Setting.query.filter_by(key="CLIPDROP_API_KEY").first()
    api_key = api_key_setting.value if api_key_setting else None

    if not api_key:
        current_app.logger.error("CLIPDROP_API_KEY is not set in the database.")
        return render_template("_result_card.html",
                               error="Art generation is not configured. Please contact an administrator.")

    image_url = build_image_url(prompt, emotion, api_key)
    advice = advice_for(emotion)

    return render_template("_result_card.html", image_url=image_url, prompt=prompt, emotion=emotion, advice=advice)


@bp.route("/feedback", methods=["POST"])
@login_required
def feedback():
    """Handles user feedback submission."""
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
        log_event("feedback_submit", user=session.get("username"), data={"emotion": new_feedback.emotion})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"DB insert failed: {e}")
        return "<p class='error'>Sorry, there was a problem saving your feedback.</p>"
    return "<p class='muted success'>Thank you for your feedback!</p>"


# ------------------------------
# Admin Routes (Login is handled by the main login route)
# ------------------------------

@bp.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Displays the main admin dashboard."""
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


@bp.route("/admin/feedback")
@admin_required
def admin_feedback():
    """Displays all user feedback with charts."""
    feedback_data = Feedback.query.order_by(Feedback.created_at.desc()).all()

    # Chart data aggregation
    emotion_counts = db.session.query(Feedback.emotion, func.count(Feedback.emotion)).group_by(Feedback.emotion).all()
    mood_yes = Feedback.query.filter_by(predicted_correct=1).count()
    mood_no = Feedback.query.filter_by(predicted_correct=0).count()
    advice_yes = Feedback.query.filter_by(advice_ok=1).count()
    advice_no = Feedback.query.filter_by(advice_ok=0).count()

    seven_days_ago = datetime.utcnow().date() - timedelta(days=6)
    daily_activity = db.session.query(
        func.date(Feedback.created_at), func.count(Feedback.id)
    ).filter(
        func.date(Feedback.created_at) >= seven_days_ago
    ).group_by(
        func.date(Feedback.created_at)
    ).order_by(
        func.date(Feedback.created_at)
    ).all()

    emotion_data = {'labels': [e[0].capitalize() for e in emotion_counts], 'values': [e[1] for e in emotion_counts]}
    rating_data = {'mood_yes': mood_yes, 'mood_no': mood_no, 'advice_yes': advice_yes, 'advice_no': advice_no}

    # Prepare daily activity chart data
    dates = [(seven_days_ago + timedelta(days=i)) for i in range(7)]
    activity_counts = {d.strftime('%Y-%m-%d'): 0 for d in dates}
    for activity in daily_activity:
        activity_counts[activity[0].strftime('%Y-%m-%d')] = activity[1]

    activity_data = {
        'labels': [d.strftime('%d/%m') for d in dates],
        'values': [activity_counts[d.strftime('%Y-%m-%d')] for d in dates]
    }

    return render_template("admin_feedback.html", feedback_data=feedback_data, emotion_data=emotion_data,
                           rating_data=rating_data, activity_data=activity_data)


@bp.route("/admin/logs")
@admin_required
def admin_logs():
    """Displays system logs with filtering."""
    query = Log.query
    applied_filters = {}

    if request.args.get('event'):
        query = query.filter(Log.event.ilike(f"%{request.args.get('event')}%"))
        applied_filters['event'] = request.args.get('event')
    if request.args.get('user'):
        query = query.filter(Log.username.ilike(f"%{request.args.get('user')}%"))
        applied_filters['user'] = request.args.get('user')

    limit_rows = int(request.args.get('rows', 500))
    applied_filters['rows'] = limit_rows

    logs = query.order_by(Log.timestamp.desc()).limit(limit_rows).all()
    return render_template("logs.html", rows=logs, applied_filters=applied_filters)


@bp.route("/admin/user/<username>")
@admin_required
def admin_view_user(username):
    """Displays a detailed view of a single user's activity."""
    user = User.query.filter_by(username=username).first_or_404()
    feedback = Feedback.query.filter_by(username=username).order_by(Feedback.created_at.desc()).all()
    logs = Log.query.filter_by(username=username).order_by(Log.timestamp.desc()).all()
    last_login_log = Log.query.filter_by(username=username, event='login_success').order_by(
        Log.timestamp.desc()).first()

    user_data = {
        "username": user.username,
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
        flash("Admins cannot be deleted.", "error")
        return redirect(url_for("main.admin_dashboard"))

    user = User.query.filter_by(username=username).first()
    if user:
        try:
            Feedback.query.filter_by(username=username).delete()
            Log.query.filter_by(username=username).delete()
            db.session.delete(user)
            db.session.commit()
            log_event("user_deleted", user=session.get("username"), data={"deleted_user": username})
            flash(f"User '{username}' and all their data have been successfully deleted.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while deleting user '{username}'.", "error")
            current_app.logger.error(f"Failed to delete user {username}: {e}")
    else:
        flash(f"User '{username}' not found.", "error")

    return redirect(url_for("main.admin_dashboard"))


@bp.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    """Admin settings page to manage API keys."""
    if request.method == "POST":
        api_key_setting = Setting.query.filter_by(key="CLIPDROP_API_KEY").first()
        if not api_key_setting:
            api_key_setting = Setting(key="CLIPDROP_API_KEY")
            db.session.add(api_key_setting)

        api_key_setting.value = request.form.get("api_key", "").strip()
        db.session.commit()
        log_event("settings_update", user=session.get("username"), data={"setting": "CLIPDROP_API_KEY"})
        flash("Settings have been saved successfully!", "success")
        return redirect(url_for("main.admin_settings"))

    api_key_setting = Setting.query.filter_by(key="CLIPDROP_API_KEY").first()
    current_api_key = api_key_setting.value if api_key_setting else ""
    return render_template("admin_settings.html", clipdrop_api_key=current_api_key)


# ------------------------------
# Export Routes
# ------------------------------

@bp.route('/admin/export/<export_format>', methods=["GET"])
@admin_required
def export_data(export_format):
    """Handles exporting feedback data to CSV, Excel, or PDF."""
    query = Feedback.query
    emotion_filter = request.args.get('emotion')
    if emotion_filter:
        query = query.filter(Feedback.emotion == emotion_filter)

    feedback_list = query.all()
    if not feedback_list:
        flash("No data available for the selected filter.", "warning")
        return redirect(url_for("main.admin_feedback"))

    # Convert to list of dicts for pandas
    data_for_df = [
        {
            "id": f.id,
            "username": f.username,
            "emotion": f.emotion,
            "prompt": f.prompt,
            "image_url": f.image_url,
            "advice": f.advice,
            "predicted_correct": f.predicted_correct,
            "advice_ok": f.advice_ok,
            "comments": f.comments,
            "created_at": f.created_at.strftime('%d/%m/%Y %H:%M:%S') if f.created_at else None
        } for f in feedback_list
    ]
    df = pd.DataFrame(data_for_df)

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
    elif export_format == 'pdf':
        # PDF generation is complex and requires a library like ReportLab.
        # This is a very basic implementation.
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(72, 800, "AI Art Mood App - Data Report")
        p.drawString(72, 780, f"Emotion Filter: {emotion_filter or 'All'}")
        y = 750
        for item in data_for_df:
            if y < 100:
                p.showPage()
                y = 800
            p.drawString(72, y, f"{item['created_at']} - {item['username']} - {item['emotion']}")
            y -= 20
        p.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name='mood_app_data.pdf')

    return "Invalid format", 400

