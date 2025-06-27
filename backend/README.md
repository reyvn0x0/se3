

##  Quick Start

### Mit Docker (Empfohlen)
```bash
# 1. Environment konfigurieren
cp .env.template .env
# .env bearbeiten

# 2. Services starten
docker-compose up -d

# 3. Datenbank mit Beispieldaten füllen
docker exec -it stundenplan_backend python database_setup.py full

# 4. Backend läuft auf http://localhost:5000
```

### Lokal
```bash
# 1. Virtual Environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Dependencies
pip install -r requirements.txt

# 3. Environment
cp .env.template .env
# .env bearbeiten

# 4. MySQL Datenbank erstellen
mysql -u root -p
CREATE DATABASE stundenplan_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 5. Datenbank setup
python database_setup.py full

# 6. Server starten
python run.py
```

## 📡 API Endpoints

### Authentication
- `POST /api/auth/register` - Registrierung
- `POST /api/auth/login` - Anmeldung
- `GET /api/auth/profile` - Profil abrufen

### Health
- `GET /api/health` - System Health Check
- `GET /api/ping` - Einfacher Ping


## 🎯 Features

✅ Benutzer-Authentifizierung mit JWT
✅ CRUD-Operationen für Stundenpläne und Kurse  
✅ Benachrichtigungssystem
✅ Import/Export (JSON, CSV, Excel)
✅ Kommentarfunktion
✅ MySQL-Integration
✅ Docker-Support
✅ Health Monitoring
✅ Error Handling
✅ CORS-Support für React Frontend


