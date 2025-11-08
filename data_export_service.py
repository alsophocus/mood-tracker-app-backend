"""
SOLID-compliant Data Export Service
Single Responsibility: Handles data export/import operations
"""

import json
import csv
from io import StringIO
from datetime import datetime

class DataExportService:
    def __init__(self, db_instance):
        self.db = db_instance
    
    def export_user_data(self, user_id, format_type):
        """Export user data in specified format"""
        try:
            # Get all user data
            data = self._get_user_data(user_id)
            
            if format_type == 'json':
                return {
                    'success': True,
                    'data': data,
                    'filename': f'mood_data_{datetime.now().strftime("%Y%m%d")}.json'
                }
            elif format_type == 'csv':
                csv_data = self._convert_to_csv(data)
                return {
                    'success': True,
                    'data': csv_data,
                    'filename': f'mood_data_{datetime.now().strftime("%Y%m%d")}.csv'
                }
            else:
                return {'success': False, 'error': 'Unsupported format'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_user_data(self, user_id):
        """Get all user data from database"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get moods
            cursor.execute("""
                SELECT id, mood, date, timestamp, notes
                FROM moods 
                WHERE user_id = %s
                ORDER BY date DESC
            """, (user_id,))
            moods = [dict(row) for row in cursor.fetchall()]
            
            # Get goals
            cursor.execute("""
                SELECT id, title, description, target_value, current_value, created_at
                FROM mood_goals 
                WHERE user_id = %s
            """, (user_id,))
            goals = [dict(row) for row in cursor.fetchall()]
            
            return {
                'moods': moods,
                'goals': goals,
                'export_date': datetime.now().isoformat()
            }
    
    def _convert_to_csv(self, data):
        """Convert data to CSV format"""
        output = StringIO()
        
        # Write moods to CSV
        if data['moods']:
            writer = csv.DictWriter(output, fieldnames=['date', 'mood', 'notes'])
            writer.writeheader()
            for mood in data['moods']:
                writer.writerow({
                    'date': mood['date'],
                    'mood': mood['mood'],
                    'notes': mood.get('notes', '')
                })
        
        return output.getvalue()
    
    def import_user_data(self, user_id, import_data):
        """Import user data"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Import moods
                if 'moods' in import_data:
                    for mood in import_data['moods']:
                        cursor.execute("""
                            INSERT INTO moods (user_id, mood, date, notes)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (user_id, date) DO NOTHING
                        """, (
                            user_id,
                            mood['mood'],
                            mood['date'],
                            mood.get('notes', '')
                        ))
                
                conn.commit()
                return {'success': True, 'message': 'Data imported successfully'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
