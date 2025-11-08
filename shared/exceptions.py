"""
Custom exceptions following SOLID principles.

Defines application-specific exceptions for better error handling.
"""


class AppException(Exception):
    """Base exception for all application exceptions - Open/Closed Principle."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ValidationError(AppException):
    """Raised when validation fails - Single Responsibility Principle."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class NotFoundError(AppException):
    """Raised when resource is not found - Single Responsibility Principle."""

    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class AuthenticationError(AppException):
    """Raised when authentication fails - Single Responsibility Principle."""

    def __init__(self, message: str):
        super().__init__(message, status_code=401)


class AuthorizationError(AppException):
    """Raised when authorization fails - Single Responsibility Principle."""

    def __init__(self, message: str):
        super().__init__(message, status_code=403)


class DatabaseError(AppException):
    """Raised when database operations fail - Single Responsibility Principle."""

    def __init__(self, message: str):
        super().__init__(message, status_code=500)
