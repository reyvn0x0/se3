from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Timetable, Course
from datetime import datetime

timetable_bp = Blueprint('timetable', __name__)

@timetable_bp.route('/', methods=['GET'])
@jwt_required()
def get_timetables():
    """Alle Stundenpläne des Benutzers abrufen"""
    try:
        current_user_id = get_jwt_identity()
        timetables = Timetable.query.filter_by(user_id=current_user_id).all()
        
        return jsonify({
            'timetables': [timetable.to_dict() for timetable in timetables]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Fehler beim Laden der Stundenpläne: {str(e)}'}), 500

@timetable_bp.route('/active', methods=['GET'])
@jwt_required()
def get_active_timetable():
    """Aktiven Stundenplan abrufen"""
    try:
        current_user_id = get_jwt_identity()
        timetable = Timetable.query.filter_by(
            user_id=current_user_id, 
            is_active=True
        ).first()
        
        if not timetable:
            return jsonify({'error': 'Kein aktiver Stundenplan gefunden'}), 404
        
        return jsonify({
            'timetable': timetable.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Fehler beim Laden des aktiven Stundenplans: {str(e)}'}), 500

@timetable_bp.route('/', methods=['POST'])
@jwt_required()
def create_timetable():
    """Neuen Stundenplan erstellen"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({'error': 'Name ist erforderlich'}), 400
        
        timetable = Timetable(
            user_id=current_user_id,
            name=data['name'],
            is_active=data.get('is_active', True),
            semester=data.get('semester'),
            year=data.get('year')
        )
        
        db.session.add(timetable)
        db.session.commit()
        
        return jsonify({
            'message': 'Stundenplan erfolgreich erstellt',
            'timetable': timetable.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Fehler beim Erstellen des Stundenplans: {str(e)}'}), 500
