from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)

    # Many-to-many relationships
    rated_movies = db.relationship(
        'UserMovieRating', back_populates='user', cascade="all, delete-orphan")
    rated_games = db.relationship(
        'UserGameRating', back_populates='user', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class Movie(db.Model):
    __tablename__ = 'movies'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    genre = db.Column(db.String(500), nullable=False)
    tags = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    actors = db.Column(db.String(300), nullable=True)
    popularity = db.Column(db.Integer, nullable=True)

    # Many-to-many relationship
    rated_by_users = db.relationship(
        'UserMovieRating', back_populates='movie', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Movie {self.title}>"

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'genre': self.genre,
            'tags': [tag.strip() for tag in self.tags.split(',')] if self.tags else [],
            'actors': [actor.strip() for actor in self.actors.split(',')] if self.actors else [],
            'rating': self.rating,
            'popularity': self.popularity
        }


class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    genre = db.Column(db.String(500), nullable=False)
    tags = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    cost = db.Column(db.Float, nullable=True)
    popularity = db.Column(db.Integer, nullable=True)

    # Many-to-many relationship
    rated_by_users = db.relationship(
        'UserGameRating', back_populates='game', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Game {self.title}>"

    def to_dict(self):
        if hasattr(self, '_cached_dict'):
            return self._cached_dict

        self._cached_dict = {
            'id': self.id,
            'title': self.title,
            'genre': self.genre,
            'tags': [tag.strip() for tag in self.tags.split(',')] if self.tags else [],
            'rating': self.rating,
            'cost': self.cost,
            'popularity': self.popularity
        }
        return self._cached_dict


class UserMovieRating(db.Model):
    __tablename__ = 'user_movie_ratings'

    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.id'), primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey(
        'movies.id'), primary_key=True)
    rating = db.Column(db.Float, nullable=False)  # Rating score

    # Relationships
    user = db.relationship('User', back_populates='rated_movies')
    movie = db.relationship('Movie', back_populates='rated_by_users')

    def __repr__(self):
        return f"<UserMovieRating User {self.user_id}, Movie {self.movie_id}, Rating {self.rating}>"


class UserGameRating(db.Model):
    __tablename__ = 'user_game_ratings'

    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.id'), primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey(
        'games.id'), primary_key=True)
    rating = db.Column(db.Float, nullable=False)  # Rating score

    # Relationships
    user = db.relationship('User', back_populates='rated_games')
    game = db.relationship('Game', back_populates='rated_by_users')

    def __repr__(self):
        return f"<UserGameRating User {self.user_id}, Game {self.game_id}, Rating {self.rating}>"
