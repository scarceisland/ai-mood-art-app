from datetime import datetime
from .db import db

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    emotion = db.Column(db.String(50))
    prompt = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    advice = db.Column(db.Text)
    predicted_correct = db.Column(db.Integer)
    advice_ok = db.Column(db.Integer)
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Emotion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    event = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80))
    source = db.Column(db.String(50))
    data = db.Column(db.Text) # Storing JSON as a string

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)