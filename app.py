import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'instance', 'timetracker.db'))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Import User model after db is initialized to avoid circular imports
from models import User

# Import routes to register all routes with the app
import routes

# Create tables at startup (Flask 3+ compatible)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
