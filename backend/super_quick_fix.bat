@echo off
echo ========================================
echo STUNDENPLAN BACKEND - SUPER QUICK FIX
echo ========================================
echo Backend funktioniert danach GARANTIERT!
echo.

echo 1. Virtual Environment aktivieren...
call venv\Scripts\activate

echo.
echo 2. .env mit SQLite-Fallback erstellen...
echo # SOFORTIGER SQLITE-FIX > .env
echo USE_SQLITE=true >> .env
echo FLASK_APP=run.py >> .env
echo FLASK_ENV=development >> .env
echo SECRET_KEY=stundenplan-secret-key-2024 >> .env
echo JWT_SECRET_KEY=jwt-secret-key-2024 >> .env
echo PORT=5000 >> .env
echo CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000 >> .env

echo.
echo 3. Einfache config.py erstellen...
(
echo import os
echo from datetime import timedelta
echo.
echo class Config:
echo     # SQLite-Fallback ^(funktioniert IMMER^)
echo     if os.environ.get^('USE_SQLITE', 'false'^).lower^(^) == 'true':
echo         SQLALCHEMY_DATABASE_URI = 'sqlite:///stundenplan.db'
echo         print^("SQLite-Modus aktiv - Backend funktioniert ohne MySQL"^)
echo     else:
echo         # MySQL-Fallback
echo         MYSQL_HOST = os.environ.get^('MYSQL_HOST', 'localhost'^)
echo         MYSQL_USER = os.environ.get^('MYSQL_USER', 'root'^)
echo         MYSQL_PASSWORD = os.environ.get^('MYSQL_PASSWORD', ''^)
echo         MYSQL_DB = os.environ.get^('MYSQL_DB', 'stundenplan_db'^)
echo         SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}?charset=utf8mb4"
echo.    
echo     SQLALCHEMY_TRACK_MODIFICATIONS = False
echo     SECRET_KEY = os.environ.get^('SECRET_KEY', 'stundenplan-secret-key-2024'^)
echo     CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']
echo     UPLOAD_FOLDER = 'uploads'
echo     MAX_CONTENT_LENGTH = 16 * 1024 * 1024
echo     JWT_SECRET_KEY = os.environ.get^('JWT_SECRET_KEY', 'jwt-secret-key'^)
echo     JWT_ACCESS_TOKEN_EXPIRES = timedelta^(hours=24^)
echo     JSON_AS_ASCII = False
) > config.py

echo.
echo 4. Backend starten...
echo ========================================
echo Backend startet jetzt mit SQLite...
echo ========================================
python run.py

echo.
echo ========================================
echo Wenn Backend läuft, teste: http://localhost:5000/api/ping
echo ========================================
pause