"""
Tag and context models following SOLID principles
Single Responsibility Principle - Each model has one clear purpose
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class TagCategory(Enum):
    """
    Tag categories following Open/Closed Principle
    Easy to extend with new categories without modifying existing code
    """
    WORK = "work"
    HEALTH = "health"
    SOCIAL = "social"
    ACTIVITIES = "activities"
    ENVIRONMENT = "environment"
    EMOTIONS = "emotions"
    
    @classmethod
    def get_color(cls, category: str) -> str:
        """Get default color for category"""
        colors = {
            cls.WORK.value: '#FF6B6B',
            cls.HEALTH.value: '#4ECDC4',
            cls.SOCIAL.value: '#45B7D1',
            cls.ACTIVITIES.value: '#96CEB4',
            cls.ENVIRONMENT.value: '#FFEAA7',
            cls.EMOTIONS.value: '#DDA0DD'
        }
        return colors.get(category, '#6750A4')

@dataclass
class Tag:
    """
    Tag domain model following Single Responsibility Principle
    Represents a mood trigger tag with its properties
    """
    id: Optional[int]
    name: str
    category: str
    color: str = '#6750A4'
    icon: Optional[str] = None
    created_at: Optional[datetime] = None
    is_active: bool = True
    
    def __post_init__(self):
        """Validate tag data"""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Tag name cannot be empty")
        
        if not self.category:
            raise ValueError("Tag category is required")
        
        # Set default color based on category if not provided
        if self.color == '#6750A4' and self.category:
            self.color = TagCategory.get_color(self.category)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tag to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'color': self.color,
            'icon': self.icon,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tag':
        """Create tag from dictionary"""
        return cls(
            id=data.get('id'),
            name=data['name'],
            category=data['category'],
            color=data.get('color', '#6750A4'),
            icon=data.get('icon'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            is_active=data.get('is_active', True)
        )

@dataclass
class MoodContext:
    """
    Mood context model following Single Responsibility Principle
    Represents contextual information about a mood entry
    """
    location: Optional[str] = None
    activity: Optional[str] = None
    weather: Optional[str] = None
    sleep_hours: Optional[float] = None
    energy_level: Optional[int] = None  # 1-5 scale
    
    def __post_init__(self):
        """Validate context data"""
        if self.energy_level is not None:
            if not (1 <= self.energy_level <= 5):
                raise ValueError("Energy level must be between 1 and 5")
        
        if self.sleep_hours is not None:
            if not (0 <= self.sleep_hours <= 24):
                raise ValueError("Sleep hours must be between 0 and 24")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return {
            'location': self.location,
            'activity': self.activity,
            'weather': self.weather,
            'sleep_hours': self.sleep_hours,
            'energy_level': self.energy_level
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MoodContext':
        """Create context from dictionary"""
        return cls(
            location=data.get('location'),
            activity=data.get('activity'),
            weather=data.get('weather'),
            sleep_hours=data.get('sleep_hours'),
            energy_level=data.get('energy_level')
        )
    
    def is_empty(self) -> bool:
        """Check if context has any data"""
        return all(value is None for value in [
            self.location, self.activity, self.weather, 
            self.sleep_hours, self.energy_level
        ])

@dataclass
class EnhancedMoodEntry:
    """
    Enhanced mood entry with tags and context
    Following Single Responsibility Principle
    """
    id: Optional[int]
    user_id: int
    date: str
    mood: str
    notes: str
    timestamp: Optional[datetime]
    tags: List[Tag]
    context: MoodContext
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert enhanced mood entry to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date,
            'mood': self.mood,
            'notes': self.notes,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'tags': [tag.to_dict() for tag in self.tags],
            'context': self.context.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedMoodEntry':
        """Create enhanced mood entry from dictionary"""
        return cls(
            id=data.get('id'),
            user_id=data['user_id'],
            date=data['date'],
            mood=data['mood'],
            notes=data.get('notes', ''),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None,
            tags=[Tag.from_dict(tag_data) for tag_data in data.get('tags', [])],
            context=MoodContext.from_dict(data.get('context', {}))
        )
    
    def get_tag_names(self) -> List[str]:
        """Get list of tag names for this mood entry"""
        return [tag.name for tag in self.tags]
    
    def has_tag(self, tag_name: str) -> bool:
        """Check if mood entry has specific tag"""
        return tag_name.lower() in [tag.name.lower() for tag in self.tags]
    
    def get_tags_by_category(self, category: str) -> List[Tag]:
        """Get tags filtered by category"""
        return [tag for tag in self.tags if tag.category == category]
