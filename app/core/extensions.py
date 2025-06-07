from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flasgger import Swagger

db = SQLAlchemy()
jwt = JWTManager()
swagger = Swagger()
migrate = Migrate()


def register_extensions(app: Flask):
    jwt.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    swagger.init_app(app)
