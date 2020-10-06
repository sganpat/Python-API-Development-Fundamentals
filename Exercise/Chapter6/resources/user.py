# import modules
from flask import request, url_for, render_template
from flask_restful import Resource
from flask_jwt_extended import (
    jwt_optional, 
    get_jwt_identity, 
    jwt_required
)
from http import HTTPStatus
from webargs import fields
from webargs.flaskparser import use_kwargs
import os


# package imports
from utils import hash_password, generate_token, verify_token
from models.user import User 
from schemas.user import UserSchema
from models.recipe import Recipe 
from schemas.recipe import RecipeSchema 
from mailgun import MailgunApi


user_schema = UserSchema()
user_public_schema = UserSchema(exclude=('email',))
recipe_list_schema = RecipeSchema(many=True)

mailgun = MailgunApi(
    domain = os.environ.get('MAILGUN_DOMAIN'),
    api_key = os.environ.get('MAILGUN_API_KEY')
)

class UserListResource(Resource):
    def post(self):
        json_data = request.get_json()

        data, errors = user_schema.load(data=json_data)

        if errors:
            return {'message':'Validation errors', 'errors':errors}, HTTPStatus.BAD_REQUEST

        if User.get_by_username(data.get('username')):
            return {'message':'username already in use'}, HTTPStatus.BAD_REQUEST
        
        if User.get_by_email(data.get('email')):
            return {'message':'email already in use'}, HTTPStatus.BAD_REQUEST
        
        user = User(**data)

        user.save()

        token = generate_token(user.email, salt='activate')
        subject = 'Please confirm your registration.'

        link = url_for(
            'useractivateresource',
            token=token,
            _external=True
        )

        text = 'Hi,\n \
            Thanks for using SmileCook! \
            Please confirm your registration by clicking on the link:\n \
            {}'.format(link)

        mailgun.send_email(
            to=user.email,
            subject=subject,
            text=text,
            html=render_template('action.html', activation_link=link)
        )

        return user_schema.dump(user).data, HTTPStatus.CREATED


class UserActivateResource(Resource):

    def get(self, token):
        email = verify_token(token, salt='activate')

        if email is False:
            return {'message':'Invalid token or token expired'}, HTTPStatus.BAD_REQUEST

        user = User.get_by_email(email = email)

        if not user:
            return {'message':'User not found'}, HTTPStatus.NOT_FOUND
        
        if user.is_active is True:
            return {'message':'User account is already activated'}, HTTPStatus.BAD_REQUEST
        
        user.is_active = True

        user.save()

        return {'message':'User activated'}, HTTPStatus.OK


class UserResource(Resource):

    @jwt_optional
    def get (self, username):

        user = User.get_by_username(username=username)

        if user is None:
            return {'message':'user not found'}, HTTPStatus.NOT_FOUND

        current_user = get_jwt_identity()

        if current_user == user.id:
            data = user_schema.dump(user).data 
        else:
            data = user_public_schema.dump(user).data

        return data, HTTPStatus.OK


class MeResource(Resource):

    @jwt_required
    def get(self):
        user = User.get_by_id(id=get_jwt_identity())

        return user_schema.dump(user).data, HTTPStatus.OK


class UserRecipeListResource(Resource):

    @jwt_optional
    @use_kwargs({'visibility':fields.Str(missing='public')})
    def get(self, username, visibility):
        user = User.get_by_username(username=username)

        if user is None:
            return {'message':'User not found'}, HTTPStatus.NOT_FOUND
        
        current_user = get_jwt_identity()

        if current_user == user.id and visibility in ['all', 'private']:
            pass
        else:
            visibility = 'public'
        
        recipes = Recipe.get_all_by_user(user_id=user.id, visibility=visibility)

        return recipe_list_schema.dump(recipes).data, HTTPStatus.OK


