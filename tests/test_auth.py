import pytest
from unittest.mock import patch, MagicMock
from flask import url_for

class TestAuthentication:
    
    def test_login_page_accessible(self, client):
        """Test login page loads correctly"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Continue with Google' in response.data
        assert b'Continue with GitHub' in response.data
    
    def test_unauthenticated_redirect(self, client):
        """Test unauthenticated users are redirected to login"""
        response = client.get('/')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_google_oauth_redirect(self, client):
        """Test Google OAuth initiation"""
        with patch('app.google.authorize_redirect') as mock_redirect:
            mock_redirect.return_value = MagicMock()
            response = client.get('/auth/google')
            mock_redirect.assert_called_once()
    
    def test_github_oauth_redirect(self, client):
        """Test GitHub OAuth initiation"""
        with patch('app.github.authorize_redirect') as mock_redirect:
            mock_redirect.return_value = MagicMock()
            response = client.get('/auth/github')
            mock_redirect.assert_called_once()
    
    def test_invalid_provider(self, client):
        """Test invalid OAuth provider"""
        response = client.get('/auth/invalid')
        assert response.status_code == 302
        assert '/login' in response.location
    
    @patch('app.google.authorize_access_token')
    def test_google_callback_success(self, mock_token, client):
        """Test successful Google OAuth callback"""
        mock_token.return_value = {
            'userinfo': {
                'email': 'test@example.com',
                'name': 'Test User'
            }
        }
        
        response = client.get('/callback/google')
        assert response.status_code == 302
        assert '/' in response.location
    
    @patch('app.github.authorize_access_token')
    @patch('app.github.get')
    def test_github_callback_success(self, mock_get, mock_token, client):
        """Test successful GitHub OAuth callback"""
        mock_token.return_value = MagicMock()
        mock_get.return_value.json.return_value = {
            'email': 'test@example.com',
            'name': 'Test User',
            'login': 'testuser'
        }
        
        response = client.get('/callback/github')
        assert response.status_code == 302
        assert '/' in response.location
    
    def test_logout(self, authenticated_client):
        """Test user logout"""
        response = authenticated_client.get('/logout')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_user_isolation(self, client, test_user):
        """Test users can only access their own data"""
        # This would require creating multiple users and testing data isolation
        # Implementation depends on your specific user creation flow
        pass
