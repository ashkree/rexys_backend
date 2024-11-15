from recommender import MovieRecommender, GameRecommender
from models import Movie, UserMovieRating, Game, UserGameRating
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload

recommend_bp = Blueprint('recommend', __name__)


@recommend_bp.route('/movies', methods=['POST'])
def recommend_movies():
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        user_id = request.json.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        user_preferences = request.json.get('preferences', {})
        if not user_preferences:
            return jsonify({"error": "User preferences are required"}), 400

        # Get user history
        user_ratings = UserMovieRating.query.filter_by(user_id=user_id).all()
        user_history = [rating.movie.to_dict() for rating in user_ratings]

        # Get all movies
        movies = Movie.query.all()
        movie_list = [movie.to_dict() for movie in movies]

        if not movie_list:
            return jsonify({"error": "No movies found in database"}), 404

        # Get recommendations
        recommender = MovieRecommender(movie_list)
        recommendations = recommender.recommend(user_preferences, user_history)

        response = [{**item[0], "score": item[1]} for item in recommendations]

        return jsonify({
            "recommendations": response,
            "total_recommendations": len(response)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@recommend_bp.route('/games', methods=['POST'])
def recommend_games():
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        user_id = request.json.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        user_preferences = request.json.get('preferences', {})
        if not user_preferences:
            return jsonify({"error": "User preferences are required"}), 400

        games = Game.query.options(joinedload(
            Game.rated_by_users)).paginate(page=1, per_page=1000)

        user_history = Game.query.join(UserGameRating).filter(
            UserGameRating.user_id == user_id
        ).all()

        game_list = [game.to_dict() for game in games.items]
        history_list = [game.to_dict() for game in user_history]

        if not game_list:
            return jsonify({"error": "No games found in database"}), 404

        recommender = GameRecommender(game_list)
        recommendations = recommender.recommend(user_preferences, history_list)

        response = [{**item[0], "score": item[1]} for item in recommendations]

        return jsonify({
            "recommendations": response,
            "total_recommendations": len(response)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
