from flask import Blueprint, jsonify, request
from app import db
from datetime import datetime

api = Blueprint('api', __name__)

# Health Check
@api.route('/health')
def health_check():
    """System Health Check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'Backend läuft erfolgreich!'
    }), 200

# Basis Stundenplan APIs (für Frontend)
schedules_db = [
    {"id": 1, "name": "Mein Stundenplan", "courses": []},
    {"id": 2, "name": "Backup Stundenplan", "courses": []}
]

@api.route('/schedules', methods=['GET'])
def get_schedules():
    """Alle Stundenpläne abrufen"""
    return jsonify({
        'schedules': schedules_db,
        'count': len(schedules_db)
    })

@api.route('/schedules', methods=['POST'])
def create_schedule():
    """Neuen Stundenplan erstellen"""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Name ist erforderlich'}), 400
        
        new_schedule = {
            "id": len(schedules_db) + 1,
            "name": data['name'],
            "courses": []
        }
        schedules_db.append(new_schedule)
        
        return jsonify({
            'message': 'Stundenplan erstellt',
            'schedule': new_schedule
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/schedules/<int:schedule_id>', methods=['GET'])
def get_schedule(schedule_id):
    """Einzelnen Stundenplan abrufen"""
    for schedule in schedules_db:
        if schedule["id"] == schedule_id:
            return jsonify(schedule)
    
    return jsonify({'error': 'Stundenplan nicht gefunden'}), 404