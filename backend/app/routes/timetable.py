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
        return jsonify({'error': f'Stundenpläne konnten nicht geladen werden: {str(e)}'}), 500

@timetable_bp.route('/', methods=['POST'])
@jwt_required()
def create_timetable():
    """Neuen Stundenplan erstellen"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # Validation
        if not data.get('name'):
            return jsonify({'error': 'Name ist erforderlich'}), 400

        # Wenn dieser Stundenplan als aktiv markiert wird, andere deaktivieren
        if data.get('is_active', False):
            Timetable.query.filter_by(user_id=current_user_id).update({'is_active': False})

        timetable = Timetable(
            user_id=current_user_id,
            name=data['name'],
            semester=data.get('semester'),
            year=data.get('year'),
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
            'timetable': timetable.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': f'Stundenplan konnte nicht geladen werden: {str(e)}'}), 500

@timetable_bp.route('/<int:timetable_id>', methods=['PUT'])
@jwt_required()
def update_timetable(timetable_id):
    """Stundenplan bearbeiten"""
    try:
        current_user_id = get_jwt_identity()
        timetable = Timetable.query.filter_by(
            id=timetable_id,
            user_id=current_user_id
        ).first()

        if not timetable:
            return jsonify({'error': 'Stundenplan nicht gefunden'}), 404

        data = request.get_json()

        # Wenn dieser Stundenplan als aktiv markiert wird, andere deaktivieren
        if data.get('is_active', False):
            Timetable.query.filter_by(user_id=current_user_id).update({'is_active': False})

        # Update fields
        if 'name' in data:
            timetable.name = data['name']
        if 'semester' in data:
            timetable.semester = data['semester']
        if 'year' in data:
            timetable.year = data['year']
        if 'is_active' in data:
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

        db.session.delete(timetable)
        db.session.commit()

        return jsonify({
            'message': 'Stundenplan erfolgreich gelöscht'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Stundenplan konnte nicht gelöscht werden: {str(e)}'}), 500

@timetable_bp.route('/<int:timetable_id>/duplicate', methods=['POST'])
@jwt_required()
def duplicate_timetable(timetable_id):
    """Stundenplan duplizieren"""
    try:
        current_user_id = get_jwt_identity()
        original = Timetable.query.filter_by(
            id=timetable_id,
            user_id=current_user_id
        ).first()

        if not original:
            return jsonify({'error': 'Stundenplan nicht gefunden'}), 404

        data = request.get_json()
        new_name = data.get('name', f"{original.name} (Kopie)")

        # Create duplicate timetable
        duplicate = Timetable(
            user_id=current_user_id,
            name=new_name,
            semester=original.semester,
            year=original.year,
            is_active=False
        )

        db.session.add(duplicate)
        db.session.flush()  # Get ID

        # Duplicate all courses
        for course in original.courses:
            duplicate_course = Course(
                timetable_id=duplicate.id,
                name=course.name,
                code=course.code,
                instructor=course.instructor,
                room=course.room,
                description=course.description,
                color=course.color,
                day_of_week=course.day_of_week,
                start_time=course.start_time,
                end_time=course.end_time,
                course_type=course.course_type
            )
            db.session.add(duplicate_course)

        db.session.commit()

        return jsonify({
            'message': 'Stundenplan erfolgreich dupliziert',
            'timetable': duplicate.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Stundenplan konnte nicht dupliziert werden: {str(e)}'}), 500

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
        return jsonify({'error': f'Aktiver Stundenplan konnte nicht geladen werden: {str(e)}'}), 500