# import modules
from sys import maxsize
import uuid
import os
from passlib.hash import pbkdf2_sha256 
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from flask_uploads import extension
from PIL import Image 

# package imports
from extensions import image_set, cache

# hass password before storing in database
def hash_password(password):
    return pbkdf2_sha256.hash(password)

# check hashed password
def check_password(password, hashed):
    return pbkdf2_sha256.verify(password, hashed)

# generate token to for email verification
def generate_token(email, salt=None):
    serializer = URLSafeTimedSerializer(current_app.config.get('SECRET_KEY'))

    return serializer.dumps(email, salt=salt)

# verify token recieved from user
def verify_token(token, max_age=(30 * 60), salt=None):
    serializer = URLSafeTimedSerializer(current_app.config.get('SECRET_KEY'))

    try:
        email = serializer.loads(token, max_age=max_age, salt=salt)
    except:
        return False

    return email

# save image to specified folder
def save_image(image, folder):
    filename = '{}.{}'.format(uuid.uuid4(), extension(image.filename))
    image_set.save(image, folder=folder, name=filename)
    filename = compress_image(filename=filename, folder=folder)
    return filename

# shrink and compress images before saving
def compress_image(filename, folder):
    file_path = image_set.path(filename=filename, folder=folder)
    image = Image.open(file_path)

    if image.mode != "RGB":
        image = image.convert("RGB")
    
    if max(image.width, image.height) > 1600:
        maxsize = (1600, 1600)
        image.thumbnail(maxsize, Image.ANTIALIAS)

    compressed_filename = '{}.jpg'.format(uuid.uuid4())

    compressed_file_path = image_set.path(filename=compressed_filename, folder=folder)

    image.save(compressed_file_path, optimize=True, quality=85)

    original_size = os.stat(file_path).st_size

    compressed_size = os.stat(compressed_file_path).st_size

    percentage = round((original_size-compressed_size)/original_size*100)

    print("The file size is reduced by {}%, from {} to {}.".format(percentage, original_size, compressed_size))

    os.remove(file_path)

    return compressed_filename

# clear cache 
def clear_cache(key_prefix):
    keys = [key for key in cache.cache._cache.keys() if key.startswith(key_prefix)]
    cache.delete_many(*keys)