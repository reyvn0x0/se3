from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Timetable, Course, CourseComment
from datetime import datetime, time
import re

courses_bp = Blueprint('courses', __name__)

def validate_time_format(time_str):
    """Zeitformat validieren (HH:MM)"""
    if not time_str:
        return False
    try:
        time.fromisoformat(str(time_str))
        return True
    except (ValueError, TypeError):
        return False

def validate_day_of_week(day):
    """Wochentag validieren (0=Montag, 6=Sonntag)"""
    try:
        return isinstance(day, int) and 0 <= day <= 6
    except:
        return False

def check_time_conflict(timetable_id, day_of_week, start_time, end_time, course_id=None):
    """Prüfen ob Zeitkonflikt mit anderen Kursen besteht"""
    try:
        query = Course.query.filter_by(
            timetable_id=timetable_id,
            day_of_week=day_of_week
        )

        if course_id:  # Bei Update den aktuellen Kurs ausschließen
            query = query.filter(Course.id != course_id)

        existing_courses = query.all()

        start_time_obj = time.fromisoformat(str(start_time))
        end_time_obj = time.fromisoformat(str(end_time))

        for course in existing_courses:
            # Überprüfen ob sich Zeiten überschneiden
            if not (end_time_obj <= course.start_time or start_time_obj >= course.end_time):
                return course.name

        return None
    except Exception:
        return None

@courses_bp.route('/', methods=['POST'])
@jwt_required()
def create_course():
    """Neuen Kurs erstellen"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Keine Daten empfangen'}), 400

        # Validation
        required_fields = ['timetable_id', 'name', 'day_of_week', 'start_time', 'end_time']
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({'error': f'{field} ist erforderlich'}), 400

        # Verify timetable ownership
        timetable = Timetable.query.filter_by(
            id=data['timetable_id'],
            user_id=current_user_id
        ).first()

        if not timetable:
            return jsonify({'error': 'Stundenplan nicht gefunden'}), 404

        # Validate day of week
        if not validate_day_of_week(data['day_of_week']):
            return jsonify({'error': 'Ungültiger Wochentag (0-6)'}), 400

        # Validate time format
        if not validate_time_format(data['start_time']) or not validate_time_format(data['end_time']):
            return jsonify({'error': 'Ungültiges Zeitformat (HH:MM)'}), 400

        # Check if end time is after start time
        start_time_obj = time.fromisoformat(str(data['start_time']))
        end_time_obj = time.fromisoformat(str(data['end_time']))

        if end_time_obj <= start_time_obj:
            return jsonify({'error': 'Endzeit muss nach Startzeit liegen'}), 400

        # Check for time conflicts
        conflict_course = check_time_conflict(
            data['timetable_id'],
            data['day_of_week'],
            data['start_time'],
            data['end_time']
        )

        if conflict_course:
            return jsonify({
                'error': f'Zeitkonflikt mit Kurs "{conflict_course}"'
            }), 400

        # Validate color format (hex color)
        color = data.get('color', '#3498db')
        if not re.match(r'^#[0-9A-Fa-f]{6}$', str(color)):
            color = '#3498db'

        course = Course(
            timetable_id=data['timetable_id'],
            name=str(data['name']),
            code=data.get('code'),
            instructor=data.get('instructor'),
            room=data.get('room'),
            description=data.get('description'),
            color=color,
            day_of_week=data['day_of_week'],
            start_time=start_time_obj,
            end_time=end_time_obj,
            course_type=data.get('course_type', 'Vorlesung')
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
    """Spezifischen Kurs abrufen"""
    try:
        current_user_id = get_jwt_identity()
        course = Course.query.join(Timetable).filter(
            Course.id == course_id,
            Timetable.user_id == current_user_id
        ).first()

        if not course:
            return jsonify({'error': 'Kurs nicht gefunden'}), 404

        return jsonify({
            'course': course.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': f'Kurs konnte nicht geladen werden: {str(e)}'}), 500

@courses_bp.route('/<int:course_id>', methods=['PUT'])
@jwt_required()
def update_course(course_id):
    """Kurs bearbeiten"""
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

        # Validate day of week if provided
        if 'day_of_week' in data and not validate_day_of_week(data['day_of_week']):
            return jsonify({'error': 'Ungültiger Wochentag (0-6)'}), 400

        # Validate time format if provided
        if 'start_time' in data and not validate_time_format(data['start_time']):
            return jsonify({'error': 'Ungültiges Startzeit-Format (HH:MM)'}), 400

        if 'end_time' in data and not validate_time_format(data['end_time']):
            return jsonify({'error': 'Ungültiges Endzeit-Format (HH:MM)'}), 400

        # Get current or new time values
        start_time_str = data.get('start_time', course.start_time.strftime('%H:%M'))
        end_time_str = data.get('end_time', course.end_time.strftime('%H:%M'))
        day_of_week = data.get('day_of_week', course.day_of_week)

        # Check if end time is after start time
        start_time_obj = time.fromisoformat(str(start_time_str))
        end_time_obj = time.fromisoformat(str(end_time_str))

        if end_time_obj <= start_time_obj:
            return jsonify({'error': 'Endzeit muss nach Startzeit liegen'}), 400

        # Check for time conflicts (exclude current course)
        conflict_course = check_time_conflict(
            course.timetable_id,
            day_of_week,
            start_time_str,
            end_time_str,
            course_id
        )

        if conflict_course:
            return jsonify({
                'error': f'Zeitkonflikt mit Kurs "{conflict_course}"'
            }), 400

        # Update fields
        if 'name' in data:
            course.name = str(data['name'])
        if 'code' in data:
            course.code = data['code']
        if 'instructor' in data:
            course.instructor = data['instructor']
        if 'room' in data:
            course.room = data['room']
        if 'description' in data:
            course.description = data['description']
        if 'color' in data:
            color = str(data['color'])
            if re.match(r'^#[0-9A-Fa-f]{6}$', color):
                course.color = color
        if 'day_of_week' in data:
            course.day_of_week = data['day_of_week']
        if 'start_time' in data:
            course.start_time = start_time_obj
        if 'end_time' in data:
            course.end_time = end_time_obj
        if 'course_type' in data:
            course.course_type = str(data['course_type'])

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

@courses_bp.route('/<int:course_id>/comments', methods=['GET'])
@jwt_required()
def get_course_comments(course_id):
    """Kommentare für einen Kurs abrufen"""
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
            'comments': [comment.to_dict() for comment in comments]
        }), 200

    except Exception as e:
        return jsonify({'error': f'Kommentare konnten nicht geladen werden: {str(e)}'}), 500

@courses_bp.route('/<int:course_id>/comments', methods=['POST'])
@jwt_required()
def add_course_comment(course_id):
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
            comment=str(data['comment'])
        )

        db.session.add(comment)
        db.session.commit()

        return jsonify({
            'message': 'Kommentar erfolgreich hinzugefügt',
            'comment': comment.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Kommentar konnte nicht hinzugefügt werden: {str(e)}'}), 500

@courses_bp.route('/comments/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(comment_id):
    """Kommentar bearbeiten"""
    try:
        current_user_id = get_jwt_identity()
        comment = CourseComment.query.join(Course).join(Timetable).filter(
            CourseComment.id == comment_id,
            Timetable.user_id == current_user_id
        ).first()

        if not comment:
            return jsonify({'error': 'Kommentar nicht gefunden'}), 404

        data = request.get_json()

        if not data or not data.get('comment'):
            return jsonify({'error': 'Kommentar ist erforderlich'}), 400

        comment.comment = str(data['comment'])
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
def delete_comment(comment_id):
    """Kommentar löschen"""
    try:
        current_user_id = get_jwt_identity()
        comment = CourseComment.query.join(Course).join(Timetable).filter(
            CourseComment.id == comment_id,
            Timetable.user_id == current_user_id
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

@courses_bp.route('/conflicts/<int:timetable_id>', methods=['GET'])
@jwt_required()
def check_conflicts(timetable_id):
    """Zeitkonflikte im Stundenplan prüfen"""
    try:
        current_user_id = get_jwt_identity()
        timetable = Timetable.query.filter_by(
            id=timetable_id,
            user_id=current_user_id
        ).first()

        if not timetable:
            return jsonify({'error': 'Stundenplan nicht gefunden'}), 404

        courses = Course.query.filter_by(timetable_id=timetable_id).all()
        conflicts = []

        for i, course1 in enumerate(courses):
            for course2 in courses[i+1:]:
                if (course1.day_of_week == course2.day_of_week and
                        not (course1.end_time <= course2.start_time or course1.start_time >= course2.end_time)):
                    conflicts.append({
                        'course1': course1.to_dict(),
                        'course2': course2.to_dict(),
                        'message': f'Zeitkonflikt zwischen "{course1.name}" und "{course2.name}"'
                    })

        return jsonify({
            'conflicts': conflicts,
            'count': len(conflicts)
        }), 200

    except Exception as e:
        return jsonify({'error': f'Konflikte konnten nicht geprüft werden: {str(e)}'}), 500