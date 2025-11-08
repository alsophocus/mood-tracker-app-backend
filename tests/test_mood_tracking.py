import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

class TestMoodTracking:
    
    @patch('routes.db')
    @patch('flask_login.current_user')
    def test_save_mood_valid(self, mock_user, mock_db, client):
        """Test saving a valid mood entry"""
        mock_user.id = 1
        mock_user.is_authenticated = True
        mock_db.save_mood.return_value = {'id': 1, 'mood': 'well', 'notes': 'Good day'}
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        response = client.post('/save_mood', data={
            'mood': 'well',
            'notes': 'Good day'
        })
        
        assert response.status_code == 302
        mock_db.save_mood.assert_called_once_with(1, datetime.now().date(), 'well', 'Good day')
    
    @patch('routes.db')
    @patch('flask_login.current_user')
    def test_save_mood_all_levels(self, mock_user, mock_db, client):
        """Test saving all mood levels"""
        mock_user.id = 1
        mock_user.is_authenticated = True
        
        mood_levels = ['very bad', 'bad', 'slightly bad', 'neutral', 'slightly well', 'well', 'very well']
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        for mood in mood_levels:
            mock_db.save_mood.return_value = {'id': 1, 'mood': mood}
            
            response = client.post('/save_mood', data={'mood': mood})
            assert response.status_code == 302
    
    @patch('routes.db')
    @patch('flask_login.current_user')
    def test_save_mood_with_notes(self, mock_user, mock_db, client):
        """Test saving mood with notes"""
        mock_user.id = 1
        mock_user.is_authenticated = True
        mock_db.save_mood.return_value = {'id': 1, 'mood': 'well', 'notes': 'Had a great meeting today!'}
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        response = client.post('/save_mood', data={
            'mood': 'well',
            'notes': 'Had a great meeting today!'
        })
        
        assert response.status_code == 302
        mock_db.save_mood.assert_called_once_with(1, datetime.now().date(), 'well', 'Had a great meeting today!')
    
    @patch('flask_login.current_user')
    def test_save_mood_empty_mood(self, mock_user, client):
        """Test saving with empty mood selection"""
        mock_user.id = 1
        mock_user.is_authenticated = True
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        response = client.post('/save_mood', data={'notes': 'Just notes, no mood'})
        assert response.status_code == 302
    
    @patch('routes.db')
    @patch('flask_login.current_user')
    def test_mood_update_same_day(self, mock_user, mock_db, client):
        """Test updating mood on the same day"""
        mock_user.id = 1
        mock_user.is_authenticated = True
        
        # First mood entry
        mock_db.save_mood.return_value = {'id': 1, 'mood': 'neutral'}
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        response1 = client.post('/save_mood', data={'mood': 'neutral'})
        assert response1.status_code == 302
        
        # Update mood same day
        mock_db.save_mood.return_value = {'id': 1, 'mood': 'well'}
        
        response2 = client.post('/save_mood', data={'mood': 'well'})
        assert response2.status_code == 302
        
        # Should be called twice
        assert mock_db.save_mood.call_count == 2
