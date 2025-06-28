from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # User Settings
    timezone = db.Column(db.String(50), default='Europe/Berlin')
    notification_enabled = db.Column(db.Boolean, default=True)
    theme_preference = db.Column(db.String(20), default='light')  # light, dark
    
    # Relationships
    timetables = db.relationship('Timetable', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    course_comments = db.relationship('CourseComment', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'student_id': self.student_id,
            'timezone': self.timezone,
            'notification_enabled': self.notification_enabled,
            'theme_preference': self.theme_preference,
            'created_at': self.created_at.isoformat()
        }

class Timetable(db.Model):
    __tablename__ = 'timetables'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False, default='Mein Stundenplan')
    is_active = db.Column(db.Boolean, default=True)
    semester = db.Column(db.String(20), nullable=True)  # WS24, SS25
    year = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    color_theme = db.Column(db.String(20), default='blue')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    courses = db.relationship('Course', backref='timetable', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_courses=False):
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'is_active': self.is_active,
            'semester': self.semester,
            'year': self.year,
            'description': self.description,
            'color_theme': self.color_theme,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_courses:
            result['courses'] = [course.to_dict() for course in self.courses]
        return result

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    timetable_id = db.Column(db.Integer, db.ForeignKey('timetables.id'), nullable=False)
    
    # Course Information
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), nullable=True)  # z.B. "MATH101"
    instructor = db.Column(db.String(100), nullable=True)
    room = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(7), default='#3498db')  # Hex color code
    
    # Schedule Information
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    # Course Type & Details
    course_type = db.Column(db.String(50), default='Vorlesung')  # Vorlesung, Übung, Praktikum
    credits = db.Column(db.Integer, nullable=True)  # ECTS
    
    # External Links
    horst_url = db.Column(db.String(500), nullable=True)  # Link zu Horst System
    moodle_url = db.Column(db.String(500), nullable=True)
    external_url = db.Column(db.String(500), nullable=True)
    
    # Status & Settings
    is_active = db.Column(db.Boolean, default=True)
    reminder_enabled = db.Column(db.Boolean, default=True)
    reminder_minutes = db.Column(db.Integer, default=15)  # Benachrichtigung X Minuten vorher
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    comments = db.relationship('CourseComment', backref='course', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='course', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_comments=False):
        result = {
            'id': self.id,
            'timetable_id': self.timetable_id,
            'name': self.name,
            'code': self.code,
            'instructor': self.instructor,
            'room': self.room,
            'description': self.description,
            'color': self.color,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'course_type': self.course_type,
            'credits': self.credits,
            'horst_url': self.horst_url,
            'moodle_url': self.moodle_url,
            'external_url': self.external_url,
            'is_active': self.is_active,
            'reminder_enabled': self.reminder_enabled,
            'reminder_minutes': self.reminder_minutes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_comments:
            result['comments'] = [comment.to_dict() for comment in self.comments]
        return result

class CourseComment(db.Model):
    __tablename__ = 'course_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    comment = db.Column(db.Text, nullable=False)
    comment_type = db.Column(db.String(50), default='note')  # note, reminder, important
    is_private = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'user_id': self.user_id,
            'comment': self.comment,
            'comment_type': self.comment_type,
            'is_private': self.is_private,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='reminder')  # reminder, info, warning, course_start
    
    # Notification Settings
    notify_time = db.Column(db.DateTime, nullable=False)  # When to notify
    is_sent = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'notify_time': self.notify_time.isoformat(),
            'is_sent': self.is_sent,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat()
        }

class DegreeProgram(db.Model):
    __tablename__ = 'degree_programs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }