import pytest
from unittest.mock import patch, MagicMock
import json

class TestAPI:
    
    @patch('routes.db')
    @patch('flask_login.current_user')
    def test_mood_data_endpoint(self, mock_user, mock_db, client, sample_moods):
        """Test mood data API endpoint"""
        mock_user.id = 1
        mock_user.is_authenticated = True
        mock_db.get_user_moods.return_value = sample_moods
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        response = client.get('/mood_data')
        assert response.status_code == 200
        assert response.is_json
        
        data = response.get_json()
        assert isinstance(data, list)
    
    @patch('routes.db')
    @patch('flask_login.current_user')
    def test_weekly_patterns_endpoint(self, mock_user, mock_db, client, sample_moods):
        """Test weekly patterns API endpoint"""
        mock_user.id = 1
        mock_user.is_authenticated = True
        mock_db.get_user_moods.return_value = sample_moods
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        response = client.get('/weekly_patterns')
        assert response.status_code == 200
        assert response.is_json
        
        data = response.get_json()
        assert 'labels' in data
        assert 'data' in data
        assert len(data['labels']) == 7
        assert len(data['data']) == 7
    
    @patch('routes.db')
    @patch('flask_login.current_user')
    def test_daily_patterns_endpoint(self, mock_user, mock_db, client, sample_moods):
        """Test daily patterns API endpoint"""
        mock_user.id = 1
        mock_user.is_authenticated = True
        mock_db.get_user_moods.return_value = sample_moods
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        response = client.get('/daily_patterns')
        assert response.status_code == 200
        assert response.is_json
        
        data = response.get_json()
        assert 'time_data' in data
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        with patch('routes.db.get_connection') as mock_conn:
            mock_context = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {'version': 'PostgreSQL 13.0'}
            mock_context.__enter__.return_value.cursor.return_value = mock_cursor
            mock_conn.return_value = mock_context
            
            response = client.get('/health')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['status'] == 'healthy'
            assert 'database' in data
            assert 'timestamp' in data
    
    @patch('routes.db')
    @patch('flask_login.current_user')
    def test_analytics_health_endpoint(self, mock_user, mock_db, client):
        """Test analytics health endpoint"""
        mock_user.id = 1
        mock_user.is_authenticated = True
        mock_db.get_user_moods.return_value = [{'mood': 'well'}] * 5
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        response = client.get('/analytics-health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'mood_count' in data
    
    def test_unauthenticated_api_access(self, client):
        """Test API endpoints require authentication"""
        endpoints = ['/mood_data', '/weekly_patterns', '/daily_patterns', '/analytics-health']
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 302  # Redirect to login
    
    @patch('routes.db')
    @patch('flask_login.current_user')
    def test_empty_mood_data(self, mock_user, mock_db, client):
        """Test API endpoints with no mood data"""
        mock_user.id = 1
        mock_user.is_authenticated = True
        mock_db.get_user_moods.return_value = []
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        # Test mood data endpoint
        response = client.get('/mood_data')
        assert response.status_code == 200
        data = response.get_json()
        assert data == []
        
        # Test weekly patterns endpoint
        response = client.get('/weekly_patterns')
        assert response.status_code == 200
        data = response.get_json()
        assert 'labels' in data
        assert 'data' in data
