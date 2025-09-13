#!/usr/bin/env python3
"""
Database connection and table creation check script.
Run this with: railway run python check_db.py
"""

import os
import sys
from sqlalchemy import text  # ← ADD THIS IMPORT

# Add the current directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def check_database():
    """Check database connection and table creation"""
    try:
        # Import your app components
        from app import create_app, db

        # Create the app instance
        app = create_app()

        # Use the app context
        with app.app_context():
            print("🔍 Checking database connection...")

            # Test basic connection - USE text() WRAPPER
            try:
                result = db.session.execute(text('SELECT 1'))  # ← ADD text() HERE
                print("✅ Database connection successful")
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                return False

            # Try to create tables
            print("🔍 Attempting to create tables...")
            try:
                db.create_all()
                db.session.commit()
                print("✅ Tables created successfully")
            except Exception as e:
                print(f"❌ Table creation failed: {e}")
                return False

            # Check what tables exist - USE text() WRAPPER
            print("🔍 Checking existing tables...")
            try:
                result = db.session.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))  # ← ADD text() HERE
                tables = [row[0] for row in result]
                print(f"✅ Tables in database: {tables}")

                if not tables:
                    print("⚠️  No tables found in the database")
                return True

            except Exception as e:
                print(f"❌ Error checking tables: {e}")
                return False

    except Exception as e:
        print(f"❌ Failed to initialize app: {e}")
        return False


if __name__ == "__main__":
    success = check_database()
    sys.exit(0 if success else 1)