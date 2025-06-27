from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Course, Notification, Timetable
from datetime import datetime, timedelta

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    """Alle Benachrichtigungen des Benutzers abrufen"""
    try:
        current_user_id = get_jwt_identity()
        
        notifications = Notification.query.filter_by(user_id=current_user_id).order_by(Notification.created_at.desc()).all()
        
        return jsonify({
            'notifications': [notification.to_dict() for notification in notifications],
            'unread_count': Notification.query.filter_by(user_id=current_user_id, is_read=False).count()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Fehler beim Laden der Benachrichtigungen: {str(e)}'}), 500

@notifications_bp.route('/', methods=['POST'])
@jwt_required()
def create_notification():
    """Neue Benachrichtigung erstellen"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['title', 'message', 'notify_time']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} ist erforderlich'}), 400
        
        try:
            notify_time = datetime.fromisoformat(data['notify_time'].replace('Z', '+00:00'))
        except:
            return jsonify({'error': 'Ungültiges Zeitformat für notify_time'}), 400
        
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
        return jsonify({'error': f'Fehler beim Erstellen der Benachrichtigung: {str(e)}'}), 500
