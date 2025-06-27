from flask import request, jsonify, g
from functools import wraps
import time
import logging

def register_middleware(app):
    """Register all middleware for the Flask app"""
    
    @app.before_request
    def before_request():
        """Execute before each request"""
        g.start_time = time.time()
        
        # Log request details
        app.logger.info(f'{request.method} {request.path} - {request.remote_addr}')
        
        # Validate Content-Type for POST/PUT requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json and request.content_type != 'multipart/form-data':
                return jsonify({
                    'error': 'Content-Type muss application/json oder multipart/form-data sein'
                }), 400
    
    @app.after_request
    def after_request(response):
        """Execute after each request"""
        # Calculate response time
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
            app.logger.info(f'Request completed in {response_time:.3f}s - Status: {response.status_code}')
        
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response
