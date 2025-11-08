"""
Database connection and schema management following SOLID principles.

Provides centralized database access with connection pooling and schema initialization.
"""
import psycopg
from psycopg.rows import dict_row
from contextlib import contextmanager
from typing import Generator, Any
from shared.config import Config
from shared.exceptions import DatabaseError


class Database:
    """
    Database manager - Single Responsibility Principle.

    Handles connection management and schema initialization.
    Uses context managers for safe connection handling.
    """

    def __init__(self):
        """Initialize database with configuration."""
        self.url = Config.DATABASE_URL
        self._initialized = False

    @contextmanager
    def get_connection(self) -> Generator[Any, None, None]:
        """
        Get database connection with automatic transaction management.

        Provides connection as context manager with automatic:
        - Commit on success
        - Rollback on exception
        - Connection cleanup

        Yields:
            Database connection with dict_row factory

        Raises:
            DatabaseError: If connection fails
        """
        if not self.url:
            raise DatabaseError("DATABASE_URL not configured")

        conn = None
        try:
            conn = psycopg.connect(self.url, row_factory=dict_row)
            yield conn
        except psycopg.Error as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"Database error: {str(e)}")
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        else:
            if conn:
                conn.commit()
        finally:
            if conn:
                conn.close()

    def initialize(self) -> None:
        """
        Initialize database schema - Idempotent Operation.

        Creates all required tables and indexes if they don't exist.
        Safe to call multiple times.

        Raises:
            DatabaseError: If initialization fails
        """
        if self._initialized:
            return

        if not self.url:
            raise DatabaseError("DATABASE_URL is required")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        name TEXT,
                        provider TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Moods table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS moods (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        date DATE NOT NULL,
                        mood TEXT NOT NULL,
                        notes TEXT DEFAULT '',
                        triggers TEXT DEFAULT '',
                        context_location TEXT DEFAULT '',
                        context_activity TEXT DEFAULT '',
                        context_weather TEXT DEFAULT '',
                        context_notes TEXT DEFAULT '',
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Tags table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tags (
                        id SERIAL PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL,
                        category TEXT NOT NULL,
                        color TEXT DEFAULT '#808080',
                        icon TEXT DEFAULT 'tag',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Mood-Tag association table (many-to-many)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mood_tags (
                        mood_id INTEGER REFERENCES moods(id) ON DELETE CASCADE,
                        tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                        PRIMARY KEY (mood_id, tag_id)
                    )
                ''')

                # Indexes for performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_moods_user_date ON moods(user_id, date DESC)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_moods_timestamp ON moods(timestamp DESC)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_moods_user_id ON moods(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_category ON tags(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_mood_tags_mood ON mood_tags(mood_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_mood_tags_tag ON mood_tags(tag_id)')

                print("✅ Database schema initialized successfully")
                self._initialized = True

        except DatabaseError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to initialize database: {str(e)}")

    def health_check(self) -> bool:
        """
        Check database connection health.

        Returns:
            True if database is accessible, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                return True
        except Exception:
            return False


# Global database instance - Singleton Pattern
db = Database()
