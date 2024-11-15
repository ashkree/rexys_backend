from flask import Blueprint, request, jsonify
from flask_cors import CORS
from models import db, User

auth_bp = Blueprint('auth', __name__)
CORS(auth_bp)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')

    if not username:
        return jsonify({"error": "Username is required"}), 400

    # Check if username already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "Username already exists"}), 409

    # Create new user
    new_user = User(username=username)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "Registration successful",
        "user_id": new_user.id
    }), 201

# User Sign In


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')

    if not username:
        return jsonify({"error": "Username is required"}), 400

    # Check if user exists
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "message": "Login successful",
        "user_id": user.id
    }), 200
