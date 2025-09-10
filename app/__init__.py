import os
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv
import click


def create_app():
    """Create and configure an instance of the Flask application."""
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

    # Configure the database using the DATABASE_URL from the environment.
    # This is the ONLY configuration needed for the database connection.
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- Initialize Extensions ---
    from .db import db
    db.init_app(app)

    # Ensure the instance folder exists for any fallback configurations
    os.makedirs(app.instance_path, exist_ok=True)

    # Configure session cookies for security
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    # Register blueprints to organize routes
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    # --- Database CLI Commands ---
    @app.cli.command("init-db")
    def init_db_command():
        """Clear existing data and create new tables, including the admin user."""
        with app.app_context():
            db.create_all()
            from .models.user import User, get_user

            admin_username = os.getenv("ADMIN_USERNAME", "admin")

            if not get_user(admin_username):
                admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
                admin_user = User(username=admin_username)
                admin_user.set_password(admin_password)
                db.session.add(admin_user)
                db.session.commit()
                click.echo(f"Admin user '{admin_username}' created.")
            else:
                click.echo(f"Admin user '{admin_username}' already exists.")

            click.echo("Initialized the database.")

    @app.cli.command("add-user")
    @click.argument("username")
    @click.argument("password")
    def add_user_command(username, password):
        """Creates a new user with a hashed password."""
        with app.app_context():
            from .models.user import User, get_user

            if get_user(username):
                click.echo(f"Error: User '{username}' already exists.")
                return

            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            click.echo(f"User '{username}' was created successfully.")

    return app

