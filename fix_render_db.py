#!/usr/bin/env python3
"""
Fix for Render deployment - handles missing columns and tables
Run this as a one-time setup script in Render's deploy commands
"""

import os
from sqlalchemy import create_engine, text
from datetime import datetime

def fix_database():
    """Fix database schema for Render deployment"""
    
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found")
        return False
    
    # Handle PostgreSQL URL format
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Check database type
            if "postgresql" in str(engine.url):
                # PostgreSQL specific fixes
                print("🔧 Fixing PostgreSQL database...")
                
                # Check if user table exists
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name = 'user'
                """))
                
                if not result.fetchone():
                    print("Creating user table...")
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS "user" (
                            id SERIAL PRIMARY KEY,
                            username VARCHAR(80) UNIQUE NOT NULL,
                            password_hash VARCHAR(120) NOT NULL,
                            is_admin BOOLEAN DEFAULT FALSE NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                
                # Check if user_id column exists in project table
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'project' AND column_name = 'user_id'
                """))
                
                if not result.fetchone():
                    print("Adding user_id column to project table...")
                    conn.execute(text("""
                        ALTER TABLE project 
                        ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES "user"(id)
                    """))
                
                # Check if user_id column exists in time_entry table
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'time_entry' AND column_name = 'user_id'
                """))
                
                if not result.fetchone():
                    print("Adding user_id column to time_entry table...")
                    conn.execute(text("""
                        ALTER TABLE time_entry 
                        ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES "user"(id)
                    """))
                
                # Check if updated_at column exists in project table
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'project' AND column_name = 'updated_at'
                """))
                
                if not result.fetchone():
                    print("Adding updated_at column to project table...")
                    conn.execute(text("""
                        ALTER TABLE project 
                        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """))
                
                # Check for settings table
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name = 'settings'
                """))
                
                if not result.fetchone():
                    print("Creating settings table...")
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS settings (
                            id SERIAL PRIMARY KEY,
                            key VARCHAR(50) UNIQUE NOT NULL,
                            value VARCHAR(255) NOT NULL,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                
                # Check for time_entry table (in case it's missing)
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name = 'time_entry'
                """))
                
                if not result.fetchone():
                    print("Creating time_entry table...")
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS time_entry (
                            id SERIAL PRIMARY KEY,
                            date DATE NOT NULL,
                            project_id INTEGER REFERENCES project(id),
                            hours DECIMAL(5,2) NOT NULL,
                            description VARCHAR(500),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            user_id INTEGER REFERENCES "user"(id)
                        )
                    """))
                
                conn.commit()
                print("✅ PostgreSQL database fixed successfully")
                
            else:
                # SQLite fixes
                print("🔧 Fixing SQLite database...")
                
                # Add user_id column to project table if missing
                try:
                    conn.execute(text("""
                        ALTER TABLE project ADD COLUMN user_id INTEGER REFERENCES user(id)
                    """))
                    print("Added user_id column to project table")
                except Exception as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"Note: {e}")
                    else:
                        print("user_id column already exists in project table")
                
                # Add user_id column to time_entry table if missing
                try:
                    conn.execute(text("""
                        ALTER TABLE time_entry ADD COLUMN user_id INTEGER REFERENCES user(id)
                    """))
                    print("Added user_id column to time_entry table")
                except Exception as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"Note: {e}")
                    else:
                        print("user_id column already exists in time_entry table")
                
                # Add updated_at column if missing
                try:
                    conn.execute(text("""
                        ALTER TABLE project ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """))
                    print("Added updated_at column to project table")
                except Exception as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"Note: {e}")
                    else:
                        print("updated_at column already exists in project table")
                
                conn.commit()
                print("✅ SQLite database fixed successfully")
                
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 Fixing database for Render deployment...")
    success = fix_database()
    if success:
        print("🎉 Database fixed successfully!")
    else:
        print("💥 Database fix failed!")
