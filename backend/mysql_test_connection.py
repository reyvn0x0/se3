#!/usr/bin/env python3
"""
KORRIGIERTER MySQL-Verbindungstest
Behebt PyMySQL-Versionsfehler
"""

import pymysql
import os
from dotenv import load_dotenv

# .env laden
load_dotenv()

def test_mysql_connection_fixed():
    """Teste MySQL-Verbindung mit korrigierter PyMySQL-Konfiguration"""
    
    print("🔄 KORRIGIERTER MYSQL-VERBINDUNGSTEST")
    print("=" * 60)
    
    # Konfigurationen ohne 'name' Parameter (PyMySQL-Fix)
    configs = [
        {
            'description': 'Root-User mit Passwort',
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': 'RM1337ftw',
            'charset': 'utf8mb4',
            'autocommit': True
        },
        {
            'description': 'Stundenplan-User',
            'host': 'localhost',
            'port': 3306,
            'user': 'stundenplan_user',
            'password': 'RM1337ftw',
            'charset': 'utf8mb4',
            'autocommit': True
        },
        {
            'description': 'Root ohne Passwort',
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '',
            'charset': 'utf8mb4',
            'autocommit': True
        }
    ]
    
    successful_config = None
    
    for i, config in enumerate(configs):
        print(f"\n🔄 Test {i+1}: {config['description']}")
        print(f"   Host: {config['host']}:{config['port']}")
        print(f"   User: {config['user']}")
        
        try:
            # Erstelle saubere Verbindungsparameter (ohne 'description')
            connection_params = {k: v for k, v in config.items() if k != 'description'}
            
            # Verbindung herstellen
            connection = pymysql.connect(**connection_params)
            
            with connection.cursor() as cursor:
                # MySQL-Version testen
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                
                # Aktuellen User testen
                cursor.execute("SELECT USER()")
                current_user = cursor.fetchone()
                
                # Datenbank-Berechtigung testen
                cursor.execute("SHOW DATABASES")
                databases = cursor.fetchall()
                
                print(f"✅ VERBINDUNG ERFOLGREICH!")
                print(f"   MySQL-Version: {version[0]}")
                print(f"   Verbunden als: {current_user[0]}")
                print(f"   Verfügbare Datenbanken: {len(databases)}")
                
                # Test: Kann Datenbank erstellen?
                try:
                    cursor.execute("CREATE DATABASE IF NOT EXISTS test_connection_check")
                    cursor.execute("DROP DATABASE test_connection_check")
                    print(f"✅ Datenbank-Operationen erfolgreich")
                    can_create_db = True
                except Exception as e:
                    print(f"⚠️  Datenbank-Operationen eingeschränkt: {e}")
                    can_create_db = False
                
                successful_config = config
                connection.close()
                
                # Wenn erfolgreich, breche ab
                break
                
        except Exception as e:
            print(f"❌ Verbindung fehlgeschlagen: {e}")
            
            # Spezifische Fehlermeldungen
            error_str = str(e).lower()
            if "access denied" in error_str:
                print("   💡 Passwort oder User falsch")
            elif "can't connect" in error_str:
                print("   💡 MySQL-Server nicht erreichbar")
            elif "unknown database" in error_str:
                print("   💡 Datenbank existiert nicht")
            elif "unexpected keyword argument" in error_str:
                print("   💡 PyMySQL-Versionsproblem - führe pip install PyMySQL==1.0.2 aus")
    
    if successful_config:
        print(f"\n🎯 EMPFOHLENE .ENV-KONFIGURATION:")
        print(f"MYSQL_HOST={successful_config['host']}")
        print(f"MYSQL_PORT={successful_config['port']}")
        print(f"MYSQL_USER={successful_config['user']}")
        print(f"MYSQL_PASSWORD={successful_config['password']}")
        print(f"MYSQL_DB=stundenplan_db")
        
        return True
    else:
        print(f"\n❌ ALLE VERBINDUNGEN FEHLGESCHLAGEN!")
        return False

def create_stundenplan_database():
    """Erstelle die Stundenplan-Datenbank"""
    print(f"\n🔄 Erstelle Datenbank 'stundenplan_db'...")
    
    connection_configs = [
        {'user': 'root', 'password': 'RM1337ftw'},
        {'user': 'stundenplan_user', 'password': 'RM1337ftw'},
        {'user': 'root', 'password': ''}
    ]
    
    for config in connection_configs:
        try:
            connection = pymysql.connect(
                host='localhost',
                port=3306,
                user=config['user'],
                password=config['password'],
                charset='utf8mb4',
                autocommit=True
            )
            
            with connection.cursor() as cursor:
                # Datenbank erstellen
                cursor.execute("CREATE DATABASE IF NOT EXISTS stundenplan_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                
                # Prüfen ob Datenbank existiert
                cursor.execute("SHOW DATABASES LIKE 'stundenplan_db'")
                result = cursor.fetchone()
                
                if result:
                    print(f"✅ Datenbank 'stundenplan_db' erfolgreich erstellt/gefunden")
                    print(f"   Mit User: {config['user']}")
                    connection.close()
                    return True
                else:
                    print(f"⚠️  Datenbank konnte nicht erstellt werden")
            
            connection.close()
            
        except Exception as e:
            print(f"❌ Datenbank-Erstellung mit {config['user']} fehlgeschlagen: {e}")
    
    return False

def test_flask_app_connection():
    """Teste Flask-App Datenbankverbindung"""
    print(f"\n🔄 Teste Flask-App Datenbankverbindung...")
    
    try:
        # Umgebungsvariablen setzen für Test
        os.environ['MYSQL_HOST'] = 'localhost'
        os.environ['MYSQL_PORT'] = '3306'
        os.environ['MYSQL_USER'] = 'root'
        os.environ['MYSQL_PASSWORD'] = 'RM1337ftw'
        os.environ['MYSQL_DB'] = 'stundenplan_db'
        
        # Flask-App-Import testen
        from app import create_app, db
        
        app = create_app()
        
        with app.app_context():
            # Datenbankverbindung testen
            db.engine.execute('SELECT 1')
            print(f"✅ Flask-App Datenbankverbindung erfolgreich!")
            return True
            
    except Exception as e:
        print(f"❌ Flask-App Datenbankverbindung fehlgeschlagen: {e}")
        
        # Spezifische Hilfe
        if "No module named" in str(e):
            print("   💡 Führe zuerst aus: pip install -r requirements.txt")
        elif "Access denied" in str(e):
            print("   💡 Prüfe MySQL-Benutzerdaten in .env")
        elif "Can't connect" in str(e):
            print("   💡 MySQL-Server läuft nicht")
        
        return False

def main():
    """Hauptfunktion"""
    print("🚀 MYSQL-VERBINDUNGSTEST UND FLASK-APP-TEST")
    print("=" * 70)
    
    # Schritt 1: PyMySQL-Version prüfen
    print(f"📦 PyMySQL-Version: {pymysql.__version__}")
    
    # Schritt 2: MySQL-Verbindung testen
    if test_mysql_connection_fixed():
        print(f"\n✅ MySQL-Verbindung funktioniert!")
        
        # Schritt 3: Datenbank erstellen
        if create_stundenplan_database():
            print(f"\n✅ Datenbank ist bereit!")
            
            # Schritt 4: Flask-App testen
            if test_flask_app_connection():
                print(f"\n🎉 ALLES BEREIT! BACKEND KANN GESTARTET WERDEN!")
                print(f"🚀 Starte mit: python run.py")
            else:
                print(f"\n⚠️  Flask-App hat Probleme, aber MySQL funktioniert")
                print(f"🔧 Prüfe .env und requirements.txt")
        else:
            print(f"\n⚠️  Datenbank-Erstellung problematisch")
    else:
        print(f"\n❌ MySQL-Verbindung funktioniert nicht!")
        print(f"\n🔧 LÖSUNGSSCHRITTE:")
        print(f"1. pip uninstall PyMySQL -y")
        print(f"2. pip install PyMySQL==1.0.2")
        print(f"3. MySQL-Setup-Befehle in Workbench ausführen")
        print(f"4. Test erneut ausführen")
    
    print("=" * 70)

if __name__ == "__main__":
    main()