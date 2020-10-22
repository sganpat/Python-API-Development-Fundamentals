# import modules
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_uploads import UploadSet, IMAGES
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# create SQLAlchemy instance
db = SQLAlchemy()

# create JWT instance
jwt = JWTManager()

# Flask-Uploads
image_set = UploadSet('images', IMAGES)

# create Flask-Caching instance
cache = Cache()

# Flask limiter instance. 
limiter = Limiter(key_func=get_remote_address)  #limit by IP address
