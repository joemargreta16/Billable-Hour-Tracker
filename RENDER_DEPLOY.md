# Render Deployment Guide

## Quick Fix for Render Deployment

If you're seeing the error `column project.updated_at does not exist`, follow these steps:

### Option 1: Use the Fix Script (Recommended)
Add this to your Render deploy commands:
```bash
python fix_render_db.py
```

### Option 2: Manual Database Fix
Run these SQL commands in your Render database:

**For PostgreSQL:**
```sql
-- Add missing updated_at column
ALTER TABLE project ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Update existing records
UPDATE project SET updated_at = created_at WHERE updated_at IS NULL;
```

### Option 3: Environment Variable Fix
Add this environment variable to your Render settings:
```
DATABASE_URL=your_database_url
```

## Updated Deploy Commands for Render

In your Render dashboard, update the **Deploy Commands** to:

```bash
# Install dependencies
pip install -r requirements.txt

# Fix database schema
python fix_render_db.py

# Initialize database
python -c "from app import app, db; from models import initialize_default_data; app.app_context().push(); db.create_all(); initialize_default_data(); print('Database initialized')"
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
3. **Ensure all tables exist** by running the fix script
4. **Check column names** match the model definitions

The application should now work correctly on Render with the new project management features.
