"""
Analytics service following Service Layer Pattern and SOLID principles.
"""
from typing import Dict, Any, List
from datetime import date, timedelta, datetime
from collections import defaultdict
from shared.models import MoodType


class AnalyticsService:
    """Analytics service for mood data analysis."""

    def __init__(self, mood_repository):
        self.mood_repository = mood_repository

    def get_mood_distribution(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get mood distribution for last N days."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        moods = self.mood_repository.find_by_user_and_date_range(user_id, start_date, end_date)
        
        distribution = defaultdict(int)
        for mood in moods:
            distribution[mood.mood] += 1
        
        return {
            'distribution': dict(distribution),
            'total': len(moods),
            'period_days': days
        }

    def get_average_mood(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Calculate average mood for last N days."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        moods = self.mood_repository.find_by_user_and_date_range(user_id, start_date, end_date)
        
        if not moods:
            return {'average': None, 'count': 0}
        
        total_value = sum(MoodType.get_value(m.mood) for m in moods)
        average = total_value / len(moods)
        
        return {
            'average': round(average, 2),
            'count': len(moods),
            'period_days': days
        }

    def get_trends(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Analyze mood trends over time."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        moods = self.mood_repository.find_by_user_and_date_range(user_id, start_date, end_date)
        
        if len(moods) < 2:
            return {'trend': 'insufficient_data', 'slope': 0}
        
        # Calculate linear regression
        mood_values = [(i, MoodType.get_value(m.mood)) for i, m in enumerate(moods)]
        
        n = len(mood_values)
        x_values = [i for i, _ in mood_values]
        y_values = [v for _, v in mood_values]
        
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in mood_values)
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        slope = numerator / denominator if denominator != 0 else 0
        
        trend = 'improving' if slope > 0.05 else 'declining' if slope < -0.05 else 'stable'
        
        return {
            'trend': trend,
            'slope': round(slope, 4),
            'period_days': days
        }

    def get_hourly_patterns(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Analyze mood patterns by hour of day."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        moods = self.mood_repository.find_by_user_and_date_range(user_id, start_date, end_date)
        
        hourly_data = defaultdict(list)
        for mood in moods:
            hour = mood.hour
            hourly_data[hour].append(MoodType.get_value(mood.mood))
        
        hourly_averages = {}
        for hour, values in hourly_data.items():
            hourly_averages[hour] = round(sum(values) / len(values), 2)
        
        return {
            'hourly_averages': hourly_averages,
            'period_days': days
        }

    def get_quick_stats(self, user_id: int) -> Dict[str, Any]:
        """Get quick statistics overview."""
        today_moods = self.mood_repository.find_by_user_and_date(user_id, date.today())
        week_avg = self.get_average_mood(user_id, days=7)
        month_avg = self.get_average_mood(user_id, days=30)
        total_count = self.mood_repository.count_by_user(user_id)
        
        return {
            'today_count': len(today_moods),
            'week_average': week_avg.get('average'),
            'month_average': month_avg.get('average'),
            'total_entries': total_count
        }

    def get_week_comparison(self, user_id: int) -> Dict[str, Any]:
        """Compare current week vs previous week."""
        today = date.today()
        
        # Current week
        current_week_start = today - timedelta(days=today.weekday())
        current_week_end = today
        
        # Previous week
        prev_week_start = current_week_start - timedelta(days=7)
        prev_week_end = current_week_start - timedelta(days=1)
        
        current_moods = self.mood_repository.find_by_user_and_date_range(
            user_id, current_week_start, current_week_end
        )
        prev_moods = self.mood_repository.find_by_user_and_date_range(
            user_id, prev_week_start, prev_week_end
        )
        
        current_avg = sum(MoodType.get_value(m.mood) for m in current_moods) / len(current_moods) if current_moods else 0
        prev_avg = sum(MoodType.get_value(m.mood) for m in prev_moods) / len(prev_moods) if prev_moods else 0
        
        return {
            'current_week': {
                'average': round(current_avg, 2),
                'count': len(current_moods)
            },
            'previous_week': {
                'average': round(prev_avg, 2),
                'count': len(prev_moods)
            },
            'change': round(current_avg - prev_avg, 2) if current_moods and prev_moods else 0
        }
