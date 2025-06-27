from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SPLAN API", 
    description="Stundenplan-Management System",
    version="1.0.0"
)

# CORS für Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "SPLAN Backend läuft!", "status": "OK"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Einfache Test-Endpoints für Stundenpläne
schedules_db = [
    {"id": 1, "name": "Mein Stundenplan", "courses": []},
    {"id": 2, "name": "Backup Stundenplan", "courses": []}
]

@app.get("/schedules")
def get_schedules():
    return schedules_db

@app.post("/schedules")
def create_schedule(name: str):
    new_schedule = {
        "id": len(schedules_db) + 1,
        "name": name,
        "courses": []
    }
    schedules_db.append(new_schedule)
    return new_schedule

@app.get("/schedules/{schedule_id}")
def get_schedule(schedule_id: int):
    for schedule in schedules_db:
        if schedule["id"] == schedule_id:
            return schedule
    return {"error": "Stundenplan nicht gefunden"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)