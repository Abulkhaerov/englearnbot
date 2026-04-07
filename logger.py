import datetime
import os

LOG_FILE = "log.txt"

def _write_log(level: str, message: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [{level}] {message}"
    print(formatted)  # Print to console
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception as e:
        print(f"[ERROR] Failed to write to log file: {e}")

def info(message: str):
    _write_log("INFO", message)

def warning(message: str):
    _write_log("WARNING", message)

def error(message: str):
    _write_log("ERROR", message)

def debug(message: str):
    _write_log("DEBUG", message)