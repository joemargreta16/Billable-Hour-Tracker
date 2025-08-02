import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_migrate import Migrate

import sys
import warnings

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
migrate = Migrate()

# Create the app
app = Flask(__name__)

# Check for critical environment variables
session_secret = os.environ.get("SESSION_SECRET")
if not session_secret or session_secret == "dev-secret-key-change-in-production":
    warnings.warn("SESSION_SECRET is not set or using default. This is insecure for production.", RuntimeWarning)
app.secret_key = session_secret or "dev-secret-key-change-in-production"

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    warnings.warn("DATABASE_URL environment variable is not set. Falling back to local SQLite database.", RuntimeWarning)
    database_url = "sqlite:///timetracker.db"
else:
    # Fix for old-style postgres URLs
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)
migrate.init_app(app, db)

# Import routes after app initialization
with app.app_context():
    import routes

@app.cli.command("init-db")
def init_db_command():
    """Initializes the database."""
    import models
    db.create_all()
    models.initialize_default_data()
    # Initialize default user
    default_user = models.initialize_default_user()
    if default_user:
        # Associate existing data with the default user
        models.associate_existing_data_with_user(default_user.id)
    print("Database initialized.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    try:
        app.run(host='0.0.0.0', port=port, debug=debug_mode)
    except Exception as e:
        print(f"Error starting app: {e}", file=sys.stderr)
        sys.exit(1)
