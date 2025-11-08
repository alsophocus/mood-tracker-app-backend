"""
Tag controller following Controller Pattern and SOLID principles.
"""
from flask import request
from flask_login import current_user
from core.base_controller import BaseController
from features.auth.controller import login_required_api


class TagController(BaseController):
    """Tag controller for tag API endpoints."""

    def __init__(self, tag_service):
        super().__init__(tag_service, 'tags', '/api/tags')

    def register_routes(self):
        """Register all tag endpoints."""

        @self.blueprint.route('', methods=['GET'])
        @login_required_api
        @self.handle_request
        def get_all_tags():
            """Get all tags grouped by category."""
            tags = self.service.get_all_tags_grouped()
            return self.success_response(data={'categories': tags})

        @self.blueprint.route('', methods=['POST'])
        @login_required_api
        @self.handle_request
        def create_tag():
            """Create new tag."""
            data = self.get_json_data(required_fields=['name', 'category'])
            tag = self.service.create_tag(
                name=data['name'],
                category=data['category'],
                color=data.get('color', '#808080'),
                icon=data.get('icon', 'tag')
            )
            return self.success_response(data=tag.to_dict(), message='Tag created successfully')

        @self.blueprint.route('/mood/<int:mood_id>', methods=['GET'])
        @login_required_api
        @self.handle_request
        def get_mood_tags(mood_id):
            """Get tags for specific mood."""
            tags = self.service.get_mood_tags(mood_id)
            return self.success_response(data=[tag.to_dict() for tag in tags])

        @self.blueprint.route('/mood/<int:mood_id>', methods=['PUT'])
        @login_required_api
        @self.handle_request
        def set_mood_tags(mood_id):
            """Set tags for mood."""
            data = self.get_json_data(required_fields=['tags'])
            self.service.set_mood_tags(mood_id, data['tags'])
            return self.success_response(message='Tags updated successfully')
