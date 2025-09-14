#!/usr/bin/env python3
"""
Simple script to initialize the database
Run with: python init_db.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Force local SQLite database for development
os.environ['DATABASE_URL'] = 'sqlite:///instance/app.db'

# Ensure the instance directory exists
instance_path = Path('instance')
instance_path.mkdir(exist_ok=True)

from app import create_app
from app.db import db

app = create_app()

with app.app_context():
    try:
        # Create all tables
        db.create_all()
        print("Database tables created successfully")

        # Insert default emotions
        from app.models.app_models import Emotion

        emotions = [
            ('happy', 'Feeling of joy, contentment, and positivity'),
            ('sad', 'Feeling of unhappiness, sorrow, or disappointment'),
            ('angry', 'Feeling of strong annoyance, displeasure, or hostility'),
            ('anxious', 'Feeling of worry, nervousness, or unease'),
            ('calm', 'Feeling of peace, tranquility, and relaxation'),
            ('excited', 'Feeling of great enthusiasm and eagerness'),
            ('tired', 'Feeling of fatigue or need for rest')
        ]

        for name, description in emotions:
            if not Emotion.query.filter_by(name=name).first():
                emotion = Emotion(name=name, description=description)
                db.session.add(emotion)

        db.session.commit()
        print("Default emotions inserted")

    except Exception as e:
        print(f"Error initializing database: {e}")
        # Try with an absolute path as fallback
        try:
            # Use an absolute path for SQLite
            abs_path = os.path.abspath('instance/app.db')
            os.environ['DATABASE_URL'] = f'sqlite:///{abs_path}'

            # Recreate the app with the new database URL
            app = create_app()

            with app.app_context():
                db.create_all()
                print("Database tables created successfully with absolute path")

        except Exception as e2:
            print(f"Error with absolute path: {e2}")