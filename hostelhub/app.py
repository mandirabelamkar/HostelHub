import os
import pymysql
from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, User
from routes import register_routes

def create_database_if_not_exists():
    config = Config()
    try:
        connection = pymysql.connect(
            host=config.DB_HOST,
            port=int(config.DB_PORT),
            user=config.DB_USER,
            password=config.DB_PASS
        )
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{config.DB_NAME}`;")
        connection.commit()
        connection.close()
        print(f"Database '{config.DB_NAME}' verified/created.")
    except Exception as e:
        print(f"Skipping MySQL database creation (falling back to generic SQL settings): {e}")

def create_app():
    # Ensure database exists before initializing SQLAlchemy
    create_database_if_not_exists()
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    # Register blueprints/routes
    register_routes(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
        
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)




