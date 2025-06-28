from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Timetable, Course, CourseComment
from datetime import datetime, time
import re

courses_bp = Blueprint('courses', __name__)

def validate_time_format(time_str):
    """Zeit-Format validieren (HH:MM)"""
    try:
        time.fromisoformat(time_str)
        return True
    except:
        return False

def parse_time(time_str):
    """Zeit-String zu time Objekt konvertieren"""
    try:
        return time.fromisoformat(time_str)
    except:
        return None

@courses_bp.route('/timetable/<int:timetable_id>', methods=['GET'])
@jwt_required()
def get_timetable_courses(timetable_id):
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
            'courses': [course.to_dict() for course in courses],
            'count': len(courses)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Kurse konnten nicht geladen werden: {str(e)}'}), 500

@courses_bp.route('/', methods=['POST'])
@jwt_required()
def create_course():
    """Neuen Kurs erstellen"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Keine Daten empfangen'}), 400
        
        # Validate required fields
        required_fields = ['timetable_id', 'name', 'day_of_week', 'start_time', 'end_time']
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({'error': f'{field} ist erforderlich'}), 400
        
        # Verify timetable belongs to user
        timetable = Timetable.query.filter_by(
            id=data['timetable_id'], 
            user_id=current_user_id
        ).first()
        
        if not timetable:
            return jsonify({'error': 'Stundenplan nicht gefunden'}), 404
        
        # Validate time format
        start_time = parse_time(data['start_time'])
        end_time = parse_time(data['end_time'])
        
        if not start_time or not end_time:
            return jsonify({'error': 'Ungültiges Zeitformat (verwenden Sie HH:MM)'}), 400
        
        if start_time >= end_time:
            return jsonify({'error': 'Startzeit muss vor Endzeit liegen'}), 400
        
        # Validate day_of_week
        if not (0 <= data['day_of_week'] <= 6):
            return jsonify({'error': 'Wochentag muss zwischen 0 (Montag) und 6 (Sonntag) liegen'}), 400
        
        # Check for time conflicts
        existing_courses = Course.query.filter_by(
            timetable_id=data['timetable_id'],
            day_of_week=data['day_of_week']
        ).all()
        
        for course in existing_courses:
            if not (end_time <= course.start_time or start_time >= course.end_time):
                return jsonify({
                    'error': f'Zeitkonflikt mit Kurs "{course.name}" ({course.start_time.strftime("%H:%M")}-{course.end_time.strftime("%H:%M")})'
                }), 400
        
        # Create new course
        course = Course(
            timetable_id=data['timetable_id'],
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
            horst_url=data.get('horst_url'),
            moodle_url=data.get('moodle_url'),
            external_url=data.get('external_url'),
            reminder_enabled=data.get('reminder_enabled', True),
            reminder_minutes=data.get('reminder_minutes', 15)
        )
        
        db.session.add(course)
        db.session.commit()
        
        return jsonify({
            'message': 'Kurs erfolgreich erstellt',
            'course': course.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Kurs konnte nicht erstellt werden: {str(e)}'}), 500

@courses_bp.route('/<int:course_id>', methods=['GET'])
@jwt_required()
def get_course(course_id):
    """Spezifischen Kurs mit Details abrufen"""
    try:
        current_user_id = get_jwt_identity()
        
        course = Course.query.join(Timetable).filter(
            Course.id == course_id,
            Timetable.user_id == current_user_id
        ).first()
        
        if not course:
            return jsonify({'error': 'Kurs nicht gefunden'}), 404
        
        return jsonify({
            'course': course.to_dict(include_comments=True)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Kurs konnte nicht geladen werden: {str(e)}'}), 500

@courses_bp.route('/<int:course_id>', methods=['PUT'])
@jwt_required()
def update_course(course_id):
    """Kurs aktualisieren"""
    try:
        current_user_id = get_jwt_identity()
        
        course = Course.query.join(Timetable).filter(
            Course.id == course_id,
            Timetable.user_id == current_user_id
        ).first()
        
        if not course:
            return jsonify({'error': 'Kurs nicht gefunden'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Keine Daten empfangen'}), 400
        
        # Update basic fields
        if 'name' in data:
            course.name = data['name']
        if 'code' in data:
            course.code = data['code']
        if 'instructor' in data:
            course.instructor = data['instructor']
        if 'room' in data:
            course.room = data['room']
        if 'description' in data:
            course.description = data['description']
        if 'color' in data:
            course.color = data['color']
        if 'course_type' in data:
            course.course_type = data['course_type']
        if 'credits' in data:
            course.credits = data['credits']
        if 'horst_url' in data:
            course.horst_url = data['horst_url']
        if 'moodle_url' in data:
            course.moodle_url = data['moodle_url']
        if 'external_url' in data:
            course.external_url = data['external_url']
        if 'is_active' in data:
            course.is_active = data['is_active']
        if 'reminder_enabled' in data:
            course.reminder_enabled = data['reminder_enabled']
        if 'reminder_minutes' in data:
            course.reminder_minutes = data['reminder_minutes']
        
        # Handle time updates
        time_changed = False
        new_start_time = course.start_time
        new_end_time = course.end_time
        new_day = course.day_of_week
        
        if 'start_time' in data:
            new_start_time = parse_time(data['start_time'])
            if not new_start_time:
                return jsonify({'error': 'Ungültiges Startzeit-Format'}), 400
            time_changed = True
        
        if 'end_time' in data:
            new_end_time = parse_time(data['end_time'])
            if not new_end_time:
                return jsonify({'error': 'Ungültiges Endzeit-Format'}), 400
            time_changed = True
        
        if 'day_of_week' in data:
            if not (0 <= data['day_of_week'] <= 6):
                return jsonify({'error': 'Ungültiger Wochentag'}), 400
            new_day = data['day_of_week']
            time_changed = True
        
        # Validate time logic
        if new_start_time >= new_end_time:
            return jsonify({'error': 'Startzeit muss vor Endzeit liegen'}), 400
        
        # Check for conflicts if time changed
        if time_changed:
            existing_courses = Course.query.filter_by(
                timetable_id=course.timetable_id,
                day_of_week=new_day
            ).filter(Course.id != course_id).all()
            
            for existing_course in existing_courses:
                if not (new_end_time <= existing_course.start_time or new_start_time >= existing_course.end_time):
                    return jsonify({
                        'error': f'Zeitkonflikt mit Kurs "{existing_course.name}"'
                    }), 400
        
        # Apply time changes
        course.start_time = new_start_time
        course.end_time = new_end_time
        course.day_of_week = new_day
        course.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Kurs erfolgreich aktualisiert',
            'course': course.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Kurs konnte nicht aktualisiert werden: {str(e)}'}), 500

@courses_bp.route('/<int:course_id>', methods=['DELETE'])
@jwt_required()
def delete_course(course_id):
    """Kurs löschen"""
    try:
        current_user_id = get_jwt_identity()
        
        course = Course.query.join(Timetable).filter(
            Course.id == course_id,
            Timetable.user_id == current_user_id
        ).first()
        
        if not course:
            return jsonify({'error': 'Kurs nicht gefunden'}), 404
        
        db.session.delete(course)
        db.session.commit()
        
        return jsonify({
            'message': 'Kurs erfolgreich gelöscht'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Kurs konnte nicht gelöscht werden: {str(e)}'}), 500

# =================== COURSE COMMENTS ===================

@courses_bp.route('/<int:course_id>/comments', methods=['GET'])
@jwt_required()
def get_course_comments(course_id):
    """Kommentare eines Kurses abrufen"""
    try:
        current_user_id = get_jwt_identity()
        
        course = Course.query.join(Timetable).filter(
            Course.id == course_id,
            Timetable.user_id == current_user_id
        ).first()
        
        if not course:
            return jsonify({'error': 'Kurs nicht gefunden'}), 404
        
        comments = CourseComment.query.filter_by(course_id=course_id).all()
        
        return jsonify({
            'comments': [comment.to_dict() for comment in comments],
            'count': len(comments)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Kommentare konnten nicht geladen werden: {str(e)}'}), 500

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
        if not data or not data.get('comment'):
            return jsonify({'error': 'Kommentar ist erforderlich'}), 400
        
        comment = CourseComment(
            course_id=course_id,
            user_id=current_user_id,
            comment=data['comment'],
            comment_type=data.get('comment_type', 'note'),
            is_private=data.get('is_private', True)
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'message': 'Kommentar erfolgreich hinzugefügt',
            'comment': comment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Kommentar konnte nicht erstellt werden: {str(e)}'}), 500

@courses_bp.route('/comments/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_course_comment(comment_id):
    """Kommentar aktualisieren"""
    try:
        current_user_id = get_jwt_identity()
        
        comment = CourseComment.query.filter_by(
            id=comment_id,
            user_id=current_user_id
        ).first()
        
        if not comment:
            return jsonify({'error': 'Kommentar nicht gefunden'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Keine Daten empfangen'}), 400
        
        if 'comment' in data:
            comment.comment = data['comment']
        if 'comment_type' in data:
            comment.comment_type = data['comment_type']
        if 'is_private' in data:
            comment.is_private = data['is_private']
        
        comment.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Kommentar erfolgreich aktualisiert',
            'comment': comment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Kommentar konnte nicht aktualisiert werden: {str(e)}'}), 500

@courses_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_course_comment(comment_id):
    """Kommentar löschen"""
    try:
        current_user_id = get_jwt_identity()
        
        comment = CourseComment.query.filter_by(
            id=comment_id,
            user_id=current_user_id
        ).first()
        
        if not comment:
            return jsonify({'error': 'Kommentar nicht gefunden'}), 404
        
        db.session.delete(comment)
        db.session.commit()
        
        return jsonify({
            'message': 'Kommentar erfolgreich gelöscht'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Kommentar konnte nicht gelöscht werden: {str(e)}'}), 500