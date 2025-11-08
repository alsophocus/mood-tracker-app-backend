from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from datetime import datetime
from database import db
from analytics import MoodAnalytics, MOOD_VALUES
from pdf_export import PDFExporter

main_bp = Blueprint('main', __name__)

@main_bp.route('/triggers')
@login_required
def mood_triggers():
    """Mood triggers and context page"""
    return render_template('mood_triggers.html')

@main_bp.route('/api/tags')
@login_required
def get_tags():
    """Get all available tags"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, category, color, icon 
                FROM tags 
                ORDER BY category, name
            """)
            tags = cursor.fetchall()
            
            # Group by category
            categories = {}
            for tag in tags:
                category = tag['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append({
                    'id': tag['id'],
                    'name': tag['name'],
                    'color': tag['color'],
                    'icon': tag['icon']
                })
            
            return jsonify({'success': True, 'categories': categories})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/mood-context', methods=['POST'])
@login_required
def save_mood_context():
    """Save mood context and tags for most recent mood or create new entry"""
    try:
        data = request.get_json()
        tags = data.get('tags', [])
        context = data.get('context', {})
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get the most recent mood for this user
            cursor.execute("""
                SELECT id FROM moods 
                WHERE user_id = %s 
                ORDER BY date DESC, timestamp DESC 
                LIMIT 1
            """, (session['user_id'],))
            
            mood_result = cursor.fetchone()
            
            if not mood_result:
                return jsonify({
                    'success': False, 
                    'error': 'No mood entries found. Please add a mood first.'
                }), 400
            
            mood_id = mood_result['id']
            
            # Update mood with context
            cursor.execute("""
                UPDATE moods 
                SET context_location = %s,
                    context_activity = %s,
                    context_weather = %s,
                    context_notes = %s
                WHERE id = %s AND user_id = %s
            """, (
                context.get('location'),
                context.get('activity'), 
                context.get('weather'),
                context.get('notes'),
                mood_id,
                session['user_id']
            ))
            
            # Clear existing tags for this mood
            cursor.execute("DELETE FROM mood_tags WHERE mood_id = %s", (mood_id,))
            
            # Add new tags
            for tag_name in tags:
                # Get or create tag
                cursor.execute("SELECT id FROM tags WHERE name = %s", (tag_name,))
                tag_result = cursor.fetchone()
                
                if tag_result:
                    tag_id = tag_result['id']
                else:
                    # Create new tag in emotions category
                    cursor.execute("""
                        INSERT INTO tags (name, category, color, icon)
                        VALUES (%s, 'emotions', '#6750A4', 'tag')
                        RETURNING id
                    """, (tag_name,))
                    tag_id = cursor.fetchone()['id']
                
                # Link mood to tag
                cursor.execute("""
                    INSERT INTO mood_tags (mood_id, tag_id)
                    VALUES (%s, %s)
                    ON CONFLICT (mood_id, tag_id) DO NOTHING
                """, (mood_id, tag_id))
            
            conn.commit()
            
        return jsonify({
            'success': True, 
            'message': 'Context saved successfully',
            'mood_id': mood_id,
            'tags_count': len(tags)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/')
@login_required
def index():
    """Main dashboard"""
    recent_moods = db.get_user_moods(current_user.id, limit=5)
    all_moods = db.get_user_moods(current_user.id)
    
    analytics = MoodAnalytics(all_moods).get_summary()
    
    return render_template('index.html', moods=recent_moods, analytics=analytics, user=current_user)

@main_bp.route('/debug-timestamps')
@login_required
def debug_timestamps():
    """Debug mood timestamps for daily patterns"""
    try:
        moods = db.get_user_moods(current_user.id, limit=10)
        
        debug_data = []
        for mood in moods:
            debug_data.append({
                'id': mood.get('id'),
                'date': str(mood.get('date')),
                'mood': mood.get('mood'),
                'timestamp': str(mood.get('timestamp')),
                'timestamp_type': type(mood.get('timestamp')).__name__,
                'has_timestamp': mood.get('timestamp') is not None,
                'timestamp_hour': mood.get('timestamp').hour if mood.get('timestamp') and hasattr(mood.get('timestamp'), 'hour') else 'N/A'
            })
        
        return jsonify({
            'success': True,
            'total_moods': len(moods),
            'moods_with_timestamps': len([m for m in moods if m.get('timestamp')]),
            'sample_moods': debug_data
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@main_bp.route('/fix-unique-constraint')
@login_required
def fix_unique_constraint():
    """Remove UNIQUE constraint from moods table to allow multiple entries per day"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if constraint exists
            cursor.execute("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'moods' 
                AND constraint_type = 'UNIQUE'
            """)
            constraints = cursor.fetchall()
            
            # Drop any UNIQUE constraints on moods table
            for constraint in constraints:
                constraint_name = constraint['constraint_name']
                cursor.execute(f'ALTER TABLE moods DROP CONSTRAINT IF EXISTS {constraint_name}')
                print(f"Dropped constraint: {constraint_name}")
            
            return jsonify({
                'success': True,
                'message': f'Removed {len(constraints)} UNIQUE constraints from moods table',
                'constraints_removed': [c['constraint_name'] for c in constraints]
            })
            
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@main_bp.route('/fix-schema')
def fix_schema():
    """Fix database schema constraints"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check current table structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'moods'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            
            # Check existing constraints
            cursor.execute("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_name = 'moods'
            """)
            constraints = cursor.fetchall()
            
            # Drop and recreate the moods table with proper constraints
            cursor.execute('DROP TABLE IF EXISTS moods CASCADE')
            
            cursor.execute('''
                CREATE TABLE moods (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    date DATE NOT NULL,
                    mood TEXT NOT NULL,
                    notes TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, date)
                )
            ''')
            
            # Recreate indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_moods_user_date ON moods(user_id, date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_moods_timestamp ON moods(timestamp)')
            
            return jsonify({
                'success': True,
                'message': 'Schema fixed successfully',
                'old_columns': [dict(col) for col in columns],
                'old_constraints': [dict(cons) for cons in constraints]
            })
            
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@main_bp.route('/debug-save')
def debug_save():
    """Debug save without authentication"""
    try:
        # Test database connection
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM users')
            user_count = cursor.fetchone()['count']
            
            # Try to get first user
            cursor.execute('SELECT id FROM users LIMIT 1')
            first_user = cursor.fetchone()
            
            if first_user:
                user_id = first_user['id']
                # Try to save a test mood
                result = db.save_mood(user_id, datetime.now().date(), 'well', 'debug test')
                return jsonify({
                    'success': True,
                    'message': 'Debug save successful',
                    'user_count': user_count,
                    'test_user_id': user_id,
                    'save_result': str(result)
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No users found in database',
                    'user_count': user_count
                })
                
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@main_bp.route('/test-save')
@login_required
def test_save():
    """Test saving a mood to debug issues"""
    try:
        # Try to save a test mood
        result = db.save_mood(current_user.id, datetime.now().date(), 'well', 'test mood')
        return jsonify({
            'success': True,
            'message': 'Test mood saved successfully',
            'result': str(result),
            'user_id': current_user.id,
            'date': datetime.now().date().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'user_id': current_user.id,
            'date': datetime.now().date().isoformat()
        }), 500

@main_bp.route('/save_mood', methods=['POST'])
@login_required
def save_mood():
    """Save mood entry"""
    mood = request.form.get('mood')
    notes = request.form.get('notes', '')
    triggers = request.form.get('triggers', '')
    
    print(f"DEBUG: Received mood save request - mood: {mood}, notes: {notes}, triggers: {triggers}")
    
    # Check if user is authenticated
    if not current_user or not hasattr(current_user, 'id'):
        print("DEBUG: User not authenticated or missing ID")
        return jsonify({'error': 'User not authenticated'}), 401
    
    print(f"DEBUG: User ID: {current_user.id}")
    
    if not mood:
        print("DEBUG: No mood selected")
        return jsonify({'error': 'Please select a mood before saving.'}), 400
    
    try:
        print(f"DEBUG: Attempting to save mood for user {current_user.id}")
        
        # Use Chile timezone (UTC-3) for the date
        from datetime import timedelta
        chile_time = datetime.now() - timedelta(hours=3)
        chile_date = chile_time.date()
        
        print(f"DEBUG: Server time: {datetime.now()}, Chile time: {chile_time}, Chile date: {chile_date}")
        
        result = db.save_mood(current_user.id, chile_date, mood, notes, triggers)
        print(f"DEBUG: Mood saved successfully - result: {result}")
        
        return jsonify({
            'success': True,
            'message': 'Mood saved successfully!',
            'mood': mood,
            'notes': notes,
            'triggers': triggers,
            'date': chile_date.isoformat()
        })
            
    except Exception as e:
        print(f"DEBUG: Error saving mood - {e}")
        import traceback
        print(f"DEBUG: Traceback - {traceback.format_exc()}")
@main_bp.route('/api/analytics/triggers')
@login_required
def get_trigger_analytics():
    """Get top triggers analytics"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    TRIM(UNNEST(STRING_TO_ARRAY(triggers, ','))) as trigger,
                    COUNT(*) as count
                FROM moods 
                WHERE user_id = %s AND triggers IS NOT NULL AND triggers != ''
                GROUP BY TRIM(UNNEST(STRING_TO_ARRAY(triggers, ',')))
                ORDER BY count DESC
                LIMIT 10
            """, (current_user.id,))
            
            results = cursor.fetchall()
            triggers = [{'name': row['trigger'], 'count': row['count']} for row in results if row['trigger']]
            
            return jsonify({'success': True, 'triggers': triggers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@main_bp.route('/api/analytics/week-comparison')
@login_required
def get_week_comparison():
    """Get this week vs last week comparison"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Map mood strings to numbers
            mood_values = {
                'very bad': 1, 'bad': 2, 'slightly bad': 3, 'neutral': 4,
                'slightly well': 5, 'well': 6, 'very well': 7
            }
            
            # This week
            cursor.execute("""
                SELECT AVG(CASE 
                    WHEN mood = 'very bad' THEN 1
                    WHEN mood = 'bad' THEN 2
                    WHEN mood = 'slightly bad' THEN 3
                    WHEN mood = 'neutral' THEN 4
                    WHEN mood = 'slightly well' THEN 5
                    WHEN mood = 'well' THEN 6
                    WHEN mood = 'very well' THEN 7
                    ELSE 4
                END) as avg_mood
                FROM moods 
                WHERE user_id = %s 
                AND date >= CURRENT_DATE - INTERVAL '7 days'
            """, (current_user.id,))
            
            this_week = cursor.fetchone()['avg_mood'] or 0
            
            # Last week
            cursor.execute("""
                SELECT AVG(CASE 
                    WHEN mood = 'very bad' THEN 1
                    WHEN mood = 'bad' THEN 2
                    WHEN mood = 'slightly bad' THEN 3
                    WHEN mood = 'neutral' THEN 4
                    WHEN mood = 'slightly well' THEN 5
                    WHEN mood = 'well' THEN 6
                    WHEN mood = 'very well' THEN 7
                    ELSE 4
                END) as avg_mood
                FROM moods 
                WHERE user_id = %s 
                AND date >= CURRENT_DATE - INTERVAL '14 days'
                AND date < CURRENT_DATE - INTERVAL '7 days'
            """, (current_user.id,))
            
            last_week = cursor.fetchone()['avg_mood'] or 0
            
            # Current streak
            cursor.execute("""
                WITH daily_moods AS (
                    SELECT date, COUNT(*) as entries
                    FROM moods 
                    WHERE user_id = %s 
                    GROUP BY date
                    ORDER BY date DESC
                ),
                streak_calc AS (
                    SELECT date, 
                           ROW_NUMBER() OVER (ORDER BY date DESC) - 
                           ROW_NUMBER() OVER (PARTITION BY date - ROW_NUMBER() OVER (ORDER BY date DESC) * INTERVAL '1 day' ORDER BY date DESC) as streak_group
                    FROM daily_moods
                )
                SELECT COUNT(*) as streak
                FROM streak_calc
                WHERE streak_group = 0
            """, (current_user.id,))
            
            streak = cursor.fetchone()['streak'] or 0
            
            return jsonify({
                'success': True,
                'this_week': float(this_week),
                'last_week': float(last_week),
                'streak': streak
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@main_bp.route('/api/analytics/mood-distribution')
@login_required
def get_mood_distribution():
    """Get mood distribution for last 30 days"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT mood, COUNT(*) as count
                FROM moods 
                WHERE user_id = %s 
                AND date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY mood
                ORDER BY count DESC
            """, (current_user.id,))
            
            results = cursor.fetchall()
            distribution = [{'mood': row['mood'], 'count': row['count']} for row in results]
            
            return jsonify({'success': True, 'distribution': distribution})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@main_bp.route('/api/carousel/recent-moods')
@login_required
def get_carousel_moods():
    """Get recent moods for carousel display"""
    try:
        from carousel_service import CarouselDataService
        
        carousel_service = CarouselDataService(db)
        moods = carousel_service.get_recent_moods(current_user.id, limit=15)
        
        return jsonify({
            'success': True,
            'moods': moods
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/analytics/quick-stats')
@login_required
def get_quick_stats():
    """Get quick stats for dashboard cards"""
    from datetime import datetime, timedelta, date
    
    try:
        moods = db.get_user_moods(current_user.id)
        
        if not moods:
            return jsonify({
                'success': True,
                'today': None,
                'week': None,
                'trend': None
            })
        
        analytics = MoodAnalytics(moods)
        today = date.today()
        
        # Today's mood
        today_moods = [m for m in moods if m.get('date') == today or (hasattr(m.get('date'), 'date') and m.get('date').date() == today)]
        today_stat = None
        if today_moods:
            latest = today_moods[0]
            # Convert UTC to Chile time (UTC-3)
            timestamp = latest.get('timestamp')
            if timestamp:
                chile_time = timestamp - timedelta(hours=3)
                time_str = chile_time.strftime('%H:%M')
            else:
                time_str = 'Unknown'
            
            today_stat = {
                'mood': latest.get('mood'),
                'value': MOOD_VALUES[latest.get('mood')],
                'time': time_str
            }
        
        # This week average
        week_start = today - timedelta(days=today.weekday())
        week_moods = []
        for m in moods:
            m_date = m.get('date')
            if isinstance(m_date, str):
                m_date = datetime.strptime(m_date, '%Y-%m-%d').date()
            elif hasattr(m_date, 'date'):
                m_date = m_date.date()
            
            if week_start <= m_date <= today:
                week_moods.append(MOOD_VALUES[m.get('mood')])
        
        week_stat = None
        if week_moods:
            avg = sum(week_moods) / len(week_moods)
            week_stat = {
                'average': round(avg, 2),
                'count': len(week_moods)
            }
        
        # Trend (compare this week to last week)
        last_week_start = week_start - timedelta(days=7)
        last_week_end = week_start - timedelta(days=1)
        last_week_moods = []
        
        for m in moods:
            m_date = m.get('date')
            if isinstance(m_date, str):
                m_date = datetime.strptime(m_date, '%Y-%m-%d').date()
            elif hasattr(m_date, 'date'):
                m_date = m_date.date()
            
            if last_week_start <= m_date <= last_week_end:
                last_week_moods.append(MOOD_VALUES[m.get('mood')])
        
        trend_stat = None
        if week_moods and last_week_moods:
            this_week_avg = sum(week_moods) / len(week_moods)
            last_week_avg = sum(last_week_moods) / len(last_week_moods)
            change = this_week_avg - last_week_avg
            
            if abs(change) < 0.3:
                direction = 'stable'
            elif change > 0:
                direction = 'up'
            else:
                direction = 'down'
            
            trend_stat = {
                'direction': direction,
                'change': round(change, 2)
            }
        
        return jsonify({
            'success': True,
            'today': today_stat,
            'week': week_stat,
            'trend': trend_stat
        })
        
    except Exception as e:
        print(f"Error in quick stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@main_bp.route('/api/analytics/quick-insights')
@login_required
def get_quick_insights():
    """Generate personalized quick insights based on user data"""
    try:
        insights = []
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Week comparison insight
            cursor.execute("""
                SELECT 
                    AVG(CASE WHEN date >= CURRENT_DATE - INTERVAL '7 days' THEN
                        CASE mood WHEN 'very bad' THEN 1 WHEN 'bad' THEN 2 WHEN 'slightly bad' THEN 3 
                             WHEN 'neutral' THEN 4 WHEN 'slightly well' THEN 5 WHEN 'well' THEN 6 
                             WHEN 'very well' THEN 7 ELSE 4 END
                    END) as this_week,
                    AVG(CASE WHEN date >= CURRENT_DATE - INTERVAL '14 days' AND date < CURRENT_DATE - INTERVAL '7 days' THEN
                        CASE mood WHEN 'very bad' THEN 1 WHEN 'bad' THEN 2 WHEN 'slightly bad' THEN 3 
                             WHEN 'neutral' THEN 4 WHEN 'slightly well' THEN 5 WHEN 'well' THEN 6 
                             WHEN 'very well' THEN 7 ELSE 4 END
                    END) as last_week
                FROM moods WHERE user_id = %s
            """, (current_user.id,))
            
            week_data = cursor.fetchone()
            if week_data['this_week'] and week_data['last_week']:
                change = ((week_data['this_week'] - week_data['last_week']) / week_data['last_week']) * 100
                if abs(change) > 2:
                    direction = "improved" if change > 0 else "declined"
                    insights.append({
                        'icon': 'fa-chart-line',
                        'text': f'Your mood has {direction} {abs(change):.1f}% this week compared to last week'
                    })
            
            # Streak insight
            cursor.execute("""
                WITH daily_moods AS (
                    SELECT date FROM moods WHERE user_id = %s GROUP BY date ORDER BY date DESC
                ),
                streak_calc AS (
                    SELECT date, ROW_NUMBER() OVER (ORDER BY date DESC) - 
                           ROW_NUMBER() OVER (PARTITION BY date - ROW_NUMBER() OVER (ORDER BY date DESC) * INTERVAL '1 day' ORDER BY date DESC) as streak_group
                    FROM daily_moods
                )
                SELECT COUNT(*) as streak FROM streak_calc WHERE streak_group = 0
            """, (current_user.id,))
            
            streak = cursor.fetchone()['streak'] or 0
            if streak >= 3:
                insights.append({
                    'icon': 'fa-calendar-check',
                    'text': f'You\'ve logged moods for {streak} consecutive days - great streak!'
                })
            
            # Top trigger insight
            cursor.execute("""
                SELECT TRIM(UNNEST(STRING_TO_ARRAY(triggers, ','))) as trigger, COUNT(*) as count,
                       AVG(CASE mood WHEN 'very bad' THEN 1 WHEN 'bad' THEN 2 WHEN 'slightly bad' THEN 3 
                            WHEN 'neutral' THEN 4 WHEN 'slightly well' THEN 5 WHEN 'well' THEN 6 
                            WHEN 'very well' THEN 7 ELSE 4 END) as avg_mood
                FROM moods WHERE user_id = %s AND triggers IS NOT NULL AND triggers != ''
                GROUP BY TRIM(UNNEST(STRING_TO_ARRAY(triggers, ',')))
                HAVING COUNT(*) >= 3 AND TRIM(UNNEST(STRING_TO_ARRAY(triggers, ','))) != ''
                ORDER BY avg_mood DESC LIMIT 1
            """, (current_user.id,))
            
            top_trigger = cursor.fetchone()
            if top_trigger:
                insights.append({
                    'icon': 'fa-lightbulb',
                    'text': f'{top_trigger["trigger"].title()} days show {top_trigger["avg_mood"]:.1f}/7 average mood - your best trigger!'
                })
            
            # Total entries insight
            cursor.execute("SELECT COUNT(*) as total FROM moods WHERE user_id = %s", (current_user.id,))
            total = cursor.fetchone()['total']
            if total >= 7:
                insights.append({
                    'icon': 'fa-database',
                    'text': f'You\'ve tracked {total} mood entries - building great self-awareness!'
                })
            
            # Default insights if no data
            if not insights:
                insights = [
                    {'icon': 'fa-heart', 'text': 'Start logging moods regularly to see personalized insights'},
                    {'icon': 'fa-tags', 'text': 'Add triggers to your mood entries to discover patterns'},
                    {'icon': 'fa-chart-line', 'text': 'Track for a week to see your mood trends and improvements'}
                ]
        
        return jsonify({'success': True, 'insights': insights})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@main_bp.route('/debug-moods')
@login_required
def debug_moods():
    """Debug endpoint to check mood data integrity"""
    try:
        moods = db.get_user_moods(current_user.id, limit=10)
        
        debug_info = {
            'total_moods': len(moods),
            'recent_moods': []
        }
        
        for mood in moods:
            debug_info['recent_moods'].append({
                'id': mood.get('id'),
                'date': str(mood.get('date')),
                'mood': mood.get('mood'),
                'timestamp': str(mood.get('timestamp')),
                'timestamp_type': type(mood.get('timestamp')).__name__,
                'has_timestamp': mood.get('timestamp') is not None,
                'notes': mood.get('notes', '')[:50] if mood.get('notes') else None
            })
        
        # Test daily patterns
        analytics = MoodAnalytics(moods)
        daily_patterns = analytics.get_daily_patterns()
        
        debug_info['daily_patterns_summary'] = {
            'total_hours_with_data': sum(1 for x in daily_patterns['data'] if x is not None),
            'sample_hours': [(i, daily_patterns['data'][i]) for i in range(0, 24, 4)]
        }
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'error': str(e), 'type': type(e).__name__}), 500

@main_bp.route('/recent_moods')
@login_required
def recent_moods():
    """Get recent moods as JSON for AJAX updates"""
    recent_moods = db.get_user_moods(current_user.id, limit=5)
    
    # Add debug info
    debug_info = []
    for mood in recent_moods:
        debug_info.append({
            'id': mood.get('id'),
            'date': str(mood.get('date')),
            'mood': mood.get('mood'),
            'timestamp': str(mood.get('timestamp')) if mood.get('timestamp') else None,
            'has_timestamp': mood.get('timestamp') is not None
        })
    
    return jsonify({
        'moods': recent_moods,
        'debug': debug_info,
        'total_count': len(recent_moods)
    })

@main_bp.route('/mood_data')
@login_required
def mood_data():
    """Get monthly mood trend data"""
    moods = db.get_user_moods(current_user.id)
    analytics = MoodAnalytics(moods)
    return jsonify(analytics.get_monthly_trends())

@main_bp.route('/weekly_patterns')
@login_required
def weekly_patterns():
    """Get weekly mood patterns for specific week"""
    from datetime import date, timedelta, datetime
    import calendar
    
    # Check for new simple format: start_date (Monday of the week)
    start_date_str = request.args.get('start_date')
    
    moods = db.get_user_moods(current_user.id)
    analytics = MoodAnalytics(moods)
    
    if start_date_str:
        # New format: start_date=2025-10-21
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = start_date + timedelta(days=6)
            
            result = analytics.get_weekly_patterns_for_period(
                start_date, 
                end_date, 
                f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
            )
            return jsonify(result)
        except Exception as e:
            print(f"Error in weekly patterns: {str(e)}")
            return jsonify({"error": "Invalid date parameter"}), 400
    
    # Legacy format support: year, month, week
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int) 
    week_of_month = request.args.get('week', type=int)
    
    # Debug: Log what we're working with
    print(f"DEBUG: Weekly patterns request - year={year}, month={month}, week={week_of_month}")
    print(f"DEBUG: Found {len(moods) if moods else 0} moods for user {current_user.id}")
    if moods:
        print(f"DEBUG: Sample mood: {dict(moods[0])}")
    
    if year and month and week_of_month:
        # Calculate date range for specific week of month
        try:
            first_day = date(year, month, 1)
            first_weekday = first_day.weekday()  # 0=Monday, 6=Sunday
            
            # Calculate the start of the specified week
            days_to_first_monday = (7 - first_weekday) % 7
            first_monday = first_day + timedelta(days=days_to_first_monday)
            
            # Calculate start and end of the requested week
            week_start = first_monday + timedelta(weeks=week_of_month - 1)
            week_end = week_start + timedelta(days=6)
            
            # Ensure we don't go outside the month boundaries
            last_day = date(year, month, calendar.monthrange(year, month)[1])
            
            print(f"DEBUG: Week calculation - start={week_start}, end={week_end}")
            
            if week_start.month == month:
                start_date = week_start
                end_date = min(week_end, last_day)
                result = analytics.get_weekly_patterns_for_period(start_date, end_date, f"Week {week_of_month} of {calendar.month_name[month]} {year}")
                print(f"DEBUG: Weekly patterns result: {result}")
                return jsonify(result)
            else:
                return jsonify({"error": "Week does not exist in this month"}), 400
        except Exception as e:
            print(f"DEBUG: Error in weekly patterns: {str(e)}")
            return jsonify({"error": "Invalid date parameters"}), 400
    else:
        result = analytics.get_weekly_patterns()
        print(f"DEBUG: Default weekly patterns result: {result}")
        
        # Ensure we always return a valid structure
        if not result.get('labels') and not result.get('days'):
            result = {
                'labels': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                'data': [0, 0, 0, 0, 0, 0, 0],
                'period': 'No data available'
            }
        elif result.get('labels') and not result.get('days'):
            result['days'] = result['labels']
            
        return jsonify(result)

@main_bp.route('/weekly_trends')
@login_required
def weekly_trends():
    """Get 4-week comparison data with SOLID dependency injection"""
    try:
        # Dependency Injection - inject database dependency
        from analytics import FourWeekComparisonService
        four_week_service = FourWeekComparisonService(db)
        
        # Get 4-week comparison data
        result = four_week_service.get_four_week_comparison(current_user.id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to get 4-week comparison'),
                'weeks': [],
                'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'weeks': [],
            'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        }), 500

@main_bp.route('/monthly_trends')
@login_required
def monthly_trends():
    """Get monthly mood trends with trend analysis - SOLID dependency injection"""
    from datetime import date
    
    try:
        # Get year parameter
        year = request.args.get('year', type=int)
        if not year:
            year = date.today().year
        
        # Dependency Injection - inject dependencies
        from analytics import TrendAnalysisService
        trend_service = TrendAnalysisService()
        
        moods = db.get_user_moods(current_user.id)
        analytics = MoodAnalytics(moods)
        
        # Get base monthly trends data
        result = analytics.get_monthly_trends_for_year(year)
        
        if result and 'data' in result:
            # Add trend analysis using SOLID service
            regression = trend_service.calculate_linear_regression(result['data'])
            trend_direction = trend_service.get_trend_direction(regression['slope'])
            trend_line = trend_service.generate_trend_line_data(result['data'], regression)
            
            # Enhance result with trend analysis
            result['trend_analysis'] = {
                'regression': regression,
                'direction': trend_direction,
                'trend_line': trend_line,
                'slope_percentage': round(regression['slope'] * 100, 2)
            }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            'data': [0] * 12,
            'period': f'Error loading {year if year else "current year"}'
        }), 500

@main_bp.route('/daily_patterns_minutes')
@login_required
def daily_patterns_minutes():
    """Get daily mood patterns with minute precision"""
    selected_date = request.args.get('date')
    
    # Get user's moods
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date, mood, notes, timestamp 
            FROM moods 
            WHERE user_id = %s 
            ORDER BY timestamp DESC
        ''', (current_user.id,))
        mood_entries = cursor.fetchall()
    
    # Convert to analytics format
    moods = []
    for entry in mood_entries:
        moods.append({
            'date': entry['date'],
            'mood': entry['mood'],
            'notes': entry['notes'],
            'timestamp': entry['timestamp']
        })
    
    analytics = MoodAnalytics(moods)
    result = analytics.get_daily_patterns_with_minutes(selected_date)
    
    return jsonify(result)

@main_bp.route('/daily_patterns')
@login_required
def daily_patterns():
    """Get daily mood patterns for specific date or all dates"""
    selected_date = request.args.get('date')
    print(f"DEBUG: Daily patterns requested for date: {selected_date}")
    
    moods = db.get_user_moods(current_user.id)
    print(f"DEBUG: Found {len(moods)} total moods for user {current_user.id}")
    
    if moods and selected_date:
        print(f"DEBUG: Sample mood dates: {[str(mood.get('date')) for mood in moods[:3]]}")
    
    analytics = MoodAnalytics(moods)
    
    if selected_date:
        result = analytics.get_daily_patterns_for_date(selected_date)
        print(f"DEBUG: Result for {selected_date}: {len([x for x in result.get('data', []) if x is not None])} non-null values")
    else:
        result = analytics.get_daily_patterns()
    
    # Add debug info
    debug_info = {
        'total_moods': len(moods),
        'moods_with_timestamps': len([m for m in moods if m.get('timestamp')]),
        'sample_timestamps': [str(m.get('timestamp')) for m in moods[:3] if m.get('timestamp')],
        'hours_with_data': sum(1 for x in result.get('data', []) if x is not None)
    }
    
    # Ensure we always return a valid structure
    if not result.get('labels') or not result.get('data'):
        result = {
            'labels': [f"{hour:02d}:00" for hour in range(24)],
            'data': [None] * 24,
            'period': 'No data available'
        }
    
    # Add debug info to result
    result['debug'] = debug_info
    
    return jsonify(result)

@main_bp.route('/hourly_average_mood')
@login_required
def hourly_average_mood():
    """Get average mood per hour across all user data"""
    moods = db.get_user_moods(current_user.id)
    analytics = MoodAnalytics(moods)
    result = analytics.get_hourly_averages()
    return jsonify(result)

@main_bp.route('/export_pdf')
@login_required
def export_pdf():
    """Export mood data as PDF"""
    moods = db.get_user_moods(current_user.id)
    exporter = PDFExporter(current_user, moods)
    buffer = exporter.generate_report()
    
    filename = f'mood_report_{datetime.now().strftime("%Y%m%d")}.pdf'
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@main_bp.route('/api/pdf-simple')
@login_required
def simple_pdf_export():
    """Simple server-side PDF export"""
    try:
        moods = db.get_user_moods(current_user.id)
        exporter = PDFExporter(current_user, moods)
        buffer = exporter.generate_report()
        
        filename = f'mood_report_{datetime.now().strftime("%Y%m%d")}.pdf'
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'PDF generation failed'
        }), 500

@main_bp.route('/api/pdf-test')
@login_required
def pdf_test_api():
    """API endpoint to test PDF export data"""
    try:
        # Get user moods for analytics
        moods = db.get_user_moods(current_user.id)
        analytics = MoodAnalytics(moods).get_summary()
        
        # Prepare PDF test data
        pdf_data = {
            'user_name': current_user.name or 'User',
            'total_entries': len(moods),
            'current_streak': analytics.get('current_streak', 0),
            'average_mood': analytics.get('daily_average', 0),
            'best_day': analytics.get('best_day', 'N/A'),
            'recent_moods': [
                {
                    'date': mood['date'].strftime('%Y-%m-%d') if mood['date'] else 'N/A',
                    'mood': mood['mood'],
                    'notes': mood['notes'] or ''
                } for mood in moods[:5]  # Last 5 moods
            ],
            'pdf_ready': True,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': pdf_data,
            'message': 'PDF data ready for export'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to prepare PDF data'
        }), 500

@main_bp.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT version()')
            version = cursor.fetchone()['version']
        
        return {
            'status': 'healthy',
            'database': f"PostgreSQL: {version}",
            'timestamp': datetime.now().isoformat(),
            'database_url_set': bool(db.url),
            'database_initialized': db._initialized
        }
    except Exception as e:
        # Return degraded status instead of 500 error
        return {
            'status': 'degraded',
            'database_status': 'unavailable',
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'database_url_set': bool(db.url),
            'database_initialized': db._initialized,
            'note': 'App running but database unavailable'
        }, 200  # Return 200 instead of 500 for health checks

@main_bp.route('/debug')
def debug_info():
    """Debug information endpoint"""
    import os
    return {
        'environment_vars': {
            'DATABASE_URL': 'SET' if os.environ.get('DATABASE_URL') else 'NOT SET',
            'GOOGLE_CLIENT_ID': 'SET' if os.environ.get('GOOGLE_CLIENT_ID') else 'NOT SET',
            'SECRET_KEY': 'SET' if os.environ.get('SECRET_KEY') else 'NOT SET',
            'PORT': os.environ.get('PORT', 'NOT SET')
        },
        'config': {
            'database_url_configured': bool(db.url),
            'database_initialized': db._initialized
        },
        'timestamp': datetime.now().isoformat()
    }

@main_bp.route('/test-db')
def test_database():
    """Test database operations"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM moods')
            result = cursor.fetchone()
            return {'mood_count': result['count'], 'status': 'success'}
    except Exception as e:
        return {'error': str(e), 'status': 'error'}, 500

@main_bp.route('/reset-database-confirm-delete-all-data')
def reset_database():
    """Reset database - DELETE ALL MOOD DATA"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count existing data
            cursor.execute('SELECT COUNT(*) as count FROM moods')
            mood_result = cursor.fetchone()
            mood_count = mood_result['count'] if mood_result else 0
            
            cursor.execute('SELECT COUNT(*) as count FROM users')
            user_result = cursor.fetchone()
            user_count = user_result['count'] if user_result else 0
            
            # Delete all moods
            cursor.execute('DELETE FROM moods')
            deleted_count = cursor.rowcount
            
            # Reset sequence
            cursor.execute('ALTER SEQUENCE moods_id_seq RESTART WITH 1')
            
            return {
                'status': 'success',
                'message': 'Database reset completed',
                'deleted_moods': deleted_count,
                'remaining_users': user_count,
                'original_mood_count': mood_count,
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 500

@main_bp.route('/analytics-health')
@login_required
def analytics_health():
    """Analytics system health check"""
    try:
        mood_count = len(db.get_user_moods(current_user.id))
        return {'status': 'healthy', 'mood_count': mood_count}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}, 500

@main_bp.route('/fix-mood-dates')
@login_required
def fix_mood_dates():
    """Fix mood dates that were saved with wrong timezone"""
    try:
        from datetime import timedelta
        
        # Get all user moods
        moods = db.get_user_moods(current_user.id)
        print(f"DEBUG: Found {len(moods)} moods to potentially fix")
        
        fixed_count = 0
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            for mood in moods:
                mood_id = mood['id']
                current_date = mood['date']
                timestamp = mood['timestamp']
                
                # Check if this mood was likely saved with UTC timezone
                # (if timestamp hour suggests it was saved late at night Chile time)
                if hasattr(timestamp, 'hour'):
                    # If timestamp is between 00:00-05:59 UTC, it was likely saved 
                    # the previous day in Chile time (21:00-02:59 Chile time)
                    if 0 <= timestamp.hour <= 5:
                        # Shift date back by one day
                        corrected_date = current_date - timedelta(days=1)
                        
                        cursor.execute('''
                            UPDATE moods 
                            SET date = %s 
                            WHERE id = %s
                        ''', (corrected_date, mood_id))
                        
                        fixed_count += 1
                        print(f"DEBUG: Fixed mood {mood_id}: {current_date} -> {corrected_date}")
        
        return jsonify({
            'success': True,
            'message': f'Fixed {fixed_count} mood dates',
            'total_moods': len(moods),
            'fixed_count': fixed_count
        })
        
    except Exception as e:
        import traceback
        print(f"DEBUG: Error fixing mood dates: {e}")
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
@main_bp.route('/add-fake-data')
@login_required
def add_fake_data():
    """Add fake mood data for current week for testing"""
    try:
        import random
        from datetime import datetime, date, timedelta
        
        # Get current week dates (Sunday to Saturday)
        timezone_service = container.get_timezone_service()
        today = timezone_service.get_chile_date()
        
        # Find Sunday of current week (start of week)
        days_since_sunday = today.weekday() + 1  # Monday=0, so Sunday=6, adjust to Sunday=0
        if days_since_sunday == 7:  # If today is Sunday
            days_since_sunday = 0
        
        week_start = today - timedelta(days=days_since_sunday)
        
        moods = ['very bad', 'bad', 'slightly bad', 'neutral', 'slightly well', 'well', 'very well']
        notes_options = ['', 'feeling good', 'rough day', 'work stress', 'relaxing', 'productive', 'tired']
        
        added_count = 0
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Add mood entries for each day of the current week
            for day_offset in range(7):  # Sunday to Saturday
                current_date = week_start + timedelta(days=day_offset)
                
                # Add 3-8 random moods per day
                moods_per_day = random.randint(3, 8)
                
                for _ in range(moods_per_day):
                    # Random hour between 6 AM and 11 PM
                    hour = random.randint(6, 23)
                    minute = random.randint(0, 59)
                    
                    # Create timestamp for the specific date
                    fake_timestamp = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute)
                    
                    # Random mood and notes
                    mood = random.choice(moods)
                    notes = random.choice(notes_options)
                    
                    cursor.execute('''
                        INSERT INTO moods (user_id, date, mood, notes, timestamp)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (current_user.id, current_date, mood, notes, fake_timestamp))
                    
                    added_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Added {added_count} fake mood entries for current week',
            'week_start': week_start.isoformat(),
            'week_end': (week_start + timedelta(days=6)).isoformat(),
            'added_count': added_count
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
@main_bp.route('/admin/cleanup-until-oct19')
@login_required
def cleanup_until_oct19():
    """Admin endpoint to delete mood data until October 19, 2025"""
    from datetime import date
    
    target_date = date(2025, 10, 19)
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count records first
            cursor.execute('SELECT COUNT(*) FROM moods WHERE date <= %s', (target_date,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                return jsonify({
                    'success': True,
                    'message': 'No records to delete',
                    'deleted': 0,
                    'remaining': 0
                })
            
            # Delete mood entries until target date
            cursor.execute('DELETE FROM moods WHERE date <= %s', (target_date,))
            deleted_moods = cursor.rowcount
            
            conn.commit()
            
            # Get remaining count
            cursor.execute('SELECT COUNT(*) FROM moods')
            remaining = cursor.fetchone()[0]
            
            return jsonify({
                'success': True,
                'message': f'Successfully deleted {deleted_moods} mood entries until {target_date}',
                'deleted': deleted_moods,
                'remaining': remaining,
                'target_date': str(target_date)
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
