"""
SOLID-compliant interfaces for mood insights system
Interface Segregation Principle - specific interfaces for different concerns
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import date, datetime


class MoodAnalyzerInterface(ABC):
    """Interface for mood analysis operations"""
    
    @abstractmethod
    def analyze_mood_patterns(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Analyze mood patterns over specified period"""
        pass
    
    @abstractmethod
    def get_trigger_correlations(self, user_id: int) -> List[Dict[str, Any]]:
        """Get correlations between triggers and mood levels"""
        pass


class InsightGeneratorInterface(ABC):
    """Interface for generating insights from mood data"""
    
    @abstractmethod
    def generate_insights(self, user_id: int) -> List[Dict[str, Any]]:
        """Generate actionable insights for user"""
        pass
    
    @abstractmethod
    def get_mood_trends(self, user_id: int, period: str = 'month') -> Dict[str, Any]:
        """Get mood trends for specified period"""
        pass


class GoalTrackerInterface(ABC):
    """Interface for goal tracking operations"""
    
    @abstractmethod
    def create_goal(self, user_id: int, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new mood goal"""
        pass
    
    @abstractmethod
    def get_user_goals(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all goals for user"""
        pass
    
    @abstractmethod
    def update_goal_progress(self, goal_id: int, progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update goal progress"""
        pass


class ReminderServiceInterface(ABC):
    """Interface for reminder system"""
    
    @abstractmethod
    def create_reminder(self, user_id: int, reminder_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new reminder"""
        pass
    
    @abstractmethod
    def get_user_reminders(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all reminders for user"""
        pass
    
    @abstractmethod
    def should_send_reminder(self, user_id: int) -> bool:
        """Check if reminder should be sent"""
        pass


class DataExportInterface(ABC):
    """Interface for data export/import operations"""
    
    @abstractmethod
    def export_user_data(self, user_id: int, format: str = 'json') -> Dict[str, Any]:
        """Export all user data"""
        pass
    
    @abstractmethod
    def import_user_data(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Import user data"""
        pass
