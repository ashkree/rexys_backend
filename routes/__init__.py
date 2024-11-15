from .recommend import recommend_bp
from .rating import ratings_bp
from .auth import auth_bp


def register_blueprints(app):
    app.register_blueprint(recommend_bp, url_prefix='/recommend')
    app.register_blueprint(ratings_bp, url_prefix='/ratings')
    app.register_blueprint(auth_bp, url_prefix='/auth')
