from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any

MOOD_VALUES = {
    'very bad': 1, 'bad': 2, 'slightly bad': 3, 'neutral': 4,
    'slightly well': 5, 'well': 6, 'very well': 7
}

class TrendAnalysisService:
    """Single Responsibility: Handle trend analysis and linear regression calculations"""
    
    def __init__(self):
        pass
    
    def calculate_linear_regression(self, data_points: List[float]) -> Dict[str, float]:
        """Calculate linear regression for trend analysis"""
        if not data_points or len(data_points) < 2:
            return {'slope': 0, 'intercept': 0, 'correlation': 0}
        
        # Filter out None values and create x,y pairs
        valid_points = [(i, val) for i, val in enumerate(data_points) if val is not None]
        
        if len(valid_points) < 2:
            return {'slope': 0, 'intercept': 0, 'correlation': 0}
        
        n = len(valid_points)
        x_values = [point[0] for point in valid_points]
        y_values = [point[1] for point in valid_points]
        
        # Calculate means
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n
        
        # Calculate slope and intercept
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in valid_points)
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return {'slope': 0, 'intercept': y_mean, 'correlation': 0}
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Calculate correlation coefficient
        y_variance = sum((y - y_mean) ** 2 for y in y_values)
        if y_variance == 0:
            correlation = 0
        else:
            correlation = numerator / (denominator * y_variance) ** 0.5
        
        return {
            'slope': round(slope, 4),
            'intercept': round(intercept, 4),
            'correlation': round(correlation, 4)
        }
    
    def get_trend_direction(self, slope: float) -> Dict[str, str]:
        """Determine trend direction and description"""
        if slope > 0.1:
            return {
                'direction': 'improving',
                'icon': 'trending_up',
                'description': 'Improving trend',
                'color': '#4CAF50'  # Green for upward
            }
        elif slope < -0.1:
            return {
                'direction': 'declining',
                'icon': 'trending_down', 
                'description': 'Declining trend',
                'color': '#F44336'  # Red for downward
            }
        else:
            return {
                'direction': 'stable',
                'icon': 'trending_flat',
                'description': 'Stable trend',
                'color': '#FF9800'  # Orange for flat
            }
    
    def generate_trend_line_data(self, data_points: List[float], regression: Dict[str, float]) -> List[float]:
        """Generate trend line data points for chart overlay"""
        if not data_points:
            return []
        
        trend_line = []
        slope = regression['slope']
        intercept = regression['intercept']
        
        for i in range(len(data_points)):
            if data_points[i] is not None:
                trend_value = slope * i + intercept
                # Clamp to valid mood range (1-7)
                trend_value = max(1, min(7, trend_value))
                trend_line.append(round(trend_value, 2))
            else:
                trend_line.append(None)
        
        return trend_line

class FourWeekComparisonService:
    """Single Responsibility: Handle 4-week comparison data analysis"""
    
    def __init__(self, db):
        self.db = db
    
    def get_four_week_comparison(self, user_id: int) -> Dict[str, Any]:
        """Get last 4 weeks of data with date ranges for comparison"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get data for last 4 weeks
                cursor.execute("""
                    SELECT date, mood 
                    FROM moods 
                    WHERE user_id = %s 
                    AND date >= CURRENT_DATE - INTERVAL '28 days'
                    ORDER BY date
                """, (user_id,))
                
                rows = cursor.fetchall()
                
                # Group data by weeks
                weeks_data = self._group_by_weeks(rows)
                
                return {
                    'success': True,
                    'weeks': weeks_data,
                    'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _group_by_weeks(self, rows: List[Dict]) -> List[Dict]:
        """Group mood data by 4-week periods with date ranges"""
        # Calculate week boundaries (last 4 weeks)
        today = datetime.now().date()
        weeks = []
        
        for week_offset in range(4):
            # Calculate start of each week (Monday)
            days_back = (today.weekday() + 7 * week_offset)
            week_start = today - timedelta(days=days_back)
            week_end = week_start + timedelta(days=6)
            
            # Get data for this week
            week_data = [None] * 7  # Mon-Sun
            week_entries = []
            
            for row in rows:
                mood_date = row['date']
                if week_start <= mood_date <= week_end:
                    day_of_week = mood_date.weekday()  # 0=Monday
                    mood_value = MOOD_VALUES.get(row['mood'].lower(), 4)
                    week_data[day_of_week] = mood_value
                    week_entries.append(mood_value)
            
            # Calculate week average
            week_average = sum(week_entries) / len(week_entries) if week_entries else None
            
            # Format date range
            date_range = f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d')}"
            
            weeks.append({
                'label': date_range,
                'data': week_data,
                'average': round(week_average, 1) if week_average else None,
                'entries_count': len(week_entries)
            })
        
        # Reverse to show oldest to newest
        return list(reversed(weeks))

class MoodAnalytics:
    def __init__(self, moods):
        self.moods = moods
    
    def calculate_streak(self):
        """Calculate current good mood streak"""
        streak = 0
        for mood_entry in reversed(self.moods):
            mood_value = MOOD_VALUES[mood_entry['mood']]
            if mood_value >= 5:  # slightly well or better
                streak += 1
            else:
                break
        return streak
    
    def calculate_averages(self):
        """Calculate mood averages"""
        if not self.moods:
            return {'daily': 0, 'good_days': 0, 'bad_days': 0, 'total_entries': 0}
        
        daily_moods = defaultdict(list)
        for mood_entry in self.moods:
            date = mood_entry['date']
            mood_value = MOOD_VALUES[mood_entry['mood']]
            daily_moods[date].append(mood_value)
        
        daily_averages = []
        good_days = []
        bad_days = []
        
        for date, mood_list in daily_moods.items():
            daily_avg = sum(mood_list) / len(mood_list)
            daily_averages.append(daily_avg)
            
            if daily_avg >= 5:
                good_days.append(daily_avg)
            elif daily_avg <= 3:
                bad_days.append(daily_avg)
        
        return {
            'daily': round(sum(daily_averages) / len(daily_averages), 2) if daily_averages else 0,
            'good_days': round(sum(good_days) / len(good_days), 2) if good_days else 0,
            'bad_days': round(sum(bad_days) / len(bad_days), 2) if bad_days else 0,
            'total_entries': len(daily_averages)
        }
    
    def get_weekly_patterns(self):
        """Get mood patterns by day of week"""
        weekly_patterns = defaultdict(list)
        
        for mood_entry in self.moods:
            date_str = str(mood_entry['date'])
            mood_value = MOOD_VALUES[mood_entry['mood']]
            day_of_week = datetime.strptime(date_str, '%Y-%m-%d').strftime('%A')
            weekly_patterns[day_of_week].append(mood_value)
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return {
            'labels': days,
            'data': [
                round(sum(weekly_patterns[day]) / len(weekly_patterns[day]), 2) 
                if day in weekly_patterns and len(weekly_patterns[day]) > 0
                else 0  # Use 0 instead of None to prevent JSON serialization issues
                for day in days
            ]
        }
    
    def get_monthly_trends(self):
        """Get monthly mood trends"""
        monthly_data = defaultdict(list)
        
        for mood_entry in self.moods:
            date_str = str(mood_entry['date'])
            mood_value = MOOD_VALUES[mood_entry['mood']]
            month = date_str[:7]  # YYYY-MM
            monthly_data[month].append(mood_value)
        
        chart_data = []
        for month in sorted(monthly_data.keys()):
            avg_mood = sum(monthly_data[month]) / len(monthly_data[month])
            chart_data.append({'month': month, 'mood': round(avg_mood, 1)})
        
        return chart_data
    
    def get_daily_patterns(self):
        """Get mood patterns by hour of day"""
        # Initialize hourly data (0-23 hours)
        hourly_moods = {hour: [] for hour in range(24)}
        
        for mood_entry in self.moods:
            timestamp = mood_entry.get('timestamp')
            if not timestamp:
                continue
            
            mood_value = MOOD_VALUES[mood_entry['mood']]
            
            if isinstance(timestamp, str):
                from datetime import datetime
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Convert UTC to UTC-3 (Chile timezone)
            from datetime import timedelta
            chile_time = timestamp - timedelta(hours=3)
            hour = chile_time.hour
            
            hourly_moods[hour].append(mood_value)
        
        # Create labels and data for all 24 hours
        labels = [f"{hour:02d}:00" for hour in range(24)]
        data = []
        
        for hour in range(24):
            if hourly_moods[hour]:
                data.append(round(sum(hourly_moods[hour]) / len(hourly_moods[hour]), 2))
            else:
                data.append(None)  # No data for this hour
        
        return {
            'labels': labels,
            'data': data,
            'period': 'Average Mood by Hour (All Days)'
        }
    
    def get_summary(self):
        """Get complete analytics summary"""
        averages = self.calculate_averages()
        streak = self.calculate_streak()
        weekly = self.get_weekly_patterns()
        
        # Find best day
        best_day = "N/A"
        best_avg = 0
        for i, day in enumerate(weekly['labels']):
            if weekly['data'][i] > best_avg:
                best_avg = weekly['data'][i]
                best_day = day
        
        return {
            'current_streak': streak,
            'daily_average': averages['daily'],
            'good_days_average': averages['good_days'],
            'bad_days_average': averages['bad_days'],
            'total_entries': averages['total_entries'],
            'best_day': best_day,
            'weekly_patterns': weekly
        }
    
    def get_daily_patterns_for_date(self, selected_date):
        """Get mood patterns for a specific date with precise minute positioning"""
        from datetime import datetime, timedelta
        
        print(f"DEBUG: Getting daily patterns for date: {selected_date}")
        
        # Parse the selected date
        try:
            target_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            print(f"DEBUG: Invalid date format: {selected_date}")
            return {'labels': [], 'data': [], 'period': f'Invalid date: {selected_date}'}
        
        # Filter moods for the selected date
        filtered_moods = []
        for mood_entry in self.moods:
            timestamp = mood_entry.get('timestamp')
            if not timestamp:
                continue
                
            print(f"DEBUG: Checking mood date: {timestamp} (type: {type(timestamp)})")
            
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Convert UTC to Chile timezone (UTC-3)
            chile_time = timestamp - timedelta(hours=3)
            print(f"DEBUG: Formatted date: {chile_time.date()}")
            
            if chile_time.date() == target_date:
                # Add precise time information for positioning
                mood_entry_with_time = mood_entry.copy()
                mood_entry_with_time['precise_time'] = chile_time.hour + (chile_time.minute / 60.0)  # Hour with decimal minutes
                mood_entry_with_time['display_time'] = chile_time.strftime('%H:%M')
                mood_entry_with_time['chile_timestamp'] = chile_time
                filtered_moods.append(mood_entry_with_time)
        
        print(f"DEBUG: Filtered moods count: {len(filtered_moods)}")
        
        if not filtered_moods:
            return {
                'labels': [f"{hour:02d}:00" for hour in range(24)],
                'data': [None] * 24,
                'mood_points': [],
                'period': f'Daily Patterns for {selected_date} (No data)'
            }
        
        # Sort by timestamp
        filtered_moods.sort(key=lambda x: x['chile_timestamp'])
        
        # Create chart data with precise positioning
        mood_points = []
        for mood_entry in filtered_moods:
            mood_value = MOOD_VALUES[mood_entry['mood']]
            mood_points.append({
                'x': mood_entry['precise_time'],  # Exact hour.minute position
                'y': mood_value,
                'time': mood_entry['display_time'],
                'mood': mood_entry['mood'],
                'notes': mood_entry.get('notes', ''),
                'timestamp': mood_entry['chile_timestamp'].isoformat()
            })
        
        # Create hourly labels (keep the same format)
        labels = [f"{hour:02d}:00" for hour in range(24)]
        
        return {
            'labels': labels,
            'data': [None] * 24,  # Keep empty for hourly structure
            'mood_points': mood_points,  # Precise positioning data
            'period': f'Daily Patterns for {selected_date}',
            'total_entries': len(mood_points)
        }
        """Get mood patterns with exact minute timestamps for a specific date"""
        from datetime import datetime, timedelta
        
        # Filter moods for the selected date if provided
        filtered_moods = self.moods
        if selected_date:
            try:
                target_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
                filtered_moods = []
                for mood_entry in self.moods:
                    timestamp = mood_entry.get('timestamp')
                    if timestamp:
                        if isinstance(timestamp, str):
                            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        # Convert to Chile timezone
                        chile_time = timestamp - timedelta(hours=3)
                        if chile_time.date() == target_date:
                            filtered_moods.append(mood_entry)
            except ValueError:
                filtered_moods = self.moods
        
        # Collect all mood points with exact timestamps
        mood_points = []
        for mood_entry in filtered_moods:
            timestamp = mood_entry.get('timestamp')
            if not timestamp:
                continue
            
            mood_value = MOOD_VALUES[mood_entry['mood']]
            
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Convert UTC to Chile timezone (UTC-3)
            chile_time = timestamp - timedelta(hours=3)
            
            # Format as HH:MM for precise time display
            time_label = chile_time.strftime('%H:%M')
            
            mood_points.append({
                'time': time_label,
                'timestamp': chile_time.isoformat(),
                'mood_value': mood_value,
                'mood_name': mood_entry['mood'],
                'notes': mood_entry.get('notes', '')
            })
        
        # Sort by timestamp
        mood_points.sort(key=lambda x: x['timestamp'])
        
        # Prepare chart data
        labels = [point['time'] for point in mood_points]
        data = [point['mood_value'] for point in mood_points]
        
        return {
            'labels': labels,
            'data': data,
            'mood_points': mood_points,
            'total_entries': len(mood_points),
            'date': selected_date or 'All dates'
        }
        """Get mood patterns for a specific date"""
        from datetime import datetime
        
        print(f"DEBUG: Filtering moods for date: {selected_date}")
        print(f"DEBUG: Total moods to filter: {len(self.moods)}")
        
        # Filter moods for the selected date
        filtered_moods = []
        for mood_entry in self.moods:
            mood_date = mood_entry.get('date')
            print(f"DEBUG: Checking mood date: {mood_date} (type: {type(mood_date)})")
            
            if isinstance(mood_date, str):
                if mood_date == selected_date:
                    filtered_moods.append(mood_entry)
                    print(f"DEBUG: String date match found")
            elif hasattr(mood_date, 'strftime'):
                formatted_date = mood_date.strftime('%Y-%m-%d')
                print(f"DEBUG: Formatted date: {formatted_date}")
                if formatted_date == selected_date:
                    filtered_moods.append(mood_entry)
                    print(f"DEBUG: Date object match found")
        
        print(f"DEBUG: Filtered moods count: {len(filtered_moods)}")
        
        # Create temporary analytics instance for filtered data
        temp_analytics = MoodAnalytics(filtered_moods)
        result = temp_analytics.get_daily_patterns()
        result['period'] = f"Daily Patterns for {selected_date}"
        
        # If no data for the date, return empty structure
        if not filtered_moods:
            print(f"DEBUG: No moods found for {selected_date}, returning empty data")
            result = {
                'labels': [f"{hour:02d}:00" for hour in range(24)],
                'data': [None] * 24,
                'period': f"No data for {selected_date}"
            }
        
        return result
    
    def get_weekly_patterns_for_period(self, start_date, end_date, period_label):
        """Get weekly patterns for a specific date range"""
        from datetime import datetime
        from collections import defaultdict
        
        # Group moods by day of week
        daily_moods = defaultdict(list)
        
        for mood_entry in self.moods:
            mood_date = mood_entry.get('date')
            
            # Convert mood_date to date object for comparison
            if isinstance(mood_date, str):
                try:
                    mood_date = datetime.strptime(mood_date, '%Y-%m-%d').date()
                except:
                    continue
            elif hasattr(mood_date, 'date'):
                mood_date = mood_date.date()
            
            if start_date <= mood_date <= end_date:
                mood_value = MOOD_VALUES[mood_entry['mood']]
                day_of_week = mood_date.weekday()  # 0=Monday, 6=Sunday
                daily_moods[day_of_week].append(mood_value)
        
        # Calculate averages for each day
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        data = []
        counts = []
        
        for day_index in range(7):
            if daily_moods[day_index]:
                avg = round(sum(daily_moods[day_index]) / len(daily_moods[day_index]), 2)
                data.append(avg)
                counts.append(len(daily_moods[day_index]))
            else:
                data.append(None)  # null for days with no data (creates gaps in line)
                counts.append(0)
        
        return {
            'labels': days,
            'days': days,
            'data': data,
            'counts': counts,
            'period': period_label,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
    
    def get_weekly_trends_for_month(self, year, month):
        """Get weekly mood trends (averages) for a specific month"""
        from datetime import date, timedelta
        import calendar
        
        # Calculate month boundaries
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        # Calculate first Monday of the month for week calculation
        first_weekday = first_day.weekday()  # 0=Monday, 6=Sunday
        days_to_first_monday = (7 - first_weekday) % 7
        first_monday = first_day + timedelta(days=days_to_first_monday)
        
        # Initialize weekly data
        weekly_moods = {}
        week_labels = []
        
        # Calculate weeks in this month
        current_week_start = first_monday
        week_num = 1
        
        while current_week_start.month <= month and current_week_start.year == year:
            week_end = current_week_start + timedelta(days=6)
            # Ensure we don't go past month end
            week_end = min(week_end, last_day)
            
            weekly_moods[week_num] = []
            week_labels.append(f"Week {week_num}")
            
            # Collect moods for this week
            for mood_entry in self.moods:
                mood_date = mood_entry.get('date')
                
                # Convert mood_date to date object
                if isinstance(mood_date, str):
                    try:
                        mood_date = datetime.strptime(mood_date, '%Y-%m-%d').date()
                    except:
                        continue
                elif hasattr(mood_date, 'date'):
                    mood_date = mood_date.date()
                
                # Check if mood is in this week
                if current_week_start <= mood_date <= week_end:
                    mood_value = MOOD_VALUES[mood_entry['mood']]
                    weekly_moods[week_num].append(mood_value)
            
            # Move to next week
            current_week_start += timedelta(days=7)
            week_num += 1
            
            # Safety check
            if week_num > 6:
                break
        
        # Calculate averages for each week
        data = []
        for i in range(1, week_num):
            if weekly_moods[i]:
                avg = round(sum(weekly_moods[i]) / len(weekly_moods[i]), 1)
                data.append(avg)
            else:
                data.append(0)
        
        return {
            'labels': week_labels,
            'data': data,
            'period': f"Weekly Mood Averages for {calendar.month_name[month]} {year}",
            'year': year,
            'month': month
        }
    
    def get_monthly_trends_for_year(self, year):
        """Get monthly mood trends (averages) for a specific year"""
        import calendar
        
        # Initialize monthly data for all 12 months
        monthly_moods = {month: [] for month in range(1, 13)}
        
        # Collect moods for each month
        for mood_entry in self.moods:
            mood_date = mood_entry.get('date')
            
            # Convert mood_date to date object
            if isinstance(mood_date, str):
                try:
                    mood_date = datetime.strptime(mood_date, '%Y-%m-%d').date()
                except:
                    continue
            elif hasattr(mood_date, 'date'):
                mood_date = mood_date.date()
            
            # Check if mood is in the target year
            if mood_date.year == year:
                mood_value = MOOD_VALUES[mood_entry['mood']]
                monthly_moods[mood_date.month].append(mood_value)
        
        # Calculate averages for each month
        month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        data = []
        
        for month in range(1, 13):
            if monthly_moods[month]:
                avg = round(sum(monthly_moods[month]) / len(monthly_moods[month]), 1)
                data.append(avg)
            else:
                data.append(0)
        
        return {
            'labels': month_labels,
            'data': data,
            'period': f"Monthly Mood Averages for {year}",
            'year': year
        }
    
    def get_hourly_averages(self):
        """Get average mood per hour across all user data"""
        from collections import defaultdict
        from datetime import datetime, timedelta
        
        hourly_totals = defaultdict(list)
        earliest_date = None
        latest_date = None
        
        # Group moods by hour (same logic as get_daily_patterns)
        for mood_entry in self.moods:
            timestamp = mood_entry.get('timestamp')
            if not timestamp:
                continue
            
            mood_value = MOOD_VALUES[mood_entry['mood']]
            
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Track date range
            if earliest_date is None or timestamp < earliest_date:
                earliest_date = timestamp
            if latest_date is None or timestamp > latest_date:
                latest_date = timestamp
            
            # Convert UTC to UTC-3 (Chile timezone)
            chile_time = timestamp - timedelta(hours=3)
            hour = chile_time.hour
            
            hourly_totals[hour].append(mood_value)
        
        # Calculate averages and counts for each hour
        data = []
        counts = []
        for hour in range(24):
            if hourly_totals[hour]:
                avg = round(sum(hourly_totals[hour]) / len(hourly_totals[hour]), 2)
                data.append(avg)
                counts.append(len(hourly_totals[hour]))
            else:
                data.append(None)  # null for hours with no data (creates gaps in line)
                counts.append(0)
        
        # Format date range
        date_range = None
        if earliest_date and latest_date:
            date_range = {
                'start': earliest_date.strftime('%Y-%m-%d'),
                'end': latest_date.strftime('%Y-%m-%d')
            }
        
        return {
            'labels': [f"{hour:02d}:00" for hour in range(24)],
            'data': data,
            'counts': counts,
            'date_range': date_range,
            'period': 'Average Mood Per Hour (All Time)'
        }
