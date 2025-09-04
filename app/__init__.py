import os
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv


def create_app():
    """Create and configure an instance of the Flask application."""
    # Load environment variables from a .env file in the project root.
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")

    app = Flask(
        __name__,
        static_folder=str(project_root / "static"),
        template_folder=str(project_root / "templates"),
    )

    # --- Core Application Configuration ---
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")
    app.config["DEBUG"] = (os.getenv("DEBUG", "true").lower() == "true")
    app.config["ADMIN_RESET_CODE"] = os.getenv("ADMIN_RESET_CODE", "")

    # Configure data directory and database path.
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    app.config["DB_FILE"] = os.getenv("DB_FILE", "mood_app.db")
    app.config["DATABASE_PATH"] = str(data_dir / app.config["DB_FILE"])

    # Ensure the instance folder exists for any fallback configurations.
    os.makedirs(app.instance_path, exist_ok=True)

    # Configure session cookies for security.
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # SESSION_COOKIE_SECURE=True  # Enable if serving over HTTPS
    )

    # Register blueprints to organize routes.
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
