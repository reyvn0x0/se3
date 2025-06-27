from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models import Course, Conflict, Schedule
from datetime import datetime, time
from typing import List
import secrets
import string
import os
import shutil
from fastapi import UploadFile
import json
import csv
import io

def check_schedule_conflicts(db: Session, schedule_id: int):
    """Check for conflicts in a schedule and create/update conflict records"""
    
    # Clear existing conflicts for this schedule
    db.query(Conflict).filter(Conflict.schedule_id == schedule_id).delete()
    
    # Get all courses for this schedule
    courses = db.query(Course).filter(Course.schedule_id == schedule_id).all()
    
    conflicts_found = []
    
    # Check for time overlaps
    for i, course_a in enumerate(courses):
        for course_b in courses[i+1:]:
            
            # Check if courses are on the same day
            if course_a.day_of_week == course_b.day_of_week:
                
                # Check time overlap
                if times_overlap(course_a.start_time, course_a.end_time, 
                               course_b.start_time, course_b.end_time):
                    
                    # Determine severity
                    severity = "HIGH"  # Time overlap is always high severity
                    
                    conflict = Conflict(
                        schedule_id=schedule_id,
                        course_a_id=course_a.id,
                        course_b_id=course_b.id,
                        conflict_type="TIME_OVERLAP",
                        severity=severity,
                        description=f"Zeitüberschneidung zwischen {course_a.name} und {course_b.name}"
                    )
                    
                    db.add(conflict)
                    conflicts_found.append(conflict)
                
                # Check room conflict (same time, same room)
                elif (course_a.room and course_b.room and 
                      course_a.room == course_b.room and
                      times_overlap(course_a.start_time, course_a.end_time,
                                   course_b.start_time, course_b.end_time)):
                    
                    conflict = Conflict(
                        schedule_id=schedule_id,
                        course_a_id=course_a.id,
                        course_b_id=course_b.id,
                        conflict_type="ROOM_CONFLICT",
                        severity="MEDIUM",
                        description=f"Raumkonflikt zwischen {course_a.name} und {course_b.name} in Raum {course_a.room}"
                    )
                    
                    db.add(conflict)
                    conflicts_found.append(conflict)
    
    db.commit()
    return conflicts_found

def times_overlap(start1: time, end1: time, start2: time, end2: time) -> bool:
    """Check if two time periods overlap"""
    return start1 < end2 and start2 < end1

def generate_share_token() -> str:
    """Generate a random share token"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

# =================== FILE MANAGEMENT ===================

def save_uploaded_file(file: UploadFile) -> str:
    """Save uploaded file and return file path"""
    
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return file_path

# =================== IMPORT/EXPORT SERVICES ===================

def import_schedule_from_json(db: Session, user_id: int, schedule_data: dict) -> Schedule:
    """Import schedule from JSON data"""
    
    # Create new schedule
    schedule = Schedule(
        user_id=user_id,
        name=schedule_data.get("name", "Imported Schedule"),
        description=schedule_data.get("description", "Imported from JSON"),
        color_theme=schedule_data.get("color_theme", "blue")
    )
    
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    
    # Import courses
    courses_data = schedule_data.get("courses", [])
    for course_data in courses_data:
        course = Course(
            schedule_id=schedule.id,
            name=course_data["name"],
            course_code=course_data.get("course_code"),
            instructor=course_data.get("instructor"),
            room=course_data.get("room"),
            building=course_data.get("building"),
            day_of_week=course_data["day_of_week"],
            start_time=datetime.strptime(course_data["start_time"], "%H:%M:%S").time(),
            end_time=datetime.strptime(course_data["end_time"], "%H:%M:%S").time(),
            color_code=course_data.get("color_code", "#3B82F6"),
            notes=course_data.get("notes"),
            course_type=course_data.get("course_type", "Vorlesung"),
            credits=course_data.get("credits"),
            semester=course_data.get("semester"),
            is_mandatory=course_data.get("is_mandatory", True)
        )
        db.add(course)
    
    db.commit()
    
    # Check for conflicts
    check_schedule_conflicts(db, schedule.id)
    
    return schedule

def import_schedule_from_csv(db: Session, user_id: int, csv_content: str) -> Schedule:
    """Import schedule from CSV content"""
    
    # Create new schedule
    schedule = Schedule(
        user_id=user_id,
        name="Imported Schedule (CSV)",
        description="Imported from CSV file"
    )
    
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    
    # Parse CSV
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    
    for row in csv_reader:
        # Map day names to numbers
        day_mapping = {
            "monday": 0, "montag": 0,
            "tuesday": 1, "dienstag": 1,
            "wednesday": 2, "mittwoch": 2,
            "thursday": 3, "donnerstag": 3,
            "friday": 4, "freitag": 4,
            "saturday": 5, "samstag": 5,
            "sunday": 6, "sonntag": 6
        }
        
        day_str = row.get("day", "").lower()
        day_of_week = day_mapping.get(day_str, 0)
        
        course = Course(
            schedule_id=schedule.id,
            name=row["name"],
            course_code=row.get("course_code"),
            instructor=row.get("instructor"),
            room=row.get("room"),
            day_of_week=day_of_week,
            start_time=datetime.strptime(row["start_time"], "%H:%M").time(),
            end_time=datetime.strptime(row["end_time"], "%H:%M").time(),
            color_code=row.get("color_code", "#3B82F6"),
            notes=row.get("notes"),
            course_type=row.get("course_type", "Vorlesung")
        )
        db.add(course)
    
    db.commit()
    
    # Check for conflicts
    check_schedule_conflicts(db, schedule.id)
    
    return schedule

def export_schedule_to_json(schedule: Schedule) -> dict:
    """Export schedule to JSON format"""
    
    courses_data = []
    for course in schedule.courses:
        courses_data.append({
            "name": course.name,
            "course_code": course.course_code,
            "instructor": course.instructor,
            "room": course.room,
            "building": course.building,
            "day_of_week": course.day_of_week,
            "start_time": course.start_time.strftime("%H:%M:%S"),
            "end_time": course.end_time.strftime("%H:%M:%S"),
            "color_code": course.color_code,
            "notes": course.notes,
            "course_type": course.course_type,
            "credits": course.credits,
            "semester": course.semester,
            "is_mandatory": course.is_mandatory
        })
    
    return {
        "schedule": {
            "name": schedule.name,
            "description": schedule.description,
            "color_theme": schedule.color_theme,
            "courses": courses_data
        },
        "export_info": {
            "exported_at": datetime.now().isoformat(),
            "format": "json",
            "version": "1.0"
        }
    }

def export_schedule_to_csv(schedule: Schedule) -> str:
    """Export schedule to CSV format"""
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "name", "course_code", "instructor", "room", "building", 
        "day", "start_time", "end_time", "color_code", "notes", 
        "course_type", "credits", "semester", "is_mandatory"
    ])
    
    # Day mapping
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Write courses
    for course in schedule.courses:
        writer.writerow([
            course.name,
            course.course_code or "",
            course.instructor or "",
            course.room or "",
            course.building or "",
            day_names[course.day_of_week],
            course.start_time.strftime("%H:%M"),
            course.end_time.strftime("%H:%M"),
            course.color_code,
            course.notes or "",
            course.course_type,
            course.credits or "",
            course.semester or "",
            course.is_mandatory
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    return csv_content

# =================== UTILITY FUNCTIONS ===================

def get_week_schedule(db: Session, schedule_id: int, user_id: int) -> dict:
    """Get organized week view of schedule"""
    
    # Verify schedule ownership
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == user_id
    ).first()
    
    if not schedule:
        return None
    
    # Get all courses
    courses = db.query(Course).filter(Course.schedule_id == schedule_id).all()
    
    # Organize by day
    week_schedule = {
        0: [],  # Monday
        1: [],  # Tuesday
        2: [],  # Wednesday
        3: [],  # Thursday
        4: [],  # Friday
        5: [],  # Saturday
        6: []   # Sunday
    }
    
    for course in courses:
        week_schedule[course.day_of_week].append(course)
    
    # Sort courses by start time for each day
    for day in week_schedule:
        week_schedule[day].sort(key=lambda x: x.start_time)
    
    return {
        "schedule": schedule,
        "week": week_schedule,
        "total_courses": len(courses)
    }

def get_schedule_statistics(db: Session, schedule_id: int, user_id: int) -> dict:
    """Get statistics for a schedule"""
    
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == user_id
    ).first()
    
    if not schedule:
        return None
    
    courses = db.query(Course).filter(Course.schedule_id == schedule_id).all()
    conflicts = db.query(Conflict).filter(
        Conflict.schedule_id == schedule_id,
        Conflict.resolved == False
    ).all()
    
    # Calculate total credits
    total_credits = sum(course.credits or 0 for course in courses)
    
    # Count by course type
    course_types = {}
    for course in courses:
        course_type = course.course_type
        course_types[course_type] = course_types.get(course_type, 0) + 1
    
    # Count by day
    days_count = {}
    for course in courses:
        day = course.day_of_week
        days_count[day] = days_count.get(day, 0) + 1
    
    return {
        "total_courses": len(courses),
        "total_credits": total_credits,
        "total_conflicts": len(conflicts),
        "course_types": course_types,
        "days_distribution": days_count,
        "mandatory_courses": len([c for c in courses if c.is_mandatory]),
        "optional_courses": len([c for c in courses if not c.is_mandatory])
    }