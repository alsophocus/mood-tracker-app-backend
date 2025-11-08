"""
Insights controller following Controller Pattern and SOLID principles.
"""
from flask import Blueprint
from flask_login import current_user
from features.auth.controller import login_required_api


class InsightsController:
    """Insights controller for mood insights endpoints."""

    def __init__(self, insights_service):
        self.service = insights_service
        self.blueprint = Blueprint('insights', __name__, url_prefix='/api/insights')

    def register_routes(self):
        """Register all insights endpoints."""

        @self.blueprint.route('', methods=['GET'])
        @login_required_api
        def get_insights():
            """Get personalized insights."""
            data = self.service.generate_insights(current_user.id)
            return {'success': True, 'data': data}, 200

        @self.blueprint.route('/tag-correlations', methods=['GET'])
        @login_required_api
        def get_tag_correlations():
            """Get tag-mood correlations."""
            data = self.service.get_tag_correlations(current_user.id)
            return {'success': True, 'data': data}, 200
