"""
Configuration management following SOLID principles.

Centralizes all configuration with environment variable support.
"""
import os
from typing import Optional


class Config:
    """
    Application configuration - Single Responsibility Principle.

    Manages all configuration settings from environment variables.
    Provides validation and sensible defaults.
    """

    # Database
    DATABASE_URL: str = os.environ.get('DATABASE_URL', '')

    # Flask
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG: bool = os.environ.get('DEBUG', 'False').lower() == 'true'
    PORT: int = int(os.environ.get('PORT', 5000))

    # OAuth - Google
    GOOGLE_CLIENT_ID: Optional[str] = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET: Optional[str] = os.environ.get('GOOGLE_CLIENT_SECRET')

    # OAuth - GitHub
    GITHUB_CLIENT_ID: Optional[str] = os.environ.get('GITHUB_CLIENT_ID')
    GITHUB_CLIENT_SECRET: Optional[str] = os.environ.get('GITHUB_CLIENT_SECRET')

    # Application Settings
    MAX_MOODS_PER_DAY: int = 10  # Reasonable limit to prevent abuse
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100

    @classmethod
    def validate(cls) -> None:
        """
        Validate required configuration - Fail Fast Principle.

        Raises:
            ValueError: If required configuration is missing
        """
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL is required")

        if not cls.SECRET_KEY or cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            if not cls.DEBUG:
                raise ValueError("SECRET_KEY must be set in production")

    @classmethod
    def get_oauth_redirect_url(cls, provider: str) -> str:
        """
        Get OAuth redirect URL for provider.

        Args:
            provider: OAuth provider name ('google' or 'github')

        Returns:
            Redirect URL string
        """
        # In production, this would come from environment
        base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
        return f"{base_url}/api/auth/callback/{provider}"
