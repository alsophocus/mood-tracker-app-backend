"""
Export service following Service Layer Pattern and SOLID principles.
"""
from typing import Dict, Any
from datetime import date, timedelta
import json
from shared.models import MoodType


class ExportService:
    """Export service for exporting mood data."""

    def __init__(self, mood_repository, tag_repository):
        self.mood_repository = mood_repository
        self.tag_repository = tag_repository

    def export_to_json(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Export mood data to JSON format."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        moods = self.mood_repository.find_by_user_and_date_range(user_id, start_date, end_date)
        
        export_data = {
            'export_date': date.today().isoformat(),
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'total_entries': len(moods),
            'moods': []
        }
        
        for mood in moods:
            tags = self.tag_repository.get_mood_tags(mood.id)
            mood_data = mood.to_dict()
            mood_data['tags'] = [tag.name for tag in tags]
            export_data['moods'].append(mood_data)
        
        return export_data

    def export_to_csv(self, user_id: int, days: int = 30) -> str:
        """Export mood data to CSV format."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        moods = self.mood_repository.find_by_user_and_date_range(user_id, start_date, end_date)
        
        # CSV header
        csv_lines = ['Date,Time,Mood,MoodValue,Notes,Triggers,Tags']
        
        for mood in moods:
            tags = self.tag_repository.get_mood_tags(mood.id)
            tag_names = ';'.join([tag.name for tag in tags])
            
            csv_lines.append(
                f"{mood.date.isoformat()},"
                f"{mood.timestamp.strftime('%H:%M:%S')},"
                f"{mood.mood},"
                f"{mood.mood_value},"
                f'"{mood.notes}",'
                f'"{mood.triggers}",'
                f'"{tag_names}"'
            )
        
        return '\n'.join(csv_lines)

    def get_summary_stats(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get summary statistics for export."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        moods = self.mood_repository.find_by_user_and_date_range(user_id, start_date, end_date)
        
        if not moods:
            return {
                'total_entries': 0,
                'average_mood': None,
                'most_common_mood': None
            }
        
        avg_value = sum(MoodType.get_value(m.mood) for m in moods) / len(moods)
        
        mood_counts = {}
        for mood in moods:
            mood_counts[mood.mood] = mood_counts.get(mood.mood, 0) + 1
        
        most_common = max(mood_counts.items(), key=lambda x: x[1])[0]
        
        return {
            'total_entries': len(moods),
            'average_mood': round(avg_value, 2),
            'most_common_mood': most_common,
            'mood_distribution': mood_counts
        }
