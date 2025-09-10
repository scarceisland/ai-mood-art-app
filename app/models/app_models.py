from app.db import db
from sqlalchemy.dialects.postgresql import JSONB

class Feedback(db.Model):
    """Represents user feedback in the database."""
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, index=True)
    emotion = db.Column(db.String(50))
    prompt = db.Column(db.Text)
    image_url = db.Column(db.String(512))
    advice = db.Column(db.Text)
    predicted_correct = db.Column(db.Integer)
    advice_ok = db.Column(db.Integer)
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

class Log(db.Model):
    """Represents a single log event in the database."""
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), index=True)
    event = db.Column(db.String(100))
    source = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    # created_at is also present in some queries, can be merged with timestamp
    created_at = db.Column(db.DateTime)
    data = db.Column(JSONB)

class Settings(db.Model):
    """Represents a key-value setting in the database."""
    __tablename__ = 'settings'
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text)
