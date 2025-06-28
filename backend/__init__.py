from flask import Flask, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, static_folder='../frontend/build', static_url_path='/')
    
    # Konfiguration
    app.config.from_object('config.Config')
    
    # Extensions initialisieren
    db.init_app(app)
    
    # CORS für React Frontend
    CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])
    
    # Blueprints registrieren
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # API Blueprints
    from app.api_routes import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')
    
    # Error Handler für 404
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Nicht gefunden',
            'message': 'Die angeforderte Ressource wurde nicht gefunden'
        }), 404
    
    # Root Route für React Frontend (Development)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_react_app(path):
        if path != "" and os.path.exists(app.static_folder + '/' + path):
            return send_from_directory(app.static_folder, path)
        else:
            # Für Development: JSON Response
            return jsonify({
                'message': 'Flask Backend läuft!',
                'status': 'OK',
                'frontend_note': 'React Frontend sollte auf Port 3000 laufen',
                'available_endpoints': [
                    '/api/health',
                    '/api/schedules',
                    '/degree_programs'
                ]
            })
    
    # Datenbank erstellen
    with app.app_context():
        db.create_all()
    
    return app