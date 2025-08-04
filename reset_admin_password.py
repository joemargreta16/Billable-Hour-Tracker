#!/usr/bin/env python3
"""
Script to reset the admin user's password to a known value for testing.
"""

from app import app, db
from models import User

def reset_admin_password():
    with app.app_context():
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Admin user not found.")
            return
        
        new_password = "admin123"
        admin_user.set_password(new_password)
        try:
            db.session.commit()
            print(f"Admin password reset successfully to: {new_password}")
        except Exception as e:
            db.session.rollback()
            print(f"Error resetting admin password: {e}")

if __name__ == "__main__":
    reset_admin_password()
