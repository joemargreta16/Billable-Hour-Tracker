"""
Script to manually add user_id columns to project and time_entry tables
Supports both SQLite and PostgreSQL databases
"""
import os
import sys

def add_columns_sqlite():
    """Add user_id columns to SQLite database"""
    import sqlite3
    
    # Connect to the database
    db_path = os.path.join('instance', 'timetracker.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add user_id column to project table if it doesn't exist
    try:
        cursor.execute("ALTER TABLE project ADD COLUMN user_id INTEGER REFERENCES user(id)")
        print("Added user_id column to project table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("user_id column already exists in project table")
        else:
            print(f"Error adding user_id column to project table: {e}")

    # Add user_id column to time_entry table if it doesn't exist
    try:
        cursor.execute("ALTER TABLE time_entry ADD COLUMN user_id INTEGER REFERENCES user(id)")
        print("Added user_id column to time_entry table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("user_id column already exists in time_entry table")
        else:
            print(f"Error adding user_id column to time_entry table: {e}")

    # Commit changes and close connection
    conn.commit()
    conn.close()

def add_columns_postgresql():
    """Add user_id columns to PostgreSQL database"""
    import psycopg2
    
    # Get database connection details from environment variables
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL environment variable not set")
        return False
    
    # Parse database URL
    # Format: postgresql://username:password@host:port/database
    try:
        # Handle different URL formats
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        # Extract connection parameters
        from urllib.parse import urlparse
        parsed = urlparse(database_url)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],  # Remove leading '/'
            user=parsed.username,
            password=parsed.password
        )
        cursor = conn.cursor()
        
        # Add user_id column to project table if it doesn't exist
        try:
            cursor.execute("""
                ALTER TABLE project 
                ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES "user"(id)
            """)
            print("Added user_id column to project table")
        except Exception as e:
            print(f"Error adding user_id column to project table: {e}")

        # Add user_id column to time_entry table if it doesn't exist
        try:
            cursor.execute("""
                ALTER TABLE time_entry 
                ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES "user"(id)
            """)
            print("Added user_id column to time_entry table")
        except Exception as e:
            print(f"Error adding user_id column to time_entry table: {e}")

        # Commit changes and close connection
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error connecting to PostgreSQL database: {e}")
        return False

def main():
    """Main function to determine database type and add columns"""
    # Check if DATABASE_URL is set to determine database type
    database_url = os.environ.get("DATABASE_URL", "")
    
    if "postgresql" in database_url or "postgres://" in database_url:
        print("Detected PostgreSQL database")
        success = add_columns_postgresql()
        if success:
            print("Finished adding columns to PostgreSQL database")
        else:
            print("Failed to add columns to PostgreSQL database")
            sys.exit(1)
    else:
        print("Using SQLite database")
        add_columns_sqlite()
        print("Finished adding columns to SQLite database")

if __name__ == "__main__":
    main()
