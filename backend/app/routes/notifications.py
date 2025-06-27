from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Notification
from datetime import datetime

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    """Alle Benachrichtigungen des Benutzers abrufen"""
    try:
        current_user_id = get_jwt_identity()
        notifications = Notification.query.filter_by(user_id=current_user_id).all()
        
        return jsonify({
            'notifications': [notification.to_dict() for notification in notifications],
            'count': len(notifications)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Benachrichtigungen konnten nicht geladen werden: {str(e)}'}), 500

@notifications_bp.route('/', methods=['POST'])
@jwt_required()
def create_notification():
    """Neue Benachrichtigung erstellen"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Keine Daten empfangen'}), 400
        
        # Basic validation
        if not data.get('title') or not data.get('message'):
            return jsonify({'error': 'Titel und Nachricht sind erforderlich'}), 400
        
        notify_time = datetime.utcnow()
        if 'notify_time' in data:
            try:
                notify_time = datetime.fromisoformat(str(data['notify_time']).replace('Z', '+00:00'))
            except:
                pass
        
        notification = Notification(
            user_id=current_user_id,
            course_id=data.get('course_id'),
            title=str(data['title']),
            message=str(data['message']),
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
