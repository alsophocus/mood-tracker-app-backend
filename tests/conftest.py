import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from app import create_app
from database import Database
from auth import User

@pytest.fixture
def app():
    """Create test app with in-memory database"""
    # Mock database URL for testing
    test_db_url = "postgresql://test:test@localhost:5432/test_db"
    
    with patch.dict(os.environ, {
        'DATABASE_URL': test_db_url,
        'SECRET_KEY': 'test-secret-key',
        'GOOGLE_CLIENT_ID': 'test-google-id',
        'GOOGLE_CLIENT_SECRET': 'test-google-secret',
        'FLASK_DEBUG': 'true'
    }):
        app = create_app()
        app.config['TESTING'] = True
        yield app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def mock_db():
    """Mock database for testing"""
    with patch('database.db') as mock:
        mock.get_connection = MagicMock()
        mock.initialize = MagicMock()
        mock.create_user = MagicMock()
        mock.get_user = MagicMock()
        mock.save_mood = MagicMock()
        mock.get_user_moods = MagicMock()
        yield mock

@pytest.fixture
def test_user():
    """Create test user"""
    return User(1, 'test@example.com', 'Test User', 'google')

@pytest.fixture
def authenticated_client(client, test_user):
    """Client with authenticated user"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
    return client

@pytest.fixture
def sample_moods():
    """Sample mood data"""
    from datetime import datetime, timedelta
    base_date = datetime.now().date()
    return [
        {
            'id': i,
            'user_id': 1,
            'date': base_date - timedelta(days=i),
            'mood': mood,
            'notes': f'Note {i}',
            'timestamp': datetime.now()
        }
        for i, mood in enumerate(['very well', 'well', 'neutral', 'bad', 'very bad'])
    ]
