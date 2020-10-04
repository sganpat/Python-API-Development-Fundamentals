from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

# Database
db = SQLAlchemy()

# JWT
jwt = JWTManager()
