import pandas as pd
from models import db,  Movie, Game

def seed_games_and_movies():
    seed_movies()
    seed_games()

    print(Game.query.count())
    print(Movie.query.count())

def seed_movies():
    print("Loading movies data...")
    try:
        # Load the CSV file and select only the necessary columns
        movies_data = pd.read_csv('data/imdb_top_1000.csv', usecols=[
            'Series_Title', 'Genre', 'IMDB_Rating', 'Overview',
            'Star1', 'Star2', 'Star3', 'Star4', 'No_of_Votes'
        ])

        # Rename columns and combine stars into 'actors'
        movies_data = movies_data.rename(columns={
            'Series_Title': 'title',
            'Genre': 'genre',
            'IMDB_Rating': 'rating',
            'Overview': 'tags',
            'No_of_Votes': 'popularity'
        })

        movies_data['actors'] = movies_data[['Star1', 'Star2',
                                             'Star3', 'Star4']].apply(lambda x: ', '.join(x), axis=1)
        movies_data = movies_data.drop(
            columns=['Star1', 'Star2', 'Star3', 'Star4'])

        # Create Movie objects
        movies = [
            Movie(
                title=row['title'][:255],
                genre=row['genre'][:255],
                tags=row['tags'][:500],
                rating=row['rating'],
                # Ensure actors fit into a reasonable column length
                actors=row['actors'][:500],
                popularity=row['popularity']
            )
            for _, row in movies_data.iterrows()
        ]

        # Insert into the database
        db.session.bulk_save_objects(movies)
        print("Movies data loaded successfully!")
    except Exception as e:
        print(f"Error seeding movies: {e}")
        db.session.rollback()

def seed_games():
    print("Loading games data...")
    try:
        # Load the CSV file and select only the necessary columns
        games_data = pd.read_csv('data/merged_steam_data.csv', usecols=[
            'name', 'categories', 'genres', 
            'positive_ratings', 'negative_ratings', 'owners'
        ])
        
        # Rename columns to match the database schema
        games_data = games_data.rename(columns={
            'name': 'title',
            'categories': 'tags',
            'genres': 'genre'
        })

        # Calculate the normalized rating on a scale of 1 to 10
        games_data['rating'] = games_data.apply(
            lambda row: calculate_game_rating(row['positive_ratings'], row['negative_ratings']), axis=1
        )

        # Parse owners range and calculate the average for popularity
        games_data['popularity'] = games_data['owners'].apply(parse_average_owners)

        print("Preview of games to be inserted:")
        print(games_data[['title', 'genre', 'rating', 'popularity']].head())  # Preview the data

        games = [
            Game(
                title=row['title'][:255],
                genre=row['genre'][:255] if pd.notna(row['genre']) else '',
                tags=row['tags'][:500] if pd.notna(row['tags']) else '',
                rating=row['rating'],
                popularity=row['popularity']  # Average of owners range
            )
            for _, row in games_data.iterrows()
        ]

        db.session.bulk_save_objects(games)
        db.session.commit()
        print("Games data loaded successfully!")

    except Exception as e:
        print(f"Error seeding games: {e}")
        db.session.rollback()


def calculate_game_rating(positive_ratings, negative_ratings):
    """Calculate a normalized rating on a scale of 1 to 10."""
    total_ratings = positive_ratings + negative_ratings

    if total_ratings == 0:
        return 5.0  # Default neutral rating if no ratings exist

    normalized_rating = positive_ratings / total_ratings
    return round(1 + 9 * normalized_rating, 1)  # Scale to 1-10 range


def parse_average_owners(owners_range):
    """Parse the owners range and calculate the average."""
    try:
        # Owners range format: "100,000 .. 200,000"
        min_owners, max_owners = map(lambda x: int(x.replace(',', '').strip()), owners_range.split('..'))
        return (min_owners + max_owners) // 2  # Calculate the average
    except Exception as e:
        print(f"Error parsing owners range '{owners_range}': {e}")
        return 0  # Default popularity if parsing fails
