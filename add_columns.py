from app import app, db
from sqlalchemy import text

with app.app_context():
    # Add user_id column to project table
    try:
        db.session.execute(text("ALTER TABLE project ADD COLUMN user_id INTEGER"))
        print("Added user_id column to project table")
    except Exception as e:
        print(f"Error adding user_id column to project table: {e}")
    
    # Add user_id column to time_entry table
    try:
        db.session.execute(text("ALTER TABLE time_entry ADD COLUMN user_id INTEGER"))
        print("Added user_id column to time_entry table")
    except Exception as e:
        print(f"Error adding user_id column to time_entry table: {e}")
    
    # Create users table
    try:
        db.session.execute(text("""
            CREATE TABLE user (
                id INTEGER PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(120) NOT NULL,
                is_admin BOOLEAN NOT NULL,
                created_at DATETIME
            )
        """))
        print("Created user table")
    except Exception as e:
        print(f"Error creating user table: {e}")
    
    db.session.commit()
    print("Database schema updated")
