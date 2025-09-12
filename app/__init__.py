import os
import time
import click
from flask import Flask
from sqlalchemy.exc import OperationalError, IntegrityError
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

    # --- Automatic Database Initialization with Retry Logic ---
    with app.app_context():
        max_retries = 5
        retry_delay = 2  # seconds
        for attempt in range(max_retries):
            try:
                # Import all models here so they are registered with SQLAlchemy
                from .models import user, app_models
                # Create tables if they don't exist
                db.create_all()

                # Attempt to create the admin user
                admin_username = os.getenv("ADMIN_USERNAME", "admin").lower()
                admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
                admin_user = User(username=admin_username, is_admin=True)
                admin_user.set_password(admin_pass)
                db.session.add(admin_user)
                db.session.commit()
                print("Admin user created successfully.")

                # If we get here, initialization was successful.
                print("Database tables created and admin user ensured.")
                break
            except IntegrityError:
                # This happens if the admin user already exists, which is fine.
                db.session.rollback()
                print("Admin user already exists. Initialization complete.")
                break
            except OperationalError as e:
                db.session.rollback()
                print(f"Database connection attempt {attempt + 1}/{max_retries} failed.")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("Max retries reached. Could not connect to the database.")
                    raise
            except Exception as e:
                db.session.rollback()
                print(f"An unexpected error occurred during initialization: {e}")
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