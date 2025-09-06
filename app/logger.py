import json
import datetime as dt
from flask import current_app
from .utils import get_db


def _now_str() -> str:
    """Returns the current time as an ISO 8601 formatted string."""
    return dt.datetime.now().isoformat()


import json
import datetime as dt
from flask import current_app
from .utils import get_db


def _now_str() -> str:
    """Returns the current time as an ISO 8601 formatted string."""
    return dt.datetime.now().isoformat()


def log_event(event: str, user: str | None = None, data: dict | None = None, source: str | None = None) -> None:
    """
    Writes a single event to the `logs` database table.
    """
    app = current_app._get_current_object()

    record = {
        "timestamp": _now_str(),
        "event": str(event),
        "user": "" if user is None else str(user),
        "source": "" if source is None else str(source),
        "data": json.dumps(data) if data is not None else None,
    }

    try:
        db = get_db()

        # Determine placeholder style based on database type
        if hasattr(db, 'cursor'):  # PostgreSQL connection (has cursor method)
            placeholders = "%s, %s, %s, %s, %s"
        else:  # SQLite connection
            placeholders = "?, ?, ?, ?, ?"

        db.execute(
            f"""
            INSERT INTO logs (timestamp, event, username, source, data)
            VALUES ({placeholders})
            """,
            (
                record["timestamp"],
                record["event"],
                record["user"],
                record["source"],
                record["data"],
            )
        )
        db.commit()
    except Exception as e:
        app.logger.error(f"Failed to write to logs database: {e}")