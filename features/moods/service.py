"""
Mood service following Service Layer Pattern and SOLID principles.
"""
from typing import Dict, Any, List, Optional
from datetime import date
from core.base_service import BaseService
from shared.models import MoodEntry, MoodType
from shared.exceptions import ValidationError, NotFoundError, AuthorizationError
from shared.config import Config


class MoodService(BaseService[MoodEntry, int]):
    """Mood service for mood tracking business logic."""

    def __init__(self, repository):
        super().__init__(repository)

    def _validate_create(self, data: Dict[str, Any]) -> None:
        required = ['user_id', 'date', 'mood']
        missing = [f for f in required if f not in data]
        if missing:
            raise ValidationError(f"Missing required fields: {', '.join(missing)}")

        mood = data['mood']
        if not MoodType.is_valid(mood):
            valid_moods = [m.value for m in MoodType]
            raise ValidationError(f"Invalid mood value '{mood}'. Must be one of: {', '.join(valid_moods)}")

        try:
            if isinstance(data['date'], str):
                date.fromisoformat(data['date'])
        except ValueError:
            raise ValidationError("Invalid date format. Use YYYY-MM-DD")

        user_id = data['user_id']
        mood_date = data['date'] if isinstance(data['date'], date) else date.fromisoformat(data['date'])
        existing_count = len(self.repository.find_by_user_and_date(user_id, mood_date))
        if existing_count >= Config.MAX_MOODS_PER_DAY:
            raise ValidationError(f"Maximum {Config.MAX_MOODS_PER_DAY} mood entries per day reached")

    def _validate_update(self, id: int, data: Dict[str, Any]) -> None:
        if 'mood' in data:
            if not MoodType.is_valid(data['mood']):
                valid_moods = [m.value for m in MoodType]
                raise ValidationError(f"Invalid mood value. Must be one of: {', '.join(valid_moods)}")

    def create_mood(self, user_id: int, mood_date: date, mood: str, notes: str = '', triggers: str = '', context: Optional[Dict[str, str]] = None) -> MoodEntry:
        data = {'user_id': user_id, 'date': mood_date, 'mood': mood}
        self._validate_create(data)
        ctx = context or {}
        return self.repository.create_mood(
            user_id=user_id,
            date=mood_date,
            mood=mood,
            notes=notes,
            triggers=triggers,
            context_location=ctx.get('location', ''),
            context_activity=ctx.get('activity', ''),
            context_weather=ctx.get('weather', ''),
            context_notes=ctx.get('notes', '')
        )

    def get_user_moods(self, user_id: int, limit: Optional[int] = None, offset: int = 0) -> List[MoodEntry]:
        if limit and limit > Config.MAX_PAGE_SIZE:
            limit = Config.MAX_PAGE_SIZE
        return self.repository.find_by_user(user_id, limit=limit, offset=offset)

    def get_user_moods_by_date_range(self, user_id: int, start_date: date, end_date: date) -> List[MoodEntry]:
        return self.repository.find_by_user_and_date_range(user_id, start_date, end_date)

    def get_recent_mood(self, user_id: int) -> Optional[MoodEntry]:
        return self.repository.get_most_recent(user_id)

    def update_mood(self, mood_id: int, user_id: int, updates: Dict[str, Any]) -> MoodEntry:
        self._validate_update(mood_id, updates)
        updated = self.repository.update_mood(mood_id, user_id, updates)
        if not updated:
            mood = self.repository.find_by_id(mood_id)
            if not mood:
                raise NotFoundError(f"Mood {mood_id} not found")
            else:
                raise AuthorizationError("Not authorized to update this mood")
        return updated

    def delete_mood(self, mood_id: int, user_id: int) -> bool:
        deleted = self.repository.delete_by_user(mood_id, user_id)
        if not deleted:
            mood = self.repository.find_by_id(mood_id)
            if not mood:
                raise NotFoundError(f"Mood {mood_id} not found")
            else:
                raise AuthorizationError("Not authorized to delete this mood")
        return True

    def get_mood_count(self, user_id: int) -> int:
        return self.repository.count_by_user(user_id)
