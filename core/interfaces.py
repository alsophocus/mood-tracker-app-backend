"""
Core interfaces and types following Interface Segregation Principle.

This module defines common interfaces and type definitions used across the application.
Following SOLID principles to ensure loose coupling and high cohesion.
"""
from typing import Protocol, TypeVar, Generic, Optional, List, Dict, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

# Generic type for entity IDs
ID = TypeVar('ID', int, str)

# Generic type for entities
T = TypeVar('T')


@dataclass
class APIResponse:
    """
    Standard API response wrapper - Single Responsibility Principle.

    Provides consistent response structure across all API endpoints.
    """
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {'success': self.success}
        if self.data is not None:
            result['data'] = self.data
        if self.error:
            result['error'] = self.error
        if self.message:
            result['message'] = self.message
        return result


class IRepository(Protocol[T, ID]):
    """
    Repository interface - Interface Segregation Principle.

    Defines the contract for data access operations.
    Implementations should handle database-specific logic.
    """

    def find_by_id(self, id: ID) -> Optional[T]:
        """Find entity by ID."""
        ...

    def find_all(self) -> List[T]:
        """Find all entities."""
        ...

    def save(self, entity: T) -> T:
        """Save entity and return saved instance."""
        ...

    def delete(self, id: ID) -> bool:
        """Delete entity by ID. Returns True if deleted."""
        ...


class IService(Protocol[T, ID]):
    """
    Service interface - Interface Segregation Principle.

    Defines the contract for business logic operations.
    Services orchestrate repositories and implement domain logic.
    """

    def get(self, id: ID) -> Optional[T]:
        """Get entity by ID."""
        ...

    def create(self, data: Dict[str, Any]) -> T:
        """Create new entity."""
        ...

    def update(self, id: ID, data: Dict[str, Any]) -> Optional[T]:
        """Update entity."""
        ...

    def delete(self, id: ID) -> bool:
        """Delete entity."""
        ...


class DatabaseConnection(Protocol):
    """
    Database connection interface - Dependency Inversion Principle.

    Abstracts database connection to allow different implementations.
    """

    def execute(self, query: str, params: tuple = ()) -> Any:
        """Execute query and return result."""
        ...

    def commit(self) -> None:
        """Commit transaction."""
        ...

    def rollback(self) -> None:
        """Rollback transaction."""
        ...

    def close(self) -> None:
        """Close connection."""
        ...
