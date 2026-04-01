import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-hostelhub-key'
    
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASS = os.environ.get('DB_PASS', '')
    DB_NAME = os.environ.get('DB_NAME', 'hostelhub')    
    # SQLAlchemy configuration
    # Try using MySQL, fallback or override to SQLite for dev test
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), 'hostelhub.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
