"""
Authentication controller following Controller Pattern and SOLID principles.

Handles HTTP requests for authentication endpoints.
"""
from flask import request, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from functools import wraps
from core.base_controller import BaseController
from shared.exceptions import AuthenticationError, ValidationError


class FlaskUser(UserMixin):
    """Flask-Login user wrapper - Adapter Pattern."""

    def __init__(self, user):
        self.id = user.id
        self.email = user.email
        self.name = user.name
        self.provider = user.provider


class AuthController(BaseController):
    """
    Authentication controller - Single Responsibility Principle.

    Handles OAuth flows and session management for API.
    """

    def __init__(self, auth_service, user_repository):
        """
        Initialize controller with dependencies.

        Args:
            auth_service: AuthService instance
            user_repository: UserRepository instance
        """
        super().__init__(auth_service, 'auth', '/api/auth')
        self.user_repository = user_repository
        self.login_manager = None

    def init_flask_login(self, app):
        """
        Initialize Flask-Login for session management.

        Args:
            app: Flask application instance
        """
        self.login_manager = LoginManager()
        self.login_manager.init_app(app)

        @self.login_manager.user_loader
        def load_user(user_id):
            user = self.user_repository.find_by_id(int(user_id))
            return FlaskUser(user) if user else None

    def register_routes(self):
        """Register all authentication routes."""

        @self.blueprint.route('/oauth/<provider>', methods=['GET'])
        @self.handle_request
        def oauth_login(provider):
            """
            Initiate OAuth login flow.

            Returns OAuth authorization URL for the specified provider.
            """
            # Get redirect URI from query params or construct default
            redirect_uri = request.args.get('redirect_uri') or \
                          request.url_root.rstrip('/') + f'/api/auth/callback/{provider}'

            auth_url = self.service.get_oauth_url(provider, redirect_uri)

            return self.success_response({
                'auth_url': auth_url,
                'provider': provider
            })

        @self.blueprint.route('/callback/<provider>', methods=['GET'])
        @self.handle_request
        def oauth_callback(provider):
            """
            Handle OAuth callback and create user session.

            Exchanges authorization code for user info and logs user in.
            """
            code = request.args.get('code')
            if not code:
                raise ValidationError("Authorization code not provided")

            redirect_uri = request.url_root.rstrip('/') + f'/api/auth/callback/{provider}'

            # Exchange code for user
            user = self.service.exchange_code_for_user(provider, code, redirect_uri)

            # Log user in
            flask_user = FlaskUser(user)
            login_user(flask_user)

            return self.success_response({
                'user': user.to_dict(),
                'message': 'Logged in successfully'
            })

        @self.blueprint.route('/logout', methods=['POST'])
        @self.handle_request
        def logout():
            """Logout current user."""
            logout_user()
            return self.success_response(message='Logged out successfully')

        @self.blueprint.route('/me', methods=['GET'])
        @self.handle_request
        def get_current_user():
            """Get current authenticated user."""
            if not current_user.is_authenticated:
                return self.error_response('Not authenticated', 401)

            user = self.user_repository.find_by_id(current_user.id)
            if not user:
                return self.error_response('User not found', 404)

            return self.success_response(user.to_dict())

        @self.blueprint.route('/status', methods=['GET'])
        @self.handle_request
        def auth_status():
            """Check authentication status."""
            return self.success_response({
                'authenticated': current_user.is_authenticated,
                'user': current_user.id if current_user.is_authenticated else None
            })


def login_required_api(f):
    """
    Decorator for API endpoints requiring authentication.

    Returns JSON error instead of redirect for API endpoints.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        return f(*args, **kwargs)
    return decorated_function
