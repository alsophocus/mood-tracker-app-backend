"""
Domain models following SOLID principles.

This module contains the core domain entities and value objects
that represent the business concepts in the mood tracking application.
Each model has a single responsibility and encapsulates related behavior.
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Dict, Any
from enum import Enum

class MoodType(Enum):
    """
    Enumeration of available mood types - Open/Closed Principle for easy extension.
    
    Using an enum ensures type safety and makes it easy to add new mood types
    without modifying existing code that uses mood values.
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
        Get numeric value for mood - Single Responsibility.
        
        Converts mood string to numeric value for analytics and charting.
        Uses a 1-7 scale where 1 is worst and 7 is best mood.
        
        Args:
            mood_str: String representation of the mood
            
        Returns:
            Numeric value between 1-7, defaults to 4 (neutral) for invalid moods
            
        Example:
            >>> MoodType.get_value("very well")
            7
            >>> MoodType.get_value("bad")
            2
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
        return mood_values.get(mood_str, 4)  # Default to neutral if invalid

@dataclass
class MoodEntry:
    """
    Mood entry domain model - Single Responsibility Principle.
    
    Represents a single mood entry with all associated data and behavior.
    Encapsulates mood-related calculations and transformations.
    """
    id: Optional[int]  # None for new entries, populated after saving
    user_id: int  # Foreign key to user who created this mood
    date: date  # Date the mood represents (not necessarily creation date)
    mood: MoodType  # The actual mood value
    notes: str  # Optional user notes about the mood
    timestamp: datetime  # When the mood was actually recorded
    
    @property
    def mood_value(self) -> int:
        """
        Get numeric mood value for analytics.
        
        Delegates to MoodType.get_value() to maintain single source of truth
        for mood value calculations.
        
        Returns:
            Numeric value between 1-7 representing mood intensity
        """
        return MoodType.get_value(self.mood.value)
    
    @property
    def hour(self) -> int:
        """
        Get hour from timestamp for time-based analytics.
        
        Extracts the hour component for daily pattern analysis.
        Useful for understanding mood variations throughout the day.
        
        Returns:
            Hour of day (0-23) when mood was recorded
        """
        return self.timestamp.hour
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for API responses.
        
        Transforms the domain model into a format suitable for JSON serialization
        and API responses. Handles datetime serialization and includes computed values.
        
        Returns:
            Dictionary representation suitable for JSON serialization
            
        Example:
            {
                'id': 123,
                'user_id': 1,
                'date': '2025-10-19',
                'mood': 'well',
                'mood_value': 6,
                'notes': 'Great day!',
                'timestamp': '2025-10-19T14:30:00',
                'hour': 14
            }
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat(),  # Convert date to ISO string
            'mood': self.mood.value,  # Use enum value, not enum object
            'mood_value': self.mood_value,  # Include computed numeric value
            'notes': self.notes,
            'timestamp': self.timestamp.isoformat(),  # Convert datetime to ISO string
            'hour': self.hour  # Include computed hour for convenience
        }

@dataclass
class User:
    """
    User domain model - Single Responsibility Principle.
    
    Represents a user in the system with OAuth authentication data.
    Encapsulates user-related behavior and data transformations.
    """
    id: Optional[int]  # None for new users, populated after creation
    email: str  # Unique identifier from OAuth provider
    name: str  # Display name from OAuth provider
    provider: str  # OAuth provider name (e.g., 'google', 'github')
    created_at: Optional[datetime] = None  # When user account was created
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for API responses.
        
        Transforms the user model into a format suitable for JSON serialization.
        Handles optional datetime fields safely.
        
        Returns:
            Dictionary representation suitable for JSON serialization
            
        Example:
            {
                'id': 1,
                'email': 'user@example.com',
                'name': 'John Doe',
                'provider': 'google',
                'created_at': '2025-10-19T10:00:00'
            }
        """
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'provider': self.provider,
            # Handle None created_at gracefully
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
