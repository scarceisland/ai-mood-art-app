import json
from datetime import datetime
from flask import current_app
from .db import db
from .models.app_models import Log

def log_event(event: str, user: str | None = None, data: dict | None = None, source: str | None = None) -> None:
    """Writes a single event to the `logs` database table using SQLAlchemy."""
    app = current_app._get_current_object()
    try:
        new_log = Log(
            timestamp=datetime.utcnow(),
            event=str(event),
            username="" if user is None else str(user),
            source="" if source is None else str(source),
            data=json.dumps(data) if data is not None else None,
        )
        db.session.add(new_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Failed to write to logs database: {e}")