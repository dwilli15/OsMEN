"""
Daily Digest Generation and Management Module

Aggregates daily activities, analyzes patterns, and generates insights.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors


class DigestGenerator:
    def __init__(self, data_dir: str = '.copilot'):
        self.data_dir = data_dir
        self.feedback_file = os.path.join(data_dir, 'daily_feedback.json')
        
    def get_digest_data(self, date: str = None) -> Dict[str, Any]:
        """Generate digest data for a specific date."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
            
        # Aggregate data from various sources
        activities = self._get_activities(date)
        task_stats = self._get_task_statistics(date)
        procrastination = self._get_procrastination_insights(date)
        health = self._get_health_correlations(date)
        feedback = self._get_feedback(date)
        
        return {
            'date': date,
            'activities': activities,
            'task_statistics': task_stats,
            'procrastination_insights': procrastination,
            'health_correlations': health,
            'feedback': feedback,
            'generated_at': datetime.now().isoformat()
        }
    
    def _get_activities(self, date: str) -> List[Dict[str, Any]]:
        """Get chronological activity timeline."""
        # Mock data - in production, aggregate from memory system
        return [
            {'time': '09:00', 'type': 'task_completed', 'description': 'Completed homework assignment', 'status': 'success'},
            {'time': '11:30', 'type': 'reminder', 'description': 'Reminder sent for exam preparation', 'status': 'sent'},
            {'time': '14:00', 'type': 'study_session', 'description': 'Study session: 50 min deep focus', 'status': 'completed'},
            {'time': '16:30', 'type': 'calendar_sync', 'description': 'Synced to Google Calendar', 'status': 'success'},
        ]
    
    def _get_task_statistics(self, date: str) -> Dict[str, Any]:
        """Get task completion statistics."""
        return {
            'completed': 8,
            'pending': 3,
            'overdue': 1,
            'completion_rate': 0.73,
            'on_time': 7,
            'late': 1,
            'by_type': {
                'homework': 4,
                'exam_prep': 2,
                'reading': 2
            },
            'by_priority': {
                'critical': 1,
                'high': 3,
                'medium': 4
            },
            'effort_accuracy': 0.85
        }
    
    def _get_procrastination_insights(self, date: str) -> Dict[str, Any]:
        """Get procrastination pattern insights."""
        return {
            'avg_days_before_due': 2.3,
            'procrastination_score': 0.42,
            'trend': 'improving',
            'by_task_type': {
                'homework': 1.8,
                'exam_prep': 3.5,
                'reading': 2.1
            },
            'suggestions': [
                'Start exam prep earlier (currently avg 3.5 days before)',
                'Morning energy levels are highest - schedule difficult tasks then'
            ]
        }
    
    def _get_health_correlations(self, date: str) -> Dict[str, Any]:
        """Get health-productivity correlations."""
        return {
            'sleep_impact': {
                'hours': 7.2,
                'quality': 'good',
                'productivity_correlation': 0.78,
                'impact': 'positive'
            },
            'energy_patterns': {
                'morning': 0.85,
                'afternoon': 0.65,
                'evening': 0.50,
                'night': 0.30,
                'peak_time': 'morning'
            },
            'location_productivity': {
                'library': 0.90,
                'home': 0.70,
                'campus': 0.75,
                'cafe': 0.60,
                'best_location': 'library'
            }
        }
    
    def _get_feedback(self, date: str) -> Dict[str, Any]:
        """Get manual feedback for the date."""
        if not os.path.exists(self.feedback_file):
            return None
            
        try:
            with open(self.feedback_file, 'r') as f:
                all_feedback = json.load(f)
                return all_feedback.get(date)
        except:
            return None
    
    def save_feedback(self, date: str, feedback: Dict[str, Any]) -> bool:
        """Save daily feedback."""
        try:
            all_feedback = {}
            if os.path.exists(self.feedback_file):
                with open(self.feedback_file, 'r') as f:
                    all_feedback = json.load(f)
            
            all_feedback[date] = {
                **feedback,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.feedback_file, 'w') as f:
                json.dump(all_feedback, f, indent=2)
            
            return True
        except Exception as e:
            print(f'Error saving feedback: {e}')
            return False
    
    def export_pdf(self, date: str, output_path: str) -> bool:
        """Export digest as PDF."""
        try:
            data = self.get_digest_data(date)
            
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title = Paragraph(f"<b>Daily Digest - {date}</b>", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 0.3*inch))
            
            # Task Statistics
            story.append(Paragraph("<b>Task Statistics</b>", styles['Heading2']))
            stats = data['task_statistics']
            stats_data = [
                ['Completed', str(stats['completed'])],
                ['Pending', str(stats['pending'])],
                ['Overdue', str(stats['overdue'])],
                ['Completion Rate', f"{stats['completion_rate']*100:.1f}%"],
            ]
            stats_table = Table(stats_data)
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(stats_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Health Correlations
            story.append(Paragraph("<b>Health Insights</b>", styles['Heading2']))
            health = data['health_correlations']
            health_text = f"""
            Sleep: {health['sleep_impact']['hours']} hours ({health['sleep_impact']['quality']})<br/>
            Peak Energy: {health['energy_patterns']['peak_time'].title()}<br/>
            Best Location: {health['location_productivity']['best_location'].title()}
            """
            story.append(Paragraph(health_text, styles['BodyText']))
            story.append(Spacer(1, 0.3*inch))
            
            # Feedback
            if data['feedback']:
                story.append(Paragraph("<b>Daily Reflection</b>", styles['Heading2']))
                fb = data['feedback']
                feedback_text = f"""
                Mood: {fb.get('mood', 'N/A')}/5<br/>
                Productivity: {fb.get('productivity', 'N/A')}/5<br/>
                Challenges: {fb.get('challenges', 'None noted')}<br/>
                Wins: {fb.get('wins', 'None noted')}
                """
                story.append(Paragraph(feedback_text, styles['BodyText']))
            
            doc.build(story)
            return True
        except Exception as e:
            print(f'Error exporting PDF: {e}')
            return False
    
    def export_json(self, date: str, output_path: str) -> bool:
        """Export digest as JSON."""
        try:
            data = self.get_digest_data(date)
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f'Error exporting JSON: {e}')
            return False
