#!/usr/bin/env python3
"""
Script to create an initial admin user for the Time Tracker application.
Run this script to set up the first admin account.
"""

import os
import sys
from app import app, db
from models import User

def create_admin_user():
    """Create the initial admin user"""
    with app.app_context():
        # Check if any users exist
        user_count = User.query.count()
        if user_count > 0:
            print("Users already exist in the database.")
            print("This script is intended for initial setup only.")
            return
        
        print("Creating initial admin user...")
        
        # Create admin user
        admin_user = User(
            username='admin',
            is_admin=True
        )
        admin_user.set_password('admin123')
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
            print("Please change the password immediately after first login.")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")

if __name__ == "__main__":
    create_admin_user()
