# In your app/__init__.py file

import os
import click
from flask import Flask
from .db import db


def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # --- Core Application Configuration ---
    # Get database URL from environment variable with fallback
    database_url = os.getenv("DATABASE_URL")

    # If DATABASE_URL is not set or is a Railway internal URL, use SQLite for local development
    if not database_url or "railway.internal" in database_url:
        # Ensure instance folder exists
        os.makedirs(app.instance_path, exist_ok=True)
        database_url = f"sqlite:///{os.path.join(app.instance_path, 'app.db')}"
        print(f"Using SQLite database for local development: {database_url}")

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key"),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Initialize extensions
    db.init_app(app)

    # Import models to ensure they are registered with SQLAlchemy
    from .models import app_models, user

    # --- Blueprints ---
    from . import routes
    app.register_blueprint(routes.bp)

    # --- CLI Commands ---
    @app.cli.command("init-db")
    def init_db_command():
        """Clear existing data and create new tables and admin user."""
        with app.app_context():
            db.create_all()
            print("Initialized the database.")

            # Import the User model here, inside the function
            from .models.user import User

            admin_username = os.getenv("ADMIN_USERNAME", "admin").lower()
            admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")

            # Check if admin already exists
            if not User.query.filter_by(username=admin_username).first():
                admin_user = User(username=admin_username, is_admin=True)
                admin_user.set_password(admin_pass)
                db.session.add(admin_user)
                db.session.commit()
                click.echo("Admin user created successfully.")
            else:
                click.echo("Admin user already exists.")

    return app