from flask import Flask, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__, static_folder='../frontend/build', static_url_path='/')
    
    # Konfiguration laden
    app.config.from_object('config.Config')
    
    # Extensions initialisieren
    db.init_app(app)
    jwt.init_app(app)
    
    # CORS für React Frontend
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Upload-Verzeichnis erstellen
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Error Handler und Middleware registrieren
    register_error_handlers(app)
    register_middleware(app)
    
    # Blueprints registrieren
    register_blueprints(app)
    
    # Root Route für React Frontend (Development)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_react_app(path):
        if path != "" and os.path.exists(app.static_folder + '/' + path):
            return send_from_directory(app.static_folder, path)
        else:
            # Für Development: JSON Response
            return jsonify({
                'message': '🎓 Stundenplan Backend API',
                'status': 'running',
                'version': '1.0.0',
                'frontend_note': 'React Frontend sollte auf Port 3000 laufen',
                'api_endpoints': {
                    'authentication': '/api/auth/*',
                    'timetables': '/api/timetable/*',
                    'courses': '/api/courses/*',
                    'notifications': '/api/notifications/*',
                    'import_export': '/api/data/*',
                    'health': '/api/health'
                },
                'documentation': 'Siehe README.md für vollständige API-Dokumentation'
            })
    
    # Datenbank-Tabellen erstellen
    with app.app_context():
        db.create_all()
        print("✅ Datenbank-Tabellen erstellt/überprüft")
    
    return app

def register_blueprints(app):
    """Alle Blueprints registrieren"""
    try:
        # Authentication
        from app.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        print("✅ Auth Routes geladen")
        
        # Timetable Management
        from app.routes.timetable import timetable_bp
        app.register_blueprint(timetable_bp, url_prefix='/api/timetable')
        print("✅ Timetable Routes geladen")
        
        # Course Management
        from app.routes.courses import courses_bp
        app.register_blueprint(courses_bp, url_prefix='/api/courses')
        print("✅ Course Routes geladen")
        
        # Notifications
        from app.routes.notifications import notifications_bp
        app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
        print("✅ Notification Routes geladen")
        
        # Import/Export
        from app.routes.export_import import export_import_bp
        app.register_blueprint(export_import_bp, url_prefix='/api/data')
        print("✅ Import/Export Routes geladen")
        
        # Health & API Routes
        from app.api_routes import api as api_blueprint
        app.register_blueprint(api_blueprint, url_prefix='/api')
        print("✅ API Routes geladen")
        
        # Optional: Bestehende routes (falls vorhanden)
        try:
            from app.routes import main as main_blueprint
            app.register_blueprint(main_blueprint)
            print("✅ Main Routes geladen")
        except ImportError:
            print("ℹ️  Main Routes übersprungen")
            
    except ImportError as e:
        print(f"⚠️  Route Import Fehler: {e}")
        # Minimale Fallback-Routen
        @app.route('/api/health')
        def health():
            return jsonify({'status': 'healthy', 'message': 'Backend läuft'})

def register_error_handlers(app):
    """Error Handler registrieren"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Ungültige Anfrage',
            'message': str(error.description) if hasattr(error, 'description') else 'Bad Request'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Nicht autorisiert',
            'message': 'Anmeldung erforderlich'
        }), 401
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Nicht gefunden',
            'message': 'Die angeforderte Ressource wurde nicht gefunden'
        }), 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error(f'Server Error: {error}')
        return jsonify({
            'error': 'Interner Serverfehler',
            'message': 'Ein unerwarteter Fehler ist aufgetreten'
        }), 500
    
    # JWT Error Handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token abgelaufen',
            'message': 'Bitte melden Sie sich erneut an'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'error': 'Ungültiger Token',
            'message': 'Token ist ungültig'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'error': 'Token fehlt',
            'message': 'Autorisierungs-Token erforderlich'
        }), 401

def register_middleware(app):
    """Middleware registrieren"""
    from flask import request, g
    import time
    
    @app.before_request
    def before_request():
        """Vor jeder Anfrage ausführen"""
        g.start_time = time.time()
        
        # Request Logging
        app.logger.info(f'{request.method} {request.path} - {request.remote_addr}')
        
        # Content-Type Validierung für POST/PUT
        if request.method in ['POST', 'PUT', 'PATCH']:
            if request.path.startswith('/api/') and not request.is_json and request.content_type != 'multipart/form-data':
                return jsonify({
                    'error': 'Content-Type muss application/json oder multipart/form-data sein'
                }), 400
    
    @app.after_request
    def after_request(response):
        """Nach jeder Anfrage ausführen"""
        # Response Zeit berechnen
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
            app.logger.info(f'Request completed in {response_time:.3f}s - Status: {response.status_code}')
        
        # Security Headers hinzufügen
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response