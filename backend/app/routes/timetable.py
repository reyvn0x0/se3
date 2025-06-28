from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Timetable
from datetime import datetime

timetable_bp = Blueprint('timetable', __name__)

@timetable_bp.route('/', methods=['GET'])
@jwt_required()
def get_user_timetables():
    """Alle Stundenpläne des Benutzers abrufen"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'Benutzer nicht gefunden'}), 404
        
        timetables = Timetable.query.filter_by(user_id=current_user_id).all()
        
        return jsonify({
            'timetables': [timetable.to_dict() for timetable in timetables],
            'count': len(timetables)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Stundenpläne konnten nicht geladen werden: {str(e)}'}), 500

@timetable_bp.route('/', methods=['POST'])
@jwt_required()
def create_timetable():
    """Neuen Stundenplan erstellen"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'Benutzer nicht gefunden'}), 404
        
        data = request.get_json()
        if not data or not data.get('name'):
            return jsonify({'error': 'Name ist erforderlich'}), 400
        
        # Check if user wants this as active timetable
        if data.get('is_active', False):
            # Deactivate other timetables
            Timetable.query.filter_by(user_id=current_user_id, is_active=True).update({'is_active': False})
        
        # Create new timetable
        timetable = Timetable(
            user_id=current_user_id,
            name=data['name'],
            description=data.get('description'),
            semester=data.get('semester'),
            year=data.get('year'),
            color_theme=data.get('color_theme', 'blue'),
            is_active=data.get('is_active', False)
        )
        
        db.session.add(timetable)
        db.session.commit()
        
        return jsonify({
            'message': 'Stundenplan erfolgreich erstellt',
            'timetable': timetable.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Stundenplan konnte nicht erstellt werden: {str(e)}'}), 500

@timetable_bp.route('/<int:timetable_id>', methods=['GET'])
@jwt_required()
def get_timetable(timetable_id):
    """Spezifischen Stundenplan mit Kursen abrufen"""
    try:
        current_user_id = get_jwt_identity()
        
        timetable = Timetable.query.filter_by(
            id=timetable_id, 
            user_id=current_user_id
        ).first()
        
        if not timetable:
            return jsonify({'error': 'Stundenplan nicht gefunden'}), 404
        
        return jsonify({
            'timetable': timetable.to_dict(include_courses=True)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Stundenplan konnte nicht geladen werden: {str(e)}'}), 500

@timetable_bp.route('/<int:timetable_id>', methods=['PUT'])
@jwt_required()
def update_timetable(timetable_id):
    """Stundenplan aktualisieren"""
    try:
        current_user_id = get_jwt_identity()
        
        timetable = Timetable.query.filter_by(
            id=timetable_id, 
            user_id=current_user_id
        ).first()
        
        if not timetable:
            return jsonify({'error': 'Stundenplan nicht gefunden'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Keine Daten empfangen'}), 400
        
        # Update fields
        if 'name' in data:
            timetable.name = data['name']
        if 'description' in data:
            timetable.description = data['description']
        if 'semester' in data:
            timetable.semester = data['semester']
        if 'year' in data:
            timetable.year = data['year']
        if 'color_theme' in data:
            timetable.color_theme = data['color_theme']
        
        # Handle is_active change
        if 'is_active' in data:
            if data['is_active']:
                # Deactivate other timetables
                Timetable.query.filter_by(user_id=current_user_id, is_active=True).update({'is_active': False})
            timetable.is_active = data['is_active']
        
        timetable.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Stundenplan erfolgreich aktualisiert',
            'timetable': timetable.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Stundenplan konnte nicht aktualisiert werden: {str(e)}'}), 500

@timetable_bp.route('/<int:timetable_id>', methods=['DELETE'])
@jwt_required()
def delete_timetable(timetable_id):
    """Stundenplan löschen"""
    try:
        current_user_id = get_jwt_identity()
        
        timetable = Timetable.query.filter_by(
            id=timetable_id, 
            user_id=current_user_id
        ).first()
        
        if not timetable:
            return jsonify({'error': 'Stundenplan nicht gefunden'}), 404
        
        # Don't delete if it's the only timetable
        user_timetables_count = Timetable.query.filter_by(user_id=current_user_id).count()
        if user_timetables_count <= 1:
            return jsonify({'error': 'Sie müssen mindestens einen Stundenplan behalten'}), 400
        
        db.session.delete(timetable)
        db.session.commit()
        
        return jsonify({
            'message': 'Stundenplan erfolgreich gelöscht'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Stundenplan konnte nicht gelöscht werden: {str(e)}'}), 500

@timetable_bp.route('/<int:timetable_id>/activate', methods=['POST'])
@jwt_required()
def activate_timetable(timetable_id):
    """Stundenplan als aktiv setzen"""
    try:
        current_user_id = get_jwt_identity()
        
        timetable = Timetable.query.filter_by(
            id=timetable_id, 
            user_id=current_user_id
        ).first()
        
        if not timetable:
            return jsonify({'error': 'Stundenplan nicht gefunden'}), 404
        
        # Deactivate all other timetables
        Timetable.query.filter_by(user_id=current_user_id).update({'is_active': False})
        
        # Activate this timetable
        timetable.is_active = True
        timetable.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Stundenplan aktiviert',
            'timetable': timetable.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Stundenplan konnte nicht aktiviert werden: {str(e)}'}), 500

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
            # If no active timetable, get the first one
            timetable = Timetable.query.filter_by(user_id=current_user_id).first()
            if timetable:
                timetable.is_active = True
                db.session.commit()
        
        if not timetable:
            return jsonify({'error': 'Kein Stundenplan gefunden'}), 404
        
        return jsonify({
            'timetable': timetable.to_dict(include_courses=True)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Aktiver Stundenplan konnte nicht geladen werden: {str(e)}'}), 500

@timetable_bp.route('/<int:timetable_id>/duplicate', methods=['POST'])
@jwt_required()
def duplicate_timetable(timetable_id):
    """Stundenplan duplizieren"""
    try:
        current_user_id = get_jwt_identity()
        
        original_timetable = Timetable.query.filter_by(
            id=timetable_id, 
            user_id=current_user_id
        ).first()
        
        if not original_timetable:
            return jsonify({'error': 'Stundenplan nicht gefunden'}), 404
        
        data = request.get_json() or {}
        
        # Create duplicate
        new_timetable = Timetable(
            user_id=current_user_id,
            name=data.get('name', f"{original_timetable.name} (Kopie)"),
            description=data.get('description', original_timetable.description),
            semester=data.get('semester', original_timetable.semester),
            year=data.get('year', original_timetable.year),
            color_theme=data.get('color_theme', original_timetable.color_theme),
            is_active=False
        )
        
        db.session.add(new_timetable)
        db.session.flush()  # Get the ID
        
        # Duplicate courses
        for course in original_timetable.courses:
            from app.models import Course
            new_course = Course(
                timetable_id=new_timetable.id,
                name=course.name,
                code=course.code,
                instructor=course.instructor,
                room=course.room,
                description=course.description,
                color=course.color,
                day_of_week=course.day_of_week,
                start_time=course.start_time,
                end_time=course.end_time,
                course_type=course.course_type,
                credits=course.credits,
                horst_url=course.horst_url,
                moodle_url=course.moodle_url,
                external_url=course.external_url,
                reminder_enabled=course.reminder_enabled,
                reminder_minutes=course.reminder_minutes
            )
            db.session.add(new_course)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Stundenplan erfolgreich dupliziert',
            'timetable': new_timetable.to_dict(include_courses=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Stundenplan konnte nicht dupliziert werden: {str(e)}'}), 500