"""
Authentication service following Service Layer Pattern and SOLID principles.

Handles OAuth authentication logic and user session management.
"""
import requests
import urllib.parse
from typing import Dict, Any, Optional
from core.base_service import BaseService
from shared.models import User
from shared.config import Config
from shared.exceptions import AuthenticationError, ValidationError


class AuthService(BaseService[User, int]):
    """
    Authentication service - Single Responsibility Principle.

    Manages OAuth flows and user authentication.
    """

    def __init__(self, repository):
        """Initialize with user repository."""
        super().__init__(repository)

    def _validate_create(self, data: Dict[str, Any]) -> None:
        """Validate user creation data."""
        required_fields = ['email', 'name', 'provider']
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            raise ValidationError(f"Missing required fields: {', '.join(missing)}")

        if data['provider'] not in ['google', 'github']:
            raise ValidationError(f"Invalid provider: {data['provider']}")

    def _validate_update(self, id: int, data: Dict[str, Any]) -> None:
        """Validate user update data."""
        # Users are generally not updated via API
        pass

    def get_oauth_url(self, provider: str, redirect_uri: str) -> str:
        """
        Generate OAuth authorization URL for provider.

        Args:
            provider: OAuth provider ('google' or 'github')
            redirect_uri: Callback URL after OAuth

        Returns:
            OAuth authorization URL

        Raises:
            ValidationError: If provider is invalid or not configured
        """
        if provider not in ['google', 'github']:
            raise ValidationError(f"Invalid OAuth provider: {provider}")

        client_id = getattr(Config, f'{provider.upper()}_CLIENT_ID')
        if not client_id:
            raise ValidationError(f"{provider.title()} OAuth not configured")

        if provider == 'google':
            params = {
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'scope': 'openid email profile',
                'response_type': 'code',
                'access_type': 'offline'
            }
            return 'https://accounts.google.com/o/oauth2/auth?' + urllib.parse.urlencode(params)

        elif provider == 'github':
            params = {
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'scope': 'user:email',
                'response_type': 'code'
            }
            return 'https://github.com/login/oauth/authorize?' + urllib.parse.urlencode(params)

    def exchange_code_for_user(self, provider: str, code: str, redirect_uri: str) -> User:
        """
        Exchange OAuth code for user information and create/get user.

        Args:
            provider: OAuth provider
            code: Authorization code from OAuth callback
            redirect_uri: Callback URL used in OAuth flow

        Returns:
            User instance

        Raises:
            AuthenticationError: If OAuth exchange fails
        """
        user_info = self._exchange_code_for_info(provider, code, redirect_uri)

        if not user_info or not user_info.get('email'):
            raise AuthenticationError("Could not retrieve user information from OAuth provider")

        # Create or get user
        user = self.repository.create_or_get(
            email=user_info['email'],
            name=user_info.get('name', user_info['email']),
            provider=provider
        )

        # Update last login
        self.repository.update_last_login(user.id)

        return user

    def _exchange_code_for_info(self, provider: str, code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for user information - Helper Method.

        Args:
            provider: OAuth provider
            code: Authorization code
            redirect_uri: Callback URL

        Returns:
            Dictionary with user info (email, name) or None

        Raises:
            AuthenticationError: If exchange fails
        """
        try:
            if provider == 'google':
                return self._exchange_google_code(code, redirect_uri)
            elif provider == 'github':
                return self._exchange_github_code(code, redirect_uri)
            else:
                raise AuthenticationError(f"Unsupported provider: {provider}")
        except requests.RequestException as e:
            raise AuthenticationError(f"OAuth provider communication failed: {str(e)}")

    def _exchange_google_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange Google OAuth code for user info."""
        # Get access token
        token_response = requests.post('https://oauth2.googleapis.com/token', data={
            'client_id': Config.GOOGLE_CLIENT_ID,
            'client_secret': Config.GOOGLE_CLIENT_SECRET,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        })

        if token_response.status_code != 200:
            raise AuthenticationError("Failed to exchange Google authorization code")

        token_data = token_response.json()
        access_token = token_data.get('access_token')

        # Get user info
        user_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if user_response.status_code != 200:
            raise AuthenticationError("Failed to get Google user information")

        user_data = user_response.json()
        return {
            'email': user_data.get('email'),
            'name': user_data.get('name', user_data.get('email'))
        }

    def _exchange_github_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange GitHub OAuth code for user info."""
        # Get access token
        token_response = requests.post(
            'https://github.com/login/oauth/access_token',
            data={
                'client_id': Config.GITHUB_CLIENT_ID,
                'client_secret': Config.GITHUB_CLIENT_SECRET,
                'code': code,
                'redirect_uri': redirect_uri
            },
            headers={'Accept': 'application/json'}
        )

        if token_response.status_code != 200:
            raise AuthenticationError("Failed to exchange GitHub authorization code")

        token_data = token_response.json()
        access_token = token_data.get('access_token')

        # Get user info
        user_response = requests.get(
            'https://api.github.com/user',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            }
        )

        if user_response.status_code != 200:
            raise AuthenticationError("Failed to get GitHub user information")

        user_data = user_response.json()

        # GitHub email might be private, need to fetch separately
        email = user_data.get('email')
        if not email:
            email_response = requests.get(
                'https://api.github.com/user/emails',
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Accept': 'application/json'
                }
            )
            if email_response.status_code == 200:
                emails = email_response.json()
                primary = next((e for e in emails if e.get('primary')), None)
                email = primary['email'] if primary else emails[0]['email']

        return {
            'email': email,
            'name': user_data.get('name') or user_data.get('login', email)
        }
