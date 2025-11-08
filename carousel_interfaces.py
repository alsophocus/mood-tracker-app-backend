"""
SOLID-compliant interfaces for carousel system
Interface Segregation Principle - specific interfaces for carousel concerns
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class CarouselDataInterface(ABC):
    """Interface for carousel data management"""
    
    @abstractmethod
    def get_recent_moods(self, user_id: int, limit: int = 15) -> List[Dict[str, Any]]:
        """Get recent mood entries for carousel"""
        pass


class CarouselControllerInterface(ABC):
    """Interface for carousel control logic"""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize carousel"""
        pass
    
    @abstractmethod
    def start_auto_scroll(self) -> None:
        """Start automatic scrolling"""
        pass
    
    @abstractmethod
    def pause_auto_scroll(self) -> None:
        """Pause automatic scrolling"""
        pass
    
    @abstractmethod
    def next_slide(self) -> None:
        """Move to next slide"""
        pass
    
    @abstractmethod
    def previous_slide(self) -> None:
        """Move to previous slide"""
        pass
