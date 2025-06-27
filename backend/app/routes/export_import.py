from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Timetable, Course
from datetime import datetime
import json

export_import_bp = Blueprint('export_import', __name__)

@export_import_bp.route('/export/json/<int:timetable_id>', methods=['GET'])
@jwt_required()
def export_timetable_json(timetable_id):
    """Stundenplan als JSON exportieren"""
    try:
        current_user_id = get_jwt_identity()
        timetable = Timetable.query.filter_by(
            id=timetable_id,
            user_id=current_user_id
        ).first()
        
        if not timetable:
            return jsonify({'error': 'Stundenplan nicht gefunden'}), 404
        
        export_data = {
            'timetable': timetable.to_dict(),
            'export_info': {
                'exported_at': datetime.utcnow().isoformat(),
                'version': '1.0'
            }
        }
        
        return jsonify(export_data), 200
        
    except Exception as e:
        return jsonify({'error': f'Export fehlgeschlagen: {str(e)}'}), 500

@export_import_bp.route('/export/formats', methods=['GET'])
def get_export_formats():
    """Verfügbare Export-Formate abrufen"""
    return jsonify({
        'formats': [
            {
                'name': 'JSON',
                'extension': 'json',
                'description': 'JavaScript Object Notation',
                'supports_import': True
            }
        ]
    }), 200
