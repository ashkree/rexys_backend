import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from models import db, Game
from app import create_app


def extract_tags_with_tfidf(df, column='detailed_description', top_n=5):
    tfidf = TfidfVectorizer(stop_words='english', max_features=1000)
    tfidf_matrix = tfidf.fit_transform(df[column])
    feature_names = tfidf.get_feature_names_out()

    tags_list = []
    for row in tfidf_matrix:
        indices = row.toarray().argsort()[0, -top_n:][::-1]
        tags = [feature_names[i] for i in indices]
        tags_list.append(', '.join(tags))
    return tags_list


def extract_average_owners(owners_range):
    try:
        min_owners, max_owners = map(int, owners_range.split('-'))
        return (min_owners + max_owners) // 2
    except ValueError:
        return 0


def load_games(csv_path, limit=5000):
    # Load limited data
    df = pd.read_csv(csv_path, nrows=limit).fillna('')
    print(f"Loaded {len(df)} rows from CSV")

    # Generate tags
    df['Tags'] = extract_tags_with_tfidf(
        df, column='detailed_description', top_n=5)
    print("Generated tags using TF-IDF")

    # Create Game objects
    games = []
    for _, row in df.iterrows():
        try:
            # Calculate rating safely
            total_ratings = row['positive_ratings'] + row['negative_ratings']
            rating = row['positive_ratings'] / \
                total_ratings if total_ratings > 0 else 0

            game = Game(
                title=row['name'],
                genre=row['genres'],
                tags=row['Tags'],
                rating=rating * 10,  # Convert to 0-10 scale
                cost=row['price'],
                popularity=extract_average_owners(row['owners'])
            )
            games.append(game)
        except Exception as e:
            print(f"Error processing game {row['name']}: {e}")

    # Insert into database
    with create_app().app_context():
        db.session.bulk_save_objects(games)
        db.session.commit()
        print(f"Successfully inserted {len(games)} games")


if __name__ == "__main__":
    load_games('data/merged_steam_data.csv', limit=5000)
