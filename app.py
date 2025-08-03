import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

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
            hashed_pw = generate_password_hash(password)
            new_user = User(username=username, password=hashed_pw)
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
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

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
