"""
Base controller implementation following Controller Pattern and SOLID principles.

Provides abstract base class for all controller/route implementations.
Handles HTTP concerns and delegates to service layer.
"""
from abc import ABC
from typing import Generic, TypeVar
from flask import Blueprint, jsonify, request
from functools import wraps

T = TypeVar('T')  # Entity type
ID = TypeVar('ID', int, str)  # ID type


class BaseController(ABC, Generic[T, ID]):
    """
    Abstract base controller - Open/Closed Principle.

    Provides common HTTP handling while allowing specific implementations.
    Follows Single Responsibility: handles HTTP requests/responses only.
    Business logic is delegated to service layer.
    """

    def __init__(self, service, blueprint_name: str, url_prefix: str):
        """
        Initialize controller with service dependency - Dependency Inversion.

        Args:
            service: Service implementing IService interface
            blueprint_name: Name for Flask blueprint
            url_prefix: URL prefix for all routes (e.g., '/api/moods')
        """
        self.service = service
        self.blueprint = Blueprint(blueprint_name, __name__, url_prefix=url_prefix)

    def handle_request(self, handler_func):
        """
        Decorator for consistent error handling across routes - DRY Principle.

        Wraps route handlers with try/except to provide consistent error responses.
        Automatically handles common exceptions and returns proper HTTP status codes.

        Args:
            handler_func: Route handler function

        Returns:
            Wrapped function with error handling
        """
        @wraps(handler_func)
        def wrapper(*args, **kwargs):
            try:
                result = handler_func(*args, **kwargs)

                # If result is APIResponse, convert to JSON
                if hasattr(result, 'to_dict'):
                    response_dict = result.to_dict()
                    status_code = 200 if result.success else 400
                    return jsonify(response_dict), status_code

                # If result is tuple (response, status), return as is
                if isinstance(result, tuple):
                    return result

                # Otherwise, wrap in success response
                return jsonify({'success': True, 'data': result}), 200

            except ValueError as e:
                # Validation errors
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 400

            except PermissionError as e:
                # Authorization errors
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 403

            except Exception as e:
                # Unexpected errors
                print(f"Unexpected error in {handler_func.__name__}: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': 'Internal server error'
                }), 500

        return wrapper

    def get_json_data(self, required_fields: list = None) -> dict:
        """
        Get and validate JSON data from request - DRY Principle.

        Args:
            required_fields: Optional list of required field names

        Returns:
            Dictionary of request data

        Raises:
            ValueError: If required fields are missing
        """
        data = request.get_json()

        if not data:
            raise ValueError("Request body must be valid JSON")

        if required_fields:
            missing = [field for field in required_fields if field not in data]
            if missing:
                raise ValueError(f"Missing required fields: {', '.join(missing)}")

        return data

    def success_response(self, data=None, message=None):
        """
        Create success response - DRY Principle.

        Args:
            data: Optional response data
            message: Optional success message

        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {'success': True}
        if data is not None:
            response['data'] = data
        if message:
            response['message'] = message
        return jsonify(response), 200

    def error_response(self, error: str, status_code: int = 400):
        """
        Create error response - DRY Principle.

        Args:
            error: Error message
            status_code: HTTP status code (default 400)

        Returns:
            Tuple of (response_dict, status_code)
        """
        return jsonify({
            'success': False,
            'error': error
        }), status_code
