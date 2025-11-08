"""
Base repository implementation following Repository Pattern and SOLID principles.

Provides abstract base class for all repository implementations.
Handles common database operations with proper error handling.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
from contextlib import contextmanager

T = TypeVar('T')  # Entity type
ID = TypeVar('ID', int, str)  # ID type


class BaseRepository(ABC, Generic[T, ID]):
    """
    Abstract base repository - Open/Closed Principle.

    Provides common repository functionality while allowing specific implementations.
    Subclasses must implement abstract methods for entity-specific logic.
    """

    def __init__(self, db):
        """
        Initialize repository with database dependency.

        Args:
            db: Database instance implementing connection management
        """
        self.db = db

    @contextmanager
    def get_connection(self):
        """
        Get database connection with automatic transaction management.

        Yields connection and handles commit/rollback automatically.
        Follows context manager protocol for clean resource management.
        """
        with self.db.get_connection() as conn:
            yield conn

    @abstractmethod
    def _to_entity(self, row: Dict[str, Any]) -> T:
        """
        Convert database row to entity - Template Method Pattern.

        Subclasses must implement this to define entity mapping.

        Args:
            row: Database row as dictionary

        Returns:
            Entity instance
        """
        pass

    @abstractmethod
    def _to_dict(self, entity: T) -> Dict[str, Any]:
        """
        Convert entity to dictionary for database operations.

        Subclasses must implement this to define entity serialization.

        Args:
            entity: Entity instance

        Returns:
            Dictionary suitable for database operations
        """
        pass

    @abstractmethod
    def _get_table_name(self) -> str:
        """
        Get table name for this repository.

        Returns:
            Table name as string
        """
        pass

    def find_by_id(self, id: ID) -> Optional[T]:
        """
        Find entity by ID - Single Responsibility Principle.

        Args:
            id: Entity identifier

        Returns:
            Entity if found, None otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            table = self._get_table_name()
            cursor.execute(f"SELECT * FROM {table} WHERE id = %s", (id,))
            row = cursor.fetchone()
            return self._to_entity(row) if row else None

    def find_all(self, limit: Optional[int] = None) -> List[T]:
        """
        Find all entities with optional limit.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of entities
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            table = self._get_table_name()
            query = f"SELECT * FROM {table}"
            if limit:
                query += f" LIMIT {limit}"
            cursor.execute(query)
            rows = cursor.fetchall()
            return [self._to_entity(row) for row in rows]

    def find_by(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[T]:
        """
        Find entities matching filters - Open/Closed Principle.

        Generic filtering method that works for any entity type.

        Args:
            filters: Dictionary of field:value pairs to filter by
            limit: Maximum number of results

        Returns:
            List of matching entities
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            table = self._get_table_name()

            where_clauses = [f"{key} = %s" for key in filters.keys()]
            where_str = " AND ".join(where_clauses)
            values = tuple(filters.values())

            query = f"SELECT * FROM {table} WHERE {where_str}"
            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, values)
            rows = cursor.fetchall()
            return [self._to_entity(row) for row in rows]

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching optional filters.

        Args:
            filters: Optional dictionary of field:value pairs

        Returns:
            Count of matching entities
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            table = self._get_table_name()

            if filters:
                where_clauses = [f"{key} = %s" for key in filters.keys()]
                where_str = " AND ".join(where_clauses)
                values = tuple(filters.values())
                cursor.execute(f"SELECT COUNT(*) as count FROM {table} WHERE {where_str}", values)
            else:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")

            result = cursor.fetchone()
            return result['count'] if result else 0

    def delete(self, id: ID) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity identifier

        Returns:
            True if entity was deleted, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            table = self._get_table_name()
            cursor.execute(f"DELETE FROM {table} WHERE id = %s", (id,))
            return cursor.rowcount > 0
