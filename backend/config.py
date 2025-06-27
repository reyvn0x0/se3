import os
import urllib.parse
from datetime import timedelta

class Config:
    # MySQL Database Configuration (mit URL-Encoding)
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'RM1337ftw')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'stundenplan_db')
    
    # URL-Encoding f�r Passwort (wichtig bei Sonderzeichen)
    _encoded_password = urllib.parse.quote_plus(MYSQL_PASSWORD)
    
    # Sichere Database URI mit URL-Encoding
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{_encoded_password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
    
    # SQLAlchemy Configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'echo': False  # Set to True for SQL debugging
    }
    
    # Security Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'stundenplan-secret-key-2024')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-2024')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')
    
    # Upload Configuration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # Flask Configuration
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    @classmethod
    def debug_connection_string(cls):
        """Debug-Funktion f�r Verbindungsstring"""
        print(f"Host: {cls.MYSQL_HOST}")
        print(f"Port: {cls.MYSQL_PORT}")  
        print(f"User: {cls.MYSQL_USER}")
        print(f"Database: {cls.MYSQL_DB}")
        print(f"Password length: {len(cls.MYSQL_PASSWORD)}")
        print(f"Encoded password length: {len(cls._encoded_password)}")
        print(f"Connection URI: {cls.SQLALCHEMY_DATABASE_URI}")
