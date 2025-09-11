import os
import click
from flask import Flask
from sqlalchemy.exc import OperationalError
from .db import db
from .models.user import User

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # --- Core Application Configuration ---
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions
    db.init_app(app)

    # --- Automatic Database Initialization with Error Handling ---
    with app.app_context():
        try:
            # Import all models here so they are registered with SQLAlchemy
            from .models import user, app_models
            # Create tables if they don't exist
            db.create_all()

            # Check if the admin user exists and create it if not
            admin_username = os.getenv("ADMIN_USERNAME", "admin").lower()
            if not User.query.filter_by(username=admin_username).first():
                admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
                admin_user = User(username=admin_username, is_admin=True)
                admin_user.set_password(admin_pass)
                db.session.add(admin_user)
                db.session.commit()
                print("Database tables created and admin user ensured.")
        except OperationalError as e:
            # This can happen on the first startup if the DB isn't ready.
            # The app will crash, Render will restart it, and it will succeed on the next try.
            print(f"Database initialization failed, likely a startup race condition: {e}")
            # Re-raising the error ensures Render restarts the service.
            raise

    # Register blueprints
    from . import routes
    app.register_blueprint(routes.bp)

    # --- Optional CLI Commands (for local development) ---
    @click.command("add-user")
    @click.argument("username")
    @click.argument("password")
    def add_user_command(username, password):
        """Creates a new user with a password."""
        with app.app_context():
            if User.query.filter_by(username=username).first():
                click.echo(f"Error: User '{username}' already exists.")
                return
            new_user = User(username=username, is_admin=False)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            click.echo(f"User '{username}' created successfully.")

    app.cli.add_command(add_user_command)

    return app