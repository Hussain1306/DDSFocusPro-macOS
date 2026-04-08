#!/usr/bin/env python3
"""
Per-User Program Tracker
Tracks programs and time usage for each user, following the same pattern as users_screenshots
Structure: logs/{date}/{email}/{task}/program_tracking_{timestamp}.json
"""

import json
import time
import threading
from datetime import datetime
from collections import defaultdict
from .active_window_tracker import get_tracker as get_window_tracker

class UserProgramTracker:
    def __init__(self):
        # Per-user tracking sessions
        self.user_sessions = {}
        self.tracking_threads = {}
        
    def start_user_tracking(self, email, task_name="general"):
        """Start tracking programs for a specific user"""
        user_key = f"{email}|{task_name}"
        
        # Skip the default task selection - use "general" instead
        if task_name in ["-- İş Emri Seçin --", "-- Select a Task --", "--_İş_Emri_Seçin_--"]:
            task_name = "general"
            user_key = f"{email}|{task_name}"
        
        if user_key in self.user_sessions:
            print(f" User {email} already being tracked for task: {task_name}")
            return
        
        # Initialize user session
        self.user_sessions[user_key] = {
            'email': email,
            'task_name': task_name,
            'session_start': datetime.now().isoformat(),
            'last_capture': time.time(),
            'program_data': defaultdict(lambda: {
                'total_time': 0,
                'last_time': 0,
                'sessions': [],
                'browser_domains': set(),
                'window_titles': set()
            }),
            'tracking_active': True
        }
        
        # Start tracking thread for this user
        thread = threading.Thread(
            target=self._user_tracking_loop, 
            args=(user_key,), 
            daemon=True
        )
        self.tracking_threads[user_key] = thread
        thread.start()
        
        print(f" Started program tracking for {email} - {task_name}")
    
    def stop_user_tracking(self, email, task_name="general"):
        """Stop tracking programs for a specific user"""
        # Skip the default task selection - use "general" instead
        if task_name in ["-- İş Emri Seçin --", "-- Select a Task --", "--_İş_Emri_Seçin_--"]:
            task_name = "general"
            
        user_key = f"{email}|{task_name}"
        
        if user_key not in self.user_sessions:
            print(f" No tracking session found for {email} - {task_name}")
            return None
        
        # Stop tracking
        self.user_sessions[user_key]['tracking_active'] = False
        self.user_sessions[user_key]['session_end'] = datetime.now().isoformat()
        
        # Generate final report
        final_report = self._generate_user_report(user_key)
        
        # Upload final report to S3 (only once per session)
        print(f" Uploading final session data to S3...")
        self._upload_program_data_to_s3(user_key)
        
        # Cleanup
        if user_key in self.tracking_threads:
            del self.tracking_threads[user_key]
        del self.user_sessions[user_key]
        
        print(f" Stopped program tracking for {email} - {task_name}")
        print(f" Final report uploaded to S3 with {final_report.get('programs_tracked', 0)} programs")
        return final_report
    
    def stop_all_tracking(self):
        """Stop all active tracking sessions"""
        active_sessions = list(self.user_sessions.keys())
        print(f" Stopping {len(active_sessions)} active tracking sessions...")
        
        for user_key in active_sessions:
            session = self.user_sessions[user_key]
            email = session['email']
            task_name = session['task_name']
            print(f" Stopping tracking for {email} - {task_name}")
            self.stop_user_tracking(email, task_name)
        
        print(" All tracking sessions stopped")
    
    def _user_tracking_loop(self, user_key):
        """Main tracking loop for a specific user"""
        capture_interval = 10  # Capture program data every 10 seconds (faster for testing)
        
        session = self.user_sessions[user_key]
        
        print(f" Starting tracking loop for {user_key}")
        
        while session.get('tracking_active', False):
            try:
                current_time = time.time()
                
                # Check if it's time to capture (every 10 seconds for testing)
                if current_time - session['last_capture'] >= capture_interval:
                    print(f"⏰ Time to capture data for {user_key}")
                    self._capture_user_program_data(user_key)
                    session['last_capture'] = current_time
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                print(f" Error in user tracking loop for {user_key}: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(5)
    
    def _capture_user_program_data(self, user_key):
        """Capture current program data for user (like taking a screenshot)"""
        session = self.user_sessions[user_key]
        
        try:
            # Make sure active window tracker is running first
            from .active_window_tracker import get_tracker, start_active_window_tracking
            
            # Start active window tracking if not already started
            tracker = get_tracker()
            if not tracker.tracking:
                start_active_window_tracking()
                print(" Started active window tracking for user session")
            
            # Get short, aggregated program summary using the new aggregator
            from .program_usage_aggregator import get_short_program_summary
            program_summary = get_short_program_summary()
            
            print(f" Capturing data for {user_key}, found {program_summary['active_programs_count']} active programs")
            
            if not program_summary.get('programs'):
                print(f" No active programs found")
                # Don't upload during session - only at the end
                return
            
            # Update session data with aggregated program information
            for program in program_summary['programs']:
                process_name = program['program']
                
                # Store the current total time (this comes from the aggregator)
                session['program_data'][process_name]['total_time'] = program['total_time_seconds']
                session['program_data'][process_name]['last_time'] = program['total_time_seconds']
                
                # Store recent window titles (limited to avoid bloat)
                if program.get('window_titles'):
                    for title in program['window_titles']:
                        session['program_data'][process_name]['window_titles'].add(title)
                
                # Store browser domains if available
                if program.get('browser_domains'):
                    for domain in program['browser_domains']:
                        session['program_data'][process_name]['browser_domains'].add(domain)
                
                print(f" {process_name}: {program['time_formatted']}")
            
            # DON'T upload during session - only upload when session ends
            print(f" Data updated for {user_key} (will upload when session ends)")
            
        except Exception as e:
            print(f" Error capturing program data for {user_key}: {e}")
            import traceback
            traceback.print_exc()
    
    def _upload_program_data_to_s3(self, user_key):
        """Upload current program tracking data to S3 (following screenshot pattern)"""
        session = self.user_sessions[user_key]
        
        try:
            # Create program tracking data (like screenshot data)
            tracking_data = self._generate_user_report(user_key)
            
            # Always upload, even if no programs tracked yet (for debugging)
            print(f" Uploading program data for {user_key}: {tracking_data['programs_tracked']} programs")
            
            # Upload to S3 using the same pattern as screenshots
            from moduller.s3_uploader import upload_program_tracking_to_s3
            result_url = upload_program_tracking_to_s3(
                session['email'], 
                tracking_data, 
                session['task_name']
            )
            
            if result_url:
                print(f" Program tracking data uploaded: {result_url}")
            else:
                print(f" Failed to upload program tracking data")
                
        except Exception as e:
            print(f" Error uploading program data to S3: {e}")
            import traceback
            traceback.print_exc()
    
    def _generate_user_report(self, user_key):
        """Generate program tracking report for user"""
        session = self.user_sessions[user_key]
        
        # Calculate session duration
        start_time = datetime.fromisoformat(session['session_start'])
        end_time = datetime.now()
        session_duration = (end_time - start_time).total_seconds()
        
        # Format program data
        programs = []
        for process_name, data in session['program_data'].items():
            program_entry = {
                'process_name': process_name,
                'total_time_seconds': round(data['total_time'], 2),
                'total_time_formatted': self._format_duration(data['total_time']),
                'window_titles': list(data['window_titles']),
                'browser_domains': list(data['browser_domains']) if data['browser_domains'] else None
            }
            programs.append(program_entry)
        
        # Sort by time spent (descending)
        programs.sort(key=lambda x: x['total_time_seconds'], reverse=True)
        
        return {
            'user_email': session['email'],
            'task_name': session['task_name'],
            'date': datetime.now().strftime("%Y-%m-%d"),
            'session_start': session['session_start'],
            'session_end': session.get('session_end', datetime.now().isoformat()),
            'session_duration_seconds': round(session_duration, 2),
            'session_duration_formatted': self._format_duration(session_duration),
            'programs_tracked': len(programs),
            'programs': programs,
            'capture_timestamp': datetime.now().isoformat()
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
            secs = int(seconds % 60)
            return f"{hours}h {minutes}m {secs}s"
    
    def get_user_current_data(self, email, task_name="general"):
        """Get current tracking data for a user"""
        # Skip the default task selection - use "general" instead
        if task_name in ["-- İş Emri Seçin --", "-- Select a Task --", "--_İş_Emri_Seçin_--"]:
            task_name = "general"
            
        user_key = f"{email}|{task_name}"
        
        if user_key not in self.user_sessions:
            return None
        
        return self._generate_user_report(user_key)

# Global tracker instance
_user_program_tracker = None

def get_user_program_tracker():
    """Get global user program tracker instance"""
    global _user_program_tracker
    if _user_program_tracker is None:
        _user_program_tracker = UserProgramTracker()
    return _user_program_tracker

def start_user_program_tracking(email, task_name="general"):
    """Start program tracking for a user (like starting screenshot capture)"""
    tracker = get_user_program_tracker()
    tracker.start_user_tracking(email, task_name)
    return tracker

def stop_user_program_tracking(email, task_name="general"):
    """Stop program tracking for a user (like stopping screenshot capture)"""
    tracker = get_user_program_tracker()
    return tracker.stop_user_tracking(email, task_name)

def get_user_program_data(email, task_name="general"):
    """Get current program tracking data for a user"""
    tracker = get_user_program_tracker()
    return tracker.get_user_current_data(email, task_name)

def stop_all_user_tracking():
    """Stop all active user tracking sessions"""
    tracker = get_user_program_tracker()
    tracker.stop_all_tracking()

if __name__ == "__main__":
    # Test the user program tracker
    print("🧪 Testing User Program Tracker")
    
    # Start tracking for test user
    test_email = "test@example.com"
    test_task = "Development"
    
    tracker = start_user_program_tracking(test_email, test_task)
    
    try:
        # Track for 60 seconds
        for i in range(12):  # 12 x 5 seconds = 60 seconds
            time.sleep(5)
            data = get_user_program_data(test_email, test_task)
            if data and data['programs']:
                print(f"\n Update {i+1}/12:")
                for program in data['programs'][:3]:  # Top 3
                    print(f"  {program['process_name']}: {program['total_time_formatted']}")
    
    except KeyboardInterrupt:
        print("\n Stopping tracker...")
    
    finally:
        final_report = stop_user_program_tracking(test_email, test_task)
        if final_report:
            print(f"\n Final Report for {test_email}:")
            print(f"Session duration: {final_report['session_duration_formatted']}")
            print(f"Programs tracked: {final_report['programs_tracked']}")
            for program in final_report['programs']:
                print(f"  {program['process_name']}: {program['total_time_formatted']}")
