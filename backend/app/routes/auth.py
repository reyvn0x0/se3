from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity,
    create_refresh_token, get_jwt
)
from app import db
from app.models import User
from datetime import datetime, timedelta
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """E-Mail Validierung"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Passwort Validierung"""
    if len(password) < 6:
        return False, "Passwort muss mindestens 6 Zeichen lang sein"
    if not re.search(r'[A-Za-z]', password):
        return False, "Passwort muss mindestens einen Buchstaben enthalten"
    if not re.search(r'[0-9]', password):
        return False, "Passwort muss mindestens eine Zahl enthalten"
    return True, "Passwort ist gültig"

@auth_bp.route('/register', methods=['POST'])
def register():
    """Benutzer registrieren"""
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['username', 'email', 'password', 'full_name']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} ist erforderlich'}), 400
        
        # Email validation
        if not validate_email(data['email']):
            return jsonify({'error': 'Ungültige E-Mail-Adresse'}), 400
        
        # Password validation
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Benutzername bereits vergeben'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'E-Mail bereits registriert'}), 400
        
        # Check student_id if provided
        if data.get('student_id') and User.query.filter_by(student_id=data['student_id']).first():
            return jsonify({'error': 'Matrikelnummer bereits vergeben'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            student_id=data.get('student_id')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)
        )
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'message': 'Registrierung erfolgreich',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Registrierung fehlgeschlagen: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Benutzer anmelden"""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Benutzername und Passwort erforderlich'}), 400
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == data['username']) | 
            (User.email == data['username'])
        ).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Ungültige Anmeldedaten'}), 401
        
        # Create tokens
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)
        )
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'message': 'Erfolgreich angemeldet',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Anmeldung fehlgeschlagen: {str(e)}'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Access Token erneuern"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'Benutzer nicht gefunden'}), 404
        
        new_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'access_token': new_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Token-Erneuerung fehlgeschlagen: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Benutzerprofil abrufen"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'Benutzer nicht gefunden'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Profil konnte nicht geladen werden: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Benutzerprofil aktualisieren"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'Benutzer nicht gefunden'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Keine Daten empfangen'}), 400
        
        # Update allowed fields
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'student_id' in data:
            # Check if student_id is already taken
            if data['student_id'] and User.query.filter(
                User.student_id == data['student_id'],
                User.id != user.id
            ).first():
                return jsonify({'error': 'Matrikelnummer bereits vergeben'}), 400
            user.student_id = data['student_id']
        if 'timezone' in data:
            user.timezone = data['timezone']
        if 'notification_enabled' in data:
            user.notification_enabled = data['notification_enabled']
        if 'theme_preference' in data:
            user.theme_preference = data['theme_preference']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profil erfolgreich aktualisiert',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Profil-Update fehlgeschlagen: {str(e)}'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Passwort ändern"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'Benutzer nicht gefunden'}), 404
        
        data = request.get_json()
        if not data or not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Aktuelles und neues Passwort erforderlich'}), 400
        
        # Verify current password
        if not user.check_password(data['current_password']):
            return jsonify({'error': 'Aktuelles Passwort ist falsch'}), 400
        
        # Validate new password
        is_valid, message = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Update password
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({
            'message': 'Passwort erfolgreich geändert'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Passwort-Änderung fehlgeschlagen: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Benutzer abmelden"""
    # JWT wird clientseitig gelöscht
    return jsonify({
        'message': 'Erfolgreich abgemeldet'
    }), 200