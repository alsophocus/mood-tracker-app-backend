import pytest
from unittest.mock import patch, MagicMock
from database import Database
from datetime import datetime

class TestDatabase:
    
    @patch('psycopg.connect')
    def test_database_initialization(self, mock_connect):
        """Test database initialization"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        db = Database()
        db.url = "postgresql://test:test@localhost:5432/test"
        db.initialize()
        
        # Verify tables are created
        assert mock_cursor.execute.call_count >= 2  # Users and moods tables
        mock_conn.commit.assert_called()
    
    @patch('psycopg.connect')
    def test_create_user_new(self, mock_connect):
        """Test creating new user"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Mock no existing user
        mock_cursor.fetchone.side_effect = [None, {'id': 1, 'email': 'test@example.com', 'name': 'Test', 'provider': 'google'}]
        
        db = Database()
        db.url = "postgresql://test:test@localhost:5432/test"
        
        user = db.create_user('test@example.com', 'Test', 'google')
        
        assert user['email'] == 'test@example.com'
        mock_cursor.execute.assert_called()
    
    @patch('psycopg.connect')
    def test_create_user_existing(self, mock_connect):
        """Test getting existing user"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_conn
        mock_connect.return_value = mock_conn
        
        # Mock existing user
        existing_user = {'id': 1, 'email': 'test@example.com', 'name': 'Test', 'provider': 'google'}
        mock_cursor.fetchone.return_value = existing_user
        
        db = Database()
        db.url = "postgresql://test:test@localhost:5432/test"
        
        user = db.create_user('test@example.com', 'Test', 'google')
        
        assert user == existing_user
    
    @patch('psycopg.connect')
    def test_save_mood(self, mock_connect):
        """Test saving mood entry"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        mood_data = {'id': 1, 'user_id': 1, 'date': datetime.now().date(), 'mood': 'well', 'notes': 'Good day'}
        mock_cursor.fetchone.return_value = mood_data
        
        db = Database()
        db.url = "postgresql://test:test@localhost:5432/test"
        
        result = db.save_mood(1, datetime.now().date(), 'well', 'Good day')
        
        assert result == mood_data
        mock_cursor.execute.assert_called()
    
    @patch('psycopg.connect')
    def test_get_user_moods(self, mock_connect):
        """Test getting user moods"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        moods = [
            {'id': 1, 'user_id': 1, 'date': datetime.now().date(), 'mood': 'well', 'notes': 'Good'},
            {'id': 2, 'user_id': 1, 'date': datetime.now().date(), 'mood': 'neutral', 'notes': 'OK'}
        ]
        mock_cursor.fetchall.return_value = moods
        
        db = Database()
        db.url = "postgresql://test:test@localhost:5432/test"
        
        result = db.get_user_moods(1)
        
        assert result == moods
        mock_cursor.execute.assert_called_with('SELECT * FROM moods WHERE user_id = %s ORDER BY date DESC', (1,))
