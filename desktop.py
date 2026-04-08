import os, sys, time, threading, subprocess, requests, logging, json, signal, atexit
import webview, psutil, webbrowser

TRAY = False
try:
    from pystray import Icon, Menu, MenuItem
    from PIL import Image as PILImage
    TRAY = True
except:
    logging.warning("pystray/PIL not available")

def fix_cwd():
    if getattr(sys, 'frozen', False):
        p = os.path.dirname(sys.executable)
        if sys.platform == 'darwin' and 'Contents/MacOS' in p:
            r = os.path.abspath(os.path.join(p, '..', '..', '..', '..'))
            if os.path.exists(os.path.join(r, 'app.py')):
                os.chdir(r)
            else:
                os.chdir(p)
        else:
            os.chdir(p)
    else:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

fix_cwd()
for d in ["logs", "output", "data"]:
    os.makedirs(d, exist_ok=True)

logging.basicConfig(level=logging.DEBUG,
    handlers=[logging.FileHandler("logs/app.log", mode="w", encoding="utf-8"), logging.StreamHandler()],
    format="%(asctime)s [%(levelname)s] %(message)s")

window_img = None
subprocess_proc = None
flask_ready = False
flask_port = 5000
cleanup_in_progress = False
flask_pids = set()
pid_file = "ddsfocus_pids.txt"
tray_icon = None

def save_pid(pid):
    flask_pids.add(pid)
    with open(pid_file, 'w') as f:
        for p in flask_pids: f.write(f"{p}\n")

def load_pids():
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            for l in f: flask_pids.add(int(l.strip()))

def remove_pid(pid):
    flask_pids.discard(pid)
    with open(pid_file, 'w') as f:
        for p in flask_pids: f.write(f"{p}\n")

def cleanup_pid_file():
    if os.path.exists(pid_file): os.remove(pid_file)

def kill_by_pid(pid):
    try:
        if sys.platform == 'darwin':
            subprocess.run(['kill', '-9', str(pid)], capture_output=True, timeout=3)
        else:
            subprocess.run(['taskkill', '/F', '/PID', str(pid), '/T'], capture_output=True, timeout=3)
    except: pass

def kill_by_port(port):
    try:
        if sys.platform == 'darwin':
            r = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True, timeout=5)
            for p in r.stdout.strip().split():
                if p.isdigit(): subprocess.run(['kill', '-9', p], capture_output=True, timeout=3)
        else:
            r = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, timeout=5)
            for line in r.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 4 and parts[-1].isdigit():
                        subprocess.run(['taskkill', '/F', '/PID', parts[-1], '/T'], capture_output=True, timeout=3)
    except: pass

def save_crash(reason):
    try:
        sf = os.path.join("data", "current_session.json")
        if not os.path.exists(sf): return
        with open(sf, "r") as f: d = json.load(f)
        e, t, s = d.get("email"), d.get("task_id"), d.get("staff_id")
        if not (e and t and s): return
        requests.post(f"http://127.0.0.1:{flask_port}/end_task_session",
            json={"email": e, "staff_id": s, "task_id": t,
                  "end_time": int(time.time()), "note": f"GUI crash: {reason}", "meetings": []}, timeout=3)
    except: pass

def exc_handler(typ, val, tb):
    logging.error("Uncaught exception", exc_info=(typ, val, tb))
    save_crash(f"{typ.__name__}: {val}")

sys.excepthook = exc_handler

def aggressive_cleanup():
    for rnd in range(7):
        killed = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                pn = (proc.info.get('name') or '').lower()
                cmd = ' '.join(proc.info.get('cmdline') or [])
                if ('connector' in pn or 'ddsfocuspro' in pn or
                    ('python' in pn and any(s in cmd for s in ['app.py', 'connector']))):
                    if proc.pid != os.getpid():
                        kill_by_pid(proc.pid)
                        killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied): continue
        for pid in list(flask_pids):
            kill_by_pid(pid); killed = True
        for port in range(5000, 5010): kill_by_port(port)
        if not killed: break
        time.sleep(1)
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'connector' in (proc.info.get('name') or '').lower() and proc.pid != os.getpid():
                proc.kill()
        except: pass
    logging.info("Aggressive cleanup done")

def cleanup_and_exit():
    global subprocess_proc, cleanup_in_progress
    if cleanup_in_progress: return
    cleanup_in_progress = True
    logging.info("[CLEANUP] UI closed - cleaning up...")
    try:
        sf = "data/current_session.json"
        if os.path.exists(sf):
            with open(sf, "r", encoding="utf-8") as f: d = json.load(f)
            e, s, t = d.get("email"), d.get("staff_id"), d.get("task_id")
            if e and s and t:
                try: requests.post(f"http://127.0.0.1:{flask_port}/end_task_session",
                    json={"email": e, "staff_id": s, "task_id": t,
                          "end_time": int(time.time()), "note": "App closed by user", "meetings": []}, timeout=5)
                except: pass
            os.remove(sf)
    except: pass
    try: requests.post(f"http://127.0.0.1:{flask_port}/shutdown", timeout=3)
    except: pass
    if tray_icon:
        try: tray_icon.stop()
        except: pass
    for pid in list(flask_pids):
        kill_by_pid(pid); remove_pid(pid)
    if subprocess_proc and subprocess_proc.poll() is None:
        kill_by_pid(subprocess_proc.pid)
    for port in range(5000, 5010): kill_by_port(port)
    cleanup_pid_file()
    logging.info("[CLEANUP] Done")
    try: sys.exit(0)
    except: os._exit(0)

def create_tray():
    if not TRAY: return None
    try:
        img = None
        for base in [os.getcwd(), os.path.dirname(__file__)]:
            for fn in ["icon.ico", "favicon.ico", "icon.png"]:
                p = os.path.join(base, "static", fn)
                if os.path.exists(p):
                    img = PILImage.open(p).convert("RGBA").resize((32, 32), PILImage.Resampling.LANCZOS); break
            if img: break
        if not img: img = PILImage.new("RGBA", (32, 32), (0, 96, 57, 255))
        def show_fn(icon, item):
            try:
                if webview.windows:
                    webview.windows[0].show()
                    webview.windows[0].restore()
            except: pass
        def exit_fn(icon, item): cleanup_and_exit()
        menu = Menu(MenuItem("Show DDS Focus Pro", show_fn, default=True), Menu.SEPARATOR, MenuItem("Exit", exit_fn))
        tray = Icon(name="DDSFocusPro", icon=img, title="DDS Focus Pro", menu=menu)
        return tray
    except Exception as e:
        logging.error(f"Tray error: {e}"); return None

def run_tray():
    global tray_icon
    if TRAY:
        tray_icon = create_tray()
        if tray_icon: tray_icon.run()

def start_flask():
    global subprocess_proc
    for port in [5000, 5001, 5002, 5003, 5004, 5005]:
        try:
            if requests.get(f"http://127.0.0.1:{port}", timeout=2).status_code == 200:
                global flask_port; flask_port = port
                logging.info(f"Using existing connector on port {port}")
                return
        except: pass
    base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
    cwd = os.getcwd()
    exe = None
    for path in [os.path.join(cwd, "connector"), os.path.join(base, "connector"),
                 os.path.join(cwd, "dist", "connector"), os.path.join(base, "dist", "connector")]:
        if os.path.exists(path): exe = path; break
    kwargs = {'cwd': os.path.dirname(exe) if exe else cwd}
    if sys.platform == 'win32': kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
    elif sys.platform == 'darwin': kwargs['stdout'] = subprocess.DEVNULL; kwargs['stderr'] = subprocess.DEVNULL
    if exe:
        subprocess_proc = subprocess.Popen([exe, f"--gui-pid={os.getpid()}"], **kwargs)
        save_pid(subprocess_proc.pid)
        logging.info(f"Started connector PID {subprocess_proc.pid}")
    else:
        py = os.path.join(cwd, "app.py")
        if not os.path.exists(py): py = os.path.join(base, "app.py")
        if os.path.exists(py):
            subprocess_proc = subprocess.Popen([sys.executable, py, f"--gui-pid={os.getpid()}"], **kwargs)
            save_pid(subprocess_proc.pid)
            logging.info(f"Started app.py PID {subprocess_proc.pid}")
        else:
            logging.error("No connector.exe or app.py found!")

def wait_ready(max_wait=120):
    global flask_ready, flask_port
    start = time.time()
    for port in [5000, 5001, 5002, 5003, 5004, 5005]:
        while time.time() - start < max_wait:
            try:
                if requests.get(f"http://127.0.0.1:{port}", timeout=2).status_code == 200:
                    flask_ready = True; flask_port = port
                    logging.info(f"Flask ready on port {port}")
                    return f"http://127.0.0.1:{port}"
            except: pass
            time.sleep(1)
    return None

def health_monitor():
    time.sleep(15)
    while not cleanup_in_progress:
        time.sleep(30)
        if not flask_port: continue
        try:
            if requests.get(f"http://127.0.0.1:{flask_port}/heartbeat", timeout=5).status_code == 200: continue
        except: pass
        logging.error("[HEALTH] Connector down - restarting")
        try: start_flask(); wait_ready(30)
        except: pass
        break

signal.signal(signal.SIGINT, lambda s, f: cleanup_and_exit())
signal.signal(signal.SIGTERM, lambda s, f: cleanup_and_exit())

if __name__ == '__main__':
    logging.info("Starting DDS Focus Pro...")
    load_pids()
    start_flask()
    threading.Thread(target=health_monitor, daemon=True).start()
    if TRAY: threading.Thread(target=run_tray, daemon=True).start()
    try:
        lp = None
        for path in [os.path.join(os.getcwd(), "templates", "loader.html"),
                     os.path.join(os.path.dirname(__file__), "templates", "loader.html")]:
            if os.path.exists(path): lp = path; break
        if not lp: raise FileNotFoundError("loader.html not found")
        with open(lp, "r", encoding="utf-8") as f: html = f.read()
        gui = 'cocoa' if sys.platform == 'darwin' else 'edgechromium'
        webview.create_window(title="DDS Focus Pro", html=html, width=1024, height=750, resizable=True)
        webview.start(gui=gui, debug=False)
    except Exception as e:
        logging.error(f"WebView error: {e}")
    cleanup_and_exit()