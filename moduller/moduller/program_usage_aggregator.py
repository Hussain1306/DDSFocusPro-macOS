#!/usr/bin/env python3
"""
Program Usage Aggregator
Creates short, useful summaries of program usage with total time spent
"""

import json
import time
from datetime import datetime
from collections import defaultdict
from .active_window_tracker import get_current_activity_summary

class ProgramUsageAggregator:
    def __init__(self):
        self.program_totals = defaultdict(lambda: {
            'total_time': 0,
            'last_seen': None,
            'window_titles': set(),
            'browser_domains': set(),
            'is_browser': False
        })
        self.session_start = datetime.now()
        self.last_update = time.time()
    
    def update_program_usage(self):
        """Update program usage from active window tracker"""
        try:
            # Get current activity summary
            summary = get_current_activity_summary()
            current_time = datetime.now()
            
            # Clear old data to get fresh totals
            # Update program totals with current data from tracker
            for app in summary.get('applications', []):
                program_name = app['process_name']
                
                # Use the tracker's total time directly (it's already accumulated)
                self.program_totals[program_name]['total_time'] = app['total_time_seconds']
                self.program_totals[program_name]['last_seen'] = current_time.isoformat()
                
                # Add all window titles
                for title in app.get('all_window_titles', [app.get('window_title', '')]):
                    if title:
                        window_title = title[:100]  # Limit length
                        self.program_totals[program_name]['window_titles'].add(window_title)
                
                # Handle browser info
                browser_info = app.get('browser_info', {})
                if browser_info.get('is_browser'):
                    self.program_totals[program_name]['is_browser'] = True
                    if browser_info.get('domain'):
                        self.program_totals[program_name]['browser_domains'].add(browser_info['domain'])
                
                # Keep only last 3 window titles to avoid bloat
                if len(self.program_totals[program_name]['window_titles']) > 3:
                    titles_list = list(self.program_totals[program_name]['window_titles'])
                    self.program_totals[program_name]['window_titles'] = set(titles_list[-3:])
                
                # Keep only last 5 domains to avoid bloat
                if len(self.program_totals[program_name]['browser_domains']) > 5:
                    domains_list = list(self.program_totals[program_name]['browser_domains'])
                    self.program_totals[program_name]['browser_domains'] = set(domains_list[-5:])
            
            self.last_update = time.time()
            
        except Exception as e:
            print(f" Error updating program usage: {e}")
    
    def get_short_summary(self, min_time_seconds=1):
        """Get short, useful summary of program usage"""
        self.update_program_usage()
        
        # Filter programs with meaningful usage time
        active_programs = []
        total_session_time = 0
        
        for program_name, data in self.program_totals.items():
            if data['total_time'] >= min_time_seconds:
                # Convert sets to lists for JSON serialization
                program_entry = {
                    "program": program_name,
                    "total_time_seconds": round(data['total_time'], 1),
                    "time_formatted": self._format_duration(data['total_time']),
                    "window_titles": list(data['window_titles'])[:2],  # Only show 2 most recent
                    "is_browser": data['is_browser'],
                    "last_seen": data['last_seen']
                }
                
                # Add browser domains only if it's a browser
                if data['is_browser'] and data['browser_domains']:
                    program_entry["browser_domains"] = list(data['browser_domains'])[:3]  # Top 3 domains
                
                active_programs.append(program_entry)
                total_session_time += data['total_time']
        
        # Sort by time spent (descending)
        active_programs.sort(key=lambda x: x['total_time_seconds'], reverse=True)
        
        # Calculate session duration
        session_duration = (datetime.now() - self.session_start).total_seconds()
        
        return {
            "capture_time": datetime.now().isoformat(),
            "session_duration_seconds": round(session_duration, 1),
            "session_duration_formatted": self._format_duration(session_duration),
            "total_tracked_time_seconds": round(total_session_time, 1),
            "total_tracked_time_formatted": self._format_duration(total_session_time),
            "active_programs_count": len(active_programs),
            "programs": active_programs[:10]  # Top 10 programs only
        }
    
    def get_top_programs(self, top_n=5):
        """Get just the top N programs with time usage"""
        summary = self.get_short_summary()
        return {
            "capture_time": summary["capture_time"],
            "session_duration": summary["session_duration_formatted"], 
            "top_programs": summary["programs"][:top_n]
        }
    
    def _format_duration(self, seconds):
        """Format duration in human readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def reset_session(self):
        """Reset tracking for new session"""
        self.program_totals.clear()
        self.session_start = datetime.now()
        self.last_update = time.time()
        print(" Program usage aggregator reset")

# Global aggregator instance
_aggregator_instance = None

def get_program_aggregator():
    """Get global aggregator instance"""
    global _aggregator_instance
    if _aggregator_instance is None:
        _aggregator_instance = ProgramUsageAggregator()
    return _aggregator_instance

def get_short_program_summary():
    """Get short program usage summary"""
    aggregator = get_program_aggregator()
    return aggregator.get_short_summary()

def get_top_programs_only(top_n=5):
    """Get only top N programs"""
    aggregator = get_program_aggregator()
    return aggregator.get_top_programs(top_n)

if __name__ == "__main__":
    # Test the aggregator
    print("🧪 Testing Program Usage Aggregator")
    
    # Start window tracking first
    from .active_window_tracker import start_active_window_tracking
    start_active_window_tracking()
    
    aggregator = get_program_aggregator()
    
    try:
        # Test for 30 seconds
        for i in range(6):  # 6 x 5 seconds = 30 seconds
            time.sleep(5)
            
            if i % 2 == 0:  # Every 10 seconds
                summary = get_short_program_summary()
                print(f"\n Summary after {(i+1)*5}s:")
                print(f"Session: {summary['session_duration_formatted']}")
                print(f"Programs: {summary['active_programs_count']}")
                
                for program in summary['programs'][:3]:
                    print(f"  {program['program']}: {program['time_formatted']}")
                    if program.get('browser_domains'):
                        print(f"    Domains: {', '.join(program['browser_domains'])}")
    
    except KeyboardInterrupt:
        print("\n Stopping test...")
    
    print(f"\n Final Summary:")
    final_summary = get_top_programs_only(5)
    print(json.dumps(final_summary, indent=2))
