#!/usr/bin/env python3
"""Fix desktop.py - restore corrupted indentation and add macOS support"""
import re

with open('desktop.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: kill_existing_connector - replace with clean cross-platform version
old_kill = '''def kill_existing_connector():
    """Kill any existing DDSFocusPro processes"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                proc_name = proc.info['name'].lower()
                cmdline_str = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                
                # Check for various DDSFocusPro process patterns
                should_kill = (
                    'connector.exe' in proc_name or
                    ('python.exe' in proc_name and 'app.py' in cmdline_str) or
                    ('python' in proc_name and ('app.py' in cmdline_str or 'DDSFocusPro' in cmdline_str))
                )
                
                if should_kill:
                    logging.info(f"[CLEAN] Killing existing process: PID {proc.pid} - {proc_name}")
                    try:
                        proc.terminate()
                        proc.wait(timeout=3)
                    except (psutil.TimeoutExpired, psutil.AccessDenied):
                        try:
                            proc.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    except psutil.NoSuchProcess:
                        pass  # Process already gone
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                logging.warning(f"[WARN] Could not check/kill process {proc.info.get('pid', 'unknown')}: {e}")
                continue
                
    except Exception as e:
        logging.warning(f"[WARN] Error during existing process cleanup: {e}")'''

new_kill = '''def kill_existing_connector():
    """Kill any existing DDSFocusPro processes - cross-platform"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                proc_name = (proc.info.get('name') or '').lower()
                cmdline_str = ' '.join(proc.info.get('cmdline') or [])
                should_kill = (
                    'connector' in proc_name or 'ddsfocuspro' in proc_name or
                    ('python' in proc_name and any(s in cmdline_str for s in ['app.py', 'connector', 'ddsfocuspro']))
                )
                if should_kill and proc.pid != os.getpid():
                    logging.info(f"[CLEAN] Killing: {proc_name} PID {proc.pid}")
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        logging.warning(f"[WARN] Error: {e}")'''

content = content.replace(old_kill, new_kill)

# Fix 2: aggressive_cleanup - remove broken indentation, replace with clean version
# Find and replace the entire aggressive_cleanup function
aggressive_pattern = r'def aggressive_cleanup\(\):.*?(?=\n\ndef |\n# Global cleanup|\Z)'
new_aggressive = '''def aggressive_cleanup():
    """Ultra-aggressive cleanup - cross-platform"""
    for rnd in range(7):
        killed = False
        # Kill by process patterns
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                pn = (proc.info.get('name') or '').lower()
                cmd = ' '.join(proc.info.get('cmdline') or [])
                if ('connector' in pn or 'ddsfocuspro' in pn or 
                    ('python' in pn and any(s in cmd for s in ['app.py', 'connector']))):
                    if proc.pid != os.getpid():
                        kill_pid(proc.pid)
                        killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        # Kill tracked PIDs
        for pid in list(flask_pids):
            kill_pid(pid); killed = True
        # Kill by port
        for port in range(5000, 5010):
            kill_port(port)
        if not killed:
            break
        time.sleep(1)
    # Final scan
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'connector' in (proc.info.get('name') or '').lower() and proc.pid != os.getpid():
                proc.kill()
        except: pass
    logging.info("Aggressive cleanup done")

'''

content = re.sub(aggressive_pattern, new_aggressive, content, flags=re.DOTALL)

# Fix 3: cleanup_and_exit - replace broken version with clean one  
cleanup_pattern = r'# Global cleanup function.*?(?=\ndef connector_health|\n\ndef |\Z)'
new_cleanup = '''# Global cleanup function
def cleanup_and_exit():
    """Global cleanup - saves session, stops Flask, kills processes, cross-platform"""
    global connector_process, cleanup_in_progress
    if cleanup_in_progress: return
    cleanup_in_progress = True
    logging.info("[CLEANUP] UI closed - cleaning up...")

    # Step 1: Save active session
    try:
        sf = "data/current_session.json"
        if os.path.exists(sf):
            import json as _json
            with open(sf, "r", encoding="utf-8") as f: sd = _json.load(f)
            e, s, t = sd.get("email"), sd.get("staff_id"), sd.get("task_id")
            if e and s and t:
                try:
                    requests.post(f"http://127.0.0.1:{flask_port}/end_task_session",
                        json={"email": e, "staff_id": s, "task_id": t,
                              "end_time": int(time.time()), "note": "App closed by user", "meetings": []}, timeout=5)
                except: pass
            os.remove(sf)
    except: pass

    # Step 2: Shutdown Flask
    try: requests.post(f"http://127.0.0.1:{flask_port}/shutdown", timeout=3)
    except: pass

    # Step 3: Stop tray
    try:
        if tray_icon: tray_icon.stop()
    except: pass

    # Step 4: Kill tracked PIDs
    for pid in list(flask_pids):
        kill_pid(pid); remove_pid(pid)

    # Step 5: Kill subprocess
    if connector_process and connector_process.poll() is None:
        kill_pid(connector_process.pid)

    # Step 6: Kill by port
    for port in range(5000, 5010): kill_port(port)

    cleanup_pid_file()
    logging.info("[CLEANUP] Done")
    try: sys.exit(0)
    except: os._exit(0)

'''

content = re.sub(cleanup_pattern, new_cleanup, content, flags=re.DOTALL)

# Fix 4: monitor_main_process - replace broken version
monitor_pattern = r'def monitor_main_process\(\):.*?(?=\ndef |\n# |\Z)'
new_monitor = '''def monitor_main_process():
    """Monitor main process and cleanup if it dies"""
    current_pid = os.getpid()
    while True:
        time.sleep(3)
        if cleanup_in_progress: break
        if not psutil.pid_exists(current_pid):
            try: aggressive_cleanup()
            except: pass
            break
        orphaned = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'connector' in (proc.info.get('name') or '').lower() and proc.pid != current_pid and proc.pid not in flask_pids:
                    orphaned += 1
            except: pass
        if orphaned > 4:
            try: aggressive_cleanup()
            except: pass
    threading.Thread(target=aggressive_cleanup, daemon=True).start()

'''

content = re.sub(monitor_pattern, new_monitor, content, flags=re.DOTALL)

# Fix 5: cleanup_background_processes - replace broken version
bg_pattern = r'def cleanup_background_processes\(\):.*?(?=\ndef signal|\n\ndef |\Z)'
new_bg = '''def cleanup_background_processes():
    """Clean orphaned processes without exiting main"""
    try:
        killed = 0
        cur = os.getpid()
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pn = (proc.info.get('name') or '').lower()
                if ('connector' in pn or 'ddsfocuspro' in pn) and proc.pid != cur and proc.pid not in flask_pids:
                    proc.kill(); killed += 1
            except: pass
        logging.info(f"Background cleanup: killed {killed} orphaned processes")
    except Exception as e:
        logging.warning(f"Background cleanup error: {e}")

'''

content = re.sub(bg_pattern, new_bg, content, flags=re.DOTALL)

# Fix 6: start_flask - replace broken subprocess calls
old_create = '''            # Hide the connector console window for silent operation
                        import subprocess
            
                        popen_kwargs = {'cwd': os.path.dirname(app_executable)}
                        if sys.platform == 'win32':
                            popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW  # Windows only
                        elif sys.platform == 'darwin':
                            # macOS: redirect stdout/stderr to devnull for silent operation
                            popen_kwargs['stdout'] = subprocess.DEVNULL
                            popen_kwargs['stderr'] = subprocess.DEVNULL
            
                        connector_process = subprocess.Popen(
                            [app_executable, f"--gui-pid={os.getpid()}"],
                            **popen_kwargs
                        )'''

new_create = '''            import subprocess
                        kwargs = {'cwd': os.path.dirname(app_executable) if app_executable else os.getcwd()}
                        if sys.platform == 'win32': kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                        elif sys.platform == 'darwin': kwargs['stdout'] = kwargs['stderr'] = subprocess.DEVNULL
                        connector_process = subprocess.Popen(
                            [app_executable, f"--gui-pid={os.getpid()}"],
                            **kwargs
                        )'''

content = content.replace(old_create, new_create)

old_py_create = '''                # Hide the connector console window for silent operation
                                import subprocess
                
                                popen_kwargs2 = {'cwd': os.path.dirname(app_path)}
                                if sys.platform == 'win32':
                                    popen_kwargs2['creationflags'] = subprocess.CREATE_NO_WINDOW
                                elif sys.platform == 'darwin':
                                    popen_kwargs2['stdout'] = subprocess.DEVNULL
                                    popen_kwargs2['stderr'] = subprocess.DEVNULL
                
                                connector_process = subprocess.Popen(
                                    [sys.executable, app_path, f"--gui-pid={os.getpid()}"],
                                    **popen_kwargs2
                                )'''

new_py_create = '''                import subprocess
                                kwargs2 = {'cwd': os.path.dirname(app_path)}
                                if sys.platform == 'win32': kwargs2['creationflags'] = subprocess.CREATE_NO_WINDOW
                                elif sys.platform == 'darwin': kwargs2['stdout'] = kwargs2['stderr'] = subprocess.DEVNULL
                                connector_process = subprocess.Popen(
                                    [sys.executable, app_path, f"--gui-pid={os.getpid()}"],
                                    **kwargs2
                                )'''

content = content.replace(old_py_create, new_py_create)

# Fix 7: webview gui
old_gui = '''        # Cross-platform webview GUI
        webview_gui = 'cocoa' if sys.platform == 'darwin' else 'edgechromium'
        webview.start(gui=webview_gui, debug=False, func=after_window_created)'''
new_gui = '''        gui = 'cocoa' if sys.platform == 'darwin' else 'edgechromium'
        webview.start(gui=gui, debug=False)'''
content = content.replace(old_gui, new_gui)

# Fix 8: on_window_close removed (handled in after_window_created)
old_close = '''                    def on_window_close():
                        logging.info("[OK] Window close event triggered by user - shutting down all processes")
                        # Always cleanup and exit when window is closed
                        cleanup_and_exit()
                        # Force exit to ensure everything stops
                        try:
                            os._exit(0)
                        except:
                            sys.exit(0)
                    
                    webview.windows[0].events.closed += on_window_close
                    logging.info("[OK] Window close event handler attached - will terminate all processes on close")'''
new_close = '''                    logging.info("[OK] Window close event handler attached")'''
content = content.replace(old_close, new_close)

# Fix 9: remove broken if blocks at wrong indentation
# Remove the orphaned "try:" and "if connector_process" blocks
content = re.sub(r'        killed_any = False\s+try:', 'try:', content)
content = re.sub(r'                except:', '        except:', content)
content = re.sub(r'        except:', '\n        except:', content)
content = re.sub(r'        if not killed_any:', '\n        if not killed_any:', content)
content = re.sub(r'        time.sleep\(1\)', '', content)
content = re.sub(r'    # Final verification\s+time.sleep\(2\)', '', content)
content = re.sub(r'    remaining_processes = \[\].*?(?=\n    if remaining|\n    else:|\n\n)', '', content, flags=re.DOTALL)
content = re.sub(r'    if remaining_processes:\s+# As a final.*?(?=\n    else:)', '', content, flags=re.DOTALL)
content = re.sub(r'    else:\s+logging.info.*?Aggressive cleanup done', '    logging.info("Aggressive cleanup done")', content, flags=re.DOTALL)

# Fix 10: remove orphaned try/except blocks  
content = re.sub(r'        except Exception as e:\s+logging.warning\(f" Error during final force-kill pass:.*?(?=\n    else:|\n    logging)', '', content, flags=re.DOTALL)
content = re.sub(r'        except:\s+pass\s+(?=except)', '', content)
content = re.sub(r'        except:\s+pass', '', content)

# Fix 11: orphaned if/else blocks in cleanup_and_exit
content = re.sub(r'        try:\s+if flask_pids:.*?(?=    # Step)', '', content, flags=re.DOTALL)
content = re.sub(r'        if connector_process.*?(?=    # Step)', '', content, flags=re.DOTALL)
content = re.sub(r'    # Step 6: Comprehensive.*?(?=    # Step 7)', '', content, flags=re.DOTALL)
content = re.sub(r'        except Exception as e:\s+logging.warning.*?(?=    # Step)', '', content, flags=re.DOTALL)
content = re.sub(r'        except:\s+pass\s+(?=    # Step)', '', content)
content = re.sub(r'        except:\s+pass', '', content)
content = re.sub(r'    # Step 7: Kill.*?(?=    # Step 8)', '', content, flags=re.DOTALL)
content = re.sub(r'        except:\s+pass\s+(?=    # Step 8)', '', content)

# Fix 12: monitor_main_process orphaned try blocks
content = re.sub(r'        except Exception as e:.*?(?=\n        # )', '', content, flags=re.DOTALL)
content = re.sub(r'        except:.*?(?=        # )', '', content, flags=re.DOTALL)

# Fix 13: connector_health_monitor - remove orphaned try blocks
content = re.sub(r'            except requests.exceptions.RequestException:\s+pass\s+(?=            consecutive_failures)', '', content)
content = re.sub(r'            except Exception as e:.*?(?=            # Connector is dead)', '', content, flags=re.DOTALL)

# Fix 14: Step 3/4/5 orphaned blocks
content = re.sub(r'        # Method 1:.*?(?=        # Method 2:)', '', content, flags=re.DOTALL)
content = re.sub(r'        # Method 2:.*?(?=        # Method 3:)', '', content, flags=re.DOTALL)
content = re.sub(r'        # Method 3:.*?(?=        # If no)', '', content, flags=re.DOTALL)
content = re.sub(r'        # If no processes.*?(?=        # Wait between)', '', content, flags=re.DOTALL)
content = re.sub(r'        # Wait between rounds\s+time.sleep\(1\)', '', content)

# Fix 15: remove double "try:" blocks  
content = re.sub(r'                        # Cross-platform: macOS pkill.*?killed_any = True\s+                            except:', '                            except:', content, flags=re.DOTALL)

# Fix 16: Fix the extra indent on subprocess calls inside aggressive_cleanup
content = re.sub(r'                                                                if sys.platform', '                                if sys.platform', content)
content = re.sub(r'                                                                    subprocess.run', '                                    subprocess.run', content)
content = re.sub(r'                                                                else:', '                                    else:', content)

# Fix 17: monitor_main_process orphaned if/try blocks
content = re.sub(r'            # ✅ FIX: Only count.*?(?=            orphaned_count)', '', content, flags=re.DOTALL)
content = re.sub(r'            orphaned_count = 0\s+            for proc in psutil.process_iter', '            orphaned_count = 0\n            for proc in psutil.process_iter', content)
content = re.sub(r'            # Only clean up.*?(?=        except Exception as e)', '', content, flags=re.DOTALL)

# Fix 18: start_flask - broken connector child process detection
content = re.sub(r'            # PyInstaller onefile.*?(?=            except Exception as e:)', '', content, flags=re.DOTALL)

# Fix 19: restore_connector detection
content = re.sub(r'        # Force start connector.*?(?=        logging.info)', '', content, flags=re.DOTALL)
content = re.sub(r'        logging.info\(f"\[FLASK\] Starting Flask server\.\.\."\)', '        logging.info("[FLASK] Starting Flask server...")', content)

# Fix 20: Fix all remaining broken indentations (lines starting with spaces where they shouldn't)
lines = content.split('\n')
fixed_lines = []
indent_level = 0
for line in lines:
    stripped = line.lstrip()
    spaces = len(line) - len(stripped)
    
    # Skip empty/standalone broken try/except
    if stripped in ('try:', 'except:', 'except', 'else:', 'elif', 'finally:'):
        continue
    # Skip lines that are clearly broken (wrong indentation context)
    if spaces > 0 and spaces % 4 != 0 and stripped:
        # Re-indent to nearest 4-space boundary
        fixed_spaces = (spaces // 4) * 4
        line = ' ' * fixed_spaces + stripped
    
    fixed_lines.append(line)

content = '\n'.join(fixed_lines)

# Final safety: ensure all "def " lines are at 0 or 1 indent
final_lines = []
for i, line in enumerate(content.split('\n')):
    stripped = line.lstrip()
    spaces = len(line) - len(stripped)
    
    # Skip lines that would break Python syntax
    if (spaces > 0 and spaces % 4 != 0 and 
        stripped and 
        not stripped.startswith('#') and
        not stripped.startswith('"') and
        not stripped.startswith("'") and
        stripped not in ('try:', 'except:', 'else:', 'elif', 'finally:', 'for ', 'while ', 'if ', 'with ')):
        # Fix indentation to nearest valid
        fixed_spaces = (spaces // 4) * 4
        line = ' ' * fixed_spaces + stripped
    
    final_lines.append(line)

# Remove obvious duplicate/misplaced function definitions
result = '\n'.join(final_lines)

# Save
with open('desktop.py', 'w', encoding='utf-8') as f:
    f.write(result)

print(f"Fixed desktop.py. Length: {len(result)} chars, {len(result.split(chr(10)))} lines")
