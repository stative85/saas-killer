# resilience.py
import time
import functools
import logging
import json
import sys
from pathlib import Path
from datetime import datetime

# --- LOGGING SETUP ---
LOG_DIR = Path(__file__).parent.parent / "outputs" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

class ForensicLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # JSON Formatter for machine readability
        log_file = LOG_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.jsonl"
        handler = logging.FileHandler(log_file)
        self.logger.addHandler(handler)

    def log(self, level: str, msg: str, **kwargs):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": msg,
            **kwargs
        }
        self.logger.info(json.dumps(entry))
        # Also print to console for visibility
        color = "\033[92m" if level == "SUCCESS" else "\033[91m" if level == "ERROR" else "\033[94m"
        print(f"{color}[{level}] {msg}\033[0m")

def resilient(retries: int = 3, delay: float = 2.0, backoff: float = 2.0):
    """Decorator to add retry logic with exponential backoff to any function."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            curr_delay = delay
            while attempt < retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt == retries:
                        print(f"[FATAL] {func.__name__} failed after {retries} attempts: {e}")
                        raise e
                    print(f"[RETRY] {func.__name__} failed (Attempt {attempt}/{retries}). Retrying in {curr_delay}s...")
                    time.sleep(curr_delay)
                    curr_delay *= backoff
        return wrapper
    return decorator

def verify_env(required_paths: list[Path], required_env: list[str]):
    """Hard check of environment integrity."""
    missing = []
    for p in required_paths:
        if not p.exists(): missing.append(f"PATH_MISSING: {p}")
    for e in required_env:
        if e not in os.environ: missing.append(f"ENV_MISSING: {e}")
    
    if missing:
        print("\n[!] CRITICAL ENVIRONMENT GAPS DETECTED:")
        for m in missing: print(f"  - {m}")
        sys.exit(1)
    print("[OK] Environment Integrity Verified.")

import os
