#!/usr/bin/env python3
"""
Script to apply database migrations using Flask-Migrate
This is the proper way to update the database schema
"""

from app import app, db, migrate
from flask_migrate import upgrade

def apply_migrations():
    """Apply all pending migrations"""
    try:
        with app.app_context():
            print("Applying database migrations...")
            # This will apply all pending migrations
            upgrade()
            print("✅ Database migrations applied successfully")
            return True
    except Exception as e:
        print(f"❌ Error applying migrations: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Applying database migrations...")
    success = apply_migrations()
    if success:
        print("🎉 Migrations applied successfully!")
    else:
        print("💥 Migration application failed!")
