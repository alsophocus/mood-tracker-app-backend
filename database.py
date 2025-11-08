import psycopg
from psycopg.rows import dict_row
from config import Config
from contextlib import contextmanager

class Database:
    def __init__(self):
        self.url = Config.DATABASE_URL
        self._initialized = False
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = psycopg.connect(self.url, row_factory=dict_row)
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        else:
            conn.commit()
        finally:
            conn.close()
    
    def initialize(self):
        """Initialize database schema"""
        if self._initialized:
            return
        
        if not self.url:
            raise ValueError("DATABASE_URL is required but not set")
            
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
                        notes TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Indexes for performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_moods_user_date ON moods(user_id, date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_moods_timestamp ON moods(timestamp)')
                
            self._initialized = True
        except Exception as e:
            print(f"Database initialization error: {e}")
            raise
    
    def create_user(self, email, name, provider):
        """Create or get user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Try to get existing user
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = cursor.fetchone()
            
            if user:
                return user
            
            # Create new user
            cursor.execute(
                'INSERT INTO users (email, name, provider) VALUES (%s, %s, %s) RETURNING *',
                (email, name, provider)
            )
            return cursor.fetchone()
    
    def get_user(self, user_id):
        """Get user by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            return cursor.fetchone()
    
    def save_mood(self, user_id, date, mood, notes='', triggers=''):
        """Save mood entry with current timestamp and triggers"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # First, try to add triggers column if it doesn't exist
                try:
                    cursor.execute('ALTER TABLE moods ADD COLUMN triggers TEXT DEFAULT \'\'')
                    conn.commit()
                    print("Added triggers column to moods table")
                except Exception as e:
                    # Column probably already exists, rollback and continue
                    conn.rollback()
                
                # Always insert new entry (no more unique constraint)
                cursor.execute('''
                    INSERT INTO moods (user_id, date, mood, notes, triggers, timestamp)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    RETURNING *
                ''', (user_id, date, mood, notes, triggers))
                
                conn.commit()
                return cursor.fetchone()
                
            except Exception as e:
                conn.rollback()
                raise e
    
    def get_user_moods(self, user_id, limit=None):
        """Get user's moods ordered by date and timestamp"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = 'SELECT * FROM moods WHERE user_id = %s ORDER BY date DESC, timestamp DESC'
            if limit:
                query += f' LIMIT {limit}'
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
    
    def get_all_moods(self):
        """Get all moods from all users"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM moods ORDER BY date DESC')
            return cursor.fetchall()

# Global database instance
db = Database()
