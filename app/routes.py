import os, json, csv, math
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, send_file
from werkzeug.security import check_password_hash
import io, csv

from .utils import get_db, login_required, admin_required
from .mood_detector import EMOTIONS, advice_for
from .image_generator import build_image_url
from .logger import log_event
from models.user import USERS, ADMIN_USERNAME

bp = Blueprint("main", __name__)

# ---------- Auth ----------
@bp.get("/login")
def login_page():
    return render_template("login.html", admin_username=ADMIN_USERNAME)

@bp.post("/login")
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if username in USERS and check_password_hash(USERS[username], password):
        session["username"] = username
        log_event("login_success", user=username)
        return redirect(url_for("main.home"))
    log_event("login_fail", user=username)
    return render_template("login.html", admin_username=ADMIN_USERNAME, error="Invalid credentials")

@bp.get("/logout")
def logout():
    user = session.get("username")
    session.clear()
    log_event("logout", user=user)
    return redirect(url_for("main.login_page"))

# ---------- Main ----------
@bp.get("/")
@login_required
def home():
    return render_template("home.html", emotions=EMOTIONS, admin_username=ADMIN_USERNAME)

# HTMX endpoint to generate (returns partial)
@bp.post("/generate")
@login_required
def generate():
    emotion = request.form.get("emotion", "").lower()
    prompt = (request.form.get("prompt", "") or f"{emotion} abstract scene").strip()
    if emotion not in EMOTIONS:
        log_event("generate_invalid_emotion", user=session["username"], data={"emotion": emotion})
        return render_template("_result_card.html", error="Please choose a valid emotion.")
    image_url = build_image_url(prompt, emotion)
    advice = advice_for(emotion)
    log_event("generate", user=session["username"], data={"emotion": emotion, "prompt": prompt})
    return render_template("_result_card.html", emotion=emotion, prompt=prompt, image_url=image_url, advice=advice)

# store feedback from the partial form (HTMX)
@bp.post("/feedback")
@login_required
def feedback():
    username = session["username"]
    data = {
        "emotion": request.form.get("emotion",""),
        "prompt": request.form.get("prompt",""),
        "image_url": request.form.get("image_url",""),
        "advice": request.form.get("advice",""),
        "predicted_correct": 1 if request.form.get("predicted_correct") == "1" else 0,
        "advice_ok": 1 if request.form.get("advice_ok") == "1" else 0,
        "comments": request.form.get("comments","").strip(),
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO feedback (username, emotion, prompt, image_url, advice, predicted_correct, advice_ok, comments, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, data["emotion"], data["prompt"], data["image_url"], data["advice"],
          data["predicted_correct"], data["advice_ok"], data["comments"], data["created_at"]))
    conn.commit()
    conn.close()

    log_event("feedback_submit", user=username, data={
        "emotion": data["emotion"],
        "predicted_correct": data["predicted_correct"],
        "advice_ok": data["advice_ok"]
    })

    # Replace the result card with a thank-you via HTMX
    return render_template("_result_card.html", saved=True)

# ---------- Admin ----------
@bp.get("/admin")
@login_required
@admin_required
def admin():
    conn = get_db()
    rows = conn.cursor().execute("SELECT * FROM feedback ORDER BY id DESC").fetchall()
    conn.close()
    log_event("admin_view_feedback", user=session["username"], data={"count": len(rows)})
    return render_template("admin.html", rows=rows, admin_username=ADMIN_USERNAME)

@bp.get("/export")
@login_required
@admin_required
def export_feedback():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, created_at, username, emotion, prompt, image_url, advice, predicted_correct, advice_ok, comments
        FROM feedback ORDER BY id ASC
    """)
    data = cur.fetchall()
    conn.close()

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["id","created_at","username","emotion","prompt","image_url","advice","matched","advice_ok","comments"])
    for row in data:
        writer.writerow(row)
    mem = io.BytesIO(out.getvalue().encode("utf-8"))

    log_event("admin_export_csv", user=session["username"], data={"rows": len(data)})
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="feedback.csv")


# ---------- Admin: Log Viewer ----------
def _read_jsonl(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                rows.append({
                    "ts": obj.get("ts",""),
                    "event": obj.get("event",""),
                    "user": obj.get("user",""),
                    "data": json.dumps(obj.get("data",{}), ensure_ascii=False)
                })
            except Exception:
                continue
    return rows

def _read_csv(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "ts": r.get("ts",""),
                "event": r.get("event",""),
                "user": r.get("user",""),
                "data": r.get("data_json","")
            })
    return rows

@bp.get("/admin/logs")
@login_required
@admin_required
def admin_logs():
    page = max(int(request.args.get("page", 1)), 1)
    source = (request.args.get("source","auto") or "auto").lower()
    event_filter = (request.args.get("event","") or "").strip().lower()

    # Resolve source
    jsonl_path = current_app.config["LOG_JSONL_PATH"]
    csv_path = current_app.config["LOG_CSV_PATH"]

    rows = []
    chosen = source
    if source == "jsonl":
        rows = _read_jsonl(jsonl_path)
    elif source == "csv":
        rows = _read_csv(csv_path)
    else:
        # auto: prefer JSONL if exists, else CSV
        if os.path.exists(jsonl_path):
            rows = _read_jsonl(jsonl_path)
            chosen = "jsonl"
        else:
            rows = _read_csv(csv_path)
            chosen = "csv"

    # Latest first
    rows = list(reversed(rows))

    # Filter by event type
    if event_filter:
        rows = [r for r in rows if r["event"].lower().find(event_filter) != -1]

    # Pagination
    page_size = int(current_app.config.get("LOG_VIEW_PAGE_SIZE", 25))
    total = len(rows)
    pages = max(math.ceil(total / page_size), 1)
    start = (page - 1) * page_size
    end = start + page_size
    page_rows = rows[start:end]

    return render_template(
        "logs.html",
        rows=page_rows,
        page=page,
        pages=pages,
        total=total,
        source=chosen,
        event=event_filter
    )

@bp.get("/admin/logs/download")
@login_required
@admin_required
def admin_logs_download():
    src = (request.args.get("source","jsonl") or "jsonl").lower()
    path = current_app.config["LOG_JSONL_PATH"] if src == "jsonl" else current_app.config["LOG_CSV_PATH"]

    if not os.path.exists(path):
        # Return an empty file with proper name
        from flask import Response
        return Response("", mimetype="text/plain", headers={
            "Content-Disposition": f'attachment; filename="{os.path.basename(path)}"'
        })

    from flask import send_file
    return send_file(path, as_attachment=True, download_name=os.path.basename(path))
