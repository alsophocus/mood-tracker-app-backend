"""
SOLID-compliant Goal Tracker Service
Single Responsibility: Handles all goal-related operations
"""

class GoalTracker:
    def __init__(self, db_instance):
        self.db = db_instance
    
    def get_user_goals(self, user_id):
        """Get all goals for a user"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, description, target_value, current_value, 
                           created_at, target_date, status
                    FROM mood_goals 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC
                """, (user_id,))
                
                goals = cursor.fetchall()
                return [dict(goal) for goal in goals]
        except Exception as e:
            print(f"Error getting goals: {e}")
            return []
    
    def create_goal(self, user_id, goal_data):
        """Create a new goal"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO mood_goals (user_id, title, description, target_value, target_date)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    user_id,
                    goal_data.get('title'),
                    goal_data.get('description'),
                    goal_data.get('target_value', 1),
                    goal_data.get('target_date')
                ))
                
                goal_id = cursor.fetchone()['id']
                conn.commit()
                
                return {'success': True, 'goal_id': goal_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_goal_progress(self, goal_id, progress_data):
        """Update goal progress"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE mood_goals 
                    SET current_value = %s, status = %s
                    WHERE id = %s
                """, (
                    progress_data.get('current_value'),
                    progress_data.get('status', 'active'),
                    goal_id
                ))
                
                conn.commit()
                return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
