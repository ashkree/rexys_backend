from flask import Blueprint, request, jsonify
from models import Movie, Game, UserMovieRating

recommend_bp = Blueprint('recommend', __name__)

@recommend_bp.route('/movies', methods=['POST'])
def recommend_movies():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        preferences = data.get('preferences')  # Includes genre, rating range, tags

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        # Example recommendation logic based on user's preferences
        query = Movie.query
        if preferences.get('genre'):
            query = query.filter(Movie.genre.ilike(f"%{preferences['genre']}%"))
        if preferences.get('rating'):
            query = query.filter(
                Movie.rating >= preferences['rating']['min'],
                Movie.rating <= preferences['rating']['max']
            )
        if preferences.get('tags'):
            tags = preferences['tags']
            query = query.filter(Movie.tags.any(lambda t: t.name.in_(tags)))  # Example for tag filtering

        recommendations = [movie.to_dict() for movie in query.limit(10).all()]  # Limit results to 10

        return jsonify({
            "recommendations": recommendations,
            "total_recommendations": len(recommendations)
        })
    except Exception as e:
        print(f"Error in recommend_movies: {e}")
        return jsonify({"error": "Internal server error"}), 500

@recommend_bp.route('/games', methods=['POST'])
def recommend_games():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        preferences = data.get('preferences')  # Includes genre, rating range, tags

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        # Example recommendation logic for games
        query = Game.query
        if preferences.get('genre'):
            query = query.filter(Game.genre.ilike(f"%{preferences['genre']}%"))
        if preferences.get('rating'):
            query = query.filter(
                Game.rating >= preferences['rating']['min'],
                Game.rating <= preferences['rating']['max']
            )
        if preferences.get('tags'):
            tags = preferences['tags']
            query = query.filter(Game.tags.any(lambda t: t.name.in_(tags)))  # Example for tag filtering

        recommendations = [game.to_dict() for game in query.limit(10).all()]  # Limit results to 10

        return jsonify({
            "recommendations": recommendations,
            "total_recommendations": len(recommendations)
        })
    except Exception as e:
        print(f"Error in recommend_games: {e}")
        return jsonify({"error": "Internal server error"}), 500
