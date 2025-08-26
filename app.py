# app.py (entry point for your Flask app)
# Location: Charles_MoodApp/app.py

from app import create_app  # imports the factory from app/__init__.py

# Build the Flask app using your configured factory
flask_app = create_app()

if __name__ == "__main__":
    # Honour DEBUG from .env if present (set in app/__init__.py)
    flask_app.run(debug=flask_app.config.get("DEBUG", True))
