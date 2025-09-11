import os
import sys

# Ensure the 'app' module can be found by adding the project root to the system path.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Get host and port from environment variables for flexibility
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))

    app.run(
        host=host,
        port=port,
        debug=app.config.get("DEBUG", False)  # Default to False for safety
    )