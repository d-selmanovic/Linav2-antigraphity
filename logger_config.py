import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, List

LOGS_DIR = os.getenv("LOGS_DIR", "logs")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "yes")

os.makedirs(LOGS_DIR, exist_ok=True)

# Formatierung
LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class LinaMetrics:
    """In-Memory Metriken & Monitoring für den Lina Voice Server"""

    def __init__(self):
        self.start_time = time.time()
        self.total_calls = 0
        self.active_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.total_tool_calls = 0
        self.tool_stats: Dict[str, int] = {}
        self.error_count = 0
        self.recent_errors: List[Dict[str, Any]] = []

    def record_call_start(self):
        self.total_calls += 1
        self.active_calls += 1

    def record_call_end(self, success: bool = True):
        self.active_calls = max(0, self.active_calls - 1)
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1

    def record_tool_call(self, tool_name: str, success: bool = True):
        self.total_tool_calls += 1
        self.tool_stats[tool_name] = self.tool_stats.get(tool_name, 0) + 1
        if not success:
            self.record_error(f"Tool execution failed: {tool_name}")

    def record_error(self, message: str, exc: Exception = None):
        self.error_count += 1
        err_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "message": str(message),
            "exception": str(exc) if exc else None
        }
        self.recent_errors.append(err_entry)
        if len(self.recent_errors) > 20:
            self.recent_errors.pop(0)

    def get_summary(self) -> Dict[str, Any]:
        uptime_sec = round(time.time() - self.start_time, 1)
        return {
            "uptime_seconds": uptime_sec,
            "uptime_human": f"{int(uptime_sec // 3600)}h {int((uptime_sec % 3600) // 60)}m {int(uptime_sec % 60)}s",
            "calls": {
                "total": self.total_calls,
                "active": self.active_calls,
                "successful": self.successful_calls,
                "failed": self.failed_calls
            },
            "tool_calls": {
                "total": self.total_tool_calls,
                "breakdown": self.tool_stats
            },
            "health": {
                "error_count": self.error_count,
                "last_error": self.recent_errors[-1] if self.recent_errors else None
            }
        }


# Globale Metriken-Instanz
metrics = LinaMetrics()


def setup_logging():
    """Initialisiert Rotating File Logging für Standard- und Error-Logs sowie Console"""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)

    # Verhindere doppelte Handler bei Re-Imports
    if root_logger.handlers:
        return

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # 1. Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. General App Log (logs/lina.log - max 10MB, 5 Backups)
    app_log_path = os.path.join(LOGS_DIR, "lina.log")
    app_file_handler = RotatingFileHandler(
        app_log_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    app_file_handler.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
    app_file_handler.setFormatter(formatter)
    root_logger.addHandler(app_file_handler)

    # 3. Dedicated Error Log (logs/error.log - max 10MB, 5 Backups, nur WARNING & ERROR)
    error_log_path = os.path.join(LOGS_DIR, "error.log")
    error_file_handler = RotatingFileHandler(
        error_log_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    error_file_handler.setLevel(logging.WARNING)
    error_file_handler.setFormatter(formatter)
    root_logger.addHandler(error_file_handler)

    logging.info(f"📁 Logging initialisiert: {app_log_path} und {error_log_path} (Debug={DEBUG_MODE})")


def get_logger(name: str) -> logging.Logger:
    """Gibt einen Logger mit dem angegebenen Namen zurück"""
    setup_logging()
    return logging.getLogger(name)
