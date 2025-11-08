"""
Shared data models following SOLID principles.

Defines core domain entities used across the application.
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class MoodType(Enum):
    """
    Mood type enumeration - Open/Closed Principle.

    Defines available mood types with type safety.
    Easy to extend without modifying existing code.
    """
    VERY_BAD = "very bad"
    BAD = "bad"
    SLIGHTLY_BAD = "slightly bad"
    NEUTRAL = "neutral"
    SLIGHTLY_WELL = "slightly well"
    WELL = "well"
    VERY_WELL = "very well"

    @classmethod
    def get_value(cls, mood_str: str) -> int:
        """
        Convert mood string to numeric value (1-7 scale).

        Args:
            mood_str: Mood string

        Returns:
            Numeric value (1=worst, 7=best)
        """
        mood_values = {
            cls.VERY_BAD.value: 1,
            cls.BAD.value: 2,
            cls.SLIGHTLY_BAD.value: 3,
            cls.NEUTRAL.value: 4,
            cls.SLIGHTLY_WELL.value: 5,
            cls.WELL.value: 6,
            cls.VERY_WELL.value: 7
        }
        return mood_values.get(mood_str, 4)

    @classmethod
    def is_valid(cls, mood_str: str) -> bool:
        """Check if mood string is valid."""
        return mood_str in [m.value for m in cls]


@dataclass
class User:
    """
    User domain model - Single Responsibility Principle.

    Represents a user with OAuth authentication.
    """
    id: Optional[int]
    email: str
    name: str
    provider: str
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'provider': self.provider,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class MoodEntry:
    """
    Mood entry domain model - Single Responsibility Principle.

    Represents a single mood entry with context and metadata.
    """
    id: Optional[int]
    user_id: int
    date: date
    mood: str
    notes: str
    triggers: str
    context_location: str
    context_activity: str
    context_weather: str
    context_notes: str
    timestamp: datetime
    created_at: Optional[datetime] = None
    tags: Optional[List[str]] = None

    @property
    def mood_value(self) -> int:
        """Get numeric mood value for analytics."""
        return MoodType.get_value(self.mood)

    @property
    def hour(self) -> int:
        """Get hour from timestamp for time-based analytics."""
        return self.timestamp.hour

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat(),
            'mood': self.mood,
            'mood_value': self.mood_value,
            'notes': self.notes,
            'triggers': self.triggers,
            'context': {
                'location': self.context_location,
                'activity': self.context_activity,
                'weather': self.context_weather,
                'notes': self.context_notes
            },
            'timestamp': self.timestamp.isoformat(),
            'hour': self.hour,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if self.tags is not None:
            result['tags'] = self.tags
        return result


@dataclass
class Tag:
    """
    Tag domain model - Single Responsibility Principle.

    Represents a categorized tag for mood entries.
    """
    id: Optional[int]
    name: str
    category: str
    color: str = '#808080'
    icon: str = 'tag'
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'color': self.color,
            'icon': self.icon,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
