import sys
import time
import threading
import requests
import os
import json

IDLE_THRESHOLD = 180  # seconds (3 minutes)

def get_idle_duration():
    """Get system-wide idle time. Windows (GetLastInputInfo) or macOS/Linux (IOKit)."""
    # === Windows: use ctypes Win32 API ===
    try:
        import ctypes
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [('cbSize', ctypes.c_uint), ('dwTime', ctypes.c_uint)]
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        return millis / 1000.0
    except Exception:
        pass

    # === macOS/Linux: use IOKit via subprocess ===
    try:
        import subprocess
        result = subprocess.run(
            ["sh", "-c", "ioreg -c IOHIDSystem -a 2>/dev/null || echo ''"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0 and result.stdout.strip():
            import plistlib
            data = plistlib.loads(result.stdout.encode())
            idle_nanos = data.get("HIDIdleTime", 0)
            return idle_nanos / 1_000_000_000
    except Exception:
        pass

    # === macOS fallback: AppKit NSEvent ===
    try:
        from AppKit import NSEvent
        return NSEvent.systemUptime()
    except ImportError:
        pass

    return 0  # Assume active on failure

def start_idle_monitor(flask_server_url, email, staff_id, task_id):
    def monitor():
        # Track the baseline idle time when monitoring starts
        # This allows us to detect NEW idle time accumulated during this session
        baseline_idle_time = get_idle_duration()
        print(f"🔍 Starting idle monitor - baseline idle time: {baseline_idle_time:.1f}s")
        
        while True:
            # Before checking idle, verify the session is still the same and not a meeting.
            session_file = os.path.join(os.getcwd(), 'data', 'current_session.json')
            try:
                if os.path.exists(session_file):
                    with open(session_file, 'r', encoding='utf-8') as sf:
                        current = json.load(sf)
                    # If task_id changed or session became a meeting, stop this monitor
                    if str(current.get('task_id')) != str(task_id) or current.get('is_meeting'):
                        print(" Idle monitor: session changed or is a meeting — stopping monitor.")
                        break
                else:
                    # Session file deleted = session already ended
                    print(" Idle monitor: session file gone — stopping monitor.")
                    break
            except Exception as e:
                print(f" Idle monitor: failed to read session file: {e}")

            current_idle_time = get_idle_duration()
            
            # Calculate idle time accumulated during THIS monitoring session
            # If current idle time is less than baseline, user was active (reset baseline)
            if current_idle_time < baseline_idle_time:
                baseline_idle_time = current_idle_time
                print(f"✅ Activity detected - resetting baseline to {baseline_idle_time:.1f}s")
            
            # Only consider idle time accumulated since work started
            session_idle_time = current_idle_time - baseline_idle_time
            
            if session_idle_time >= IDLE_THRESHOLD:
                print(f"💤 System idle for {int(session_idle_time)} seconds (threshold: {IDLE_THRESHOLD}). Triggering auto-pause...")

                try:
                    # ✅ FIX: Only set the idle flag — let the FRONTEND handle ending
                    # the session with properly adjusted end_time (minus idle seconds).
                    # Previously this also called /end_task_session here, causing:
                    #   1. Wrong end_time saved (included idle time)
                    #   2. Double-submit (frontend also calls /end_task_session)
                    requests.post(f"{flask_server_url}/set_idle_flag", json={
                        "idle": True,
                        "idle_seconds": int(session_idle_time)
                    })
                    print("📡 Idle flag sent to Flask backend (frontend will handle session end)")

                    # Reset heartbeat timer so heartbeat monitor
                    # doesn't double-fire on an already-ended session
                    try:
                        requests.post(f"{flask_server_url}/heartbeat",
                                      headers={"Content-Type": "application/json"})
                    except Exception:
                        pass

                except Exception as e:
                    print(" Failed to notify Flask server:", e)
                break  # exit after one trigger
            time.sleep(5)

    threading.Thread(target=monitor, daemon=True).start()
