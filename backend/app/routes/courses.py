from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Timetable, Course, CourseComment
from datetime import datetime, time

courses_bp = Blueprint('courses', __name__)

def validate_time_format(time_str):
    """Validate and convert time string to time object"""
    try:
        hour, minute = map(int, time_str.split(':'))
        return time(hour, minute)
    except:
        return None

@courses_bp.route('/timetable/<int:timetable_id>/courses', methods=['GET'])
@jwt_required()
def get_courses(timetable_id):
    """Alle Kurse eines Stundenplans abrufen"""
    try:
        current_user_id = get_jwt_identity()
        
        # Verify timetable belongs to user
        timetable = Timetable.query.filter_by(
            id=timetable_id,
            user_id=current_user_id
        ).first()
        
        if not timetable:
            return jsonify({'error': 'Stundenplan nicht gefunden'}), 404
        
        courses = Course.query.filter_by(timetable_id=timetable_id).all()
        
        return jsonify({
            'courses': [course.to_dict() for course in courses]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Fehler beim Laden der Kurse: {str(e)}'}), 500

@courses_bp.route('/timetable/<int:timetable_id>/courses', methods=['POST'])
@jwt_required()
def create_course(timetable_id):
    """Neuen Kurs erstellen"""
    try:
        current_user_id = get_jwt_identity()
        
        timetable = Timetable.query.filter_by(
            id=timetable_id,
            user_id=current_user_id
        ).first()
        
        if not timetable:
            return jsonify({'error': 'Stundenplan nicht gefunden'}), 404
        
        data = request.get_json()
        
        # Validation
        required_fields = ['name', 'day_of_week', 'start_time', 'end_time']
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({'error': f'{field} ist erforderlich'}), 400
        
        # Validate and convert times
        start_time = validate_time_format(data['start_time'])
        end_time = validate_time_format(data['end_time'])
        
        if not start_time or not end_time:
            return jsonify({'error': 'Ungültiges Zeitformat (HH:MM)'}), 400
        
        if start_time >= end_time:
            return jsonify({'error': 'Startzeit muss vor Endzeit liegen'}), 400
        
        course = Course(
            timetable_id=timetable_id,
            name=data['name'],
            code=data.get('code'),
            instructor=data.get('instructor'),
            room=data.get('room'),
            description=data.get('description'),
            color=data.get('color', '#3498db'),
            day_of_week=data['day_of_week'],
            start_time=start_time,
            end_time=end_time,
            course_type=data.get('course_type', 'Vorlesung'),
            credits=data.get('credits'),
            is_mandatory=data.get('is_mandatory', True),
            horst_link=data.get('horst_link')
        )
        
        db.session.add(course)
        db.session.commit()
        
        return jsonify({
            'message': 'Kurs erfolgreich erstellt',
            'course': course.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Fehler beim Erstellen des Kurses: {str(e)}'}), 500

@courses_bp.route('/<int:course_id>/comments', methods=['POST'])
@jwt_required()
def create_course_comment(course_id):
    """Kommentar zu einem Kurs hinzufügen"""
    try:
        current_user_id = get_jwt_identity()
        
        course = Course.query.join(Timetable).filter(
            Course.id == course_id,
            Timetable.user_id == current_user_id
        ).first()
        
        if not course:
            return jsonify({'error': 'Kurs nicht gefunden'}), 404
        
        data = request.get_json()
        
        if not data.get('comment'):
            return jsonify({'error': 'Kommentar ist erforderlich'}), 400
        
        comment = CourseComment(
            course_id=course_id,
            comment=data['comment']
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'message': 'Kommentar erfolgreich hinzugefügt',
            'comment': comment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Fehler beim Erstellen des Kommentars: {str(e)}'}), 500
