#!/usr/bin/env python3
"""
Fix for Render deployment - handles missing updated_at column
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
                
                # Check if updated_at column exists
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
                
                # Check for time_entry table
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
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                
                conn.commit()
                print("✅ PostgreSQL database fixed successfully")
                
            else:
                # SQLite fixes
                print("🔧 Fixing SQLite database...")
                
                # Add updated_at column if missing
                conn.execute(text("""
                    ALTER TABLE project ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """))
                
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
