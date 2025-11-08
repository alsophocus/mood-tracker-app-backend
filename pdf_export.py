import io
import tempfile
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.units import inch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analytics import MoodAnalytics, MOOD_VALUES

class PDFExporter:
    def __init__(self, user, moods):
        self.user = user
        self.moods = moods
        self.analytics = MoodAnalytics(moods)
    
    def generate_report(self):
        """Generate comprehensive PDF report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        story = []
        story.extend(self._create_header())
        story.extend(self._create_summary())
        story.extend(self._create_charts())
        story.extend(self._create_recent_history())
        story.extend(self._create_footer())
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _create_header(self):
        """Create PDF header"""
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=HexColor('#1e293b'),
            alignment=1
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            textColor=HexColor('#374151')
        )
        
        return [
            Paragraph("🌈 Mood Tracker Report", title_style),
            Paragraph(f"<b>User:</b> {self.user.name}<br/><b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %H:%M')}", body_style),
            Spacer(1, 20)
        ]
    
    def _create_summary(self):
        """Create summary section"""
        if not self.moods:
            return [Paragraph("No mood data available yet.", self._get_body_style())]
        
        summary = self.analytics.get_summary()
        
        summary_text = f"""
        <b>Total Mood Entries:</b> {summary['total_entries']}<br/>
        <b>Current Good Mood Streak:</b> {summary['current_streak']} days<br/>
        <b>Best Day of Week:</b> {summary['best_day']}<br/>
        <b>Overall Average Mood:</b> {summary['daily_average']:.2f}/7.0
        """
        
        return [
            Paragraph("📊 Summary", self._get_heading_style()),
            Paragraph(summary_text, self._get_body_style()),
            Spacer(1, 20)
        ]
    
    def _create_charts(self):
        """Create and embed charts"""
        if not self.moods:
            return []
        
        story = []
        
        # Mood distribution chart
        distribution_chart_path = self._create_mood_distribution_chart()
        if distribution_chart_path:
            story.extend([
                Paragraph("🎯 Mood Distribution (Last 30 Days)", self._get_heading_style()),
                Image(distribution_chart_path, width=6*inch, height=4*inch),
                Spacer(1, 20)
            ])
        
        # Weekly patterns chart
        weekly_chart_path = self._create_weekly_chart()
        if weekly_chart_path:
            story.extend([
                Paragraph("📅 Weekly Patterns", self._get_heading_style()),
                Image(weekly_chart_path, width=6*inch, height=3*inch),
                Spacer(1, 20)
            ])
        
        # Monthly trends chart
        monthly_chart_path = self._create_monthly_chart()
        if monthly_chart_path:
            story.extend([
                Paragraph("📈 Monthly Trends", self._get_heading_style()),
                Image(monthly_chart_path, width=6*inch, height=3*inch),
                Spacer(1, 20)
            ])
        
        # Daily patterns chart
        daily_chart_path = self._create_daily_patterns_chart()
        if daily_chart_path:
            story.extend([
                Paragraph("🕐 Daily Patterns", self._get_heading_style()),
                Image(daily_chart_path, width=6*inch, height=3*inch),
                Spacer(1, 20)
            ])
        
        return story
    
    def _create_mood_distribution_chart(self):
        """Create mood distribution pie chart"""
        try:
            from datetime import datetime, timedelta
            from collections import Counter
            
            # Get last 30 days of moods
            thirty_days_ago = datetime.now().date() - timedelta(days=30)
            recent_moods = [mood for mood in self.moods if mood['date'] >= thirty_days_ago]
            
            if not recent_moods:
                return None
            
            # Count mood occurrences
            mood_counts = Counter(mood['mood'] for mood in recent_moods)
            
            # Define colors for each mood
            mood_colors = {
                'very bad': '#dc2626',
                'bad': '#ff5722', 
                'slightly bad': '#ff9800',
                'neutral': '#6b7280',
                'slightly well': '#8bc34a',
                'well': '#4caf50',
                'very well': '#7d5260'
            }
            
            # Prepare data
            moods = list(mood_counts.keys())
            counts = list(mood_counts.values())
            colors = [mood_colors.get(mood, '#6b7280') for mood in moods]
            
            # Create pie chart
            fig, ax = plt.subplots(figsize=(8, 6), facecolor='white')
            wedges, texts, autotexts = ax.pie(counts, labels=[mood.title() for mood in moods], 
                                            colors=colors, autopct='%1.1f%%', startangle=90,
                                            textprops={'fontsize': 10})
            
            # Style the chart
            ax.set_title('Mood Distribution (Last 30 Days)', fontsize=14, fontweight='bold', 
                        color='#1e293b', pad=20)
            
            # Make percentage text bold and white
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(9)
            
            plt.tight_layout()
            
            chart_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            plt.savefig(chart_file.name, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            return chart_file.name
        except Exception:
            return None
    
    def _create_weekly_chart(self):
        """Create weekly patterns chart"""
        try:
            weekly_data = self.analytics.get_weekly_patterns()
            
            fig, ax = plt.subplots(figsize=(8, 4), facecolor='white')
            ax.plot(weekly_data['labels'], weekly_data['data'], marker='o', linewidth=3, 
                   markersize=8, color='#f59e0b', markerfacecolor='#f59e0b', 
                   markeredgecolor='white', markeredgewidth=2)
            ax.fill_between(weekly_data['labels'], weekly_data['data'], alpha=0.3, color='#f59e0b')
            ax.set_ylim(1, 7)
            ax.set_ylabel('Average Mood', fontsize=12, color='#374151')
            ax.set_title('Weekly Patterns', fontsize=14, fontweight='bold', color='#1e293b', pad=20)
            ax.grid(True, alpha=0.3)
            ax.set_facecolor('#f8fafc')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            chart_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            plt.savefig(chart_file.name, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            return chart_file.name
        except Exception:
            return None
    
    def _create_monthly_chart(self):
        """Create monthly trends chart"""
        try:
            monthly_data = self.analytics.get_monthly_trends()
            if not monthly_data:
                return None
            
            months = [item['month'] for item in monthly_data[-12:]]  # Last 12 months
            values = [item['mood'] for item in monthly_data[-12:]]
            
            fig, ax = plt.subplots(figsize=(8, 4), facecolor='white')
            ax.plot(months, values, marker='o', linewidth=3, markersize=8,
                   color='#3b82f6', markerfacecolor='#3b82f6', 
                   markeredgecolor='white', markeredgewidth=2)
            ax.fill_between(months, values, alpha=0.3, color='#3b82f6')
            ax.set_ylim(1, 7)
            ax.set_ylabel('Average Mood', fontsize=12, color='#374151')
            ax.set_title('Monthly Trends', fontsize=14, fontweight='bold', color='#1e293b', pad=20)
            ax.grid(True, alpha=0.3)
            ax.set_facecolor('#f8fafc')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            chart_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            plt.savefig(chart_file.name, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            return chart_file.name
        except Exception:
            return None
    
    def _create_daily_patterns_chart(self):
        """Create daily patterns (hourly) chart"""
        try:
            daily_data = self.analytics.get_daily_patterns()
            
            fig, ax = plt.subplots(figsize=(8, 4), facecolor='white')
            ax.plot(daily_data['labels'], daily_data['data'], marker='o', linewidth=3, 
                   markersize=6, color='#8b5cf6', markerfacecolor='#8b5cf6', 
                   markeredgecolor='white', markeredgewidth=2)
            ax.fill_between(daily_data['labels'], daily_data['data'], alpha=0.3, color='#8b5cf6')
            ax.set_ylim(1, 7)
            ax.set_ylabel('Average Mood', fontsize=12, color='#374151')
            ax.set_xlabel('Hour of Day', fontsize=12, color='#374151')
            ax.set_title('Daily Patterns (Average Mood by Hour)', fontsize=14, fontweight='bold', color='#1e293b', pad=20)
            ax.grid(True, alpha=0.3)
            ax.set_facecolor('#f8fafc')
            plt.xticks(range(0, 24, 2))  # Show every 2 hours
            plt.tight_layout()
            
            chart_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            plt.savefig(chart_file.name, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            return chart_file.name
        except Exception:
            return None
    
    def _create_recent_history(self):
        """Create recent mood history section"""
        if not self.moods:
            return []
        
        story = [Paragraph("📝 Recent Mood History", self._get_heading_style())]
        
        mood_emoji = {
            'very bad': '😭', 'bad': '😢', 'slightly bad': '😔', 'neutral': '😐',
            'slightly well': '🙂', 'well': '😊', 'very well': '😄'
        }
        
        for mood_entry in self.moods[:15]:  # Last 15 entries
            date_str = str(mood_entry['date'])
            mood = mood_entry['mood']
            notes = mood_entry.get('notes', '')
            
            entry_text = f"<b>{date_str}</b> {mood_emoji.get(mood, '😐')} {mood.title()}"
            
            if notes:
                notes_text = notes[:100] + "..." if len(notes) > 100 else notes
                entry_text += f"<br/><i>Notes: {notes_text}</i>"
            
            story.extend([
                Paragraph(entry_text, self._get_body_style()),
                Spacer(1, 8)
            ])
        
        return story
    
    def _create_footer(self):
        """Create PDF footer"""
        footer_style = ParagraphStyle(
            'Footer',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=9,
            textColor=HexColor('#6b7280'),
            alignment=1
        )
        
        return [
            Spacer(1, 30),
            Paragraph(f"Generated by Mood Tracker • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style)
        ]
    
    def _get_heading_style(self):
        """Get heading paragraph style"""
        return ParagraphStyle(
            'CustomHeading',
            parent=getSampleStyleSheet()['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=HexColor('#3b82f6'),
            borderWidth=1,
            borderColor=HexColor('#e2e8f0'),
            borderPadding=8,
            backColor=HexColor('#f8fafc')
        )
    
    def _get_body_style(self):
        """Get body paragraph style"""
        return ParagraphStyle(
            'CustomBody',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=11,
            spaceAfter=6,
            textColor=HexColor('#374151')
        )
