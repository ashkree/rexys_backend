import pandas as pd
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from models import db
from routes import register_blueprints
from dotenv import load_dotenv
import os
from models import db


load_dotenv()


def create_app():
    # Serve frontend files
    app = Flask(__name__, static_folder='frontend/dist')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

    # CORS configuration
    CORS(app, resources={
         r"/*": {"origins": os.getenv('FRONTEND_URL')}})

    # Initialize database
    db.init_app(app)

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


if __name__ == '__main__':
    # Use production WSGI server like Gunicorn for deployment
    app = create_app()
    app.run(debug=False)
