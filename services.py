"""
Business logic services following SOLID principles
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta

from interfaces import MoodReader, MoodWriter, UserReader, UserWriter
from models import MoodEntry, MoodType
from analytics import MoodAnalytics

class MoodServiceInterface(ABC):
    """Interface for mood business logic - Interface Segregation Principle"""
    
    @abstractmethod
    def save_mood(self, user_id: int, mood: str, notes: str = '') -> Dict[str, Any]:
        """Save mood with proper timezone handling"""
        pass
    
    @abstractmethod
    def get_user_moods(self, user_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get user moods"""
        pass
    
    @abstractmethod
    def get_daily_patterns(self, user_id: int, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Get daily mood patterns"""
        pass

class TimezoneServiceInterface(ABC):
    """Interface for timezone handling - Single Responsibility Principle"""
    
    @abstractmethod
    def get_chile_date(self) -> date:
        """Get current date in Chile timezone (UTC-3)"""
        pass
    
    @abstractmethod
    def convert_to_chile_time(self, utc_time: datetime) -> datetime:
        """Convert UTC time to Chile time"""
        pass

class MoodService(MoodServiceInterface):
    """Mood business logic implementation - Single Responsibility Principle"""
    
    def __init__(self, mood_reader: MoodReader, mood_writer: MoodWriter, timezone_service: TimezoneServiceInterface):
        self.mood_reader = mood_reader  # Dependency Inversion Principle
        self.mood_writer = mood_writer  # Dependency Inversion Principle
        self.timezone_service = timezone_service  # Dependency Inversion Principle
    
    def save_mood(self, user_id: int, mood: str, notes: str = '') -> Dict[str, Any]:
        """Save mood with proper timezone handling"""
        # Validate mood type
        try:
            mood_type = MoodType(mood)
        except ValueError:
            raise ValueError(f"Invalid mood type: {mood}")
        
        # Use Chile timezone for date
        chile_date = self.timezone_service.get_chile_date()
        
        # Save mood
        result = self.mood_writer.save_mood(user_id, chile_date, mood, notes)
        
        return {
            'success': True,
            'message': 'Mood saved successfully!',
            'mood': mood,
            'notes': notes,
            'date': chile_date.isoformat(),
            'result': result
        }
    
    def get_user_moods(self, user_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get user moods"""
        return self.mood_reader.get_user_moods(user_id, limit)
    
    def get_daily_patterns(self, user_id: int, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Get daily mood patterns"""
        moods = self.mood_reader.get_user_moods(user_id)
        analytics = MoodAnalytics(moods)
        
        if target_date:
            result = analytics.get_daily_patterns_for_date(target_date.isoformat())
        else:
            result = analytics.get_daily_patterns()
        
        # Ensure valid structure
        if not result.get('labels') or not result.get('data'):
            result = {
                'labels': [f"{hour:02d}:00" for hour in range(24)],
                'data': [None] * 24,
                'period': f'No data for {target_date}' if target_date else 'No data available'
            }
        
        return result

class ChileTimezoneService(TimezoneServiceInterface):
    """Chile timezone service implementation - Single Responsibility Principle"""
    
    def get_chile_date(self) -> date:
        """Get current date in Chile timezone (UTC-3)"""
        chile_time = datetime.now() - timedelta(hours=3)
        return chile_time.date()
    
    def convert_to_chile_time(self, utc_time: datetime) -> datetime:
        """Convert UTC time to Chile time"""
        return utc_time - timedelta(hours=3)

class UserService:
    """User business logic implementation - Single Responsibility Principle"""
    
    def __init__(self, user_reader: UserReader, user_writer: UserWriter):
        self.user_reader = user_reader  # Dependency Inversion Principle
        self.user_writer = user_writer  # Dependency Inversion Principle
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return self.user_reader.get_user(user_id)
    
    def create_or_update_user(self, email: str, name: str, provider: str) -> Dict[str, Any]:
        """Create or update user"""
        return self.user_writer.create_or_update_user(email, name, provider)

# Factory function following Dependency Inversion Principle
def create_services(mood_reader: MoodReader, mood_writer: MoodWriter, 
                   user_reader: UserReader, user_writer: UserWriter):
    """Factory to create services with proper dependencies"""
    timezone_service = ChileTimezoneService()
    mood_service = MoodService(mood_reader, mood_writer, timezone_service)
    user_service = UserService(user_reader, user_writer)
    
    return mood_service, user_service, timezone_service
