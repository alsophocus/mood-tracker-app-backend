"""
Data access interfaces following SOLID principles.

This module defines abstract interfaces for data access operations,
implementing the Interface Segregation Principle by separating
read and write operations into distinct interfaces.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import date

class MoodReader(ABC):
    """
    Interface for reading mood data - Interface Segregation Principle.
    
    Separates read operations from write operations to ensure clients
    only depend on the methods they actually use.
    """
    
    @abstractmethod
    def get_user_moods(self, user_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get user moods with optional limit.
        
        Args:
            user_id: The ID of the user whose moods to retrieve
            limit: Optional maximum number of moods to return
            
        Returns:
            List of mood dictionaries ordered by most recent timestamp
            
        Raises:
            DatabaseError: If database connection fails
        """
        pass
    
    @abstractmethod
    def get_moods_by_date(self, user_id: int, target_date: date) -> List[Dict[str, Any]]:
        """
        Get moods for specific date.
        
        Args:
            user_id: The ID of the user whose moods to retrieve
            target_date: The specific date to filter moods by
            
        Returns:
            List of mood dictionaries for the specified date
            
        Raises:
            DatabaseError: If database connection fails
        """
        pass

class MoodWriter(ABC):
    """
    Interface for writing mood data - Interface Segregation Principle.
    
    Separates write operations from read operations to ensure
    clear responsibility boundaries and easier testing.
    """
    
    @abstractmethod
    def save_mood(self, user_id: int, mood_date: date, mood: str, notes: str = '') -> Dict[str, Any]:
        """
        Save a new mood entry.
        
        Args:
            user_id: The ID of the user saving the mood
            mood_date: The date for the mood entry
            mood: The mood value (e.g., 'well', 'bad', etc.)
            notes: Optional notes accompanying the mood
            
        Returns:
            Dictionary containing the saved mood data with generated ID
            
        Raises:
            ValidationError: If mood value is invalid
            DatabaseError: If database operation fails
        """
        pass

class UserReader(ABC):
    """
    Interface for reading user data - Single Responsibility Principle.
    
    Handles only user data retrieval operations, keeping
    user management separate from mood management.
    """
    
    @abstractmethod
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        
        Args:
            user_id: The unique identifier for the user
            
        Returns:
            User dictionary if found, None otherwise
            
        Raises:
            DatabaseError: If database connection fails
        """
        pass

class UserWriter(ABC):
    """
    Interface for writing user data - Single Responsibility Principle.
    
    Handles only user data modification operations,
    separated from read operations for clear boundaries.
    """
    
    @abstractmethod
    def create_or_update_user(self, email: str, name: str, provider: str) -> Dict[str, Any]:
        """
        Create or update user.
        
        Uses upsert pattern to handle OAuth login scenarios where
        users may already exist or need to be created.
        
        Args:
            email: User's email address (unique identifier)
            name: User's display name
            provider: OAuth provider (e.g., 'google', 'github')
            
        Returns:
            Dictionary containing user data with ID
            
        Raises:
            ValidationError: If email format is invalid
            DatabaseError: If database operation fails
        """
        pass

class DatabaseConnection(ABC):
    """
    Interface for database connection management - Single Responsibility Principle.
    
    Handles only connection lifecycle management, separated from
    data operations to allow for different connection strategies.
    """
    
    @abstractmethod
    def get_connection(self):
        """
        Get database connection context manager.
        
        Returns a context manager that handles connection lifecycle,
        including automatic commit/rollback and connection cleanup.
        
        Returns:
            Context manager for database connection
            
        Raises:
            ConnectionError: If unable to establish database connection
        """
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize database schema.
        
        Creates necessary tables, indexes, and constraints if they
        don't already exist. Idempotent operation safe to run multiple times.
        
        Raises:
            DatabaseError: If schema creation fails
            PermissionError: If insufficient database privileges
        """
        pass
