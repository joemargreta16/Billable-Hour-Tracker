#!/usr/bin/env python3
"""
Enhanced script to create an initial admin user with improved security.
Run this script to set up the first admin account with secure password generation.
"""

import os
import sys
import secrets
import string
from datetime import datetime
from app import app, db
from models import User

def generate_secure_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password

def create_admin_user():
    """Create the initial admin user with enhanced security"""
    with app.app_context():
        # Check if any users exist
        user_count = User.query.count()
        if user_count > 0:
            print("Users already exist in the database.")
            print("This script is intended for initial setup only.")
            print("Use the admin interface to manage existing users.")
            return
        
        print("=" * 60)
        print("ENHANCED ADMIN USER CREATION")
        print("=" * 60)
        
        # Generate secure admin credentials
        admin_username = "admin"
        admin_password = generate_secure_password(16)
        
        # Create admin user
        admin_user = User()
        admin_user.username = admin_username
        admin_user.is_admin = True
        admin_user.set_password(admin_password)
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            
            print("\n✅ ADMIN USER CREATED SUCCESSFULLY!")
            print("-" * 40)
            print(f"Username: {admin_username}")
            print(f"Password: {admin_password}")
            print("-" * 40)
            print("⚠️  IMPORTANT SECURITY NOTES:")
            print("1. Change the password immediately after first login")
            print("2. Enable two-factor authentication if available")
            print("3. Use strong, unique passwords for all accounts")
            print("4. Regularly review admin access logs")
            print("=" * 60)
            
            # Save credentials to secure file
            with open('admin_credentials.txt', 'w') as f:
                f.write(f"Admin Username: {admin_username}\n")
                f.write(f"Admin Password: {admin_password}\n")
                f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("⚠️  Change password immediately after first login!\n")
            
            print("\n📄 Admin credentials saved to admin_credentials.txt")
            print("   (Remember to delete this file after securing your account)")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admin user: {e}")

if __name__ == "__main__":
    create_admin_user()
