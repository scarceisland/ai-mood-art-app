import os
import sys

# Ensure the 'app' module can be found by adding the project root to the system path.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", True))
