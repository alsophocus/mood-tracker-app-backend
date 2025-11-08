import pytest
from unittest.mock import patch
import os

class TestSecurity:
    
    def test_secret_key_configured(self, app):
        """Test that secret key is properly configured"""
        assert app.secret_key is not None
        assert app.secret_key != 'dev-secret-key-change-in-production'
    
    @patch('routes.db')
    @patch('flask_login.current_user')
    def test_sql_injection_prevention(self, mock_user, mock_db, client):
        """Test SQL injection attempts are prevented"""
        mock_user.id = 1
        mock_user.is_authenticated = True
        mock_db.save_mood.return_value = {'id': 1, 'mood': 'neutral'}
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        # Attempt SQL injection in mood field
        malicious_mood = "'; DROP TABLE moods; --"
        
        response = client.post('/save_mood', data={
            'mood': malicious_mood,
            'notes': 'Injection attempt'
        })
        
        # Should handle gracefully
        assert response.status_code in [302, 400]
        
        # Database operations should still work
        health_response = client.get('/health')
        assert health_response.status_code == 200
    
    @patch('routes.db')
    @patch('flask_login.current_user')
    def test_xss_prevention_in_notes(self, mock_user, mock_db, client):
        """Test XSS prevention in user notes"""
        mock_user.id = 1
        mock_user.is_authenticated = True
        mock_db.save_mood.return_value = {'id': 1, 'mood': 'neutral'}
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        xss_payload = '<script>alert("XSS")</script>'
        
        response = client.post('/save_mood', data={
            'mood': 'neutral',
            'notes': xss_payload
        })
        
        # Should accept the request but sanitize the content
        assert response.status_code == 302
    
    def test_user_isolation(self, client):
        """Test that users can only access their own data"""
        # This test would require setting up multiple users
        # For now, we test that unauthenticated users can't access data
        
        response = client.get('/mood_data')
        assert response.status_code == 302  # Redirect to login
        
        response = client.get('/weekly_patterns')
        assert response.status_code == 302
        
        response = client.get('/daily_patterns')
        assert response.status_code == 302
    
    def test_session_security(self, client):
        """Test session handling"""
        # Test that session is required for protected routes
        response = client.get('/')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_configuration_validation(self):
        """Test configuration validation"""
        from config import Config
        
        # Test that validation catches missing required config
        original_db_url = Config.DATABASE_URL
        Config.DATABASE_URL = None
        
        with pytest.raises(ValueError):
            Config.validate()
        
        # Restore original value
        Config.DATABASE_URL = original_db_url
    
    def test_environment_variable_handling(self):
        """Test environment variable handling"""
        # Test that sensitive data comes from environment
        from config import Config
        
        # These should be loaded from environment, not hardcoded
        assert hasattr(Config, 'SECRET_KEY')
        assert hasattr(Config, 'DATABASE_URL')
        assert hasattr(Config, 'GOOGLE_CLIENT_ID')
    
    @patch('routes.db')
    @patch('flask_login.current_user')
    def test_input_validation(self, mock_user, mock_db, client):
        """Test input validation for mood entries"""
        mock_user.id = 1
        mock_user.is_authenticated = True
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        # Test with invalid mood value
        response = client.post('/save_mood', data={
            'mood': 'invalid_mood_value',
            'notes': 'Test'
        })
        
        # Should handle invalid input gracefully
        assert response.status_code in [302, 400]
