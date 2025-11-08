"""
Main application entry point following SOLID principles.

Assembles all modules and initializes the Flask application.
"""
from flask import Flask, jsonify
from flask_cors import CORS
from shared.config import Config
from shared.database import db
from shared.exceptions import AppException

# Import repositories
from features.auth.repository import UserRepository
from features.moods.repository import MoodRepository
from features.tags.repository import TagRepository

# Import services
from features.auth.service import AuthService
from features.moods.service import MoodService
from features.tags.service import TagService
from features.analytics.service import AnalyticsService
from features.insights.service import InsightsService
from features.export.service import ExportService

# Import controllers
from features.auth.controller import AuthController
from features.moods.controller import MoodController
from features.tags.controller import TagController
from features.analytics.controller import AnalyticsController
from features.insights.controller import InsightsController
from features.export.controller import ExportController


def create_app():
    """
    Application factory - Dependency Injection Pattern.
    
    Creates and configures the Flask application with all dependencies.
    """
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['DEBUG'] = Config.DEBUG
    
    # Enable CORS for Flutter frontend
    CORS(app, supports_credentials=True)
    
    # Validate configuration
    try:
        Config.validate()
        print("✅ Configuration validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        if not Config.DEBUG:
            raise
    
    # Initialize database
    try:
        db.initialize()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise
    
    # Initialize repositories
    user_repo = UserRepository(db)
    mood_repo = MoodRepository(db)
    tag_repo = TagRepository(db)
    
    # Initialize services
    auth_service = AuthService(user_repo)
    mood_service = MoodService(mood_repo)
    tag_service = TagService(tag_repo)
    analytics_service = AnalyticsService(mood_repo)
    insights_service = InsightsService(mood_repo, tag_repo)
    export_service = ExportService(mood_repo, tag_repo)
    
    # Initialize controllers
    auth_controller = AuthController(auth_service, user_repo)
    mood_controller = MoodController(mood_service)
    tag_controller = TagController(tag_service)
    analytics_controller = AnalyticsController(analytics_service)
    insights_controller = InsightsController(insights_service)
    export_controller = ExportController(export_service)
    
    # Initialize Flask-Login
    auth_controller.init_flask_login(app)
    
    # Register routes
    auth_controller.register_routes()
    mood_controller.register_routes()
    tag_controller.register_routes()
    analytics_controller.register_routes()
    insights_controller.register_routes()
    export_controller.register_routes()
    
    # Register blueprints
    app.register_blueprint(auth_controller.blueprint)
    app.register_blueprint(mood_controller.blueprint)
    app.register_blueprint(tag_controller.blueprint)
    app.register_blueprint(analytics_controller.blueprint)
    app.register_blueprint(insights_controller.blueprint)
    app.register_blueprint(export_controller.blueprint)
    
    # Health check endpoint
    @app.route('/health')
    def health():
        """Health check endpoint for monitoring."""
        db_healthy = db.health_check()
        return jsonify({
            'status': 'healthy' if db_healthy else 'unhealthy',
            'database': 'connected' if db_healthy else 'disconnected'
        }), 200 if db_healthy else 503
    
    # API info endpoint
    @app.route('/api')
    def api_info():
        """API information endpoint."""
        return jsonify({
            'name': 'Mood Tracker API',
            'version': '2.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'moods': '/api/moods',
                'tags': '/api/tags',
                'analytics': '/api/analytics',
                'insights': '/api/insights',
                'export': '/api/export'
            }
        })
    
    # Global error handlers
    @app.errorhandler(AppException)
    def handle_app_exception(error):
        """Handle custom application exceptions."""
        return jsonify({
            'success': False,
            'error': error.message
        }), error.status_code
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({
            'success': False,
            'error': 'Resource not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        print(f"Internal server error: {error}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
    
    print("✅ Application initialized successfully")
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )
