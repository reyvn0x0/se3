from app import db


class DegreeProgram(db.Model):
    __tablename__ = 'degree_programs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    abbreviation = db.Column(db.String(10), nullable=False)
    modules = db.relationship('Module', backref='degree_program', lazy=True)
    students = db.relationship('Student', backref='degree_program', lazy=True)


class Semester(db.Model):
    __tablename__ = 'semesters'

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(100), nullable=False)
    modules = db.relationship('Module', backref='semester', lazy=True)


class Module(db.Model):
    __tablename__ = 'modules'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    ects = db.Column(db.Integer, nullable=False)
    degree_program_id = db.Column(db.Integer, db.ForeignKey('degree_programs.id'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semesters.id'), nullable=False)
    is_elective = db.Column(db.Boolean, default=False)
    courses = db.relationship('Course', backref='module', lazy=True)


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # e.g. Lecture, Exercise, Seminar
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturers.id'), nullable=False)
    appointments = db.relationship('Appointment', backref='course', lazy=True)


class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    weekday = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # e.g. weekly, biweekly


class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    building = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    appointments = db.relationship('Appointment', backref='room', lazy=True)


class Lecturer(db.Model):
    __tablename__ = 'lecturers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(100), nullable=False)
    courses = db.relationship('Course', backref='lecturer', lazy=True)


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    matriculation_number = db.Column(db.String(20), unique=True, nullable=False)
    degree_program_id = db.Column(db.Integer, db.ForeignKey('degree_programs.id'), nullable=False)
    current_semester = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    enrollments = db.relationship('Enrollment', backref='student', lazy=True)


# Model for Enrollment (association between Student and Course)
class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)