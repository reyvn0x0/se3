from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Timetable, Course
from datetime import datetime
import json

export_import_bp = Blueprint('export_import', __name__)

@export_import_bp.route('/export/timetable/<int:timetable_id>', methods=['GET'])
@jwt_required()
def export_timetable(timetable_id):
    """Stundenplan exportieren"""
    try:
        current_user_id = get_jwt_identity()
        
        timetable = Timetable.query.filter_by(
            id=timetable_id,
            user_id=current_user_id
        ).first()
        
        if not timetable:
            return jsonify({'error': 'Stundenplan nicht gefunden'}), 404
        
        timetable_data = {
            'timetable': {
                'id': timetable.id,
                'name': timetable.name,
                'semester': timetable.semester,
                'year': timetable.year,
                'exported_at': datetime.utcnow().isoformat(),
                'courses': []
            }
        }
        
        for course in timetable.courses:
            course_data = {
                'name': course.name,
                'code': course.code,
                'instructor': course.instructor,
                'room': course.room,
                'description': course.description,
                'color': course.color,
                'day_of_week': course.day_of_week,
                'start_time': course.start_time.strftime('%H:%M'),
                'end_time': course.end_time.strftime('%H:%M'),
                'course_type': course.course_type,
                'credits': course.credits,
                'is_mandatory': course.is_mandatory,
                'horst_link': course.horst_link
            }
            timetable_data['timetable']['courses'].append(course_data)
        
        return jsonify(timetable_data), 200
        
    except Exception as e:
        return jsonify({'error': f'Fehler beim Exportieren: {str(e)}'}), 500

@export_import_bp.route('/import/timetable', methods=['POST'])
@jwt_required()
def import_timetable():
    """Stundenplan importieren"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Keine Daten zum Importieren'}), 400
        
        timetable_name = data.get('name', 'Importierter Stundenplan')
        
        timetable = Timetable(
            user_id=current_user_id,
            name=timetable_name,
            is_active=False
        )
        
        db.session.add(timetable)
        db.session.flush()
        
        courses_data = data.get('courses', [])
        imported_courses = []
        
        for course_data in courses_data:
            try:
                if not course_data.get('name'):
                    continue
                
                start_time = datetime.strptime(course_data['start_time'], '%H:%M').time()
                end_time = datetime.strptime(course_data['end_time'], '%H:%M').time()
                
                course = Course(
                    timetable_id=timetable.id,
                    name=course_data['name'],
                    code=course_data.get('code'),
                    instructor=course_data.get('instructor'),
                    room=course_data.get('room'),
                    description=course_data.get('description'),
                    color=course_data.get('color', '#3498db'),
                    day_of_week=course_data.get('day_of_week', 0),
                    start_time=start_time,
                    end_time=end_time,
                    course_type=course_data.get('course_type', 'Vorlesung'),
                    credits=course_data.get('credits'),
                    is_mandatory=course_data.get('is_mandatory', True),
                    horst_link=course_data.get('horst_link')
                )
                
                db.session.add(course)
                imported_courses.append(course_data['name'])
                
            except Exception:
                continue
        
        db.session.commit()
        
        return jsonify({
            'message': 'Import erfolgreich abgeschlossen',
            'timetable': timetable.to_dict(),
            'imported_courses': len(imported_courses)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Fehler beim Importieren: {str(e)}'}), 500
