# import modules
import os
from flask import request
from flask.globals import current_app
from flask_jwt_extended.utils import get_current_user
from flask_restful import Resource
from http import HTTPStatus
from flask_jwt_extended import (
    get_jwt_identity, 
    jwt_required, 
    jwt_optional
)

# package imports
from models.recipe import Recipe
from schemas.recipe import RecipeSchema
from utils import save_image
from extensions import image_set


recipe_schema = RecipeSchema()
recipe_list_schema = RecipeSchema(many=True)
recipe_cover_schema = RecipeSchema(only=('recipe_cover_url',))

class RecipeListResource(Resource):
    
    def get(self):
        recipes = Recipe.get_all_published()

        return recipe_list_schema.dump(recipes).data, HTTPStatus.OK
    
    
    @jwt_required
    def post(self):
        json_data = request.get_json()
        current_user = get_jwt_identity()
        data, errors = recipe_schema.load(data=json_data)

        if errors:
            return {'message':'Validation errors', 'errors':'errors'}, HTTPStatus.BAD_REQUEST

        recipe = Recipe(**data)

        recipe.user_id = current_user

        recipe.save()

        return recipe_schema.dump(recipe).data, HTTPStatus.CREATED



class RecipeResource(Resource):

    @jwt_optional
    def get(self, recipe_id):
        recipe = Recipe.get_by_id(recipe_id=recipe_id)

        if recipe is None:
            return {'message':'recipe not found'}, HTTPStatus.NOT_FOUND

        current_user = get_jwt_identity()

        if recipe.is_publish == False and recipe.user_id != current_user:
            return {'message':'Access is not allowed'}, HTTPStatus.FORBIDDEN

        return recipe_schema.dump(recipe).data, HTTPStatus.OK


    @jwt_required
    def put(self, recipe_id):
        json_data = request.get_json()

        recipe = Recipe.get_by_id(recipe_id=recipe_id)

        if recipe is None:
            return {'message':'recipe not found'}, HTTPStatus.NOT_FOUND

        current_user = get_jwt_identity()

        if current_user != recipe.user_id:
            return {'message':'Access is not allowed'}, HTTPStatus.FORBIDDEN

        recipe.name = json_data['name']
        recipe.description = json_data['description']
        recipe.num_of_servings = json_data['num_of_servings']
        recipe.cook_time = json_data['cook_time']
        recipe.directions = json_data['directions']
        
        recipe.save()

        return recipe.data(), HTTPStatus.OK


    @jwt_required
    def patch(self, recipe_id):
        json_data = request.get_json()

        data, errors = recipe_schema.load(data=json_data, partial=('name',))

        if errors:
            return {'message':'Validation errors', 'errors': errors}, HTTPStatus.BAD_REQUEST
        
        recipe = Recipe.get_by_id(recipe_id=recipe_id)

        if recipe is None:
            return {'message':'Recipe not found'}, HTTPStatus.NOT_FOUND
        
        current_user = get_jwt_identity()

        if current_user != recipe.user_id:
            return {'message':'Access denied'}, HTTPStatus.FORBIDDEN
        
        recipe.name = data.get('name') or recipe.name
        recipe.description = data.get('description') or recipe.description
        recipe.num_of_servings = data.get('num_of_servings') or recipe.num_of_servings
        recipe.cook_time = data.get('cook_time') or recipe.cook_time
        recipe.directions = data.get('directions') or recipe.directions

        recipe.save()

        return recipe_schema.dump(recipe).data, HTTPStatus.OK


    @jwt_required
    def delete(self, recipe_id):
        recipe = Recipe.get_by_id(recipe_id=recipe_id)

        if recipe is None:
            return {'message':'recipe not found'}, HTTPStatus.NOT_FOUND

        current_user = get_jwt_identity()

        if current_user != recipe.user_id:
            return {'message':'Access is not allowed'}, HTTPStatus.FORBIDDEN

        recipe.delete()

        return {'message':'recipe deleted'}, HTTPStatus.OK



class RecipePublishResource(Resource):

    @jwt_required
    def put(self, recipe_id):
        recipe = Recipe.get_by_id(recipe_id=recipe_id)

        if recipe is None:
            return {'message':'recipe not found'}, HTTPStatus.NOT_FOUND
        
        current_user = get_jwt_identity()

        if current_user != recipe.user_id:
            return {'message':'Access denied'}, HTTPStatus.FORBIDDEN

        recipe.is_publish = True

        recipe.save()

        return {'message':'recipe published'}, HTTPStatus.OK
    

    @jwt_required
    def delete(self, recipe_id):
        recipe = Recipe.get_by_id(recipe_id=recipe_id)

        if recipe is None:
            return {'message':'recipe not found'}, HTTPStatus.NOT_FOUND

        current_user = get_jwt_identity()

        if current_user != recipe.user_id:
            return {'message':'Access denied'}, HTTPStatus.FORBIDDEN

        recipe.is_publish = False

        recipe.save()
        
        return {'message':'recipe unpublished'}, HTTPStatus.OK
    

class RecipeCoverUploadResource(Resource):

    @jwt_required
    def put(self, recipe_id):
        recipe = Recipe.get_by_id(recipe_id=recipe_id)

        if recipe is None:
            return {'message':'recipe not found'}, HTTPStatus.NOT_FOUND
        
        current_user = get_jwt_identity()

        if current_user != recipe.user_id:
            return {'message':'Access denied'}, HTTPStatus.FORBIDDEN
        
        file = request.files.get('cover')

        if not file:
            return {'message':'Not a valid image'}, HTTPStatus.BAD_REQUEST

        if not image_set.file_allowed(file, file.filename):
            return {'message':'File type not allowed'}, HTTPStatus.BAD_REQUEST

        if recipe.cover_image:
            cover_path = image_set.path(folder='covers', filename=recipe.cover_image)

            if os.path.exists(cover_path):
                os.remove(cover_path)

        filename = save_image(image=file, folder='covers')
        recipe.cover_image = filename
        recipe.save()

        return recipe_cover_schema.dump(recipe).data, HTTPStatus.OK



    