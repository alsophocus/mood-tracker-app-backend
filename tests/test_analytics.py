import pytest
from datetime import datetime, timedelta
from analytics import MoodAnalytics

class TestMoodAnalytics:
    
    def test_calculate_streak_good_moods(self, sample_moods):
        """Test streak calculation with good moods"""
        # Modify sample moods to have recent good moods
        good_moods = []
        base_date = datetime.now().date()
        for i in range(3):
            good_moods.append({
                'date': base_date - timedelta(days=i),
                'mood': 'well',  # mood value 6 (>= 5)
                'notes': f'Good day {i}'
            })
        
        analytics = MoodAnalytics(good_moods)
        streak = analytics.calculate_streak()
        
        assert streak == 3
    
    def test_calculate_streak_mixed_moods(self):
        """Test streak calculation with mixed moods"""
        base_date = datetime.now().date()
        mixed_moods = [
            {'date': base_date, 'mood': 'well', 'notes': ''},  # Good
            {'date': base_date - timedelta(days=1), 'mood': 'slightly well', 'notes': ''},  # Good
            {'date': base_date - timedelta(days=2), 'mood': 'bad', 'notes': ''},  # Bad - breaks streak
            {'date': base_date - timedelta(days=3), 'mood': 'well', 'notes': ''}  # Good but after break
        ]
        
        analytics = MoodAnalytics(mixed_moods)
        streak = analytics.calculate_streak()
        
        assert streak == 2  # Only the first 2 consecutive good moods
    
    def test_calculate_averages(self, sample_moods):
        """Test mood averages calculation"""
        analytics = MoodAnalytics(sample_moods)
        averages = analytics.calculate_averages()
        
        assert 'daily' in averages
        assert 'good_days' in averages
        assert 'bad_days' in averages
        assert 'total_entries' in averages
        assert averages['total_entries'] == len(sample_moods)
    
    def test_get_weekly_patterns(self, sample_moods):
        """Test weekly patterns calculation"""
        analytics = MoodAnalytics(sample_moods)
        patterns = analytics.get_weekly_patterns()
        
        assert 'labels' in patterns
        assert 'data' in patterns
        assert len(patterns['labels']) == 7  # 7 days of week
        assert len(patterns['data']) == 7
        
        # Check all days are present
        expected_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        assert patterns['labels'] == expected_days
    
    def test_get_monthly_trends(self, sample_moods):
        """Test monthly trends calculation"""
        analytics = MoodAnalytics(sample_moods)
        trends = analytics.get_monthly_trends()
        
        assert isinstance(trends, list)
        if trends:  # If there's data
            assert 'month' in trends[0]
            assert 'mood' in trends[0]
    
    def test_get_summary(self, sample_moods):
        """Test complete analytics summary"""
        analytics = MoodAnalytics(sample_moods)
        summary = analytics.get_summary()
        
        required_keys = [
            'current_streak', 'daily_average', 'good_days_average',
            'bad_days_average', 'total_entries', 'best_day', 'weekly_patterns'
        ]
        
        for key in required_keys:
            assert key in summary
    
    def test_empty_moods(self):
        """Test analytics with no mood data"""
        analytics = MoodAnalytics([])
        
        averages = analytics.calculate_averages()
        assert averages['daily'] == 0
        assert averages['total_entries'] == 0
        
        streak = analytics.calculate_streak()
        assert streak == 0
        
        summary = analytics.get_summary()
        assert summary['current_streak'] == 0
        assert summary['total_entries'] == 0
