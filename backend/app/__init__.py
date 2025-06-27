from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('config.Config')
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register error handlers and middleware
    from app.error_handlers import register_error_handlers
    from app.middleware import register_middleware
    register_error_handlers(app)
    register_middleware(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.timetable import timetable_bp
    from app.routes.courses import courses_bp
    from app.routes.notifications import notifications_bp
    from app.routes.export_import import export_import_bp
    from app.routes.health import health_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(timetable_bp, url_prefix='/api/timetable')
    app.register_blueprint(courses_bp, url_prefix='/api/courses')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(export_import_bp, url_prefix='/api/data')
    app.register_blueprint(health_bp, url_prefix='/api')
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app
