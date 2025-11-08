import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

class TestRoutes:
    
    def test_index_unauthenticated(self, client):
        """Test index redirects unauthenticated users"""
        response = client.get('/')
        assert response.status_code == 302
        assert '/login' in response.location
    
    @patch('routes.db')
    @patch('flask_login.current_user')
    def test_index_authenticated(self, mock_user, mock_db, client):
        """Test index page for authenticated users"""
        mock_user.id = 1
        mock_user.is_authenticated = True
        mock_db.get_user_moods.return_value = []
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        response = client.get('/')
        assert response.status_code == 200
    
    @patch('routes.db')
    @patch('flask_login.current_user')
    def test_save_mood_success(self, mock_user, mock_db, client):
        """Test successful mood saving"""
        mock_user.id = 1
        mock_user.is_authenticated = True
        mock_db.save_mood.return_value = {'id': 1, 'mood': 'well'}
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        response = client.post('/save_mood', data={
            'mood': 'well',
            'notes': 'Good day'
        })
        
        assert response.status_code == 302
        mock_db.save_mood.assert_called_once()
    
    @patch('flask_login.current_user')
    def test_save_mood_no_mood(self, mock_user, client):
        """Test mood saving without mood selection"""
        mock_user.id = 1
        mock_user.is_authenticated = True
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        response = client.post('/save_mood', data={'notes': 'No mood selected'})
        
        assert response.status_code == 302
    
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
    
    def test_health_check(self, client):
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
    
    @patch('routes.db')
    @patch('flask_login.current_user')
    def test_export_pdf(self, mock_user, mock_db, client, sample_moods):
        """Test PDF export functionality"""
        mock_user.id = 1
        mock_user.name = 'Test User'
        mock_user.is_authenticated = True
        mock_db.get_user_moods.return_value = sample_moods
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        with patch('routes.PDFExporter') as mock_exporter:
            mock_buffer = MagicMock()
            mock_exporter.return_value.generate_report.return_value = mock_buffer
            
            response = client.get('/export_pdf')
            assert response.status_code == 200
            assert response.mimetype == 'application/pdf'
