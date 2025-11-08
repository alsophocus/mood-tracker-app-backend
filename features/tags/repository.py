"""
Tag repository following Repository Pattern and SOLID principles.
"""
from typing import Optional, Dict, Any, List
from core.base_repository import BaseRepository
from shared.models import Tag


class TagRepository(BaseRepository[Tag, int]):
    """Tag repository for managing tag data."""

    def _get_table_name(self) -> str:
        return "tags"

    def _to_entity(self, row: Dict[str, Any]) -> Tag:
        return Tag(
            id=row['id'],
            name=row['name'],
            category=row['category'],
            color=row.get('color', '#808080'),
            icon=row.get('icon', 'tag'),
            created_at=row.get('created_at')
        )

    def _to_dict(self, entity: Tag) -> Dict[str, Any]:
        return {
            'name': entity.name,
            'category': entity.category,
            'color': entity.color,
            'icon': entity.icon
        }

    def find_by_name(self, name: str) -> Optional[Tag]:
        """Find tag by name."""
        tags = self.find_by({'name': name}, limit=1)
        return tags[0] if tags else None

    def find_by_category(self, category: str) -> List[Tag]:
        """Find all tags in category."""
        return self.find_by({'category': category})

    def get_all_grouped_by_category(self) -> Dict[str, List[Tag]]:
        """Get all tags grouped by category."""
        all_tags = self.find_all()
        grouped = {}
        for tag in all_tags:
            if tag.category not in grouped:
                grouped[tag.category] = []
            grouped[tag.category].append(tag)
        return grouped

    def create_or_get(self, name: str, category: str, color: str = '#808080', icon: str = 'tag') -> Tag:
        """Create tag or get existing."""
        existing = self.find_by_name(name)
        if existing:
            return existing

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tags (name, category, color, icon)
                VALUES (%s, %s, %s, %s)
                RETURNING *
            ''', (name, category, color, icon))
            row = cursor.fetchone()
            return self._to_entity(row)

    def add_mood_tag(self, mood_id: int, tag_id: int) -> None:
        """Associate tag with mood."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO mood_tags (mood_id, tag_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            ''', (mood_id, tag_id))

    def remove_mood_tag(self, mood_id: int, tag_id: int) -> None:
        """Remove tag from mood."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM mood_tags WHERE mood_id = %s AND tag_id = %s',
                (mood_id, tag_id)
            )

    def get_mood_tags(self, mood_id: int) -> List[Tag]:
        """Get all tags for a mood."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.* FROM tags t
                JOIN mood_tags mt ON mt.tag_id = t.id
                WHERE mt.mood_id = %s
            ''', (mood_id,))
            rows = cursor.fetchall()
            return [self._to_entity(row) for row in rows]

    def clear_mood_tags(self, mood_id: int) -> None:
        """Remove all tags from mood."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM mood_tags WHERE mood_id = %s', (mood_id,))
