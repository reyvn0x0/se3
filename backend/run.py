from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # Development server
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("🚀 Flask Backend wird gestartet...")
    print(f"   URL: http://localhost:{port}")
    print(f"   Debug: {debug}")
    print("   Verfügbare Endpoints:")
    print("   - / (Root)")
    print("   - /api/health")
    print("   - /api/schedules")
    print("   - /degree_programs")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )