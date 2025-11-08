"""
Tag repository implementation following SOLID principles
Single Responsibility Principle - Each class handles one type of data operation
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from tag_interfaces import (
    TagReaderInterface, TagWriterInterface, 
    MoodTagReaderInterface, MoodTagWriterInterface,
    MoodContextReaderInterface, MoodContextWriterInterface,
    EnhancedMoodReaderInterface, EnhancedMoodWriterInterface
)
from tag_models import Tag, MoodContext, EnhancedMoodEntry
from database import Database

class TagRepository(TagReaderInterface, TagWriterInterface):
    """
    Tag repository implementation following Single Responsibility Principle
    Handles only tag CRUD operations
    """
    
    def __init__(self, database: Database):
        self.db = database
    
    def get_all_tags(self) -> List[Tag]:
        """Get all active tags"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, category, color, icon, created_at, is_active
                FROM tags 
                WHERE is_active = TRUE
                ORDER BY category, name
            ''')
            
            return [self._row_to_tag(row) for row in cursor.fetchall()]
    
    def get_tags_by_category(self, category: str) -> List[Tag]:
        """Get tags filtered by category"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, category, color, icon, created_at, is_active
                FROM tags 
                WHERE category = %s AND is_active = TRUE
                ORDER BY name
            ''', (category,))
            
            return [self._row_to_tag(row) for row in cursor.fetchall()]
    
    def get_tag_by_id(self, tag_id: int) -> Optional[Tag]:
        """Get tag by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, category, color, icon, created_at, is_active
                FROM tags 
                WHERE id = %s
            ''', (tag_id,))
            
            row = cursor.fetchone()
            return self._row_to_tag(row) if row else None
    
    def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """Get tag by name"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, category, color, icon, created_at, is_active
                FROM tags 
                WHERE LOWER(name) = LOWER(%s)
            ''', (name,))
            
            row = cursor.fetchone()
            return self._row_to_tag(row) if row else None
    
    def get_popular_tags(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most used tags with usage count"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.id, t.name, t.category, t.color, t.icon, 
                       COUNT(mt.id) as usage_count
                FROM tags t
                LEFT JOIN mood_tags mt ON t.id = mt.tag_id
                WHERE t.is_active = TRUE
                GROUP BY t.id, t.name, t.category, t.color, t.icon
                ORDER BY usage_count DESC, t.name
                LIMIT %s
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def create_tag(self, tag: Tag) -> Tag:
        """Create new tag"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tags (name, category, color, icon, is_active)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, created_at
            ''', (tag.name, tag.category, tag.color, tag.icon, tag.is_active))
            
            result = cursor.fetchone()
            tag.id = result['id']
            tag.created_at = result['created_at']
            
            return tag
    
    def update_tag(self, tag: Tag) -> Tag:
        """Update existing tag"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tags 
                SET name = %s, category = %s, color = %s, icon = %s, is_active = %s
                WHERE id = %s
            ''', (tag.name, tag.category, tag.color, tag.icon, tag.is_active, tag.id))
            
            return tag
    
    def delete_tag(self, tag_id: int) -> bool:
        """Delete tag (soft delete - set inactive)"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE tags SET is_active = FALSE WHERE id = %s', (tag_id,))
            return cursor.rowcount > 0
    
    def activate_tag(self, tag_id: int) -> bool:
        """Activate tag"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE tags SET is_active = TRUE WHERE id = %s', (tag_id,))
            return cursor.rowcount > 0
    
    def _row_to_tag(self, row: Dict[str, Any]) -> Tag:
        """Convert database row to Tag object"""
        return Tag(
            id=row['id'],
            name=row['name'],
            category=row['category'],
            color=row['color'],
            icon=row['icon'],
            created_at=row['created_at'],
            is_active=row['is_active']
        )

class MoodTagRepository(MoodTagReaderInterface, MoodTagWriterInterface):
    """
    Mood-Tag relationship repository following Single Responsibility Principle
    Handles only mood-tag relationship operations
    """
    
    def __init__(self, database: Database, tag_repository: TagRepository):
        self.db = database
        self.tag_repo = tag_repository
    
    def get_mood_tags(self, mood_id: int) -> List[Tag]:
        """Get tags for specific mood entry"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.id, t.name, t.category, t.color, t.icon, t.created_at, t.is_active
                FROM tags t
                JOIN mood_tags mt ON t.id = mt.tag_id
                WHERE mt.mood_id = %s AND t.is_active = TRUE
                ORDER BY t.category, t.name
            ''', (mood_id,))
            
            return [self.tag_repo._row_to_tag(row) for row in cursor.fetchall()]
    
    def get_moods_by_tag(self, tag_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Get mood entries that have specific tag"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT m.id, m.date, m.mood, m.notes, m.timestamp
                FROM moods m
                JOIN mood_tags mt ON m.id = mt.mood_id
                WHERE mt.tag_id = %s AND m.user_id = %s
                ORDER BY m.date DESC
            ''', (tag_id, user_id))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_tag_usage_stats(self, user_id: int, tag_id: int) -> Dict[str, Any]:
        """Get usage statistics for tag"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_uses,
                    MIN(m.date) as first_used,
                    MAX(m.date) as last_used,
                    AVG(CASE 
                        WHEN m.mood = 'very bad' THEN 1
                        WHEN m.mood = 'bad' THEN 2
                        WHEN m.mood = 'slightly bad' THEN 3
                        WHEN m.mood = 'neutral' THEN 4
                        WHEN m.mood = 'slightly well' THEN 5
                        WHEN m.mood = 'well' THEN 6
                        WHEN m.mood = 'very well' THEN 7
                    END) as avg_mood_value
                FROM moods m
                JOIN mood_tags mt ON m.id = mt.mood_id
                WHERE mt.tag_id = %s AND m.user_id = %s
            ''', (tag_id, user_id))
            
            result = cursor.fetchone()
            return dict(result) if result else {}
    
    def add_tags_to_mood(self, mood_id: int, tag_ids: List[int]) -> bool:
        """Add tags to mood entry"""
        if not tag_ids:
            return True
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            for tag_id in tag_ids:
                cursor.execute('''
                    INSERT INTO mood_tags (mood_id, tag_id)
                    VALUES (%s, %s)
                    ON CONFLICT (mood_id, tag_id) DO NOTHING
                ''', (mood_id, tag_id))
            
            return True
    
    def remove_tags_from_mood(self, mood_id: int, tag_ids: List[int]) -> bool:
        """Remove tags from mood entry"""
        if not tag_ids:
            return True
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM mood_tags 
                WHERE mood_id = %s AND tag_id = ANY(%s)
            ''', (mood_id, tag_ids))
            
            return True
    
    def replace_mood_tags(self, mood_id: int, tag_ids: List[int]) -> bool:
        """Replace all tags for mood entry"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Remove all existing tags
            cursor.execute('DELETE FROM mood_tags WHERE mood_id = %s', (mood_id,))
            
            # Add new tags
            if tag_ids:
                for tag_id in tag_ids:
                    cursor.execute('''
                        INSERT INTO mood_tags (mood_id, tag_id)
                        VALUES (%s, %s)
                    ''', (mood_id, tag_id))
            
            return True
