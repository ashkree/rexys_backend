from app import app
from models import db, Game


def check_games():
    """
    Fetch and print the first 5 records from the Game table to verify data upload.
    """
    with app.app_context():
        # Query the first 5 games
        games = Game.query.limit(5).all()
        for game in games:
            print(f"Title: {game.title}")
            print(f"Genre: {game.genre}")
            print(f"Tags: {game.tags}")
            print(f"Rating: {game.rating}")
            print(f"Cost: {game.cost}")
            print(f"System Requirements: {game.system_requirements}")
            print(f"Popularity: {game.popularity}")
            print("-" * 40)


if __name__ == '__main__':
    check_games()
