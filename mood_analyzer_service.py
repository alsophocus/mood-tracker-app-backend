"""
SOLID-compliant mood analyzer service
Single Responsibility Principle - handles only mood analysis
"""

from insights_interfaces import MoodAnalyzerInterface
from database import Database
from typing import Dict, List, Any
from datetime import date, timedelta
import statistics


class MoodAnalyzer(MoodAnalyzerInterface):
    """Single Responsibility - analyzes mood patterns and correlations"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def analyze_mood_patterns(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Analyze mood patterns over specified period"""
        try:
            if not user_id:
                return {'success': False, 'error': 'Invalid user_id'}
                
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get mood data for the period
                start_date = date.today() - timedelta(days=days)
                cursor.execute("""
                    SELECT mood, date, context_location, context_activity, context_weather
                    FROM moods 
                    WHERE user_id = %s AND date >= %s
                    ORDER BY date DESC
                """, (user_id, start_date))
                
                moods = cursor.fetchall()
                
                if not moods:
                    return {
                        'success': True,
                        'period_days': days,
                        'total_entries': 0,
                        'average_mood': 0,
                        'mood_stability': 0,
                        'day_patterns': {},
                        'location_patterns': {},
                        'activity_patterns': {},
                        'message': 'No mood data found for analysis'
                    }
                
                # Convert mood strings to numeric values
                mood_values = [self._mood_to_numeric(mood['mood']) for mood in moods]
                
                # Calculate statistics
                avg_mood = round(statistics.mean(mood_values), 2)
                mood_variance = round(statistics.variance(mood_values) if len(mood_values) > 1 else 0, 2)
                
                # Analyze patterns by day of week
                day_patterns = self._analyze_day_patterns(moods)
                
                # Analyze location patterns
                location_patterns = self._analyze_location_patterns(moods)
                
                # Analyze activity patterns
                activity_patterns = self._analyze_activity_patterns(moods)
                
                return {
                    'success': True,
                    'period_days': days,
                    'total_entries': len(moods),
                    'average_mood': avg_mood,
                    'mood_stability': round(10 - mood_variance, 2),  # Higher = more stable
                    'day_patterns': day_patterns,
                    'location_patterns': location_patterns,
                    'activity_patterns': activity_patterns
                }
                
        except Exception as e:
            import traceback
            return {
                'success': False, 
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def get_trigger_correlations(self, user_id: int) -> List[Dict[str, Any]]:
        """Get correlations between triggers and mood levels"""
        try:
            if not user_id:
                return []
                
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get mood data with tags
                cursor.execute("""
                    SELECT m.mood, t.name as tag_name, t.category
                    FROM moods m
                    JOIN mood_tags mt ON m.id = mt.mood_id
                    JOIN tags t ON mt.tag_id = t.id
                    WHERE m.user_id = %s
                """, (user_id,))
                
                mood_tags = cursor.fetchall()
                
                if not mood_tags:
                    return []
                
                # Calculate correlations
                correlations = {}
                for entry in mood_tags:
                    tag = entry['tag_name']
                    mood_value = self._mood_to_numeric(entry['mood'])
                    category = entry['category']
                    
                    if tag not in correlations:
                        correlations[tag] = {
                            'tag': tag,
                            'category': category,
                            'mood_values': [],
                            'count': 0
                        }
                    
                    correlations[tag]['mood_values'].append(mood_value)
                    correlations[tag]['count'] += 1
                
                # Calculate average impact for each tag
                result = []
                for tag_data in correlations.values():
                    if tag_data['count'] >= 1:  # Need at least 1 data point
                        avg_mood = statistics.mean(tag_data['mood_values'])
                        result.append({
                            'tag': tag_data['tag'],
                            'category': tag_data['category'],
                            'average_mood': round(avg_mood, 2),
                            'frequency': tag_data['count'],
                            'impact': self._calculate_impact(avg_mood)
                        })
                
                # Sort by frequency and impact
                result.sort(key=lambda x: (x['frequency'], x['average_mood']), reverse=True)
                return result
                
        except Exception as e:
            import traceback
            print(f"Correlation error: {str(e)}")
            print(traceback.format_exc())
            return []
    
    def _mood_to_numeric(self, mood: str) -> float:
        """Convert mood string to numeric value"""
        mood_map = {
            'very bad': 1.0,
            'bad': 2.0,
            'slightly bad': 3.0,
            'neutral': 4.0,
            'slightly well': 5.0,
            'well': 6.0,
            'very well': 7.0
        }
        return mood_map.get(mood.lower(), 4.0)
    
    def _analyze_day_patterns(self, moods: List[Dict]) -> Dict[str, float]:
        """Analyze mood patterns by day of week"""
        from datetime import datetime
        
        day_moods = {}
        for mood_entry in moods:
            day_name = datetime.strptime(str(mood_entry['date']), '%Y-%m-%d').strftime('%A')
            mood_value = self._mood_to_numeric(mood_entry['mood'])
            
            if day_name not in day_moods:
                day_moods[day_name] = []
            day_moods[day_name].append(mood_value)
        
        # Calculate averages
        return {day: round(statistics.mean(values), 2) 
                for day, values in day_moods.items() if values}
    
    def _analyze_location_patterns(self, moods: List[Dict]) -> Dict[str, float]:
        """Analyze mood patterns by location"""
        location_moods = {}
        for mood_entry in moods:
            location = mood_entry.get('context_location')
            if location and location.strip():
                mood_value = self._mood_to_numeric(mood_entry['mood'])
                
                if location not in location_moods:
                    location_moods[location] = []
                location_moods[location].append(mood_value)
        
        return {loc: round(statistics.mean(values), 2) 
                for loc, values in location_moods.items() if len(values) >= 2}
    
    def _analyze_activity_patterns(self, moods: List[Dict]) -> Dict[str, float]:
        """Analyze mood patterns by activity"""
        activity_moods = {}
        for mood_entry in moods:
            activity = mood_entry.get('context_activity')
            if activity and activity.strip():
                mood_value = self._mood_to_numeric(mood_entry['mood'])
                
                if activity not in activity_moods:
                    activity_moods[activity] = []
                activity_moods[activity].append(mood_value)
        
        return {act: round(statistics.mean(values), 2) 
                for act, values in activity_moods.items() if len(values) >= 2}
    
    def _calculate_impact(self, avg_mood: float) -> str:
        """Calculate impact description based on average mood"""
        if avg_mood >= 5.5:
            return 'Positive'
        elif avg_mood <= 3.5:
            return 'Negative'
        else:
            return 'Neutral'
