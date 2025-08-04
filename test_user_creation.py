import os
import sys
import sqlite3

# Add the current directory to the Python path
sys.path.insert(0, '.')

# Import the app and database
from app import app, db
from models import User

# Test if User table exists and can be used
with app.app_context():
    # Create tables if they don't exist
    db.create_all()
    
    # Check if User table exists
    try:
        # Try to query the User table
        users = User.query.all()
        print(f"User table exists. Found {len(users)} users.")
        
        # Try to create a test user
        if len(users) == 0:
            test_user = User(username='testuser')
            test_user.set_password('testpassword')
            db.session.add(test_user)
            db.session.commit()
            print("Successfully created test user.")
            
            # Verify the user was created
            created_user = User.query.filter_by(username='testuser').first()
            if created_user and created_user.check_password('testpassword'):
                print("User authentication verified successfully.")
            else:
                print("Error: User authentication failed.")
        else:
            print("Users already exist in the database.")
            
    except Exception as e:
        print(f"Error working with User table: {e}")
