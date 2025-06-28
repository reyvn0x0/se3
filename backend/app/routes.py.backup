from flask import Blueprint, jsonify
from app.models import DegreeProgram
from app import db

main = Blueprint('main', __name__)

@main.route("/degree_programs")
def show_degree_programs():
    """Studiengänge als JSON zurückgeben (statt Template)"""
    try:
        all_degree_programs = DegreeProgram.query.all()
        return jsonify({
            'degree_programs': [
                {
                    'id': dp.id if hasattr(dp, 'id') else None,
                    'name': dp.name if hasattr(dp, 'name') else str(dp)
                } 
                for dp in all_degree_programs
            ]
        })
    except Exception as e:
        # Fallback wenn Datenbank noch nicht existiert
        return jsonify({
            'degree_programs': [
                {'id': 1, 'name': 'Informatik'},
                {'id': 2, 'name': 'Wirtschaftsinformatik'},
                {'id': 3, 'name': 'Medieninformatik'}
            ],
            'note': 'Fallback-Daten (Datenbank nicht verfügbar)'
        })

@main.route("/")
def index():
    """Root-Route für das Backend"""
    return jsonify({
        'message': 'Stundenplan Backend API',
        'status': 'running',
        'endpoints': {
            'degree_programs': '/degree_programs',
            'api_health': '/api/health',
            'api_schedules': '/api/schedules'
        }
    })