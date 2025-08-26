import os, json, csv, datetime
from typing import Dict, Any
from flask import current_app

def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _ensure_parent(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def log_event(event: str, user: str = None, data: Dict[str, Any] = None):
    """
    Writes a single-line JSON (and/or CSV) entry depending on LOG_FORMAT.
    event: e.g., "login_success", "login_fail", "generate", "feedback_submit", "export_csv"
    """
    fmt = current_app.config.get("LOG_FORMAT", "both")
    payload = {
        "ts": _now(),
        "event": event,
        "user": user or "",
        "data": data or {},
    }

    if fmt in ("jsonl", "both"):
        path = current_app.config["LOG_JSONL_PATH"]
        _ensure_parent(path)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    if fmt in ("csv", "both"):
        path = current_app.config["LOG_CSV_PATH"]
        _ensure_parent(path)
        file_exists = os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["ts", "event", "user", "data_json"])
            writer.writerow([payload["ts"], payload["event"], payload["user"], json.dumps(payload["data"], ensure_ascii=False)])
