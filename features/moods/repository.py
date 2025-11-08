"""
Mood repository following Repository Pattern and SOLID principles.
"""
from typing import Optional, Dict, Any, List
from datetime import date
from core.base_repository import BaseRepository
from shared.models import MoodEntry


class MoodRepository(BaseRepository[MoodEntry, int]):
    """Mood repository for managing mood data."""

    def _get_table_name(self) -> str:
        return "moods"

    def _to_entity(self, row: Dict[str, Any]) -> MoodEntry:
        return MoodEntry(
            id=row['id'],
            user_id=row['user_id'],
            date=row['date'],
            mood=row['mood'],
            notes=row.get('notes', ''),
            triggers=row.get('triggers', ''),
            context_location=row.get('context_location', ''),
            context_activity=row.get('context_activity', ''),
            context_weather=row.get('context_weather', ''),
            context_notes=row.get('context_notes', ''),
            timestamp=row['timestamp'],
            created_at=row.get('created_at'),
            tags=None
        )

    def _to_dict(self, entity: MoodEntry) -> Dict[str, Any]:
        return {
            'user_id': entity.user_id,
            'date': entity.date,
            'mood': entity.mood,
            'notes': entity.notes,
            'triggers': entity.triggers,
            'context_location': entity.context_location,
            'context_activity': entity.context_activity,
            'context_weather': entity.context_weather,
            'context_notes': entity.context_notes
        }

    def create_mood(self, user_id: int, date: date, mood: str, notes: str = '', triggers: str = '', context_location: str = '', context_activity: str = '', context_weather: str = '', context_notes: str = '') -> MoodEntry:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO moods (user_id, date, mood, notes, triggers, context_location, context_activity, context_weather, context_notes, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING *
            ''', (user_id, date, mood, notes, triggers, context_location, context_activity, context_weather, context_notes))
            row = cursor.fetchone()
            return self._to_entity(row)

    def find_by_user(self, user_id: int, limit: Optional[int] = None, offset: int = 0) -> List[MoodEntry]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = 'SELECT * FROM moods WHERE user_id = %s ORDER BY date DESC, timestamp DESC'
            params = [user_id]
            if limit:
                query += ' LIMIT %s'
                params.append(limit)
            if offset:
                query += ' OFFSET %s'
                params.append(offset)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._to_entity(row) for row in rows]

    def find_by_user_and_date_range(self, user_id: int, start_date: date, end_date: date) -> List[MoodEntry]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM moods WHERE user_id = %s AND date >= %s AND date <= %s
                ORDER BY date DESC, timestamp DESC
            ''', (user_id, start_date, end_date))
            rows = cursor.fetchall()
            return [self._to_entity(row) for row in rows]

    def find_by_user_and_date(self, user_id: int, target_date: date) -> List[MoodEntry]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM moods WHERE user_id = %s AND date = %s ORDER BY timestamp DESC', (user_id, target_date))
            rows = cursor.fetchall()
            return [self._to_entity(row) for row in rows]

    def get_most_recent(self, user_id: int) -> Optional[MoodEntry]:
        moods = self.find_by_user(user_id, limit=1)
        return moods[0] if moods else None

    def update_mood(self, mood_id: int, user_id: int, updates: Dict[str, Any]) -> Optional[MoodEntry]:
        allowed_fields = {'mood', 'notes', 'triggers', 'context_location', 'context_activity', 'context_weather', 'context_notes'}
        update_fields = {k: v for k, v in updates.items() if k in allowed_fields}
        if not update_fields:
            return self.find_by_id(mood_id)
        set_clauses = [f"{key} = %s" for key in update_fields.keys()]
        values = list(update_fields.values())
        values.extend([mood_id, user_id])
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = f'UPDATE moods SET {", ".join(set_clauses)} WHERE id = %s AND user_id = %s RETURNING *'
            cursor.execute(query, values)
            row = cursor.fetchone()
            return self._to_entity(row) if row else None

    def delete_by_user(self, mood_id: int, user_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM moods WHERE id = %s AND user_id = %s', (mood_id, user_id))
            return cursor.rowcount > 0

    def count_by_user(self, user_id: int) -> int:
        return self.count({'user_id': user_id})
