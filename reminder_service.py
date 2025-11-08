"""
SOLID-compliant Reminder Service
Single Responsibility: Handles all reminder-related operations
"""

from datetime import datetime, timedelta

class ReminderService:
    def __init__(self, db_instance):
        self.db = db_instance
    
    def get_user_reminders(self, user_id):
        """Get all reminders for a user"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, message, reminder_time, frequency, 
                           is_active, created_at
                    FROM mood_reminders 
                    WHERE user_id = %s 
                    ORDER BY reminder_time
                """, (user_id,))
                
                reminders = cursor.fetchall()
                return [dict(reminder) for reminder in reminders]
        except Exception as e:
            print(f"Error getting reminders: {e}")
            return []
    
    def create_reminder(self, user_id, reminder_data):
        """Create a new reminder"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO mood_reminders (user_id, title, message, reminder_time, frequency)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    user_id,
                    reminder_data.get('title'),
                    reminder_data.get('message'),
                    reminder_data.get('reminder_time'),
                    reminder_data.get('frequency', 'daily')
                ))
                
                reminder_id = cursor.fetchone()['id']
                conn.commit()
                
                return {'success': True, 'reminder_id': reminder_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def should_send_reminder(self, user_id):
        """Check if reminders should be sent"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM mood_reminders 
                    WHERE user_id = %s 
                    AND is_active = true
                    AND reminder_time <= CURRENT_TIME
                """, (user_id,))
                
                result = cursor.fetchone()
                return result['count'] > 0
        except Exception as e:
            return False
