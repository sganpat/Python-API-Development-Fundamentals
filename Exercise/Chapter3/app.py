from flask import Flask
from flask_migrate import Migrate, migrate
from flask_restful import Api
from config import Config
from extensions import db
# from models.user import User # already imported in resources.user
from resources.recipe import RecipeListResource, RecipeResource, RecipePublishResource
from resources.user import UserListResource

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    register_extensions(app)
    register_resources(app)
    return app

def register_extensions(app):
    db.init_app(app)
    migrate = Migrate(app, db)

def register_resources(app):
    api = Api(app)
    api.add_resource(UserListResource, '/users')
    api.add_resource(RecipeListResource, '/recipes')
    api.add_resource(RecipeResource, '/recipes/<int:recipe_id>')
    api.add_resource(RecipePublishResource, '/recipe/<int:recipe_id>/publish')


if __name__ == '__main__':
    app = create_app()
    app.run()

