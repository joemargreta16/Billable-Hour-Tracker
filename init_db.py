from app import app, db
from models import initialize_default_data, initialize_default_user, associate_existing_data_with_user

with app.app_context():
    # Initialize default data
    initialize_default_data()
    
    # Initialize default user
    default_user = initialize_default_user()
    if default_user:
        # Associate existing data with the default user
        associate_existing_data_with_user(default_user.id)
        
    print('Database initialized with default data and user')
