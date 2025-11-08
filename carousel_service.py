"""
SOLID-compliant carousel service implementation
Single Responsibility Principle - handles only carousel data logic
"""

from carousel_interfaces import CarouselDataInterface
from database import Database
from typing import List, Dict, Any


class CarouselDataService(CarouselDataInterface):
    """Single Responsibility - manages carousel data only"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_recent_moods(self, user_id: int, limit: int = 15) -> List[Dict[str, Any]]:
        """Get recent mood entries formatted for carousel"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT mood, date, timestamp, notes, triggers
                    FROM moods 
                    WHERE user_id = %s 
                    ORDER BY date DESC, timestamp DESC 
                    LIMIT %s
                """, (user_id, limit))
                
                moods = cursor.fetchall()
                return [self._format_mood_for_carousel(mood) for mood in moods]
        except Exception as e:
            print(f"Error fetching carousel moods: {e}")
            return []
    
    def _format_mood_for_carousel(self, mood: Dict[str, Any]) -> Dict[str, Any]:
        """Format mood data for carousel display"""
        mood_colors = {
            'very bad': '#D32F2F', 'bad': '#F57C00', 'slightly bad': '#FBC02D',
            'neutral': '#757575', 'slightly well': '#689F38', 'well': '#388E3C', 'very well': '#1976D2'
        }
        
        mood_icons = {
            'very bad': 'sentiment_very_dissatisfied', 
            'bad': 'sentiment_dissatisfied', 
            'slightly bad': 'sentiment_neutral',
            'neutral': 'sentiment_neutral', 
            'slightly well': 'sentiment_satisfied', 
            'well': 'sentiment_very_satisfied', 
            'very well': 'sentiment_very_satisfied'
        }
        
        return {
            'mood': mood['mood'],
            'icon': mood_icons.get(mood['mood'], 'sentiment_neutral'),
            'color': mood_colors.get(mood['mood'], '#757575'),
            'date': mood['date'].strftime('%b %d') if mood['date'] else '',
            'time': mood['timestamp'].strftime('%H:%M') if mood['timestamp'] else '',
            'notes': (mood['notes'][:50] + '...') if mood['notes'] and len(mood['notes']) > 50 else mood['notes'] or '',
            'triggers': mood['triggers'] or ''
        }
