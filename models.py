from app import db
from datetime import datetime, date
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """Model for storing user information"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('Project', backref='user', lazy=True)
    time_entries = db.relationship('TimeEntry', backref='user', lazy=True)
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Project(db.Model):
    """Model for storing project information"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255))
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # For data isolation
    
    # Relationship to time entries
    time_entries = db.relationship('TimeEntry', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Project {self.name}>'
    
    @property
    def updated_at(self):
        """Fallback for missing updated_at column"""
        return getattr(self, '_updated_at', self.created_at)
    
    @updated_at.setter
    def updated_at(self, value):
        """Setter for updated_at with fallback"""
        if hasattr(self, '_updated_at'):
            self._updated_at = value
        # Silently ignore if column doesn't exist
    
    def save(self):
        """Save project with error handling"""
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Log error but continue
            print(f"Database save error: {e}")
            # Try basic save without updated_at
            try:
                db.session.add(self)
                db.session.commit()
            except:
                db.session.rollback()
                raise

class TimeEntry(db.Model):
    """Model for storing time entry records"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    hours = db.Column(db.Float, nullable=False)  # Store as decimal hours (e.g., 1.5 for 1h 30m)
    description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # For data isolation
    
    def __repr__(self):
        return f'<TimeEntry {self.date} - {self.hours}h>'
    
    @property
    def hours_minutes_display(self):
        """Convert decimal hours to hours:minutes format for display"""
        total_minutes = int(self.hours * 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}:{minutes:02d}"

class Settings(db.Model):
    """Model for storing application settings"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Setting {self.key}={self.value}>'

def initialize_default_data():
    """Initialize default projects and settings if they don't exist"""
    
    # Check if projects already exist
    if Project.query.count() == 0:
        default_projects = [
            {'name': 'Client A - Development', 'description': 'Software development work for Client A'},
            {'name': 'Client B - Consulting', 'description': 'Business consulting for Client B'},
            {'name': 'Internal - Training', 'description': 'Professional development and training'},
            {'name': 'Internal - Admin', 'description': 'Administrative tasks and meetings'},
            {'name': 'Client C - Support', 'description': 'Technical support for Client C'},
        ]
        
        for project_data in default_projects:
            project = Project(**project_data)
            db.session.add(project)
    
    # Check if settings already exist
    if Settings.query.count() == 0:
        default_settings = [
            {'key': 'monthly_goal_hours', 'value': '160'},
            {'key': 'currency_symbol', 'value': '$'},
            {'key': 'default_hourly_rate', 'value': '75'},
        ]
        
        for setting_data in default_settings:
            setting = Settings(**setting_data)
            db.session.add(setting)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing default data: {e}")

def initialize_default_user():
    """Initialize default admin user if not exists"""
    # Check if any users exist
    if User.query.count() == 0:
        # Create default admin user
        admin_user = User()
        admin_user.username = 'Joemar'
        admin_user.set_password('110291')
        admin_user.is_admin = True
        db.session.add(admin_user)
        
        try:
            db.session.commit()
            print("Default admin user 'Joemar' created successfully.")
            return admin_user
        except Exception as e:
            db.session.rollback()
            print(f"Error creating default admin user: {e}")
            return None
    return None

def associate_existing_data_with_user(user_id):
    """Associate existing projects and time entries with a user for data isolation"""
    try:
        # Associate all existing projects with the user if they don't have a user_id
        projects = Project.query.filter(Project.user_id.is_(None)).all()
        for project in projects:
            project.user_id = user_id
            
        # Associate all existing time entries with the user if they don't have a user_id
        time_entries = TimeEntry.query.filter(TimeEntry.user_id.is_(None)).all()
        for entry in time_entries:
            entry.user_id = user_id
            
        db.session.commit()
        print(f"Associated {len(projects)} projects and {len(time_entries)} time entries with user ID {user_id}")
    except Exception as e:
        db.session.rollback()
        print(f"Error associating existing data with user: {e}")

def get_setting(key, default_value=None):
    """Helper function to get a setting value"""
    setting = Settings.query.filter_by(key=key).first()
    return setting.value if setting else default_value

def set_setting(key, value):
    """Helper function to set a setting value"""
    setting = Settings.query.filter_by(key=key).first()
    if setting:
        setting.value = str(value)
        setting.updated_at = datetime.utcnow()
    else:
        setting = Settings()
        setting.key = key
        setting.value = str(value)
        db.session.add(setting)
    
    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error setting {key}: {e}")
        return False
