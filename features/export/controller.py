"""
Export controller following Controller Pattern and SOLID principles.
"""
from flask import Blueprint, request, Response
from flask_login import current_user
from features.auth.controller import login_required_api
import json


class ExportController:
    """Export controller for data export endpoints."""

    def __init__(self, export_service):
        self.service = export_service
        self.blueprint = Blueprint('export', __name__, url_prefix='/api/export')

    def register_routes(self):
        """Register all export endpoints."""

        @self.blueprint.route('/json', methods=['GET'])
        @login_required_api
        def export_json():
            """Export mood data as JSON."""
            days = request.args.get('days', 30, type=int)
            data = self.service.export_to_json(current_user.id, days)
            
            return Response(
                json.dumps(data, indent=2),
                mimetype='application/json',
                headers={'Content-Disposition': 'attachment;filename=mood_data.json'}
            )

        @self.blueprint.route('/csv', methods=['GET'])
        @login_required_api
        def export_csv():
            """Export mood data as CSV."""
            days = request.args.get('days', 30, type=int)
            csv_data = self.service.export_to_csv(current_user.id, days)
            
            return Response(
                csv_data,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment;filename=mood_data.csv'}
            )

        @self.blueprint.route('/summary', methods=['GET'])
        @login_required_api
        def export_summary():
            """Get summary statistics."""
            days = request.args.get('days', 30, type=int)
            data = self.service.get_summary_stats(current_user.id, days)
            return {'success': True, 'data': data}, 200
