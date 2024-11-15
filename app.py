import os
import pandas as pd
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flask_migrate import Migrate
from models import db, Game, Movie  # Ensure these are your correct models
from routes import register_blueprints

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
         r"/*": {"origins": ["https://rexys-frontend.vercel.app", "http://localhost:5173"]}})

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

        # Load initial data into the database
        # Games data
        if not Game.query.first():  # Only load if no data exists
            print("Loading games data...")
            # Adjust path as needed
            games_data = pd.read_csv('data/merged_steam_data.csv').head(4000)
            games = [
                Game(
                    title=row['title'][:255],  # Truncate if necessary
                    genre=row['genre'][:255],
                    tags=row['tags'][:500],
                    rating=row['rating'],
                    cost=row['cost'],
                    popularity=row['popularity']
                )
                for _, row in games_data.iterrows()
            ]
            db.session.bulk_save_objects(games)
            db.session.commit()
            print("Games data loaded successfully!")

        # Movies data
        if not Movie.query.first():
            print("Loading movies data...")
            # Adjust path as needed
            movies_data = pd.read_csv('data/imdb_top_1000.csv').head(1000)
            movies = [
                Movie(
                    title=row['title'][:255],
                    genre=row['genre'][:255],
                    tags=row['tags'][:500],
                    rating=row['rating'],
                    actors=row['actors'][:300],
                    popularity=row['popularity']
                )
                for _, row in movies_data.iterrows()
            ]
            db.session.bulk_save_objects(movies)
            db.session.commit()
            print("Movies data loaded successfully!")


if __name__ == '__main__':
    app = create_app()

    # Initialize the database and load data
    initialize_data(app)

    # Start the app with Gunicorn for production
    app.run(debug=False)
