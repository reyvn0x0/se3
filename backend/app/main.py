from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime, timedelta

from app.database import engine, get_db, Base
from app.models import User, Schedule, Course, CourseFile, Conflict
from app.schemas import *
from app.auth import *
from app.services import *

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SPLAN API",
    description="Stundenplan-Management System für Studierende", 
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# =================== AUTHENTICATION ENDPOINTS ===================

@app.post("/auth/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Benutzer registrieren"""
    # Check if user exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail="Email oder Benutzername bereits registriert"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        student_id=user_data.student_id,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/auth/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Benutzer anmelden"""
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Ungültige Anmeldedaten"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@app.get("/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Aktuelle Benutzerinformationen"""
    return current_user

# =================== SCHEDULE ENDPOINTS ===================

@app.get("/schedules", response_model=List[ScheduleResponse])
def get_user_schedules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Alle Stundenpläne des Benutzers"""
    schedules = db.query(Schedule).filter(Schedule.user_id == current_user.id).all()
    return schedules

@app.post("/schedules", response_model=ScheduleResponse)
def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Neuen Stundenplan erstellen"""
    db_schedule = Schedule(
        name=schedule_data.name,
        description=schedule_data.description,
        user_id=current_user.id,
        is_default=schedule_data.is_default
    )
    
    # If this is set as default, unset other defaults
    if schedule_data.is_default:
        db.query(Schedule).filter(
            Schedule.user_id == current_user.id,
            Schedule.is_default == True
        ).update({"is_default": False})
    
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@app.get("/schedules/{schedule_id}", response_model=ScheduleDetailResponse)
def get_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Spezifischen Stundenplan mit Kursen"""
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Stundenplan nicht gefunden")
    
    return schedule

@app.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stundenplan bearbeiten"""
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Stundenplan nicht gefunden")
    
    update_data = schedule_data.dict(exclude_unset=True)
    
    # Handle default setting
    if update_data.get("is_default"):
        db.query(Schedule).filter(
            Schedule.user_id == current_user.id,
            Schedule.id != schedule_id
        ).update({"is_default": False})
    
    for field, value in update_data.items():
        setattr(schedule, field, value)
    
    db.commit()
    db.refresh(schedule)
    return schedule

@app.delete("/schedules/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stundenplan löschen"""
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Stundenplan nicht gefunden")
    
    db.delete(schedule)
    db.commit()
    return {"message": "Stundenplan erfolgreich gelöscht"}

# =================== COURSE ENDPOINTS ===================

@app.post("/schedules/{schedule_id}/courses", response_model=CourseResponse)
def add_course(
    schedule_id: int,
    course_data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kurs zu Stundenplan hinzufügen"""
    # Verify schedule ownership
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Stundenplan nicht gefunden")
    
    # Create course
    db_course = Course(
        **course_data.dict(),
        schedule_id=schedule_id
    )
    
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    
    # Check for conflicts after adding
    check_schedule_conflicts(db, schedule_id)
    
    return db_course

@app.get("/courses/{course_id}", response_model=CourseDetailResponse)
def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kurs-Details abrufen"""
    course = db.query(Course).join(Schedule).filter(
        Course.id == course_id,
        Schedule.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Kurs nicht gefunden")
    
    return course

@app.put("/courses/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    course_data: CourseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kurs bearbeiten"""
    course = db.query(Course).join(Schedule).filter(
        Course.id == course_id,
        Schedule.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Kurs nicht gefunden")
    
    update_data = course_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)
    
    db.commit()
    db.refresh(course)
    
    # Recheck conflicts after update
    check_schedule_conflicts(db, course.schedule_id)
    
    return course

@app.delete("/courses/{course_id}")
def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kurs löschen"""
    course = db.query(Course).join(Schedule).filter(
        Course.id == course_id,
        Schedule.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Kurs nicht gefunden")
    
    schedule_id = course.schedule_id
    db.delete(course)
    db.commit()
    
    # Recheck conflicts after deletion
    check_schedule_conflicts(db, schedule_id)
    
    return {"message": "Kurs erfolgreich gelöscht"}

# =================== FILE UPLOAD ENDPOINTS ===================

@app.post("/courses/{course_id}/files")
def upload_course_file(
    course_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Datei zu Kurs hochladen"""
    # Verify course ownership
    course = db.query(Course).join(Schedule).filter(
        Course.id == course_id,
        Schedule.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Kurs nicht gefunden")
    
    # Save file
    file_path = save_uploaded_file(file)
    
    # Create file record
    db_file = CourseFile(
        course_id=course_id,
        filename=file.filename,
        file_path=file_path,
        file_size=file.size if file.size else 0
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return {"message": "Datei erfolgreich hochgeladen", "file": db_file}

@app.get("/courses/{course_id}/files")
def get_course_files(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dateien eines Kurses abrufen"""
    course = db.query(Course).join(Schedule).filter(
        Course.id == course_id,
        Schedule.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Kurs nicht gefunden")
    
    files = db.query(CourseFile).filter(CourseFile.course_id == course_id).all()
    return {"files": files}

# =================== CONFLICT ENDPOINTS ===================

@app.get("/schedules/{schedule_id}/conflicts")
def get_schedule_conflicts(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Konflikte eines Stundenplans"""
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Stundenplan nicht gefunden")
    
    conflicts = db.query(Conflict).filter(
        Conflict.schedule_id == schedule_id,
        Conflict.resolved == False
    ).all()
    
    return {"conflicts": conflicts}

@app.post("/conflicts/{conflict_id}/resolve")
def resolve_conflict(
    conflict_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Konflikt als gelöst markieren"""
    conflict = db.query(Conflict).join(Schedule).filter(
        Conflict.id == conflict_id,
        Schedule.user_id == current_user.id
    ).first()
    
    if not conflict:
        raise HTTPException(status_code=404, detail="Konflikt nicht gefunden")
    
    conflict.resolved = True
    db.commit()
    
    return {"message": "Konflikt als gelöst markiert"}

# =================== SHARING ENDPOINTS ===================

@app.post("/schedules/{schedule_id}/share")
def share_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stundenplan teilen"""
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Stundenplan nicht gefunden")
    
    share_token = generate_share_token()
    schedule.share_token = share_token
    schedule.is_shared = True
    
    db.commit()
    
    return {
        "message": "Stundenplan erfolgreich geteilt",
        "share_url": f"/shared/{share_token}",
        "share_token": share_token
    }

@app.get("/shared/{share_token}")
def get_shared_schedule(share_token: str, db: Session = Depends(get_db)):
    """Geteilten Stundenplan abrufen"""
    schedule = db.query(Schedule).filter(
        Schedule.share_token == share_token,
        Schedule.is_shared == True
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Geteilter Stundenplan nicht gefunden")
    
    return schedule

# =================== IMPORT/EXPORT ENDPOINTS ===================

@app.post("/schedules/import")
def import_schedule(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stundenplan importieren"""
    try:
        if file.filename.endswith('.json'):
            content = file.file.read()
            schedule_data = json.loads(content)
            
            # Create schedule from imported data
            imported_schedule = import_schedule_from_json(db, current_user.id, schedule_data)
            return {"message": "Stundenplan erfolgreich importiert", "schedule": imported_schedule}
            
        elif file.filename.endswith('.csv'):
            content = file.file.read().decode('utf-8')
            imported_schedule = import_schedule_from_csv(db, current_user.id, content)
            return {"message": "Stundenplan erfolgreich importiert", "schedule": imported_schedule}
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import fehler: {str(e)}")

@app.get("/schedules/{schedule_id}/export")
def export_schedule(
    schedule_id: int,
    format: str = "json",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stundenplan exportieren"""
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Stundenplan nicht gefunden")
    
    if format == "json":
        return export_schedule_to_json(schedule)
    elif format == "csv":
        return export_schedule_to_csv(schedule)
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format")

# =================== UTILITY ENDPOINTS ===================

@app.get("/")
def root():
    return {
        "message": "🎓 SPLAN Backend API", 
        "status": "running",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)