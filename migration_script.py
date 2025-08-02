#!/usr/bin/env python3
"""
Migration script for production database
Run this script to add the missing updated_at column to the project table
"""

import os
import sys
from sqlalchemy import create_engine, text

def add_updated_at_column():
    """Add updated_at column to project table for production"""
    
    # Get database URL from environment
    database_url = os.environ.get("DATABASE_URL", "sqlite:///timetracker.db")
    
    # Handle PostgreSQL URL format from Render
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Check if updated_at column exists
            if "postgresql" in str(engine.url):
                # PostgreSQL check
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'project' AND column_name = 'updated_at'
                """))
                column_exists = result.fetchone() is not None
                
                if not column_exists:
                    print("Adding updated_at column to project table...")
                    conn.execute(text("""
                        ALTER TABLE project 
                        ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """))
                    conn.commit()
                    print("✅ updated_at column added successfully")
                else:
                    print("✅ updated_at column already exists")
                    
            else:
                # SQLite check
                result = conn.execute(text("PRAGMA table_info(project)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'updated_at' not in columns:
                    print("Adding updated_at column to project table...")
                    conn.execute(text("""
                        ALTER TABLE project 
                        ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """))
                    conn.commit()
                    print("✅ updated_at column added successfully")
                else:
                    print("✅ updated_at column already exists")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Running migration script...")
    success = add_updated_at_column()
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
        sys.exit(1)
