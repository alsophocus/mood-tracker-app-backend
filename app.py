from flask import Flask
from datetime import timedelta
from config import Config
from database import db
from auth import auth_bp, init_auth
from routes import main_bp
from admin_routes import sql_bp
from migration_endpoint import migration_bp
from insights_routes import insights_bp
from comprehensive_routes import comprehensive_bp

def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Configuration
    app.config.from_object(Config)
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        # In production, we might want to continue with limited functionality
        if not Config.DATABASE_URL:
            raise  # Can't continue without database
    
    # Initialize database (with fallback for debugging)
    try:
        db.initialize()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print(f"   DATABASE_URL: {Config.DATABASE_URL[:50] if Config.DATABASE_URL else 'NOT SET'}...")
        
        # In deployment, we might want to continue without database for debugging
        import os
        if os.environ.get('SKIP_DB_INIT') == 'true':
            print("⚠️ Skipping database initialization (SKIP_DB_INIT=true)")
        else:
            raise
    
    # Initialize authentication
    init_auth(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(sql_bp)  # SQL operations blueprint
    app.register_blueprint(migration_bp)  # Migration testing blueprint
    app.register_blueprint(insights_bp)  # Insights dashboard blueprint
    app.register_blueprint(comprehensive_bp)  # Comprehensive features blueprint
    
    # Add timezone conversion filter
    @app.template_filter('utc_to_local')
    def utc_to_local(utc_dt):
        if not utc_dt:
            return None
        return utc_dt - timedelta(hours=3)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        print(f"Internal server error: {error}")
        import traceback
        traceback.print_exc()
        return {'error': 'Internal server error', 'details': str(error)}, 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
