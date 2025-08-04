import sqlite3
import os

# Check if users.db exists
if os.path.exists('users.db'):
    print("users.db exists")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables in users.db:", tables)
    
    # Check if user table exists
    cursor.execute("PRAGMA table_info(user)")
    columns = cursor.fetchall()
    print("User table columns:", columns)
    
    # Check if any users exist
    try:
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()
        print("Users in database:", users)
    except Exception as e:
        print("Error querying users:", e)
    
    conn.close()
else:
    print("users.db does not exist")

# Also check timetracker.db
if os.path.exists('instance/timetracker.db'):
    print("\ntimetracker.db exists")
    conn = sqlite3.connect('instance/timetracker.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables in timetracker.db:", tables)
    conn.close()
