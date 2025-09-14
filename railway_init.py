#!/usr/bin/env python3
"""
Script to initialize the database on Railway
"""

import os
from app import create_app
from app.db import db

# Set the environment to production
os.environ['FLASK_ENV'] = 'production'

app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()
    print("Database tables created successfully on Railway")

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
    print("Default emotions inserted on Railway")