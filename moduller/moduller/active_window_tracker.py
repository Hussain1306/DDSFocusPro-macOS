#!/usr/bin/env python3
"""
Active Window Tracker Module
Cross-platform: Windows (win32gui) + macOS (AppKit/NSWorkspace)
Tracks which application/program is currently active and logs time spent
"""

import time
import json
from datetime import datetime
import threading
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

try:
    import psutil
except ImportError:
    psutil = None

window_tracker = None

# Platform detection - try Windows first, then macOS
WIN32_AVAILABLE = False
APPKIT_AVAILABLE = False

try:
    import win32gui
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    pass

try:
    from AppKit import NSWorkspace, NSApplication
    APPKIT_AVAILABLE = True
except ImportError:
    pass


class ActiveWindowTracker:
    def __init__(self):
        self.current_window = None
        self.start_time = None
        self.tracking = False
        self.session_data = defaultdict(lambda: {
            'total_time': 0,
            'window_title': '',
            'process_name': '',
            'sessions': []
        })
        self.tracking_thread = None
        self.tracking_start_time = None

    def get_active_window_info(self):
        """Get currently active window/app info - cross-platform"""

        # === Windows: use win32gui ===
        if WIN32_AVAILABLE:
            try:
                hwnd = win32gui.GetForegroundWindow()
                if hwnd == 0:
                    return None, None, None
                window_title = win32gui.GetWindowText(hwnd)
                _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    process = psutil.Process(process_id) if psutil else None
                    process_name = process.name() if process else "Unknown"
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process_name = "Unknown"
                return window_title, process_name, process_id
            except Exception as e:
                print(f"Error getting active window (Windows): {e}")
                return None, None, None

        # === macOS: use AppKit NSWorkspace ===
        if APPKIT_AVAILABLE:
            try:
                ws = NSWorkspace.sharedWorkspace()
                front_app = ws.frontmostApplication()
                if not front_app:
                    return None, None, None
                app_name = front_app.localizedName()
                bundle_id = front_app.bundleIdentifier() or ""
                pid = front_app.processIdentifier()
                return app_name, app_name, pid  # macOS: title=app_name, process_name=app_name
            except Exception as e:
                print(f"Error getting active app (macOS): {e}")
                return None, None, None

        print("No window tracking available (install pywin32 for Windows or pyobjc for macOS)")
        return None, None, None

    def start_tracking(self):
        """Start tracking active windows"""
        if self.tracking:
            return
        self.tracking = True
        self.tracking_start_time = datetime.now()
        self.tracking_thread = threading.Thread(target=self._tracking_loop, daemon=True)
        self.tracking_thread.start()
        print("Active window tracking started")

    def stop_tracking(self):
        """Stop tracking active windows"""
        self.tracking = False
        if self.current_window and self.start_time:
            self._log_window_time()
        print("Active window tracking stopped")

    def _tracking_loop(self):
        while self.tracking:
            try:
                window_title, process_name, process_id = self.get_active_window_info()
                if window_title and process_name:
                    current_window_key = f"{process_name}|{window_title}"
                    if current_window_key != self.current_window:
                        if self.current_window and self.start_time:
                            self._log_window_time()
                        self.current_window = current_window_key
                        self.start_time = time.time()
                        self.session_data[current_window_key].update({
                            'window_title': window_title,
                            'process_name': process_name,
                            'process_id': process_id
                        })
                        print(f"Active window: {process_name} - {window_title[:50]}...")
                time.sleep(1)
            except Exception as e:
                print(f"Error in tracking loop: {e}")
                time.sleep(1)

    def _log_window_time(self):
        if not self.current_window or not self.start_time:
            return
        duration = time.time() - self.start_time
        self.session_data[self.current_window]['total_time'] += duration
        self.session_data[self.current_window]['sessions'].append({
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration': duration
        })

    def get_activity_export_data(self):
        self._log_window_time()
        activities = []
        total_duration = 0
        for window_key, data in self.session_data.items():
            if data['total_time'] > 0:
                total_duration += data['total_time']
                for session in data['sessions']:
                    activities.append({
                        'window_title': data['window_title'],
                        'process_name': data['process_name'],
                        'start_time': session['start_time'],
                        'end_time': session['end_time'],
                        'duration_seconds': session['duration'],
                        'duration_formatted': self._format_duration(session['duration'])
                    })
        return {
            'export_timestamp': datetime.now().isoformat(),
            'session_duration_seconds': total_duration,
            'session_duration_formatted': self._format_duration(total_duration),
            'total_applications': len([w for w in self.session_data.values() if w['total_time'] > 0]),
            'focus_time_tracking': True,
            'detailed_activities': activities,
            'tracking_started': self.tracking_start_time.isoformat() if self.tracking_start_time else None,
            'tracking_status': 'active' if self.tracking else 'stopped'
        }

    def get_session_summary(self):
        self._log_window_time()
        if self.current_window and self.start_time:
            self.start_time = time.time()
        program_totals = defaultdict(lambda: {'total_time': 0, 'window_titles': set(), 'sessions': []})
        total_time = 0
        for window_key, data in self.session_data.items():
            if data['total_time'] > 0:
                pn = data['process_name']
                program_totals[pn]['total_time'] += data['total_time']
                program_totals[pn]['window_titles'].add(data['window_title'])
                program_totals[pn]['sessions'].extend(data['sessions'])
                total_time += data['total_time']
        summary = []
        for pn, d in program_totals.items():
            if d['total_time'] > 0:
                summary.append({
                    'process_name': pn,
                    'window_title': list(d['window_titles'])[0] if d['window_titles'] else '',
                    'all_window_titles': list(d['window_titles']),
                    'total_time_seconds': round(d['total_time'], 2),
                    'total_time_formatted': self._format_duration(d['total_time']),
                    'session_count': len(d['sessions'])
                })
        summary.sort(key=lambda x: x['total_time_seconds'], reverse=True)
        return {
            'total_session_time': round(total_time, 2),
            'total_session_time_formatted': self._format_duration(total_time),
            'applications': summary,
            'tracking_active': self.tracking,
            'timestamp': datetime.now().isoformat()
        }

    def get_detailed_report(self):
        summary = self.get_session_summary()
        detailed = []
        for window_key, data in self.session_data.items():
            if data['total_time'] > 0:
                detailed.append({
                    'process_name': data['process_name'],
                    'window_title': data['window_title'],
                    'total_time_seconds': round(data['total_time'], 2),
                    'total_time_formatted': self._format_duration(data['total_time']),
                    'sessions': data['sessions']
                })
        detailed.sort(key=lambda x: x['total_time_seconds'], reverse=True)
        return {'summary': summary, 'detailed_applications': detailed}

    def _format_duration(self, seconds):
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m {int(seconds % 60)}s"

    def reset_session(self):
        self.session_data.clear()
        self.current_window = None
        self.start_time = None
        print("Session data reset")

_tracker_instance = None

def get_tracker():
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = ActiveWindowTracker()
    return _tracker_instance

def start_active_window_tracking():
    global window_tracker
    window_tracker = get_tracker()
    window_tracker.start_tracking()
    return window_tracker

def stop_active_window_tracking():
    global window_tracker
    if window_tracker:
        window_tracker.stop_tracking()
    return window_tracker

def upload_current_activity_to_s3(email, task_name="General_Activity"):
    global window_tracker
    if window_tracker is None:
        logger.warning("Activity tracker not initialized")
        return None
    try:
        activity_data = window_tracker.get_activity_export_data()
        from moduller.s3_uploader import upload_activity_data_direct
        s3_url = upload_activity_data_direct(activity_data, email, task_name)
        if s3_url:
            logger.info("Activity data uploaded to S3: %s", s3_url)
        return s3_url
    except Exception as e:
        logger.error("Error uploading activity data: %s", e)
        return None

def get_current_activity_summary():
    tracker = get_tracker()
    return tracker.get_session_summary()

def get_detailed_activity_report():
    tracker = get_tracker()
    return tracker.get_detailed_report()

if __name__ == "__main__":
    print("Testing Active Window Tracker")
    tracker = start_active_window_tracking()
    try:
        for i in range(30):
            time.sleep(1)
            if i % 5 == 0:
                summary = get_current_activity_summary()
                print(f"\nSummary (after {i+1}s):")
                for app in summary['applications'][:3]:
                    print(f"  {app['process_name']}: {app['total_time_formatted']}")
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        stop_active_window_tracking()
        final_report = get_detailed_activity_report()
        print(f"\nFinal Report:")
        print(f"Total: {final_report['summary']['total_session_time_formatted']}")
        for app in final_report['summary']['applications']:
            print(f"  {app['process_name']}: {app['total_time_formatted']}")
