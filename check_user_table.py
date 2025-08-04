import sqlite3
import os

# Check timetracker.db for user table
if os.path.exists('instance/timetracker.db'):
    print("timetracker.db exists")
    conn = sqlite3.connect('instance/timetracker.db')
    cursor = conn.cursor()
    
    # Try to query user table
    try:
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()
        print("Users in database:", users)
    except Exception as e:
        print("No user table found:", e)
    
    conn.close()
