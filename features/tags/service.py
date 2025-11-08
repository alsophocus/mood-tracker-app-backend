"""
Tag service following Service Layer Pattern and SOLID principles.
"""
from typing import Dict, Any, List
from core.base_service import BaseService
from shared.models import Tag
from shared.exceptions import ValidationError


class TagService(BaseService[Tag, int]):
    """Tag service for managing tags and mood-tag associations."""

    def __init__(self, repository):
        super().__init__(repository)

    def _validate_create(self, data: Dict[str, Any]) -> None:
        required = ['name', 'category']
        missing = [f for f in required if not data.get(f)]
        if missing:
            raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    def _validate_update(self, id: int, data: Dict[str, Any]) -> None:
        pass

    def get_all_tags_grouped(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all tags grouped by category."""
        grouped = self.repository.get_all_grouped_by_category()
        result = {}
        for category, tags in grouped.items():
            result[category] = [tag.to_dict() for tag in tags]
        return result

    def create_tag(self, name: str, category: str, color: str = '#808080', icon: str = 'tag') -> Tag:
        """Create new tag."""
        self._validate_create({'name': name, 'category': category})
        return self.repository.create_or_get(name, category, color, icon)

    def add_tags_to_mood(self, mood_id: int, tag_names: List[str]) -> None:
        """Add tags to mood by tag names."""
        for tag_name in tag_names:
            tag = self.repository.find_by_name(tag_name)
            if tag:
                self.repository.add_mood_tag(mood_id, tag.id)

    def set_mood_tags(self, mood_id: int, tag_names: List[str]) -> None:
        """Replace all tags for a mood."""
        self.repository.clear_mood_tags(mood_id)
        self.add_tags_to_mood(mood_id, tag_names)

    def get_mood_tags(self, mood_id: int) -> List[Tag]:
        """Get all tags for a mood."""
        return self.repository.get_mood_tags(mood_id)
