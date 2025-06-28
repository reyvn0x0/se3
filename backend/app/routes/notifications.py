from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Course, Notification, Timetable
from datetime import datetime, timedelta, time, date
import calendar

notifications_bp = Blueprint('notifications', __name__)

def create_course_notifications(course, user):
    """Automatische Benachrichtigungen für einen Kurs erstellen"""
    if not course.reminder_enabled or not user.notification_enabled:
        return []
    
    notifications = []
    
    # Get next occurrence of this course
    today = date.today()
    days_ahead = course.day_of_week - today.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    
    next_course_date = today + timedelta(days=days_ahead)
    
    # Create notification time (course start time minus reminder minutes)
    course_datetime = datetime.combine(next_course_date, course.start_time)
    notify_datetime = course_datetime - timedelta(minutes=course.reminder_minutes)
    
    # Only create notification if it's in the future
    if notify_datetime > datetime.now():
        notification = Notification(
            user_id=user.id,
            course_id=course.id,
            title=f"Erinnerung: {course.name}",
            message=f"Der Kurs '{course.name}' beginnt in {course.reminder_minutes} Minuten.",
            notification_type='course_start',
            notify_time=notify_datetime
        )
        notifications.append(notification)
    
    return notifications

@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_user_notifications():
    """Alle Benachrichtigungen des Benutzers abrufen"""
    try:
        current_user_id = get_jwt_identity()
        
        # Query parameters
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 50))
        
        query = Notification.query.filter_by(user_id=current_user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
        
        # Count unread notifications
        unread_count = Notification.query.filter_by(
            user_id=current_user_id, 
            is_read=False
        ).count()
        
        return jsonify({
            'notifications': [notification.to_dict() for notification in notifications],
            'count': len(notifications),
            'unread_count': unread_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Benachrichtigungen konnten nicht geladen werden: {str(e)}'}), 500

@notifications_bp.route('/', methods=['POST'])
@jwt_required()
def create_notification():
    """Manuelle Benachrichtigung erstellen"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Keine Daten empfangen'}), 400
        
        required_fields = ['title', 'message', 'notify_time']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} ist erforderlich'}), 400
        
        # Parse notify_time
        try:
            notify_time = datetime.fromisoformat(data['notify_time'].replace('Z', '+00:00'))
        except:
            return jsonify({'error': 'Ungültiges Datum-Format für notify_time'}), 400
        
        # Validate course_id if provided
        course = None
        if data.get('course_id'):
            course = Course.query.join(Timetable).filter(
                Course.id == data['course_id'],
                Timetable.user_id == current_user_id
            ).first()
            if not course:
                return jsonify({'error': 'Kurs nicht gefunden'}), 404
        
        notification = Notification(
            user_id=current_user_id,
            course_id=data.get('course_id'),
            title=data['title'],
            message=data['message'],
            notification_type=data.get('notification_type', 'reminder'),
            notify_time=notify_time
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'message': 'Benachrichtigung erfolgreich erstellt',
            'notification': notification.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Benachrichtigung konnte nicht erstellt werden: {str(e)}'}), 500

@notifications_bp.route('/<int:notification_id>', methods=['PUT'])
@jwt_required()
def update_notification(notification_id):
    """Benachrichtigung aktualisieren"""
    try:
        current_user_id = get_jwt_identity()
        
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user_id
        ).first()
        
        if not notification:
            return jsonify({'error': 'Benachrichtigung nicht gefunden'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Keine Daten empfangen'}), 400
        
        # Update fields
        if 'title' in data:
            notification.title = data['title']
        if 'message' in data:
            notification.message = data['message']
        if 'notification_type' in data:
            notification.notification_type = data['notification_type']
        if 'notify_time' in data:
            try:
                notification.notify_time = datetime.fromisoformat(data['notify_time'].replace('Z', '+00:00'))
            except:
                return jsonify({'error': 'Ungültiges Datum-Format'}), 400
        if 'is_read' in data:
            notification.is_read = data['is_read']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Benachrichtigung erfolgreich aktualisiert',
            'notification': notification.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Benachrichtigung konnte nicht aktualisiert werden: {str(e)}'}), 500

@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """Benachrichtigung löschen"""
    try:
        current_user_id = get_jwt_identity()
        
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user_id
        ).first()
        
        if not notification:
            return jsonify({'error': 'Benachrichtigung nicht gefunden'}), 404
        
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify({
            'message': 'Benachrichtigung erfolgreich gelöscht'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Benachrichtigung konnte nicht gelöscht werden: {str(e)}'}), 500

@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """Benachrichtigung als gelesen markieren"""
    try:
        current_user_id = get_jwt_identity()
        
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user_id
        ).first()
        
        if not notification:
            return jsonify({'error': 'Benachrichtigung nicht gefunden'}), 404
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({
            'message': 'Benachrichtigung als gelesen markiert'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Status konnte nicht aktualisiert werden: {str(e)}'}), 500

@notifications_bp.route('/mark-all-read', methods=['POST'])
@jwt_required()
def mark_all_notifications_read():
    """Alle Benachrichtigungen als gelesen markieren"""
    try:
        current_user_id = get_jwt_identity()
        
        Notification.query.filter_by(
            user_id=current_user_id,
            is_read=False
        ).update({'is_read': True})
        
        db.session.commit()
        
        return jsonify({
            'message': 'Alle Benachrichtigungen als gelesen markiert'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Status konnte nicht aktualisiert werden: {str(e)}'}), 500

@notifications_bp.route('/course/<int:course_id>/generate', methods=['POST'])
@jwt_required()
def generate_course_notifications(course_id):
    """Automatische Benachrichtigungen für einen Kurs generieren"""
    try:
        current_user_id = get_jwt_identity()
        
        course = Course.query.join(Timetable).filter(
            Course.id == course_id,
            Timetable.user_id == current_user_id
        ).first()
        
        if not course:
            return jsonify({'error': 'Kurs nicht gefunden'}), 404
        
        user = User.query.get(current_user_id)
        
        # Delete existing notifications for this course
        Notification.query.filter_by(
            user_id=current_user_id,
            course_id=course_id,
            is_sent=False
        ).delete()
        
        # Generate new notifications
        notifications = create_course_notifications(course, user)
        
        for notification in notifications:
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'message': f'{len(notifications)} Benachrichtigungen für "{course.name}" erstellt',
            'notifications': [n.to_dict() for n in notifications]
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Benachrichtigungen konnten nicht generiert werden: {str(e)}'}), 500

@notifications_bp.route('/generate-all', methods=['POST'])
@jwt_required()
def generate_all_notifications():
    """Automatische Benachrichtigungen für alle Kurse generieren"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user.notification_enabled:
            return jsonify({'error': 'Benachrichtigungen sind deaktiviert'}), 400
        
        # Get active timetable
        active_timetable = Timetable.query.filter_by(
            user_id=current_user_id,
            is_active=True
        ).first()
        
        if not active_timetable:
            return jsonify({'error': 'Kein aktiver Stundenplan gefunden'}), 404
        
        # Delete existing unsent course notifications
        Notification.query.filter_by(
            user_id=current_user_id,
            is_sent=False,
            notification_type='course_start'
        ).delete()
        
        # Generate notifications for all courses
        all_notifications = []
        for course in active_timetable.courses:
            if course.is_active:
                notifications = create_course_notifications(course, user)
                all_notifications.extend(notifications)
        
        for notification in all_notifications:
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'message': f'{len(all_notifications)} Benachrichtigungen erstellt',
            'notifications': [n.to_dict() for n in all_notifications]
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Benachrichtigungen konnten nicht generiert werden: {str(e)}'}), 500

@notifications_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_notifications():
    """Kommende Benachrichtigungen abrufen"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get notifications for the next 24 hours
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        
        notifications = Notification.query.filter(
            Notification.user_id == current_user_id,
            Notification.notify_time >= now,
            Notification.notify_time <= tomorrow,
            Notification.is_sent == False
        ).order_by(Notification.notify_time).all()
        
        return jsonify({
            'upcoming_notifications': [notification.to_dict() for notification in notifications],
            'count': len(notifications)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Kommende Benachrichtigungen konnten nicht geladen werden: {str(e)}'}), 500

@notifications_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_notification_settings():
    """Benachrichtigungseinstellungen abrufen"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        return jsonify({
            'notification_enabled': user.notification_enabled,
            'timezone': user.timezone
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Einstellungen konnten nicht geladen werden: {str(e)}'}), 500

@notifications_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_notification_settings():
    """Benachrichtigungseinstellungen aktualisieren"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Keine Daten empfangen'}), 400
        
        if 'notification_enabled' in data:
            user.notification_enabled = data['notification_enabled']
        if 'timezone' in data:
            user.timezone = data['timezone']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Einstellungen erfolgreich aktualisiert',
            'settings': {
                'notification_enabled': user.notification_enabled,
                'timezone': user.timezone
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Einstellungen konnten nicht aktualisiert werden: {str(e)}'}), 500