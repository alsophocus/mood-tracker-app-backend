"""
SOLID-compliant Enhanced Analytics Service
Single Responsibility: Handles advanced analytics operations
"""

class EnhancedAnalyticsService:
    def __init__(self, db_instance):
        self.db = db_instance
    
    def get_correlation_analysis(self, user_id):
        """Get correlation analysis between moods and triggers"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT m.mood, t.name as trigger_name, COUNT(*) as frequency
                    FROM moods m
                    JOIN mood_tags mt ON m.id = mt.mood_id
                    JOIN tags t ON mt.tag_id = t.id
                    WHERE m.user_id = %s
                    GROUP BY m.mood, t.name
                    ORDER BY frequency DESC
                """, (user_id,))
                
                correlations = cursor.fetchall()
                return {
                    'success': True,
                    'correlations': [dict(row) for row in correlations]
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_predictive_insights(self, user_id):
        """Get predictive insights based on patterns"""
        try:
            # Simple pattern analysis
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT mood, COUNT(*) as count,
                           EXTRACT(DOW FROM date) as day_of_week
                    FROM moods 
                    WHERE user_id = %s
                    GROUP BY mood, EXTRACT(DOW FROM date)
                    ORDER BY count DESC
                """, (user_id,))
                
                patterns = cursor.fetchall()
                return {
                    'success': True,
                    'patterns': [dict(row) for row in patterns]
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_comparative_analytics(self, user_id):
        """Get comparative analytics over time periods"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        DATE_TRUNC('week', date) as week,
                        AVG(mood::int) as avg_mood,
                        COUNT(*) as entries
                    FROM moods 
                    WHERE user_id = %s AND date >= CURRENT_DATE - INTERVAL '8 weeks'
                    GROUP BY DATE_TRUNC('week', date)
                    ORDER BY week
                """, (user_id,))
                
                weekly_data = cursor.fetchall()
                return {
                    'success': True,
                    'weekly_trends': [dict(row) for row in weekly_data]
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
