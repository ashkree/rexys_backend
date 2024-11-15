from sqlalchemy.sql import func  # Import func for random ordering
from flask import Blueprint, request, jsonify
from models import db, UserMovieRating, UserGameRating, Movie, Game
ratings_bp = Blueprint('ratings', __name__)


# Batch rate movies


@ratings_bp.route('/<type>s/initial', methods=['GET'])
def get_initial_items(type):
    try:
        if type == 'movie':
            items = Movie.query.order_by(func.random()).limit(
                5).all()  # Fetch 5 random movies
        elif type == 'game':
            items = Game.query.order_by(func.random()).limit(
                5).all()  # Fetch 5 random games
        else:
            return jsonify({"error": "Invalid type"}), 400

        return jsonify([item.to_dict() for item in items])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ratings_bp.route('/rate/movies', methods=['POST'])
def rate_movies():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    user_id = data.get('user_id')
    ratings = data.get('ratings')

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    if not isinstance(ratings, list):
        return jsonify({"error": "Ratings should be a list"}), 400

    for rating_data in ratings:
        movie_id = rating_data.get('movie_id')
        rating = rating_data.get('rating')

        if not movie_id or not isinstance(rating, (int, float)):
            continue  # Skip invalid entries and log if necessary

        existing_rating = UserMovieRating.query.filter_by(
            user_id=user_id, movie_id=movie_id).first()

        if existing_rating:
            existing_rating.rating = rating
        else:
            new_rating = UserMovieRating(
                user_id=user_id, movie_id=movie_id, rating=rating)
            db.session.add(new_rating)

    db.session.commit()
    return jsonify({"message": "Movie ratings submitted successfully"}), 201


# Batch rate games


@ratings_bp.route('/rate/games', methods=['POST'])
def rate_games():
    """
    Allows a user to submit multiple game ratings in one request.
    """
    data = request.get_json()
    user_id = data.get('user_id')
    ratings = data.get('ratings')  # Expecting a list of game ratings

    if not user_id or not ratings:
        return jsonify({"error": "User ID and ratings are required"}), 400

    for rating_data in ratings:
        game_id = rating_data.get('game_id')
        rating = rating_data.get('rating')

        if not game_id or not rating:
            continue  # Skip invalid entries

        existing_rating = UserGameRating.query.filter_by(
            user_id=user_id, game_id=game_id).first()
        if existing_rating:
            existing_rating.rating = rating  # Update existing rating
        else:
            new_rating = UserGameRating(
                user_id=user_id, game_id=game_id, rating=rating)
            db.session.add(new_rating)

    db.session.commit()

    return jsonify({"message": "Game ratings submitted successfully"}), 201
