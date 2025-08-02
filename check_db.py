from app import app, db
from models import *

with app.app_context():
    print("Tables in database:")
    for table in db.metadata.tables.keys():
        print(f"  - {table}")
    
    print("\nCurrent data:")
    print(f"  Projects: {Project.query.count()}")
    print(f"  Time Entries: {TimeEntry.query.count()}")
    print(f"  Settings: {Settings.query.count()}")
