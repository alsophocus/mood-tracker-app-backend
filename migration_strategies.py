"""
SOLID-compliant migration strategies
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from database import Database
import psycopg


class MigrationStrategyInterface(ABC):
    """Interface Segregation Principle - specific migration strategy interface"""
    
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """Execute the migration strategy"""
        pass


class CompleteMoodTriggersStrategy(MigrationStrategyInterface):
    """Single Responsibility - handles complete mood triggers schema creation"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def execute(self) -> Dict[str, Any]:
        try:
            conn = psycopg.connect(self.db.url, autocommit=True)
            cursor = conn.cursor()
            
            # Create tags table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS public.tags (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL,
                    category VARCHAR(30) NOT NULL,
                    color VARCHAR(7) DEFAULT '#6750A4',
                    icon VARCHAR(50) DEFAULT 'tag',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create mood_tags junction table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS public.mood_tags (
                    id SERIAL PRIMARY KEY,
                    mood_id INTEGER REFERENCES moods(id) ON DELETE CASCADE,
                    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(mood_id, tag_id)
                )
            """)
            
            # Add context columns to moods table
            cursor.execute("""
                ALTER TABLE public.moods 
                ADD COLUMN IF NOT EXISTS context_location VARCHAR(100),
                ADD COLUMN IF NOT EXISTS context_activity VARCHAR(100),
                ADD COLUMN IF NOT EXISTS context_weather VARCHAR(50),
                ADD COLUMN IF NOT EXISTS context_notes TEXT
            """)
            
            # Insert default tags with Material Design 3 colors
            default_tags = [
                ('work', 'work', '#D32F2F', 'work'),
                ('exercise', 'health', '#388E3C', 'fitness_center'),
                ('sleep', 'health', '#1976D2', 'bedtime'),
                ('family', 'social', '#F57C00', 'family_restroom'),
                ('friends', 'social', '#7B1FA2', 'group'),
                ('food', 'activities', '#689F38', 'restaurant'),
                ('music', 'activities', '#0288D1', 'music_note'),
                ('weather', 'environment', '#00796B', 'wb_sunny'),
                ('stress', 'emotions', '#C62828', 'psychology'),
                ('relaxation', 'emotions', '#2E7D32', 'spa')
            ]
            
            for name, category, color, icon in default_tags:
                cursor.execute("""
                    INSERT INTO public.tags (name, category, color, icon)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (name) DO NOTHING
                """, (name, category, color, icon))
            
            # Get counts
            cursor.execute('SELECT COUNT(*) FROM public.tags')
            tag_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM public.mood_tags')
            mood_tag_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'success': True,
                'message': f'✅ Complete mood triggers schema created! {tag_count} tags, {mood_tag_count} mood-tag links.',
                'tag_count': tag_count,
                'mood_tag_count': mood_tag_count,
                'method': 'complete_schema'
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'method': 'complete_schema'}


class AutocommitMigrationStrategy(MigrationStrategyInterface):
    """Single Responsibility - handles autocommit DDL operations"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def execute(self) -> Dict[str, Any]:
        try:
            conn = psycopg.connect(self.db.url, autocommit=True)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS public.tags (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL,
                    category VARCHAR(30) NOT NULL,
                    color VARCHAR(7) DEFAULT '#6750A4'
                )
            """)
            
            cursor.execute("""
                INSERT INTO public.tags (name, category, color)
                VALUES ('work', 'work', '#FF6B6B')
                ON CONFLICT (name) DO NOTHING
            """)
            
            cursor.execute('SELECT COUNT(*) FROM public.tags')
            tag_count = cursor.fetchone()[0]
            conn.close()
            
            return {
                'success': True,
                'message': f'✅ Migration successful with autocommit! Created tags table with {tag_count} tags.',
                'tag_count': tag_count,
                'method': 'autocommit'
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'method': 'autocommit'}


class TransactionMigrationStrategy(MigrationStrategyInterface):
    """Single Responsibility - handles explicit transaction DDL operations"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def execute(self) -> Dict[str, Any]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('BEGIN')
                
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = 'tags'
                    )
                """)
                table_exists = cursor.fetchone()[0]
                
                if not table_exists:
                    cursor.execute("""
                        CREATE TABLE public.tags (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(50) UNIQUE NOT NULL,
                            category VARCHAR(30) NOT NULL,
                            color VARCHAR(7) DEFAULT '#6750A4'
                        )
                    """)
                
                cursor.execute("""
                    INSERT INTO public.tags (name, category, color)
                    SELECT 'work', 'work', '#FF6B6B'
                    WHERE NOT EXISTS (SELECT 1 FROM public.tags WHERE name = 'work')
                """)
                
                cursor.execute('COMMIT')
                cursor.execute('SELECT COUNT(*) FROM public.tags')
                tag_count = cursor.fetchone()[0]
                
                return {
                    'success': True,
                    'message': f'✅ Migration successful with explicit transaction! Tags table has {tag_count} tags.',
                    'tag_count': tag_count,
                    'method': 'explicit_transaction',
                    'table_existed': table_exists
                }
        except Exception as e:
            return {'success': False, 'error': str(e), 'method': 'explicit_transaction'}


class ReadOnlyTestStrategy(MigrationStrategyInterface):
    """Single Responsibility - tests read-only operations when DDL fails"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def execute(self) -> Dict[str, Any]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM moods LIMIT 1')
                mood_count = cursor.fetchone()[0]
                
                return {
                    'success': False,
                    'error': 'DDL operations not supported, but DML works',
                    'message': f'❌ Cannot create tables, but can read data. Found {mood_count} moods.',
                    'mood_count': mood_count,
                    'method': 'read_only_test'
                }
        except Exception as e:
            return {'success': False, 'error': str(e), 'method': 'read_only_test'}


class MigrationExecutor:
    """Open/Closed Principle - can add new strategies without modification"""
    
    def __init__(self, strategies: list[MigrationStrategyInterface]):
        self.strategies = strategies
    
    def execute_with_fallback(self) -> Dict[str, Any]:
        """Dependency Inversion - depends on abstractions, not concretions"""
        errors = {}
        
        for strategy in self.strategies:
            result = strategy.execute()
            if result.get('success'):
                return result
            errors[result.get('method', 'unknown')] = result.get('error')
        
        return {
            'success': False,
            'error': 'All migration strategies failed',
            'message': '❌ Complete migration failure',
            'method': 'all_failed',
            'errors': errors
        }
