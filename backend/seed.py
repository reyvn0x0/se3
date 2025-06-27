from app import create_app, db
from app.models import DegreeProgram, Semester, Module, Lecturer, Room, Course, Appointment, Student, Enrollment
from datetime import time

app = create_app()

with app.app_context():
    # Optional: drop all tables and recreate them (useful to reset the DB)
    db.drop_all()
    db.create_all()

    # Create some example data

    cs = DegreeProgram(name="Computer Science", abbreviation="CS")
    db.session.add(cs)

    sem1 = Semester(number=1, description="1st Semester")
    sem2 = Semester(number=2, description="2nd Semester")
    db.session.add_all([sem1, sem2])

    lecturer1 = Lecturer(name="Max Mueller", title="Prof. Dr.", email="mueller@uni.edu")
    lecturer2 = Lecturer(name="Anna Schulz", title="Dr.", email="schulz@uni.edu")
    db.session.add_all([lecturer1, lecturer2])

    room1 = Room(name="H101", building="Main Building", capacity=50)
    room2 = Room(name="B201", building="Library", capacity=30)
    db.session.add_all([room1, room2])

    module1 = Module(name="Introduction to Computer Science", description="Basics of CS", ects=5,
                     degree_program=cs, semester=sem1, is_elective=False)
    module2 = Module(name="Mathematics 1", description="Mathematical Foundations", ects=5,
                     degree_program=cs, semester=sem1, is_elective=False)
    db.session.add_all([module1, module2])

    course1 = Course(title="Intro Lecture", type="Lecture", module=module1, lecturer=lecturer1)
    course2 = Course(title="Math Exercise", type="Exercise", module=module2, lecturer=lecturer2)
    db.session.add_all([course1, course2])

    appointment1 = Appointment(course=course1, room=room1, weekday="Monday",
                               start_time=time(9,0), end_time=time(11,0), frequency="weekly")
    appointment2 = Appointment(course=course2, room=room2, weekday="Tuesday",
                               start_time=time(10,0), end_time=time(12,0), frequency="biweekly")
    db.session.add_all([appointment1, appointment2])

    db.session.commit()
    print("Seed data successfully inserted!")