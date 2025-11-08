"""
User repository following Repository Pattern and SOLID principles.

Handles all data access operations for users.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from core.base_repository import BaseRepository
from shared.models import User


class UserRepository(BaseRepository[User, int]):
    """
    User repository - Single Responsibility Principle.

    Manages user data persistence with PostgreSQL.
    """

    def _get_table_name(self) -> str:
        """Get table name for users."""
        return "users"

    def _to_entity(self, row: Dict[str, Any]) -> User:
        """Convert database row to User entity."""
        return User(
            id=row['id'],
            email=row['email'],
            name=row['name'],
            provider=row['provider'],
            created_at=row.get('created_at')
        )

    def _to_dict(self, entity: User) -> Dict[str, Any]:
        """Convert User entity to dictionary for database operations."""
        return {
            'email': entity.email,
            'name': entity.name,
            'provider': entity.provider
        }

    def find_by_email(self, email: str) -> Optional[User]:
        """
        Find user by email address.

        Args:
            email: User email address

        Returns:
            User if found, None otherwise
        """
        users = self.find_by({'email': email}, limit=1)
        return users[0] if users else None

    def create_or_get(self, email: str, name: str, provider: str) -> User:
        """
        Create new user or get existing user by email - Idempotent Operation.

        Args:
            email: User email address
            name: User display name
            provider: OAuth provider ('google', 'github', etc.)

        Returns:
            User instance (either existing or newly created)
        """
        # Try to find existing user
        existing = self.find_by_email(email)
        if existing:
            return existing

        # Create new user
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (email, name, provider)
                VALUES (%s, %s, %s)
                RETURNING *
            ''', (email, name, provider))
            row = cursor.fetchone()
            return self._to_entity(row)

    def update_last_login(self, user_id: int) -> None:
        """
        Update user's last login timestamp.

        Note: This requires an optional last_login column.
        Safe to call even if column doesn't exist.

        Args:
            user_id: User identifier
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Try to update if column exists
                cursor.execute('''
                    UPDATE users
                    SET last_login = CURRENT_TIMESTAMP
                    WHERE id = %s
                ''', (user_id,))
        except Exception:
            # Column might not exist, ignore
            pass
