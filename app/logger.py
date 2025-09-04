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
        # Convert the data dictionary to a JSON string for database storage.
        "data": json.dumps(data) if data is not None else None,
    }

    try:
        db = get_db()
        db.execute(
            """
            INSERT INTO logs (timestamp, event, user, source, data)
            VALUES (?, ?, ?, ?, ?)
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
        # If the database write fails, log the error to the console for debugging.
        app.logger.error(f"Failed to write to logs database: {e}")
