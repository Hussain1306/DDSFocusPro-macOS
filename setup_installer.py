"""
DDS FocusPro Installer - v1.7.1
A self-contained installer that replicates Inno Setup functionality.
Installs DDSFocusPro to %LOCALAPPDATA%\DDSFocusPro with shortcuts and uninstaller.
"""

import os
import sys
import shutil
import ctypes
import winreg
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading

# ============================================
# EMBEDDED CONFIGURATION
# ============================================
APP_NAME = "DDS FocusPro"
APP_VERSION = "1.7.1"
APP_PUBLISHER = "DDS Global"
MAIN_EXE = "DDSFocusPro-GUI.exe"
CONNECTOR_EXE = "connector.exe"
ICON_FILE = "icon.ico"
DEFAULT_INSTALL_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "DDSFocusPro")

# When running as compiled exe, _MEIPASS points to temp extraction folder
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = sys._MEIPASS
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_resource_path(relative_path):
    """Get path to bundled resource"""
    return os.path.join(BUNDLE_DIR, "installer_payload", relative_path)


def is_admin():
    """Check if running with admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


class InstallerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} Setup v{APP_VERSION}")
        self.root.geometry("550x420")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")
        
        # Try to set icon
        try:
            icon_path = os.path.join(BUNDLE_DIR, "installer_payload", ICON_FILE)
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 275
        y = (self.root.winfo_screenheight() // 2) - 210
        self.root.geometry(f"+{x}+{y}")
        
        self.install_dir = tk.StringVar(value=DEFAULT_INSTALL_DIR)
        self.create_desktop_shortcut = tk.BooleanVar(value=True)
        self.launch_after_install = tk.BooleanVar(value=True)
        
        self.current_frame = None
        self.show_welcome_page()
        
    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
    
    def show_welcome_page(self):
        self.clear_frame()
        self.current_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.current_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Title
        tk.Label(
            self.current_frame, text=f"Welcome to {APP_NAME}", 
            font=("Segoe UI", 18, "bold"), fg="#00d4aa", bg="#1a1a2e"
        ).pack(pady=(20, 5))
        
        tk.Label(
            self.current_frame, text=f"Version {APP_VERSION}",
            font=("Segoe UI", 11), fg="#888888", bg="#1a1a2e"
        ).pack(pady=(0, 20))
        
        tk.Label(
            self.current_frame,
            text="This wizard will install DDS FocusPro\non your computer.\n\nClick Next to continue.",
            font=("Segoe UI", 11), fg="#cccccc", bg="#1a1a2e", justify="center"
        ).pack(pady=20)
        
        # Buttons frame
        btn_frame = tk.Frame(self.current_frame, bg="#1a1a2e")
        btn_frame.pack(side="bottom", fill="x", pady=10)
        
        tk.Button(
            btn_frame, text="Cancel", command=self.root.quit,
            font=("Segoe UI", 10), bg="#333355", fg="white",
            relief="flat", padx=20, pady=5, cursor="hand2"
        ).pack(side="right", padx=5)
        
        tk.Button(
            btn_frame, text="Next  >", command=self.show_directory_page,
            font=("Segoe UI", 10, "bold"), bg="#00d4aa", fg="#1a1a2e",
            relief="flat", padx=20, pady=5, cursor="hand2"
        ).pack(side="right", padx=5)
    
    def show_directory_page(self):
        self.clear_frame()
        self.current_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.current_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        tk.Label(
            self.current_frame, text="Choose Install Location",
            font=("Segoe UI", 16, "bold"), fg="#00d4aa", bg="#1a1a2e"
        ).pack(pady=(10, 20))
        
        tk.Label(
            self.current_frame, text="Select the folder where DDS FocusPro will be installed:",
            font=("Segoe UI", 10), fg="#cccccc", bg="#1a1a2e"
        ).pack(pady=(0, 10))
        
        # Directory selection
        dir_frame = tk.Frame(self.current_frame, bg="#1a1a2e")
        dir_frame.pack(fill="x", pady=5)
        
        dir_entry = tk.Entry(
            dir_frame, textvariable=self.install_dir, font=("Segoe UI", 9),
            bg="#16213e", fg="white", insertbackground="white", relief="flat"
        )
        dir_entry.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 5))
        
        tk.Button(
            dir_frame, text="Browse...", command=self.browse_directory,
            font=("Segoe UI", 9), bg="#333355", fg="white", relief="flat",
            padx=10, cursor="hand2"
        ).pack(side="right")
        
        # Options
        tk.Checkbutton(
            self.current_frame, text="Create desktop shortcut",
            variable=self.create_desktop_shortcut, font=("Segoe UI", 10),
            fg="#cccccc", bg="#1a1a2e", selectcolor="#16213e",
            activebackground="#1a1a2e", activeforeground="#cccccc"
        ).pack(anchor="w", pady=(20, 5))
        
        tk.Checkbutton(
            self.current_frame, text="Launch application after install",
            variable=self.launch_after_install, font=("Segoe UI", 10),
            fg="#cccccc", bg="#1a1a2e", selectcolor="#16213e",
            activebackground="#1a1a2e", activeforeground="#cccccc"
        ).pack(anchor="w", pady=5)
        
        # Buttons
        btn_frame = tk.Frame(self.current_frame, bg="#1a1a2e")
        btn_frame.pack(side="bottom", fill="x", pady=10)
        
        tk.Button(
            btn_frame, text="Cancel", command=self.root.quit,
            font=("Segoe UI", 10), bg="#333355", fg="white",
            relief="flat", padx=20, pady=5, cursor="hand2"
        ).pack(side="right", padx=5)
        
        tk.Button(
            btn_frame, text="Install", command=self.start_install,
            font=("Segoe UI", 10, "bold"), bg="#00d4aa", fg="#1a1a2e",
            relief="flat", padx=20, pady=5, cursor="hand2"
        ).pack(side="right", padx=5)
        
        tk.Button(
            btn_frame, text="<  Back", command=self.show_welcome_page,
            font=("Segoe UI", 10), bg="#333355", fg="white",
            relief="flat", padx=20, pady=5, cursor="hand2"
        ).pack(side="right", padx=5)
    
    def browse_directory(self):
        folder = filedialog.askdirectory(initialdir=self.install_dir.get())
        if folder:
            self.install_dir.set(folder)
    
    def start_install(self):
        self.clear_frame()
        self.current_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.current_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        tk.Label(
            self.current_frame, text="Installing...",
            font=("Segoe UI", 16, "bold"), fg="#00d4aa", bg="#1a1a2e"
        ).pack(pady=(20, 10))
        
        self.status_label = tk.Label(
            self.current_frame, text="Preparing installation...",
            font=("Segoe UI", 10), fg="#cccccc", bg="#1a1a2e"
        )
        self.status_label.pack(pady=10)
        
        # Progress bar
        style = ttk.Style()
        style.theme_use('default')
        style.configure("green.Horizontal.TProgressbar", 
                        troughcolor='#16213e', background='#00d4aa')
        
        self.progress = ttk.Progressbar(
            self.current_frame, length=400, mode='determinate',
            style="green.Horizontal.TProgressbar"
        )
        self.progress.pack(pady=20)
        
        self.log_text = tk.Text(
            self.current_frame, height=8, font=("Consolas", 8),
            bg="#0f0f23", fg="#00d4aa", relief="flat", state="disabled"
        )
        self.log_text.pack(fill="x", pady=10)
        
        # Run install in background thread
        thread = threading.Thread(target=self.run_install, daemon=True)
        thread.start()
    
    def log(self, message):
        self.root.after(0, self._log_safe, message)
    
    def _log_safe(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
    
    def update_progress(self, value, status=""):
        self.root.after(0, self._update_progress_safe, value, status)
    
    def _update_progress_safe(self, value, status):
        self.progress['value'] = value
        if status:
            self.status_label.config(text=status)
    
    def run_install(self):
        install_dir = self.install_dir.get()
        
        try:
            # Step 1: Create install directory
            self.update_progress(5, "Creating install directory...")
            self.log(f"Install directory: {install_dir}")
            os.makedirs(install_dir, exist_ok=True)
            
            # Step 2: Copy main executables
            self.update_progress(10, "Copying DDSFocusPro-GUI.exe...")
            payload_dir = os.path.join(BUNDLE_DIR, "installer_payload")
            
            src_gui = os.path.join(payload_dir, MAIN_EXE)
            if os.path.exists(src_gui):
                shutil.copy2(src_gui, os.path.join(install_dir, MAIN_EXE))
                self.log(f"  Copied {MAIN_EXE}")
            else:
                self.log(f"  WARNING: {MAIN_EXE} not found at {src_gui}")
            
            self.update_progress(30, "Copying connector.exe...")
            src_conn = os.path.join(payload_dir, CONNECTOR_EXE)
            if os.path.exists(src_conn):
                shutil.copy2(src_conn, os.path.join(install_dir, CONNECTOR_EXE))
                self.log(f"  Copied {CONNECTOR_EXE}")
            else:
                self.log(f"  WARNING: {CONNECTOR_EXE} not found at {src_conn}")
            
            # Step 3: Copy icon
            self.update_progress(50, "Copying icon...")
            src_icon = os.path.join(payload_dir, ICON_FILE)
            if os.path.exists(src_icon):
                shutil.copy2(src_icon, os.path.join(install_dir, ICON_FILE))
                self.log(f"  Copied {ICON_FILE}")
            
            # Step 4: Copy static & templates
            self.update_progress(55, "Copying static files...")
            for folder in ["static", "templates"]:
                src_folder = os.path.join(payload_dir, folder)
                dst_folder = os.path.join(install_dir, folder)
                if os.path.exists(src_folder):
                    if os.path.exists(dst_folder):
                        shutil.rmtree(dst_folder)
                    shutil.copytree(src_folder, dst_folder)
                    self.log(f"  Copied {folder}/")
            
            # Step 5: Copy config files
            self.update_progress(65, "Copying configuration...")
            for cfg_file in [".env", "themes.json"]:
                src_cfg = os.path.join(payload_dir, cfg_file)
                if os.path.exists(src_cfg):
                    shutil.copy2(src_cfg, os.path.join(install_dir, cfg_file))
                    self.log(f"  Copied {cfg_file}")
            
            # Step 6: Create data directories
            self.update_progress(70, "Creating data directories...")
            for subdir in ["data", "logs", "output"]:
                os.makedirs(os.path.join(install_dir, subdir), exist_ok=True)
                self.log(f"  Created {subdir}/")
            
            # Step 7: Create uninstaller script
            self.update_progress(75, "Creating uninstaller...")
            self.create_uninstaller(install_dir)
            self.log("  Created uninstaller")
            
            # Step 8: Create Start Menu shortcut
            self.update_progress(80, "Creating Start Menu shortcut...")
            self.create_shortcut(
                os.path.join(install_dir, MAIN_EXE),
                os.path.join(install_dir, ICON_FILE),
                self.get_start_menu_path(),
                APP_NAME
            )
            self.log("  Created Start Menu shortcut")
            
            # Step 9: Create Desktop shortcut (optional)
            if self.create_desktop_shortcut.get():
                self.update_progress(85, "Creating desktop shortcut...")
                desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
                self.create_shortcut(
                    os.path.join(install_dir, MAIN_EXE),
                    os.path.join(install_dir, ICON_FILE),
                    desktop,
                    APP_NAME
                )
                self.log("  Created Desktop shortcut")
            
            # Step 10: Add to Add/Remove Programs
            self.update_progress(90, "Registering application...")
            self.register_uninstall(install_dir)
            self.log("  Registered in Add/Remove Programs")
            
            self.update_progress(100, "Installation complete!")
            self.log(f"\n  {APP_NAME} v{APP_VERSION} installed successfully!")
            
            # Show completion page
            self.root.after(500, self.show_complete_page)
            
        except Exception as e:
            self.log(f"\n  ERROR: {str(e)}")
            self.update_progress(0, "Installation failed!")
            self.root.after(500, lambda: messagebox.showerror(
                "Installation Failed", f"An error occurred:\n{str(e)}"
            ))
    
    def create_shortcut(self, target_exe, icon_path, shortcut_dir, name):
        """Create a Windows shortcut (.lnk) using PowerShell"""
        try:
            os.makedirs(shortcut_dir, exist_ok=True)
            shortcut_path = os.path.join(shortcut_dir, f"{name}.lnk")
            
            # Use PowerShell to create shortcut (no external dependencies)
            ps_cmd = f'''
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut("{shortcut_path}")
$s.TargetPath = "{target_exe}"
$s.WorkingDirectory = "{os.path.dirname(target_exe)}"
$s.IconLocation = "{icon_path}"
$s.Description = "{APP_NAME} v{APP_VERSION}"
$s.Save()
'''
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True, timeout=15
            )
        except Exception as e:
            self.log(f"  Warning: Could not create shortcut: {e}")
    
    def get_start_menu_path(self):
        """Get the Start Menu Programs path"""
        appdata = os.environ.get("APPDATA", "")
        return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", APP_NAME)
    
    def create_uninstaller(self, install_dir):
        """Create a batch uninstaller"""
        uninstall_bat = os.path.join(install_dir, "uninstall.bat")
        desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
        start_menu = self.get_start_menu_path()
        
        bat_content = f'''@echo off
echo ==========================================
echo  Uninstalling {APP_NAME} v{APP_VERSION}
echo ==========================================
echo.
set /p confirm="Are you sure you want to uninstall? (Y/N): "
if /i not "%confirm%"=="Y" exit /b

echo Removing desktop shortcut...
del /f /q "{os.path.join(desktop, APP_NAME + '.lnk')}" 2>nul

echo Removing Start Menu shortcut...
rmdir /s /q "{start_menu}" 2>nul

echo Removing registry entry...
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\DDSFocusPro" /f 2>nul

echo Removing application files...
cd /d "%TEMP%"
rmdir /s /q "{install_dir}" 2>nul

echo.
echo {APP_NAME} has been uninstalled.
echo.
pause
'''
        with open(uninstall_bat, 'w') as f:
            f.write(bat_content)
    
    def register_uninstall(self, install_dir):
        """Register in Windows Add/Remove Programs"""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\DDSFocusPro"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, f"{APP_NAME} {APP_VERSION}")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, APP_PUBLISHER)
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_dir)
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, 
                              os.path.join(install_dir, "uninstall.bat"))
            icon_path = os.path.join(install_dir, ICON_FILE)
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, icon_path)
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
        except Exception as e:
            self.log(f"  Warning: Could not register in Add/Remove Programs: {e}")
    
    def show_complete_page(self):
        self.clear_frame()
        self.current_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.current_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        tk.Label(
            self.current_frame, text="Installation Complete!",
            font=("Segoe UI", 18, "bold"), fg="#00d4aa", bg="#1a1a2e"
        ).pack(pady=(30, 10))
        
        tk.Label(
            self.current_frame,
            text=f"{APP_NAME} v{APP_VERSION} has been\nsuccessfully installed.",
            font=("Segoe UI", 12), fg="#cccccc", bg="#1a1a2e", justify="center"
        ).pack(pady=20)
        
        tk.Label(
            self.current_frame,
            text=f"Installed to:\n{self.install_dir.get()}",
            font=("Segoe UI", 9), fg="#888888", bg="#1a1a2e", justify="center"
        ).pack(pady=10)
        
        if self.launch_after_install.get():
            tk.Checkbutton(
                self.current_frame, text="Launch DDS FocusPro now",
                variable=self.launch_after_install, font=("Segoe UI", 10),
                fg="#cccccc", bg="#1a1a2e", selectcolor="#16213e",
                activebackground="#1a1a2e", activeforeground="#cccccc"
            ).pack(pady=10)
        
        btn_frame = tk.Frame(self.current_frame, bg="#1a1a2e")
        btn_frame.pack(side="bottom", fill="x", pady=10)
        
        tk.Button(
            btn_frame, text="Finish", command=self.finish_install,
            font=("Segoe UI", 10, "bold"), bg="#00d4aa", fg="#1a1a2e",
            relief="flat", padx=30, pady=5, cursor="hand2"
        ).pack(side="right", padx=5)
    
    def finish_install(self):
        if self.launch_after_install.get():
            exe_path = os.path.join(self.install_dir.get(), MAIN_EXE)
            if os.path.exists(exe_path):
                subprocess.Popen([exe_path], cwd=self.install_dir.get())
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = InstallerApp()
    app.run()
