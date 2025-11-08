"""
Mood controller following Controller Pattern and SOLID principles.

Handles HTTP requests for mood tracking endpoints.
"""
from flask import request
from flask_login import current_user
from datetime import date, datetime
from core.base_controller import BaseController
from features.auth.controller import login_required_api
from shared.exceptions import ValidationError


class MoodController(BaseController):
    """
    Mood controller - Single Responsibility Principle.

    Handles mood tracking API endpoints.
    """

    def __init__(self, mood_service):
        """Initialize controller with mood service."""
        super().__init__(mood_service, 'moods', '/api/moods')

    def register_routes(self):
        """Register all mood endpoints."""

        @self.blueprint.route('', methods=['POST'])
        @login_required_api
        @self.handle_request
        def create_mood():
            """Create new mood entry."""
            data = self.get_json_data(required_fields=['date', 'mood'])

            mood_date = date.fromisoformat(data['date'])

            mood = self.service.create_mood(
                user_id=current_user.id,
                mood_date=mood_date,
                mood=data['mood'],
                notes=data.get('notes', ''),
                triggers=data.get('triggers', ''),
                context=data.get('context')
            )

            return self.success_response(
                data=mood.to_dict(),
                message='Mood entry created successfully'
            )

        @self.blueprint.route('', methods=['GET'])
        @login_required_api
        @self.handle_request
        def get_moods():
            """Get moods for current user."""
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')

            if start_date_str and end_date_str:
                start = date.fromisoformat(start_date_str)
                end = date.fromisoformat(end_date_str)
                moods = self.service.get_user_moods_by_date_range(
                    current_user.id, start, end
                )
            else:
                limit = request.args.get('limit', type=int)
                offset = request.args.get('offset', 0, type=int)
                moods = self.service.get_user_moods(
                    current_user.id, limit=limit, offset=offset
                )

            return self.success_response(
                data=[mood.to_dict() for mood in moods]
            )

        @self.blueprint.route('/recent', methods=['GET'])
        @login_required_api
        @self.handle_request
        def get_recent_mood():
            """Get most recent mood entry."""
            mood = self.service.get_recent_mood(current_user.id)
            return self.success_response(data=mood.to_dict() if mood else None)

        @self.blueprint.route('/<int:mood_id>', methods=['PUT', 'PATCH'])
        @login_required_api
        @self.handle_request
        def update_mood(mood_id):
            """Update mood entry."""
            data = self.get_json_data()
            mood = self.service.update_mood(mood_id, current_user.id, data)
            return self.success_response(data=mood.to_dict(), message='Mood updated successfully')

        @self.blueprint.route('/<int:mood_id>', methods=['DELETE'])
        @login_required_api
        @self.handle_request
        def delete_mood(mood_id):
            """Delete mood entry."""
            self.service.delete_mood(mood_id, current_user.id)
            return self.success_response(message='Mood deleted successfully')
