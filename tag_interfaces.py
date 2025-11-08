"""
Tag repository interfaces following SOLID principles
Interface Segregation Principle - Separate interfaces for different responsibilities
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from tag_models import Tag, MoodContext, EnhancedMoodEntry

class TagReaderInterface(ABC):
    """
    Interface for reading tag data
    Interface Segregation Principle - Only tag reading operations
    """
    
    @abstractmethod
    def get_all_tags(self) -> List[Tag]:
        """Get all active tags"""
        pass
    
    @abstractmethod
    def get_tags_by_category(self, category: str) -> List[Tag]:
        """Get tags filtered by category"""
        pass
    
    @abstractmethod
    def get_tag_by_id(self, tag_id: int) -> Optional[Tag]:
        """Get tag by ID"""
        pass
    
    @abstractmethod
    def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """Get tag by name"""
        pass
    
    @abstractmethod
    def get_popular_tags(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most used tags with usage count"""
        pass

class TagWriterInterface(ABC):
    """
    Interface for writing tag data
    Interface Segregation Principle - Only tag writing operations
    """
    
    @abstractmethod
    def create_tag(self, tag: Tag) -> Tag:
        """Create new tag"""
        pass
    
    @abstractmethod
    def update_tag(self, tag: Tag) -> Tag:
        """Update existing tag"""
        pass
    
    @abstractmethod
    def delete_tag(self, tag_id: int) -> bool:
        """Delete tag (soft delete - set inactive)"""
        pass
    
    @abstractmethod
    def activate_tag(self, tag_id: int) -> bool:
        """Activate tag"""
        pass

class MoodTagReaderInterface(ABC):
    """
    Interface for reading mood-tag relationships
    Interface Segregation Principle - Only mood-tag reading operations
    """
    
    @abstractmethod
    def get_mood_tags(self, mood_id: int) -> List[Tag]:
        """Get tags for specific mood entry"""
        pass
    
    @abstractmethod
    def get_moods_by_tag(self, tag_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Get mood entries that have specific tag"""
        pass
    
    @abstractmethod
    def get_tag_usage_stats(self, user_id: int, tag_id: int) -> Dict[str, Any]:
        """Get usage statistics for tag"""
        pass

class MoodTagWriterInterface(ABC):
    """
    Interface for writing mood-tag relationships
    Interface Segregation Principle - Only mood-tag writing operations
    """
    
    @abstractmethod
    def add_tags_to_mood(self, mood_id: int, tag_ids: List[int]) -> bool:
        """Add tags to mood entry"""
        pass
    
    @abstractmethod
    def remove_tags_from_mood(self, mood_id: int, tag_ids: List[int]) -> bool:
        """Remove tags from mood entry"""
        pass
    
    @abstractmethod
    def replace_mood_tags(self, mood_id: int, tag_ids: List[int]) -> bool:
        """Replace all tags for mood entry"""
        pass

class MoodContextReaderInterface(ABC):
    """
    Interface for reading mood context data
    Interface Segregation Principle - Only context reading operations
    """
    
    @abstractmethod
    def get_mood_context(self, mood_id: int) -> Optional[MoodContext]:
        """Get context for specific mood entry"""
        pass
    
    @abstractmethod
    def get_context_patterns(self, user_id: int) -> Dict[str, Any]:
        """Get context patterns for user"""
        pass

class MoodContextWriterInterface(ABC):
    """
    Interface for writing mood context data
    Interface Segregation Principle - Only context writing operations
    """
    
    @abstractmethod
    def save_mood_context(self, mood_id: int, context: MoodContext) -> bool:
        """Save context for mood entry"""
        pass
    
    @abstractmethod
    def update_mood_context(self, mood_id: int, context: MoodContext) -> bool:
        """Update context for mood entry"""
        pass

class EnhancedMoodReaderInterface(ABC):
    """
    Interface for reading enhanced mood entries (with tags and context)
    Interface Segregation Principle - Only enhanced mood reading operations
    """
    
    @abstractmethod
    def get_enhanced_mood(self, mood_id: int) -> Optional[EnhancedMoodEntry]:
        """Get enhanced mood entry with tags and context"""
        pass
    
    @abstractmethod
    def get_enhanced_user_moods(self, user_id: int, limit: Optional[int] = None) -> List[EnhancedMoodEntry]:
        """Get enhanced mood entries for user"""
        pass
    
    @abstractmethod
    def get_moods_by_tags(self, user_id: int, tag_names: List[str]) -> List[EnhancedMoodEntry]:
        """Get mood entries filtered by tags"""
        pass
    
    @abstractmethod
    def get_moods_by_context(self, user_id: int, context_filters: Dict[str, Any]) -> List[EnhancedMoodEntry]:
        """Get mood entries filtered by context"""
        pass

class EnhancedMoodWriterInterface(ABC):
    """
    Interface for writing enhanced mood entries
    Interface Segregation Principle - Only enhanced mood writing operations
    """
    
    @abstractmethod
    def save_enhanced_mood(self, mood_entry: EnhancedMoodEntry) -> EnhancedMoodEntry:
        """Save enhanced mood entry with tags and context"""
        pass
    
    @abstractmethod
    def update_enhanced_mood(self, mood_entry: EnhancedMoodEntry) -> EnhancedMoodEntry:
        """Update enhanced mood entry with tags and context"""
        pass
