# Render Deployment Guide

## Quick Fix for Render Deployment

If you're seeing errors like `column project.user_id does not exist` or `column project.updated_at does not exist`, follow these steps:

### Option 1: Use the Fix Script (Recommended for immediate fix)
Add this to your Render deploy commands:
```bash
python fix_render_db.py
```

### Option 2: Apply Migrations (Recommended for proper schema management)
If you want to properly apply all database migrations:
```bash
python apply_migrations.py
```

### Option 3: Manual Database Fix
Run these SQL commands in your Render database:

**For PostgreSQL:**
```sql
-- Create user table if it doesn't exist
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(120) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add missing user_id column to project table
ALTER TABLE project ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES "user"(id);

-- Add missing user_id column to time_entry table
ALTER TABLE time_entry ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES "user"(id);

-- Add missing updated_at column to project table
ALTER TABLE project ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Create settings table if it doesn't exist
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(50) UNIQUE NOT NULL,
    value VARCHAR(255) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create time_entry table if it doesn't exist (with all required columns)
CREATE TABLE IF NOT EXISTS time_entry (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    project_id INTEGER REFERENCES project(id),
    hours DECIMAL(5,2) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES "user"(id)
);
```

**For SQLite:**
```sql
-- Add missing columns (SQLite doesn't support IF NOT EXISTS for columns in all versions)
ALTER TABLE project ADD COLUMN user_id INTEGER REFERENCES user(id);
ALTER TABLE time_entry ADD COLUMN user_id INTEGER REFERENCES user(id);
ALTER TABLE project ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
```

### Option 4: Environment Variable Fix
Add this environment variable to your Render settings:
```
DATABASE_URL=your_database_url
```

## Updated Deploy Commands for Render

In your Render dashboard, update the **Deploy Commands** to:

```bash
# Install dependencies
pip install -r requirements.txt

# Option 1: Fix database schema (quick fix)
python fix_render_db.py

# Option 2: Apply database migrations (proper approach)
# python apply_migrations.py

# Initialize database with default data and user
python init_db.py
```

## Environment Variables for Render

Make sure these are set in your Render environment:

```
DATABASE_URL=your_postgres_database_url
SESSION_SECRET=your_secret_key
PORT=8000
```

## Troubleshooting

If you still see errors:

1. **Check the logs** in Render dashboard
2. **Verify database connection** is working
3. **Ensure all tables and columns exist** by running the fix script
4. **Check that the database schema matches the model definitions**
5. **Try applying migrations** with `python apply_migrations.py`

The application should now work correctly on Render with the new project management features and user isolation.
PORT=8000
Add this environment variable to your Render settings:
