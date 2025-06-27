from flask import jsonify, request
from flask_jwt_extended.exceptions import JWTExtendedException
from werkzeug.exceptions import HTTPException
import logging

def register_error_handlers(app):
    """Register all error handlers for the Flask app"""
    
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
    @app.errorhandler(JWTExtendedException)
    def handle_jwt_exceptions(error):
        return jsonify({
            'error': 'JWT-Fehler',
            'message': str(error)
        }), 401
