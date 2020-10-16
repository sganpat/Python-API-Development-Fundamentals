# import modules
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_uploads import UploadSet, IMAGES

# Database
db = SQLAlchemy()

# JWT
jwt = JWTManager()

# Flask-Uploads
image_set = UploadSet('images', IMAGES)

