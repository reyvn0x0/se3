import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Flask Configuration"""
    
    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database Configuration (MySQL)
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'stundenplan_db')
    
    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0,
    }
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # CORS Configuration
    CORS_ORIGINS = [
        'http://localhost:3000', 
        'http://127.0.0.1:3000',
        'http://localhost:5173',  # Vite dev server
        'http://127.0.0.1:5173'
    ]
    
    # File Upload Configuration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Timezone
    TIMEZONE = 'Europe/Berlin'