# import modules
import os
from flask import request
from flask_jwt_extended.utils import get_current_user
from flask_restful import Resource
from http import HTTPStatus
from flask_jwt_extended import (
    get_jwt_identity, 
    jwt_required, 
    jwt_optional
)
from webargs import fields
from webargs.flaskparser import use_kwargs

# package imports
from models.recipe import Recipe
from schemas.recipe import RecipeSchema, RecipePaginationSchema
from utils import save_image, clear_cache
from extensions import image_set, cache, limiter


recipe_schema = RecipeSchema()
recipe_list_schema = RecipeSchema(many=True)
recipe_cover_schema = RecipeSchema(only=('recipe_cover_url',))
recipe_pagination_schema = RecipePaginationSchema()


class RecipeListResource(Resource):

    decorators = [limiter.limit('2 per minute', methods=['GET'], error_message='Too Many Requests')]
    
    @use_kwargs(
        {'q':fields.Str(missing=''),
        'page':fields.Int(missing=1), 
        'per_page':fields.Int(missing=3),
        'sort':fields.Str(missing='created_at'),
        'order':fields.Str(missing='desc')}
    )
    @cache.cached(timeout=60, query_string=True)
    def get(self, q, page, per_page, sort, order):

        # print('Querying database...')

        if sort not in ['created_at', 'cook_time', 'num_of_servings']:
            sort = 'created_at'
        
        if order not in ['asc', 'desc']:
            order = 'desc'
        
        paginated_recipes = Recipe.get_all_published(q, page, per_page, sort, order)

        return recipe_pagination_schema.dump(paginated_recipes).data, HTTPStatus.OK
    
    
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

        clear_cache('/recipes')

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
        recipe.ingredients = data.get('ingredients') or recipe.ingredients

        recipe.save()

        clear_cache('/recipes')

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

        clear_cache('/recipes')

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

        clear_cache('/recipes')

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

        clear_cache('/recipes')
        
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

        clear_cache('/recipes')

        return recipe_cover_schema.dump(recipe).data, HTTPStatus.OK



    