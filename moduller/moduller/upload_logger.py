"""
Upload Logger Module
====================
Tracks every AWS S3 and Contabo upload attempt with detailed status logging.
Creates a local log file per day at: upload_log_YYYY-MM-DD.txt (same folder as the app exe/script)

Each record includes:
- Timestamp
- Function name (which upload function was called)
- Upload type (screenshot, activity_data, session_log, etc.)
- Destination (AWS_S3 / CONTABO)
- Email / Task (project context)
- Status (ATTEMPTING, SUCCESS, FAILED, RETRYING, SKIPPED, TIMEOUT)
- Data size
- Error details (if failed)
- Duration (how long the upload took)
"""

import os
import json
import time
import logging
import threading
import traceback as _traceback
import sys as _sys
from datetime import datetime
from pathlib import Path
from functools import wraps

logger = logging.getLogger(__name__)

# ============================================
# LOG FILE CONFIGURATION
# ============================================
# Log file lives next to the running .exe (installed app) or script (dev mode)
import sys
if getattr(sys, 'frozen', False):
    # Running as PyInstaller .exe → use the folder where the .exe is located
    _APP_DIR = os.path.dirname(sys.executable)
else:
    # Running as .py script during development
    _APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_lock = threading.Lock()


def _get_log_file_path():
    """Return today's log file path (.txt for easy double-click viewing)."""
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(_APP_DIR, f"upload_log_{today}.txt")


def _write_log_entry(entry: dict):
    """
    Write a single log entry to today's log file (thread-safe).
    Each entry is one JSON line + a human-readable summary line.
    """
    log_path = _get_log_file_path()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    entry["timestamp"] = timestamp

    # Build human-readable summary
    status = entry.get("status", "UNKNOWN")
    dest = entry.get("destination", "?")
    func = entry.get("function", "?")
    upload_type = entry.get("upload_type", "?")
    email = entry.get("email", "?")
    task = entry.get("task", "?")
    size = entry.get("data_size_bytes", 0)
    duration = entry.get("duration_sec", "")
    error = entry.get("error", "")
    attempt = entry.get("attempt", "")
    max_attempts = entry.get("max_attempts", "")
    s3_key = entry.get("s3_key", "")

    # Format size nicely
    if size > 1024 * 1024:
        size_str = f"{size / (1024 * 1024):.1f} MB"
    elif size > 1024:
        size_str = f"{size / 1024:.1f} KB"
    else:
        size_str = f"{size} B"

    # Build status icon
    status_icons = {
        "ATTEMPTING": ">>>",
        "SUCCESS": "[OK]",
        "FAILED": "[FAIL]",
        "RETRYING": "[RETRY]",
        "SKIPPED": "[SKIP]",
        "TIMEOUT": "[TIMEOUT]",
    }
    icon = status_icons.get(status, "[?]")

    # Human-readable line
    summary_parts = [
        f"{timestamp}",
        f"{icon} {status}",
        f"dest={dest}",
        f"fn={func}",
        f"type={upload_type}",
        f"email={email}",
        f"task={task}",
        f"size={size_str}",
    ]
    if attempt:
        summary_parts.append(f"attempt={attempt}/{max_attempts}")
    if duration:
        summary_parts.append(f"duration={duration}s")
    if s3_key:
        summary_parts.append(f"key={s3_key}")
    if error:
        summary_parts.append(f"error={error}")

    summary_line = " | ".join(summary_parts)

    # Build detailed error block for FAILED / TIMEOUT / RETRYING entries
    error_detail_lines = ""
    if status in ("FAILED", "TIMEOUT", "RETRYING"):
        exc_type = entry.get("exc_type", "")
        exc_traceback = entry.get("exc_traceback", "")
        if exc_type or exc_traceback:
            error_detail_lines += f"    exception_type: {exc_type}\n"
            error_detail_lines += f"    error_message : {error}\n"
            if exc_traceback:
                for tb_line in exc_traceback.strip().splitlines():
                    error_detail_lines += f"    {tb_line}\n"

    with _lock:
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(summary_line + "\n")
                if error_detail_lines:
                    f.write(error_detail_lines)
        except Exception as e:
            logger.warning("Failed to write upload log entry: %s", e)


# ============================================
# PUBLIC LOGGING FUNCTIONS
# ============================================

def log_upload_attempt(function_name, upload_type, destination, email, task,
                       data_size_bytes=0, s3_key="", attempt=None, max_attempts=None):
    """Log that an upload is being attempted."""
    _write_log_entry({
        "status": "ATTEMPTING",
        "function": function_name,
        "upload_type": upload_type,
        "destination": destination,
        "email": email,
        "task": task,
        "data_size_bytes": data_size_bytes,
        "s3_key": s3_key,
        "attempt": attempt or "",
        "max_attempts": max_attempts or "",
    })


def log_upload_success(function_name, upload_type, destination, email, task,
                       data_size_bytes=0, s3_key="", url="", duration_sec=None,
                       attempt=None, max_attempts=None):
    """Log a successful upload."""
    _write_log_entry({
        "status": "SUCCESS",
        "function": function_name,
        "upload_type": upload_type,
        "destination": destination,
        "email": email,
        "task": task,
        "data_size_bytes": data_size_bytes,
        "s3_key": s3_key,
        "url": url,
        "duration_sec": round(duration_sec, 2) if duration_sec else "",
        "attempt": attempt or "",
        "max_attempts": max_attempts or "",
    })


def log_upload_failed(function_name, upload_type, destination, email, task,
                      error="", data_size_bytes=0, s3_key="", duration_sec=None,
                      attempt=None, max_attempts=None):
    """Log a failed upload with full exception details."""
    # Auto-capture exception info if called from an except block
    exc_type_name = ""
    exc_tb = ""
    exc_info = _sys.exc_info()
    if exc_info and exc_info[0] is not None:
        exc_type_name = exc_info[0].__name__
        exc_tb = _traceback.format_exception(*exc_info)
        exc_tb = "".join(exc_tb)
    _write_log_entry({
        "status": "FAILED",
        "function": function_name,
        "upload_type": upload_type,
        "destination": destination,
        "email": email,
        "task": task,
        "data_size_bytes": data_size_bytes,
        "s3_key": s3_key,
        "error": str(error),
        "exc_type": exc_type_name,
        "exc_traceback": exc_tb,
        "duration_sec": round(duration_sec, 2) if duration_sec else "",
        "attempt": attempt or "",
        "max_attempts": max_attempts or "",
    })


def log_upload_retrying(function_name, upload_type, destination, email, task,
                        error="", attempt=1, max_attempts=3, backoff_sec=0,
                        data_size_bytes=0, s3_key=""):
    """Log that an upload is being retried with full exception details."""
    exc_type_name = ""
    exc_tb = ""
    exc_info = _sys.exc_info()
    if exc_info and exc_info[0] is not None:
        exc_type_name = exc_info[0].__name__
        exc_tb = _traceback.format_exception(*exc_info)
        exc_tb = "".join(exc_tb)
    _write_log_entry({
        "status": "RETRYING",
        "function": function_name,
        "upload_type": upload_type,
        "destination": destination,
        "email": email,
        "task": task,
        "data_size_bytes": data_size_bytes,
        "s3_key": s3_key,
        "error": f"{error} | retrying in {backoff_sec}s",
        "exc_type": exc_type_name,
        "exc_traceback": exc_tb,
        "attempt": attempt,
        "max_attempts": max_attempts,
    })


def log_upload_skipped(function_name, upload_type, destination, email, task,
                       reason="", s3_key=""):
    """Log that an upload was skipped (e.g. missing credentials, timeout)."""
    _write_log_entry({
        "status": "SKIPPED",
        "function": function_name,
        "upload_type": upload_type,
        "destination": destination,
        "email": email,
        "task": task,
        "s3_key": s3_key,
        "error": reason,
    })


def log_upload_timeout(function_name, upload_type, destination, email, task,
                       error="", data_size_bytes=0, s3_key="", duration_sec=None):
    """Log that an upload timed out with full exception details."""
    exc_type_name = ""
    exc_tb = ""
    exc_info = _sys.exc_info()
    if exc_info and exc_info[0] is not None:
        exc_type_name = exc_info[0].__name__
        exc_tb = _traceback.format_exception(*exc_info)
        exc_tb = "".join(exc_tb)
    _write_log_entry({
        "status": "TIMEOUT",
        "function": function_name,
        "upload_type": upload_type,
        "destination": destination,
        "email": email,
        "task": task,
        "data_size_bytes": data_size_bytes,
        "s3_key": s3_key,
        "error": str(error),
        "exc_type": exc_type_name,
        "exc_traceback": exc_tb,
        "duration_sec": round(duration_sec, 2) if duration_sec else "",
    })


def get_today_log_path():
    """Return the path to today's upload log file."""
    return _get_log_file_path()


def get_today_summary():
    """
    Parse today's log file and return a summary dict with counts
    grouped by destination, upload_type, and status.
    """
    log_path = _get_log_file_path()
    if not os.path.exists(log_path):
        return {"date": datetime.now().strftime("%Y-%m-%d"), "total_entries": 0, "summary": {}}

    summary = {}
    total = 0
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                total += 1
                # Parse key fields from the human-readable format
                parts = {p.split("=")[0].strip(): p.split("=", 1)[1].strip()
                         for p in line.split("|") if "=" in p}
                dest = parts.get("dest", "unknown")
                utype = parts.get("type", "unknown")
                task = parts.get("task", "unknown")

                # Determine status from the icon
                status = "UNKNOWN"
                for s in ["[OK]", "[FAIL]", "[RETRY]", "[SKIP]", "[TIMEOUT]", ">>>"]:
                    if s in line:
                        status = {"[OK]": "SUCCESS", "[FAIL]": "FAILED", "[RETRY]": "RETRYING",
                                  "[SKIP]": "SKIPPED", "[TIMEOUT]": "TIMEOUT", ">>>": "ATTEMPTING"}.get(s, "UNKNOWN")
                        break

                key = f"{dest}|{utype}|{task}"
                if key not in summary:
                    summary[key] = {"destination": dest, "upload_type": utype, "task": task,
                                    "SUCCESS": 0, "FAILED": 0, "RETRYING": 0,
                                    "SKIPPED": 0, "TIMEOUT": 0, "ATTEMPTING": 0}
                if status in summary[key]:
                    summary[key][status] += 1

    except Exception as e:
        logger.warning("Failed to parse upload log summary: %s", e)

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "log_file": log_path,
        "total_entries": total,
        "summary": list(summary.values()),
    }
