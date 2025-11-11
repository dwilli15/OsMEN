#!/usr/bin/env python3
"""
Focus Guardrails Agent
Maintains focus and productivity by enforcing guardrails
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FocusGuardrailsAgent:
    """Agent for focus and productivity guardrails"""
    
    def __init__(self):
        try:
            self.simplewall_path = os.getenv('SIMPLEWALL_PATH', 'C:\\Program Files\\simplewall')
            self.focus_sessions = []
            self.blocked_sites = []
            logger.info("FocusGuardrailsAgent initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing FocusGuardrailsAgent: {e}")
            raise
        
    def start_focus_session(self, duration_minutes: int = 25) -> Dict:
        """Start a timed focus session (Pomodoro-style)"""
        try:
            session = {
                'start_time': datetime.now().isoformat(),
                'duration_minutes': duration_minutes,
                'end_time': (datetime.now() + timedelta(minutes=duration_minutes)).isoformat(),
                'status': 'active'
            }
            self.focus_sessions.append(session)
            
            # Apply focus guardrails
            self._apply_focus_rules()
            
            logger.info(f"Focus session started for {duration_minutes} minutes")
            return session
        except Exception as e:
            logger.error(f"Error starting focus session: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to start focus session'
            }
    
    def end_focus_session(self) -> Dict:
        """End the current focus session"""
        try:
            if not self.focus_sessions:
                logger.warning("Attempted to end focus session with no active sessions")
                return {'status': 'no_active_session'}
            
            current_session = self.focus_sessions[-1]
            
            # Check if session is already completed
            if current_session.get('status') == 'completed':
                logger.warning("Attempted to end already completed session")
                return {'status': 'no_active_session'}
            
            current_session['status'] = 'completed'
            current_session['actual_end_time'] = datetime.now().isoformat()
            
            # Remove focus guardrails
            self._remove_focus_rules()
            
            logger.info("Focus session ended successfully")
            return current_session
        except Exception as e:
            logger.error(f"Error ending focus session: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to end focus session'
            }
    
    def block_distracting_sites(self, sites: List[str]) -> Dict:
        """Block distracting websites"""
        try:
            results = {
                'blocked': [],
                'status': 'success'
            }
            
            for site in sites:
                # This would integrate with Simplewall to block sites
                self.blocked_sites.append(site)
                results['blocked'].append(site)
            
            logger.info(f"Blocked {len(sites)} distracting sites")
            return results
        except Exception as e:
            logger.error(f"Error blocking sites: {e}")
            return {
                'blocked': [],
                'status': 'error',
                'error': str(e),
                'message': 'Failed to block some or all sites'
            }
    
    def unblock_sites(self, sites: Optional[List[str]] = None) -> Dict:
        """Unblock websites"""
        try:
            if sites is None:
                sites = self.blocked_sites.copy()
                
            results = {
                'unblocked': [],
                'status': 'success'
            }
            
            for site in sites:
                if site in self.blocked_sites:
                    self.blocked_sites.remove(site)
                    results['unblocked'].append(site)
            
            logger.info(f"Unblocked {len(results['unblocked'])} sites")
            return results
        except Exception as e:
            logger.error(f"Error unblocking sites: {e}")
            return {
                'unblocked': [],
                'status': 'error',
                'error': str(e),
                'message': 'Failed to unblock some or all sites'
            }
    
    def monitor_app_usage(self) -> Dict:
        """Monitor application usage"""
        usage = {
            'monitored_apps': [],
            'usage_stats': {},
            'alerts': []
        }
        
        # This would integrate with system monitoring
        # Example: Track time spent in different applications
        
        return usage
    
    def get_focus_report(self) -> Dict:
        """Generate focus and productivity report"""
        report = {
            'total_sessions': len(self.focus_sessions),
            'completed_sessions': sum(1 for s in self.focus_sessions if s['status'] == 'completed'),
            'active_session': self.focus_sessions[-1] if self.focus_sessions else None,
            'blocked_sites': self.blocked_sites,
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def _apply_focus_rules(self):
        """Apply focus-time restrictions"""
        # Common distracting sites to block during focus
        default_blocks = [
            'facebook.com',
            'twitter.com',
            'reddit.com',
            'youtube.com',
            'instagram.com'
        ]
        self.block_distracting_sites(default_blocks)
    
    def _remove_focus_rules(self):
        """Remove focus-time restrictions"""
        self.unblock_sites()
    
    def send_focus_reminder(self, message: str) -> Dict:
        """Send a focus reminder notification"""
        reminder = {
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'sent': True
        }
        
        # This would integrate with notification system
        return reminder


def main():
    """Main entry point for the agent"""
    agent = FocusGuardrailsAgent()
    
    # Start a focus session
    session = agent.start_focus_session(25)
    print("Focus Session Started:")
    print(json.dumps(session, indent=2))
    
    # Get report
    report = agent.get_focus_report()
    print("\nFocus Report:")
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
