
"""
Per-User Program Tracker
Tracks programs and time usage for each user
"""

import json
import time
import threading
from datetime import datetime
from collections import defaultdict

class UserProgramTracker:
    def __init__(self):
        self.user_sessions = {}
        self.tracking_threads = {}
        
    def start_user_tracking(self, email, task_name="general"):
        """Start tracking programs for a specific user"""
        user_key = f"{email}|{task_name}"
        
        if task_name in ["-- İş Emri Seçin --", "-- Select a Task --", "--_İş_Emri_Seçin_--"]:
            task_name = "general"
            user_key = f"{email}|{task_name}"
        
        if user_key in self.user_sessions:
            print(f"User {email} already being tracked for task: {task_name}")
            return
        
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
        
        thread = threading.Thread(
            target=self._user_tracking_loop, 
            args=(user_key,), 
            daemon=True
        )
        self.tracking_threads[user_key] = thread
        thread.start()
        
        print(f"Started program tracking for {email} - {task_name}")
    
    def stop_user_tracking(self, email, task_name="general"):
        """Stop tracking programs for a specific user"""
        if task_name in ["-- İş Emri Seçin --", "-- Select a Task --", "--_İş_Emri_Seçin_--"]:
            task_name = "general"
            
        user_key = f"{email}|{task_name}"
        
        if user_key not in self.user_sessions:
            print(f"No tracking session found for {email} - {task_name}")
            return None
        
        self.user_sessions[user_key]['tracking_active'] = False
        self.user_sessions[user_key]['session_end'] = datetime.now().isoformat()
        
        final_report = self._generate_user_report(user_key)
        
        print(f"Uploading final session data to S3...")
        self._upload_program_data_to_s3(user_key)
        
        if user_key in self.tracking_threads:
            del self.tracking_threads[user_key]
        del self.user_sessions[user_key]
        
        print(f"Stopped program tracking for {email} - {task_name}")
        return final_report
    
    def stop_all_tracking(self):
        """Stop all active tracking sessions"""
        active_sessions = list(self.user_sessions.keys())
        print(f"Stopping {len(active_sessions)} active tracking sessions...")
        
        for user_key in active_sessions:
            session = self.user_sessions[user_key]
            email = session['email']
            task_name = session['task_name']
            self.stop_user_tracking(email, task_name)
    
    def _user_tracking_loop(self, user_key):
        """Main tracking loop for a specific user"""
        capture_interval = 10
        session = self.user_sessions[user_key]
        
        print(f"Starting tracking loop for {user_key}")
        
        while session.get('tracking_active', False):
            try:
                current_time = time.time()
                
                if current_time - session['last_capture'] >= capture_interval:
                    self._capture_user_program_data(user_key)
                    session['last_capture'] = current_time
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error in user tracking loop for {user_key}: {e}")
                time.sleep(5)
    
    def _capture_user_program_data(self, user_key):
        """Capture current program data for user"""
        session = self.user_sessions[user_key]
        
        try:
            from .active_window_tracker import get_tracker, start_active_window_tracking
            
            tracker = get_tracker()
            if not tracker.tracking:
                start_active_window_tracking()
            
            summary = tracker.get_session_summary()
            
            if summary.get('applications'):
                for app in summary['applications']:
                    process_name = app['process_name']
                    session['program_data'][process_name]['total_time'] = app['total_time_seconds']
                    if app.get('window_title'):
                        session['program_data'][process_name]['window_titles'].add(app['window_title'])
            
        except Exception as e:
            print(f"Error capturing program data for {user_key}: {e}")
    
    def _upload_program_data_to_s3(self, user_key):
        """Upload current program tracking data to S3"""
        session = self.user_sessions[user_key]
        
        try:
            tracking_data = self._generate_user_report(user_key)
            
            from .s3_uploader import upload_program_tracking_to_s3
            result_url = upload_program_tracking_to_s3(
                session['email'], 
                tracking_data, 
                session['task_name']
            )
            
            if result_url:
                print(f"Program tracking data uploaded: {result_url}")
                
        except Exception as e:
            print(f"Error uploading program data to S3: {e}")
    
    def _generate_user_report(self, user_key):
        """Generate program tracking report for user"""
        session = self.user_sessions[user_key]
        
        start_time = datetime.fromisoformat(session['session_start'])
        end_time = datetime.now()
        session_duration = (end_time - start_time).total_seconds()
        
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
    """Start program tracking for a user"""
    tracker = get_user_program_tracker()
    tracker.start_user_tracking(email, task_name)
    return tracker

def stop_user_program_tracking(email, task_name="general"):
    """Stop program tracking for a user"""
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