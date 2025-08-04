import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
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

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            username = request.form['username'].strip()
            password = request.form['password']
            if not username or not password:
                flash('Username and password required.')
                return render_template('signup.html')
            if User.query.filter_by(username=username).first():
                flash('Username already exists.')
                return render_template('signup.html')
            new_user = User(username=username, is_admin=False)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Signup successful. Please log in.')
            return redirect(url_for('login'))
        except Exception as e:
            print("Signup error:", e)  # This will show up in your Render logs
            flash('An error occurred during signup.')
            return render_template('signup.html')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.')
    return render_template('login.html')

# Removed duplicate dashboard and logout routes from app.py to avoid endpoint conflicts
# These routes are defined in routes.py

# @app.route('/dashboard')
# def dashboard():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
#     return render_template('dashboard.html', username=session.get('username'))

# @app.route('/logout')
# def logout():
#     session.clear()
#     flash('Logged out successfully.')
#     return redirect(url_for('login'))

# @app.route('/drop_user_table')
# def drop_user_table():
#     from sqlalchemy import text
#     try:
#         db.session.execute(text('DROP TABLE IF EXISTS "user";'))
#         db.session.commit()
#         return "User table dropped. Remove this route after use!"
#     except Exception as e:
#         print("Drop table error:", e)
#         return f"Error: {e}"

# @app.route('/add_password_column')
# def add_password_column():
#     from sqlalchemy import text
#     try:
#         db.session.execute(text('ALTER TABLE "user" ADD COLUMN password VARCHAR(128);'))
#         db.session.commit()
#         return "Password column added to user table. Remove this route after use!"
#     except Exception as e:
#         print("Alter table error:", e)
#         return f"Error: {e}"

if __name__ == '__main__':
    app.run(debug=True)
