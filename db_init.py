from app import app
from models import db

# Initialize database
with app.app_context():
    db.create_all()
    print("Database initialized.")
