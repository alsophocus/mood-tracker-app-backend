"""
Analytics controller following Controller Pattern and SOLID principles.
"""
from flask import Blueprint, request
from flask_login import current_user
from features.auth.controller import login_required_api


class AnalyticsController:
    """Analytics controller for mood analytics endpoints."""

    def __init__(self, analytics_service):
        self.service = analytics_service
        self.blueprint = Blueprint('analytics', __name__, url_prefix='/api/analytics')

    def register_routes(self):
        """Register all analytics endpoints."""

        @self.blueprint.route('/distribution', methods=['GET'])
        @login_required_api
        def get_mood_distribution():
            """Get mood distribution."""
            days = request.args.get('days', 30, type=int)
            data = self.service.get_mood_distribution(current_user.id, days)
            return {'success': True, 'data': data}, 200

        @self.blueprint.route('/average', methods=['GET'])
        @login_required_api
        def get_average_mood():
            """Get average mood."""
            days = request.args.get('days', 30, type=int)
            data = self.service.get_average_mood(current_user.id, days)
            return {'success': True, 'data': data}, 200

        @self.blueprint.route('/trends', methods=['GET'])
        @login_required_api
        def get_trends():
            """Get mood trends."""
            days = request.args.get('days', 30, type=int)
            data = self.service.get_trends(current_user.id, days)
            return {'success': True, 'data': data}, 200

        @self.blueprint.route('/hourly-patterns', methods=['GET'])
        @login_required_api
        def get_hourly_patterns():
            """Get hourly mood patterns."""
            days = request.args.get('days', 30, type=int)
            data = self.service.get_hourly_patterns(current_user.id, days)
            return {'success': True, 'data': data}, 200

        @self.blueprint.route('/quick-stats', methods=['GET'])
        @login_required_api
        def get_quick_stats():
            """Get quick statistics overview."""
            data = self.service.get_quick_stats(current_user.id)
            return {'success': True, 'data': data}, 200

        @self.blueprint.route('/week-comparison', methods=['GET'])
        @login_required_api
        def get_week_comparison():
            """Compare current week vs previous week."""
            data = self.service.get_week_comparison(current_user.id)
            return {'success': True, 'data': data}, 200
