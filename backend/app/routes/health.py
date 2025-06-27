from flask import Blueprint, jsonify, current_app
from app import db
from datetime import datetime
import os

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """System Health Check für Monitoring"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'environment': current_app.config.get('FLASK_ENV', 'unknown'),
            'checks': {}
        }
        
        # Database Health Check
        try:
            db.engine.execute('SELECT 1')
            health_status['checks']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            health_status['checks']['database'] = {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}'
            }
            health_status['status'] = 'unhealthy'
        
        # Bestimme HTTP Status Code
        if health_status['status'] == 'healthy':
            status_code = 200
        else:
            status_code = 503
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        error_response = {
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'message': f'Health check failed: {str(e)}'
        }
        return jsonify(error_response), 500

@health_bp.route('/ping', methods=['GET'])
def ping():
    """Einfacher Ping-Endpoint"""
    return jsonify({
        'message': 'pong',
        'timestamp': datetime.utcnow().isoformat()
    }), 200
