@echo off
echo =====================================
echo STUNDENPLAN BACKEND - QUICK FIX
echo =====================================
echo.

echo 1. Virtual Environment aktivieren...
call venv\Scripts\activate
if errorlevel 1 (
    echo Fehler: Virtual Environment nicht gefunden!
    echo Erstelle Virtual Environment...
    python -m venv venv
    call venv\Scripts\activate
)

echo.
echo 2. PyMySQL-Fehler beheben...
pip uninstall PyMySQL -y
pip install PyMySQL==1.0.2

echo.
echo 3. Dependencies aktualisieren...
pip install --upgrade Flask==2.3.3
pip install --upgrade Flask-SQLAlchemy==3.0.5
pip install --upgrade SQLAlchemy==1.4.53
pip install --upgrade Flask-JWT-Extended==4.5.3
pip install --upgrade Flask-CORS==4.0.0
pip install --upgrade python-dotenv==1.0.0

echo.
echo 4. Cache leeren...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul

echo.
echo 5. MySQL-Verbindung testen...
python test_mysql_connection_fixed.py

echo.
echo 6. Backend starten...
echo Druecke Enter um Backend zu starten, oder Strg+C zum Abbrechen
pause >nul
python run.py

echo.
echo =====================================
echo FERTIG!
echo =====================================
pause