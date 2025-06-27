from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Course, Timetable, Notification
from datetime import datetime, timedelta
import calendar

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    """Alle Benachrichtigungen des Benutzers abrufen"""
    try:
        current_user_id = get_jwt_identity()

        # Query parameters
        is_read = request.args.get('is_read')
        notification_type = request.args.get('type')
        limit = request.args.get('limit', 50, type=int)

        query = Notification.query.filter_by(user_id=current_user_id)

        if is_read is not None:
            query = query.filter_by(is_read=is_read.lower() == 'true')

        if notification_type:
            query = qu