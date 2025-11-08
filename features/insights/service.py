"""
Insights service following Service Layer Pattern and SOLID principles.
"""
from typing import Dict, Any, List
from datetime import date, timedelta
from collections import defaultdict
from shared.models import MoodType


class InsightsService:
    """Insights service for generating mood insights and recommendations."""

    def __init__(self, mood_repository, tag_repository):
        self.mood_repository = mood_repository
        self.tag_repository = tag_repository

    def generate_insights(self, user_id: int) -> List[Dict[str, Any]]:
        """Generate personalized insights for user."""
        insights = []
        
        # Get recent moods
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        moods = self.mood_repository.find_by_user_and_date_range(user_id, start_date, end_date)
        
        if not moods:
            return [{
                'type': 'welcome',
                'message': 'Start tracking your mood to receive personalized insights!',
                'priority': 'high'
            }]
        
        # Consistency insight
        if len(moods) >= 20:
            insights.append({
                'type': 'consistency',
                'message': f'Great job! You\'ve logged {len(moods)} moods in the last 30 days.',
                'priority': 'medium'
            })
        
        # Average mood insight
        avg_value = sum(MoodType.get_value(m.mood) for m in moods) / len(moods)
        if avg_value >= 5.5:
            insights.append({
                'type': 'positive',
                'message': 'Your average mood has been quite positive lately!',
                'priority': 'high'
            })
        elif avg_value < 3.5:
            insights.append({
                'type': 'support',
                'message': 'Your mood has been lower lately. Consider reaching out to someone you trust.',
                'priority': 'high'
            })
        
        # Streak insight
        recent_moods = self.mood_repository.find_by_user(user_id, limit=7)
        if len(recent_moods) >= 7:
            insights.append({
                'type': 'streak',
                'message': 'You\'re on a 7-day tracking streak! Keep it up!',
                'priority': 'medium'
            })
        
        # Time-based pattern
        hourly_data = defaultdict(list)
        for mood in moods:
            hourly_data[mood.hour].append(MoodType.get_value(mood.mood))
        
        if hourly_data:
            best_hours = sorted(hourly_data.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True)[:3]
            if best_hours:
                best_hour = best_hours[0][0]
                insights.append({
                    'type': 'pattern',
                    'message': f'Your mood tends to be better around {best_hour}:00.',
                    'priority': 'low'
                })
        
        return insights

    def get_tag_correlations(self, user_id: int) -> List[Dict[str, Any]]:
        """Analyze correlation between tags and mood."""
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        moods = self.mood_repository.find_by_user_and_date_range(user_id, start_date, end_date)
        
        tag_moods = defaultdict(list)
        
        for mood in moods:
            tags = self.tag_repository.get_mood_tags(mood.id)
            for tag in tags:
                tag_moods[tag.name].append(MoodType.get_value(mood.mood))
        
        correlations = []
        for tag_name, mood_values in tag_moods.items():
            if len(mood_values) >= 3:
                avg = sum(mood_values) / len(mood_values)
                correlations.append({
                    'tag': tag_name,
                    'average_mood': round(avg, 2),
                    'count': len(mood_values)
                })
        
        return sorted(correlations, key=lambda x: x['average_mood'], reverse=True)
