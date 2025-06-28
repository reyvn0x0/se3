from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Timetable, Course, CourseComment
from datetime import datetime, time
import json
import csv
import io
import pandas as pd
import tempfile
import os
from werkzeug.utils import secure_filename

export_import_bp = Blueprint('export_import', __name__)

ALLOWED_EXTENSIONS = {'csv', 'json', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_time_flexible(time_str):
    """Flexible Zeit-Parsing für verschiedene Formate"""
    if not time_str:
        return None
    
    # Bekannte Formate
    formats = ['%H:%M:%S', '%H:%M', '%H.%M', '%H,%M']
    
    for fmt in formats:
        try:
            return datetime.strptime(str(time_str).strip(), fmt).time()
        except:
            continue
    
    return None

def get_day_number(day_str):
    """Wochentag zu Nummer konvertieren"""
    if isinstance(day_str, int):
        return day_str if 0 <= day_str <= 6 else None
    
    day_mapping = {
        'monday': 0, 'montag': 0, 'mo': 0,
        'tuesday': 1, 'dienstag': 1, 'di': 1,
        'wednesday': 2, 'mittwoch': 2, 'mi': 2,
        'thursday': 3, 'donnerstag': 3, 'do': 3,
        'friday': 4, 'freitag': 4, 'fr': 4,
        'saturday': 5, 'samstag': 5, 'sa': 5,
        'sunday': 6, 'sonntag': 6, 'so': 6
    }
    
    return day_mapping.get(str(day_str).lower().strip())

# =================== EXPORT FUNCTIONS ===================

@export_import_bp.route('/export/<int:timetable_id>/<format>', methods=['GET'])
@jwt_required()
def export_timetable(timetable_id, format):
    """Stundenplan exportieren"""
    try:
        current_user_id = get_jwt_identity()
        
        # Verify timetable belongs to user
        timetable = Timetable.query.filter_by(
            id=timetable_id,
            user_id=current_user_id
        ).first()
        
        if not timetable:
            return jsonify({'error': 'Stundenplan nicht gefunden'}), 404
        
        if format not in ['json', 'csv', 'xlsx']:
            return jsonify({'error': 'Ungültiges Export-Format'}), 400
        
        courses = Course.query.filter_by(timetable_id=timetable_id).all()
        
        if format == 'json':
            return export_to_json(timetable, courses)
        elif format == 'csv':
            return export_to_csv(timetable, courses)
        elif format == 'xlsx':
            return export_to_excel(timetable, courses)
            
    except Exception as e:
        return jsonify({'error': f'Export fehlgeschlagen: {str(e)}'}), 500

def export_to_json(timetable, courses):
    """JSON Export"""
    data = {
        'timetable': timetable.to_dict(),
        'courses': [course.to_dict() for course in courses],
        'export_date': datetime.now().isoformat(),
        'format_version': '1.0'
    }
    
    # Create file
    json_data = json.dumps(data, indent=2, ensure_ascii=False)
    
    # Create in-memory file
    file_buffer = io.BytesIO()
    file_buffer.write(json_data.encode('utf-8'))
    file_buffer.seek(0)
    
    filename = f"stundenplan_{timetable.name}_{datetime.now().strftime('%Y%m%d')}.json"
    
    return send_file(
        file_buffer,
        mimetype='application/json',
        as_attachment=True,
        download_name=filename
    )

def export_to_csv(timetable, courses):
    """CSV Export"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Name', 'Code', 'Instructor', 'Room', 'Day', 'Start Time', 
        'End Time', 'Type', 'Credits', 'Description', 'Color', 'Horst URL'
    ])
    
    # Courses
    day_names = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    
    for course in courses:
        writer.writerow([
            course.name,
            course.code or '',
            course.instructor or '',
            course.room or '',
            day_names[course.day_of_week],
            course.start_time.strftime('%H:%M'),
            course.end_time.strftime('%H:%M'),
            course.course_type or '',
            course.credits or '',
            course.description or '',
            course.color or '',
            course.horst_url or ''
        ])
    
    # Create file
    file_buffer = io.BytesIO()
    file_buffer.write(output.getvalue().encode('utf-8'))
    file_buffer.seek(0)
    
    filename = f"stundenplan_{timetable.name}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return send_file(
        file_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

def export_to_excel(timetable, courses):
    """Excel Export"""
    # Create data for pandas
    day_names = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    
    course_data = []
    for course in courses:
        course_data.append({
            'Name': course.name,
            'Code': course.code or '',
            'Dozent': course.instructor or '',
            'Raum': course.room or '',
            'Wochentag': day_names[course.day_of_week],
            'Startzeit': course.start_time.strftime('%H:%M'),
            'Endzeit': course.end_time.strftime('%H:%M'),
            'Typ': course.course_type or '',
            'ECTS': course.credits or '',
            'Beschreibung': course.description or '',
            'Farbe': course.color or '',
            'Horst URL': course.horst_url or ''
        })
    
    # Create Excel file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        with pd.ExcelWriter(tmp_file.name, engine='openpyxl') as writer:
            # Timetable info
            timetable_info = pd.DataFrame([{
                'Stundenplan': timetable.name,
                'Semester': timetable.semester or '',
                'Jahr': timetable.year or '',
                'Beschreibung': timetable.description or '',
                'Erstellt': timetable.created_at.strftime('%d.%m.%Y'),
                'Export': datetime.now().strftime('%d.%m.%Y %H:%M')
            }])
            timetable_info.to_excel(writer, sheet_name='Info', index=False)
            
            # Courses
            if course_data:
                courses_df = pd.DataFrame(course_data)
                courses_df.to_excel(writer, sheet_name='Kurse', index=False)
        
        filename = f"stundenplan_{timetable.name}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return send_file(
            tmp_file.name,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

# =================== IMPORT FUNCTIONS ===================

@export_import_bp.route('/import/<int:timetable_id>', methods=['POST'])
@jwt_required()
def import_to_timetable(timetable_id):
    """Daten in bestehenden Stundenplan importieren"""
    try:
        current_user_id = get_jwt_identity()
        
        # Verify timetable belongs to user
        timetable = Timetable.query.filter_by(
            id=timetable_id,
            user_id=current_user_id
        ).first()
        
        if not timetable:
            return jsonify({'error': 'Stundenplan nicht gefunden'}), 404
        
        if 'file' not in request.files:
            return jsonify({'error': 'Keine Datei ausgewählt'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Keine Datei ausgewählt'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Ungültiger Dateityp. Erlaubt: CSV, JSON, Excel'}), 400
        
        # Parse file based on extension
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        
        if file_ext == 'json':
            result = import_from_json(file, timetable)
        elif file_ext == 'csv':
            result = import_from_csv(file, timetable)
        elif file_ext in ['xlsx', 'xls']:
            result = import_from_excel(file, timetable)
        else:
            return jsonify({'error': 'Nicht unterstütztes Dateiformat'}), 400
        
        return result
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Import fehlgeschlagen: {str(e)}'}), 500

def import_from_json(file, timetable):
    """JSON Import"""
    try:
        data = json.load(file)
        
        # Validate structure
        if 'courses' not in data:
            return jsonify({'error': 'Ungültige JSON-Struktur: "courses" fehlt'}), 400
        
        imported_courses = []
        errors = []
        
        for i, course_data in enumerate(data['courses']):
            try:
                # Required fields
                if not course_data.get('name'):
                    errors.append(f"Zeile {i+1}: Name fehlt")
                    continue
                
                # Parse times
                start_time = parse_time_flexible(course_data.get('start_time'))
                end_time = parse_time_flexible(course_data.get('end_time'))
                
                if not start_time or not end_time:
                    errors.append(f"Zeile {i+1}: Ungültige Zeitangaben")
                    continue
                
                # Parse day
                day_of_week = get_day_number(course_data.get('day_of_week'))
                if day_of_week is None:
                    errors.append(f"Zeile {i+1}: Ungültiger Wochentag")
                    continue
                
                # Create course
                course = Course(
                    timetable_id=timetable.id,
                    name=course_data['name'],
                    code=course_data.get('code'),
                    instructor=course_data.get('instructor'),
                    room=course_data.get('room'),
                    description=course_data.get('description'),
                    color=course_data.get('color', '#3498db'),
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                    course_type=course_data.get('course_type', 'Vorlesung'),
                    credits=course_data.get('credits'),
                    horst_url=course_data.get('horst_url')
                )
                
                db.session.add(course)
                imported_courses.append(course)
                
            except Exception as e:
                errors.append(f"Zeile {i+1}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'message': f'{len(imported_courses)} Kurse erfolgreich importiert',
            'imported_count': len(imported_courses),
            'errors': errors
        }), 201
        
    except json.JSONDecodeError:
        return jsonify({'error': 'Ungültige JSON-Datei'}), 400

def import_from_csv(file, timetable):
    """CSV Import"""
    try:
        # Read CSV
        content = file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content))
        
        imported_courses = []
        errors = []
        
        for i, row in enumerate(csv_reader):
            try:
                # Required fields
                if not row.get('Name') and not row.get('name'):
                    errors.append(f"Zeile {i+2}: Name fehlt")
                    continue
                
                name = row.get('Name') or row.get('name')
                
                # Parse times
                start_time_str = row.get('Start Time') or row.get('Startzeit') or row.get('start_time')
                end_time_str = row.get('End Time') or row.get('Endzeit') or row.get('end_time')
                
                start_time = parse_time_flexible(start_time_str)
                end_time = parse_time_flexible(end_time_str)
                
                if not start_time or not end_time:
                    errors.append(f"Zeile {i+2}: Ungültige Zeitangaben")
                    continue
                
                # Parse day
                day_str = row.get('Day') or row.get('Wochentag') or row.get('day_of_week')
                day_of_week = get_day_number(day_str)
                
                if day_of_week is None:
                    errors.append(f"Zeile {i+2}: Ungültiger Wochentag")
                    continue
                
                # Create course
                course = Course(
                    timetable_id=timetable.id,
                    name=name,
                    code=row.get('Code') or row.get('code'),
                    instructor=row.get('Instructor') or row.get('Dozent') or row.get('instructor'),
                    room=row.get('Room') or row.get('Raum') or row.get('room'),
                    description=row.get('Description') or row.get('Beschreibung') or row.get('description'),
                    color=row.get('Color') or row.get('Farbe') or row.get('color', '#3498db'),
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                    course_type=row.get('Type') or row.get('Typ') or row.get('course_type', 'Vorlesung'),
                    credits=int(row['Credits']) if row.get('Credits') and row['Credits'].isdigit() else None,
                    horst_url=row.get('Horst URL') or row.get('horst_url')
                )
                
                db.session.add(course)
                imported_courses.append(course)
                
            except Exception as e:
                errors.append(f"Zeile {i+2}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'message': f'{len(imported_courses)} Kurse erfolgreich importiert',
            'imported_count': len(imported_courses),
            'errors': errors
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'CSV-Import fehlgeschlagen: {str(e)}'}), 400

def import_from_excel(file, timetable):
    """Excel Import"""
    try:
        # Read Excel file
        df = pd.read_excel(file, sheet_name=0)  # First sheet
        
        imported_courses = []
        errors = []
        
        for i, row in df.iterrows():
            try:
                # Required fields
                name = row.get('Name') or row.get('name')
                if pd.isna(name) or not name:
                    errors.append(f"Zeile {i+2}: Name fehlt")
                    continue
                
                # Parse times
                start_time_str = row.get('Startzeit') or row.get('Start Time') or row.get('start_time')
                end_time_str = row.get('Endzeit') or row.get('End Time') or row.get('end_time')
                
                start_time = parse_time_flexible(start_time_str)
                end_time = parse_time_flexible(end_time_str)
                
                if not start_time or not end_time:
                    errors.append(f"Zeile {i+2}: Ungültige Zeitangaben")
                    continue
                
                # Parse day
                day_str = row.get('Wochentag') or row.get('Day') or row.get('day_of_week')
                day_of_week = get_day_number(day_str)
                
                if day_of_week is None:
                    errors.append(f"Zeile {i+2}: Ungültiger Wochentag")
                    continue
                
                # Create course
                course = Course(
                    timetable_id=timetable.id,
                    name=str(name),
                    code=str(row.get('Code', '')) if not pd.isna(row.get('Code')) else None,
                    instructor=str(row.get('Dozent', '')) if not pd.isna(row.get('Dozent')) else None,
                    room=str(row.get('Raum', '')) if not pd.isna(row.get('Raum')) else None,
                    description=str(row.get('Beschreibung', '')) if not pd.isna(row.get('Beschreibung')) else None,
                    color=str(row.get('Farbe', '#3498db')) if not pd.isna(row.get('Farbe')) else '#3498db',
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                    course_type=str(row.get('Typ', 'Vorlesung')) if not pd.isna(row.get('Typ')) else 'Vorlesung',
                    credits=int(row['ECTS']) if not pd.isna(row.get('ECTS')) and str(row.get('ECTS')).isdigit() else None,
                    horst_url=str(row.get('Horst URL', '')) if not pd.isna(row.get('Horst URL')) else None
                )
                
                db.session.add(course)
                imported_courses.append(course)
                
            except Exception as e:
                errors.append(f"Zeile {i+2}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'message': f'{len(imported_courses)} Kurse erfolgreich importiert',
            'imported_count': len(imported_courses),
            'errors': errors
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Excel-Import fehlgeschlagen: {str(e)}'}), 400

@export_import_bp.route('/template/<format>', methods=['GET'])
@jwt_required()
def download_template(format):
    """Import-Template herunterladen"""
    try:
        if format not in ['csv', 'xlsx']:
            return jsonify({'error': 'Ungültiges Template-Format'}), 400
        
        if format == 'csv':
            return create_csv_template()
        elif format == 'xlsx':
            return create_excel_template()
            
    except Exception as e:
        return jsonify({'error': f'Template konnte nicht erstellt werden: {str(e)}'}), 500

def create_csv_template():
    """CSV Template erstellen"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header with example
    writer.writerow(['Name', 'Code', 'Instructor', 'Room', 'Day', 'Start Time', 'End Time', 'Type', 'Credits', 'Description', 'Color', 'Horst URL'])
    writer.writerow(['Mathematik I', 'MATH101', 'Prof. Müller', 'A1.01', 'Montag', '08:00', '09:30', 'Vorlesung', '5', 'Grundlagen der Mathematik', '#3498db', 'https://horst.example.com/math101'])
    
    file_buffer = io.BytesIO()
    file_buffer.write(output.getvalue().encode('utf-8'))
    file_buffer.seek(0)
    
    return send_file(
        file_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name='stundenplan_template.csv'
    )

def create_excel_template():
    """Excel Template erstellen"""
    data = [{
        'Name': 'Mathematik I',
        'Code': 'MATH101',
        'Dozent': 'Prof. Müller',
        'Raum': 'A1.01',
        'Wochentag': 'Montag',
        'Startzeit': '08:00',
        'Endzeit': '09:30',
        'Typ': 'Vorlesung',
        'ECTS': 5,
        'Beschreibung': 'Grundlagen der Mathematik',
        'Farbe': '#3498db',
        'Horst URL': 'https://horst.example.com/math101'
    }]
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        with pd.ExcelWriter(tmp_file.name, engine='openpyxl') as writer:
            df = pd.DataFrame(data)
            df.to_excel(writer, sheet_name='Stundenplan', index=False)
        
        return send_file(
            tmp_file.name,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='stundenplan_template.xlsx'
        )