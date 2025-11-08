"""
SOLID-compliant insight generator service
Single Responsibility Principle - generates insights from analyzed data
"""

from insights_interfaces import InsightGeneratorInterface, MoodAnalyzerInterface
from typing import Dict, List, Any
from datetime import date, timedelta


class InsightGenerator(InsightGeneratorInterface):
    """Single Responsibility - generates actionable insights"""
    
    def __init__(self, mood_analyzer: MoodAnalyzerInterface):
        # Dependency Inversion - depends on abstraction
        self.mood_analyzer = mood_analyzer
    
    def generate_insights(self, user_id: int) -> List[Dict[str, Any]]:
        """Generate actionable insights for user"""
        insights = []
        
        # Get mood patterns
        patterns = self.mood_analyzer.analyze_mood_patterns(user_id, days=30)
        if not patterns.get('success'):
            return [{'type': 'error', 'message': 'Unable to generate insights - no mood data available'}]
        
        # Get trigger correlations
        correlations = self.mood_analyzer.get_trigger_correlations(user_id)
        
        # Generate insights based on patterns
        insights.extend(self._generate_mood_stability_insights(patterns))
        insights.extend(self._generate_day_pattern_insights(patterns))
        insights.extend(self._generate_trigger_insights(correlations))
        insights.extend(self._generate_location_insights(patterns))
        insights.extend(self._generate_activity_insights(patterns))
        
        return insights[:10]  # Limit to top 10 insights
    
    def get_mood_trends(self, user_id: int, period: str = 'month') -> Dict[str, Any]:
        """Get mood trends for specified period"""
        days_map = {'week': 7, 'month': 30, 'quarter': 90}
        days = days_map.get(period, 30)
        
        patterns = self.mood_analyzer.analyze_mood_patterns(user_id, days)
        if not patterns.get('success'):
            return {'success': False, 'error': 'Unable to get trends'}
        
        # Calculate trend direction
        trend_direction = self._calculate_trend_direction(user_id, days)
        
        return {
            'success': True,
            'period': period,
            'average_mood': patterns['average_mood'],
            'stability': patterns['mood_stability'],
            'trend_direction': trend_direction,
            'total_entries': patterns['total_entries'],
            'insights_count': len(self.generate_insights(user_id))
        }
    
    def _generate_mood_stability_insights(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights about mood stability"""
        insights = []
        stability = patterns.get('mood_stability', 0)
        
        if stability >= 8:
            insights.append({
                'type': 'positive',
                'category': 'stability',
                'title': 'Great Mood Stability! 🎯',
                'message': f'Your mood has been very consistent (stability: {stability}/10). Keep up the great routine!',
                'priority': 'high'
            })
        elif stability <= 4:
            insights.append({
                'type': 'suggestion',
                'category': 'stability',
                'title': 'Mood Fluctuations Detected 📊',
                'message': f'Your mood varies quite a bit (stability: {stability}/10). Consider tracking triggers more consistently.',
                'priority': 'medium'
            })
        
        return insights
    
    def _generate_day_pattern_insights(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights about day-of-week patterns"""
        insights = []
        day_patterns = patterns.get('day_patterns', {})
        
        if not day_patterns:
            return insights
        
        # Find best and worst days
        best_day = max(day_patterns.items(), key=lambda x: x[1])
        worst_day = min(day_patterns.items(), key=lambda x: x[1])
        
        if best_day[1] - worst_day[1] >= 1.5:  # Significant difference
            insights.append({
                'type': 'pattern',
                'category': 'weekly',
                'title': f'{best_day[0]}s are your best days! ✨',
                'message': f'You feel {best_day[1]:.1f}/7 on {best_day[0]}s vs {worst_day[1]:.1f}/7 on {worst_day[0]}s.',
                'priority': 'medium'
            })
        
        return insights
    
    def _generate_trigger_insights(self, correlations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate insights about trigger correlations"""
        insights = []
        
        if not correlations:
            return insights
        
        # Find most positive and negative triggers
        positive_triggers = [t for t in correlations if t.get('impact') == 'Positive']
        negative_triggers = [t for t in correlations if t.get('impact') == 'Negative']
        
        if positive_triggers:
            top_positive = positive_triggers[0]
            insights.append({
                'type': 'positive',
                'category': 'triggers',
                'title': f'{top_positive["tag"].title()} boosts your mood! 🚀',
                'message': f'When you engage with {top_positive["tag"]}, your average mood is {top_positive["average_mood"]:.1f}/7.',
                'priority': 'high'
            })
        
        if negative_triggers:
            top_negative = negative_triggers[0]
            insights.append({
                'type': 'warning',
                'category': 'triggers',
                'title': f'Watch out for {top_negative["tag"]} ⚠️',
                'message': f'{top_negative["tag"].title()} tends to lower your mood to {top_negative["average_mood"]:.1f}/7.',
                'priority': 'high'
            })
        
        return insights
    
    def _generate_location_insights(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights about location patterns"""
        insights = []
        location_patterns = patterns.get('location_patterns', {})
        
        if len(location_patterns) >= 2:
            best_location = max(location_patterns.items(), key=lambda x: x[1])
            insights.append({
                'type': 'suggestion',
                'category': 'location',
                'title': f'{best_location[0]} is your happy place! 🏡',
                'message': f'Your mood averages {best_location[1]:.1f}/7 when you\'re at {best_location[0]}.',
                'priority': 'low'
            })
        
        return insights
    
    def _generate_activity_insights(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights about activity patterns"""
        insights = []
        activity_patterns = patterns.get('activity_patterns', {})
        
        if len(activity_patterns) >= 2:
            best_activity = max(activity_patterns.items(), key=lambda x: x[1])
            insights.append({
                'type': 'suggestion',
                'category': 'activity',
                'title': f'{best_activity[0].title()} makes you feel great! 🎉',
                'message': f'Your mood averages {best_activity[1]:.1f}/7 during {best_activity[0]}.',
                'priority': 'medium'
            })
        
        return insights
    
    def _calculate_trend_direction(self, user_id: int, days: int) -> str:
        """Calculate if mood is trending up, down, or stable"""
        # Get recent vs older data
        recent_patterns = self.mood_analyzer.analyze_mood_patterns(user_id, days=days//2)
        older_patterns = self.mood_analyzer.analyze_mood_patterns(user_id, days=days)
        
        if not (recent_patterns.get('success') and older_patterns.get('success')):
            return 'unknown'
        
        recent_avg = recent_patterns['average_mood']
        older_avg = older_patterns['average_mood']
        
        if recent_avg > older_avg + 0.3:
            return 'improving'
        elif recent_avg < older_avg - 0.3:
            return 'declining'
        else:
            return 'stable'
