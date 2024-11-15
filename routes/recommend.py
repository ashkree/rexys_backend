from recommender import MovieRecommender, GameRecommender
from models import Movie, UserMovieRating, Game, UserGameRating, User
from flask import Blueprint, request, jsonify


recommend_bp = Blueprint('recommend', __name__)


@recommend_bp.route('/movies', methods=['POST'])
def recommend_movies():
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        user_id = request.json.get('user_id')
        if not user_id or not isinstance(user_id, int):
            return jsonify({"error": "Valid user_id is required"}), 400

        # Check if user exists
        user_exists = User.query.get(user_id)
        if not user_exists:
            return jsonify({"error": "User not found"}), 404

        user_preferences = request.json.get('preferences', {})
        if not user_preferences:
            return jsonify({"error": "User preferences are required"}), 400

        # User history
        user_ratings = UserMovieRating.query.filter_by(user_id=user_id).all()
        user_history = [rating.movie.to_dict() for rating in user_ratings]

        # All movies
        movies = Movie.query.all()
        if not movies:
            return jsonify({"error": "No movies found in database"}), 404
        movie_list = [movie.to_dict() for movie in movies]

        recommender = MovieRecommender(movie_list)
        recommendations = recommender.recommend(user_preferences, user_history)

        response = [{**item[0], "score": item[1]} for item in recommendations]

        return jsonify({
            "recommendations": response,
            "total_recommendations": len(response)
        })

    except Exception as e:
        # Log error
        print(f"Error in recommend_movies: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@recommend_bp.route('/games', methods=['POST'])
def recommend_games():
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        user_id = request.json.get('user_id')
        if not user_id or not isinstance(user_id, int):
            return jsonify({"error": "Valid user_id is required"}), 400

        # Check if user exists
        user_exists = User.query.get(user_id)
        if not user_exists:
            return jsonify({"error": "User not found"}), 404

        user_preferences = request.json.get('preferences', {})
        if not user_preferences:
            return jsonify({"error": "User preferences are required"}), 400

        # User history
        user_history = Game.query.join(UserGameRating).filter(
            UserGameRating.user_id == user_id).all()
        history_list = [game.to_dict() for game in user_history]

        # All games
        games = Game.query.paginate(page=1, per_page=1000).items
        if not games:
            return jsonify({"error": "No games found in database"}), 404
        game_list = [game.to_dict() for game in games]

        recommender = GameRecommender(game_list)
        recommendations = recommender.recommend(user_preferences, history_list)

        response = [{**item[0], "score": item[1]} for item in recommendations]

        return jsonify({
            "recommendations": response,
            "total_recommendations": len(response)
        })

    except Exception as e:
        # Log error
        print(f"Error in recommend_games: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
