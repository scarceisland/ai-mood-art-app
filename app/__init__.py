import os, sqlite3
from flask import Flask
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

def _init_db(db_path: str):
    os.makedirs(DATA_DIR, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                emotion TEXT NOT NULL,
                prompt TEXT NOT NULL,
                image_url TEXT NOT NULL,
                advice TEXT NOT NULL,
                predicted_correct INTEGER NOT NULL,
                advice_ok INTEGER NOT NULL,
                comments TEXT,
                created_at TEXT NOT NULL
            );
        """)
        conn.commit()

def create_app():
    load_dotenv(os.path.join(BASE_DIR, ".env"))

    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev_local_only_change_me")

    db_file = os.getenv("DB_FILE", "mood_app.db")
    db_path = os.path.join(DATA_DIR, db_file)
    app.config["DB_PATH"] = db_path

    # Logging config
    app.config["LOG_FORMAT"] = os.getenv("LOG_FORMAT", "both").lower()
    app.config["LOG_JSONL_PATH"] = os.path.join(DATA_DIR, os.getenv("LOG_JSONL", "session_log.jsonl"))
    app.config["LOG_CSV_PATH"] = os.path.join(DATA_DIR, os.getenv("LOG_CSV", "session_log.csv"))
    app.config["LOG_VIEW_PAGE_SIZE"] = int(os.getenv("LOG_VIEW_PAGE_SIZE", "25"))

    # Debug toggle
    app.config["DEBUG"] = str(os.getenv("DEBUG", "true")).lower() in ("1", "true", "yes", "on")

    _init_db(db_path)

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
