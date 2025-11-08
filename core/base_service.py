"""
Base service implementation following Service Layer Pattern and SOLID principles.

Provides abstract base class for all service implementations.
Encapsulates business logic and orchestrates repositories.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
from core.interfaces import APIResponse

T = TypeVar('T')  # Entity type
ID = TypeVar('ID', int, str)  # ID type


class BaseService(ABC, Generic[T, ID]):
    """
    Abstract base service - Open/Closed Principle.

    Provides common service functionality while allowing specific implementations.
    Follows Single Responsibility: orchestrates business logic, not data access.
    """

    def __init__(self, repository):
        """
        Initialize service with repository dependency - Dependency Inversion.

        Args:
            repository: Repository implementing IRepository interface
        """
        self.repository = repository

    @abstractmethod
    def _validate_create(self, data: Dict[str, Any]) -> None:
        """
        Validate data for entity creation - Template Method Pattern.

        Subclasses must implement validation logic specific to their entity.
        Should raise ValueError with descriptive message if validation fails.

        Args:
            data: Dictionary containing entity data

        Raises:
            ValueError: If validation fails
        """
        pass

    @abstractmethod
    def _validate_update(self, id: ID, data: Dict[str, Any]) -> None:
        """
        Validate data for entity update - Template Method Pattern.

        Subclasses must implement validation logic specific to their entity.
        Should raise ValueError with descriptive message if validation fails.

        Args:
            id: Entity identifier
            data: Dictionary containing update data

        Raises:
            ValueError: If validation fails
        """
        pass

    def get(self, id: ID) -> Optional[T]:
        """
        Get entity by ID - Single Responsibility Principle.

        Args:
            id: Entity identifier

        Returns:
            Entity if found, None otherwise
        """
        return self.repository.find_by_id(id)

    def get_all(self, limit: Optional[int] = None) -> List[T]:
        """
        Get all entities with optional limit.

        Args:
            limit: Maximum number of results

        Returns:
            List of entities
        """
        return self.repository.find_all(limit=limit)

    def create(self, data: Dict[str, Any]) -> T:
        """
        Create new entity with validation.

        Args:
            data: Dictionary containing entity data

        Returns:
            Created entity

        Raises:
            ValueError: If validation fails
        """
        self._validate_create(data)
        return self.repository.save(data)

    def update(self, id: ID, data: Dict[str, Any]) -> Optional[T]:
        """
        Update entity with validation.

        Args:
            id: Entity identifier
            data: Dictionary containing update data

        Returns:
            Updated entity if found, None otherwise

        Raises:
            ValueError: If validation fails
        """
        self._validate_update(id, data)
        return self.repository.update(id, data)

    def delete(self, id: ID) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity identifier

        Returns:
            True if deleted, False otherwise
        """
        return self.repository.delete(id)

    def create_response(
        self,
        success: bool,
        data: Any = None,
        error: str = None,
        message: str = None
    ) -> APIResponse:
        """
        Create standardized API response - DRY Principle.

        Helper method to create consistent responses across services.

        Args:
            success: Whether operation succeeded
            data: Optional response data
            error: Optional error message
            message: Optional success message

        Returns:
            APIResponse instance
        """
        return APIResponse(
            success=success,
            data=data,
            error=error,
            message=message
        )
