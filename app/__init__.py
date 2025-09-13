# In your app/__init__.py file

import os
import click
from flask import Flask
from .db import db  # Assuming you have db = SQLAlchemy() in app/db.py


def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # --- Core Application Configuration ---
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Initialize extensions
    db.init_app(app)

    # --- Blueprints ---
    from . import routes
    app.register_blueprint(routes.bp)

    # Note: If your blueprint is named 'main', use routes.main

    # --- CLI Commands ---
    # This is the new, recommended way to set up your database.
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