import os
import click
from flask import Flask
from .db import db


def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # --- Core Application Configuration ---
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from . import routes
    app.register_blueprint(routes.bp)

    # --- Deferred Database Initialization ---
    @app.before_first_request
    def initialize_on_first_request():
        """Defer database initialization until first request"""
        try:
            # Create tables
            db.create_all()
            print("Database tables created or already exist.")

            # Create admin user
            from .models.user import User
            admin_username = os.getenv("ADMIN_USERNAME", "admin").lower()
            admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")

            if not User.query.filter_by(username=admin_username).first():
                admin_user = User(username=admin_username, is_admin=True)
                admin_user.set_password(admin_pass)
                db.session.add(admin_user)
                db.session.commit()
                print("Admin user created on first request.")
            else:
                print("Admin user already exists.")
        except Exception as e:
            print(f"Error during first request initialization: {e}")

    # --- Optional CLI Commands (for local development) ---
    @click.command("add-user")
    @click.argument("username")
    @click.argument("password")
    def add_user_command(username, password):
        """Creates a new user with a password."""
        with app.app_context():
            from .models.user import User
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