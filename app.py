import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flask_migrate import Migrate
from models import db
from routes import register_blueprints
from seed import seed_games_and_movies  # Import seeding logic

load_dotenv()

migrate = Migrate()

def create_app():
    # Serve frontend files
    app = Flask(__name__, static_folder='frontend/dist')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # CORS configuration
    CORS(app, resources={
        r"/*": {"origins": ["https://rexys-frontend.vercel.app", "http://localhost:5173"]}
    })

    # Initialize database and migrations
    db.init_app(app)
    migrate.init_app(app, db)

    # Register routes
    register_blueprints(app)

    # Serve Vue frontend
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

    # Error handler for production
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({"error": "An unexpected error occurred."}), 500

    return app


def initialize_data(app):
    """Function to reset the database and initialize it with data."""
    with app.app_context():
        # Drop all tables if they exist
        db.drop_all()
        print("Existing tables dropped!")

        # Create fresh tables
        db.create_all()
        print("Database tables created!")

        # Seed database
        seed_games_and_movies()


if __name__ == '__main__':
    app = create_app()

    initialize_data(app)

    # Start the app with Gunicorn for production
    app.run(debug=False)
