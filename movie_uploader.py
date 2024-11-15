import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from models import db, Movie
from app import app  # Import your Flask app


def extract_tags_with_tfidf(df, column='Overview', top_n=5):
    """
    Extract top N tags from the Overview column using TF-IDF.

    :param df: DataFrame containing movie data.
    :param column: Column name to extract tags from.
    :param top_n: Number of top tags to extract.
    :return: List of top tags for each movie.
    """
    # Initialize TF-IDF Vectorizer
    tfidf = TfidfVectorizer(stop_words='english', max_features=1000)

    # Fit TF-IDF on the Overview column
    tfidf_matrix = tfidf.fit_transform(df[column])

    # Get feature names (i.e., the terms)
    feature_names = tfidf.get_feature_names_out()

    # Extract top N tags for each movie
    tags_list = []
    for row in tfidf_matrix:
        indices = row.toarray().argsort()[0, -top_n:][::-1]  # Top N indices
        tags = [feature_names[i] for i in indices]
        tags_list.append(', '.join(tags))
    return tags_list


def load_movies_with_tfidf(csv_path):
    # Load CSV
    df = pd.read_csv(csv_path)

    # Clean and process data
    df = df.fillna('')
    df['No_of_Votes'] = df['No_of_Votes'].fillna(0).astype(int)
    df['Actors'] = df['Star1'] + ', ' + df['Star2'] + \
        ', ' + df['Star3'] + ', ' + df['Star4']

    # Generate tags using TF-IDF
    df['Tags'] = extract_tags_with_tfidf(df, column='Overview', top_n=5)

    # Transform into Movie objects
    movies = []
    for _, row in df.iterrows():
        movie = Movie(
            title=row['Series_Title'],
            genre=row['Genre'],
            tags=row['Tags'],  # Processed tags from TF-IDF
            rating=row['IMDB_Rating'],
            actors=row['Actors'],
            popularity=row['No_of_Votes']
        )
        movies.append(movie)

    # Insert into the database
    with app.app_context():
        db.session.bulk_save_objects(movies)
        db.session.commit()
        print(f"""Inserted {len(movies)}
              movies with TF-IDF tags into the database.""")


# Usage
load_movies_with_tfidf('data/imdb_top_1000.csv')
