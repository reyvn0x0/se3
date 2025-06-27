from app import create_app, db
from app.models import *  # Import all models/entities

app = create_app()

with app.app_context():
    db.create_all()
    print("Tables were created :)")