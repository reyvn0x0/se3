#!/usr/bin/env python3
"""
Test-Script für SQLAlchemy-Konfiguration
Führen Sie dieses Skript aus, um zu testen, ob SQLAlchemy korrekt funktioniert
"""

import os
import sys
from datetime import datetime

def test_imports():
    """Test basic imports"""
    print("🔄 Teste Imports...")
    try:
        import flask
        print(f"✅ Flask {flask.__version__} erfolgreich importiert")
        
        import sqlalchemy
        print(f"✅ SQLAlchemy {sqlalchemy.__version__} erfolgreich importiert")
        
        import flask_sqlalchemy
        print(f"✅ Flask-SQLAlchemy {flask_sqlalchemy.__version__} erfolgreich importiert")
        
        import pymysql
        print(f"✅ PyMySQL {pymysql.__version__} erfolgreich importiert")
        
        return True
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        return False

def test_app_creation():
    """Test Flask app creation"""
    print("\n🔄 Teste Flask-App-Erstellung...")
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db = SQLAlchemy(app)
        
        print("✅ Flask-App erfolgreich erstellt")
        print("✅ SQLAlchemy erfolgreich initialisiert")
        return True
    except Exception as e:
        print(f"❌ App-Erstellungsfehler: {e}")
        return False

def test_database_models():
    """Test database model creation"""
    print("\n🔄 Teste Datenbankmodelle...")
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from datetime import datetime
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db = SQLAlchemy(app)
        
        # Simple test model
        class TestUser(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String(80), unique=True, nullable=False)
            created_at = db.Column(db.DateTime, default=datetime.utcnow)
            
        with app.app_context():
            db.create_all()
            
            # Create test user
            user = TestUser(username='test_user')
            db.session.add(user)
            db.session.commit()
            
            # Query test
            found_user = TestUser.query.filter_by(username='test_user').first()
            if found_user:
                print("✅ Datenbankmodelle funktionieren korrekt")
                return True
            else:
                print("❌ Datenbankabfrage fehlgeschlagen")
                return False
                
    except Exception as e:
        print(f"❌ Datenbankmodell-Fehler: {e}")
        return False

def test_mysql_connection():
    """Test MySQL connection if configured"""
    print("\n🔄 Teste MySQL-Verbindung...")
    try:
        import pymysql
        
        # Read from environment or use defaults
        host = os.environ.get('MYSQL_HOST', 'localhost')
        user = os.environ.get('MYSQL_USER', 'root')
        password = os.environ.get('MYSQL_PASSWORD', '')
        
        if not password:
            print("⚠️  Kein MySQL-Passwort gesetzt. Überspringe MySQL-Test.")
            print("   Setze MYSQL_PASSWORD in der .env Datei")
            return True
        
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        
        print(f"✅ MySQL-Verbindung erfolgreich. Version: {version[0]}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"⚠️  MySQL-Verbindung fehlgeschlagen: {e}")
        print("   Überprüfe MySQL-Server und Anmeldedaten in .env")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 STUNDENPLAN BACKEND - SQLALCHEMY TEST")
    print("=" * 60)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test app creation
    if not test_app_creation():
        all_passed = False
    
    # Test database models
    if not test_database_models():
        all_passed = False
    
    # Test MySQL connection
    if not test_mysql_connection():
        # MySQL connection failure is not critical for basic functionality
        pass
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALLE KRITISCHEN TESTS BESTANDEN!")
        print("✅ SQLAlchemy ist korrekt konfiguriert")
        print("✅ Backend kann gestartet werden")
        print("\nStarte das Backend mit: python run.py")
    else:
        print("❌ EINIGE TESTS FEHLGESCHLAGEN!")
        print("🔧 Behebe die oben genannten Probleme vor dem Start")
        print("\nInstalliere Dependencies mit:")
        print("pip install -r requirements.txt")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())