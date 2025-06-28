from flask import Blueprint, jsonify, request
from app import db
from datetime import datetime

api = Blueprint('api', __name__)

# Health Check
@api.route('/health')
def health_check():
    """System Health Check"""
    try:
        # Test Datenbankverbindung
        db.session.execute('SELECT 1')
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'version': '1.0.0',
            'services': {
                'authentication': 'running',
                'timetables': 'running', 
                'courses': 'running',
                'notifications': 'running',
                'import_export': 'running'
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'disconnected',
            'error': str(e)
        }), 503

@api.route('/ping')
def ping():
    """Einfacher Ping-Endpoint"""
    return jsonify({
        'message': 'pong',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

# Basis API Info
@api.route('/')
def api_info():
    """API Informationen"""
    return jsonify({
        'name': 'Stundenplan Backend API',
        'version': '1.0.0',
        'description': 'Backend für Stundenplan-Management System',
        'endpoints': {
            'authentication': {
                'base_url': '/api/auth',
                'endpoints': [
                    'POST /register - Benutzer registrieren',
                    'POST /login - Benutzer anmelden', 
                    'GET /profile - Profil abrufen',
                    'PUT /profile - Profil aktualisieren',
                    'POST /change-password - Passwort ändern'
                ]
            },
            'timetables': {
                'base_url': '/api/timetable',
                'endpoints': [
                    'GET / - Alle Stundenpläne',
                    'POST / - Stundenplan erstellen',
                    'GET /{id} - Stundenplan abrufen',
                    'PUT /{id} - Stundenplan aktualisieren',
                    'DELETE /{id} - Stundenplan löschen',
                    'GET /active - Aktiven Stundenplan abrufen'
                ]
            },
            'courses': {
                'base_url': '/api/courses',
                'endpoints': [
                    'GET /timetable/{id} - Kurse eines Stundenplans',
                    'POST / - Kurs erstellen',
                    'GET /{id} - Kurs abrufen', 
                    'PUT /{id} - Kurs aktualisieren',
                    'DELETE /{id} - Kurs löschen',
                    'GET /{id}/comments - Kurs-Kommentare'
                ]
            },
            'notifications': {
                'base_url': '/api/notifications',
                'endpoints': [
                    'GET / - Benachrichtigungen abrufen',
                    'POST / - Benachrichtigung erstellen',
                    'POST /generate-all - Alle Benachrichtigungen generieren'
                ]
            },
            'import_export': {
                'base_url': '/api/data',
                'endpoints': [
                    'GET /export/{timetable_id}/{format} - Stundenplan exportieren',
                    'POST /import/{timetable_id} - Daten importieren',
                    'GET /template/{format} - Import-Template'
                ]
            }
        },
        'authentication': 'JWT Bearer Token required for most endpoints',
        'supported_formats': ['JSON', 'CSV', 'Excel'],
        'demo_credentials': {
            'username': 'demo_student',
            'password': 'demo123'
        }
    })

# Basis Stundenplan APIs für Legacy-Kompatibilität
schedules_db = [
    {"id": 1, "name": "Mein Stundenplan", "courses": []},
    {"id": 2, "name": "Backup Stundenplan", "courses": []}
]

@api.route('/schedules', methods=['GET'])
def get_schedules():
    """Legacy: Alle Stundenpläne abrufen"""
    return jsonify({
        'schedules': schedules_db,
        'count': len(schedules_db),
        'note': 'Legacy endpoint - use /api/timetable for full functionality'
    })

@api.route('/schedules', methods=['POST'])
def create_schedule():
    """Legacy: Neuen Stundenplan erstellen"""
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
            'schedule': new_schedule,
            'note': 'Legacy endpoint - use /api/timetable for full functionality'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/schedules/<int:schedule_id>', methods=['GET'])
def get_schedule(schedule_id):
    """Legacy: Einzelnen Stundenplan abrufen"""
    for schedule in schedules_db:
        if schedule["id"] == schedule_id:
            return jsonify({
                **schedule,
                'note': 'Legacy endpoint - use /api/timetable for full functionality'
            })
    
    return jsonify({'error': 'Stundenplan nicht gefunden'}), 404

@api.route('/schedules/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """Legacy: Stundenplan aktualisieren"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Keine Daten empfangen'}), 400
        
        for i, schedule in enumerate(schedules_db):
            if schedule["id"] == schedule_id:
                if 'name' in data:
                    schedules_db[i]['name'] = data['name']
                if 'courses' in data:
                    schedules_db[i]['courses'] = data['courses']
                
                return jsonify({
                    'message': 'Stundenplan aktualisiert',
                    'schedule': schedules_db[i],
                    'note': 'Legacy endpoint - use /api/timetable for full functionality'
                })
        
        return jsonify({'error': 'Stundenplan nicht gefunden'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Legacy: Stundenplan löschen"""
    global schedules_db
    original_length = len(schedules_db)
    schedules_db = [s for s in schedules_db if s["id"] != schedule_id]
    
    if len(schedules_db) < original_length:
        return jsonify({
            'message': 'Stundenplan gelöscht',
            'note': 'Legacy endpoint - use /api/timetable for full functionality'
        }), 200
    else:
        return jsonify({'error': 'Stundenplan nicht gefunden'}), 404

# Studiengänge API
@api.route('/degree-programs', methods=['GET'])
def get_degree_programs():
    """Alle Studiengänge abrufen"""
    try:
        from app.models import DegreeProgram
        degree_programs = DegreeProgram.query.all()
        
        return jsonify({
            'degree_programs': [dp.to_dict() for dp in degree_programs]
        })
    except Exception as e:
        # Fallback wenn Datenbank-Model noch nicht existiert
        return jsonify({
            'degree_programs': [
                {'id': 1, 'name': 'Informatik', 'code': 'INF'},
                {'id': 2, 'name': 'Wirtschaftsinformatik', 'code': 'WIN'},
                {'id': 3, 'name': 'Medieninformatik', 'code': 'MIN'},
                {'id': 4, 'name': 'Cyber Security', 'code': 'CYS'},
                {'id': 5, 'name': 'Data Science', 'code': 'DAS'}
            ],
            'note': 'Fallback data - database might not be initialized'
        })

# System Status
@api.route('/status')
def system_status():
    """System Status und Statistiken"""
    try:
        from app.models import User, Timetable, Course, Notification
        
        user_count = User.query.count()
        timetable_count = Timetable.query.count()
        course_count = Course.query.count()
        notification_count = Notification.query.count()
        
        return jsonify({
            'system': 'operational',
            'timestamp': datetime.utcnow().isoformat(),
            'statistics': {
                'users': user_count,
                'timetables': timetable_count,
                'courses': course_count,
                'notifications': notification_count
            },
            'database': 'connected',
            'uptime': 'Available via /api/health'
        })
        
    except Exception as e:
        return jsonify({
            'system': 'limited',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'database': 'error'
        }), 503