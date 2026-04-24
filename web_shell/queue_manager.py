# web_shell/queue_manager.py
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "narrative-forge" / "outputs" / "job_queue.db"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT UNIQUE,
        status TEXT,
        mode TEXT,
        path TEXT,
        created_at DATETIME,
        finished_at DATETIME,
        error_msg TEXT
    )''')
    conn.commit()
    conn.close()

def add_job(run_id: str, mode: str, path: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO jobs (run_id, status, mode, path, created_at) VALUES (?, ?, ?, ?, ?)",
              (run_id, "PENDING", mode, path, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_next_job():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Atomic Claim
    c.execute("SELECT id, run_id, mode, path FROM jobs WHERE status = 'PENDING' ORDER BY created_at ASC LIMIT 1")
    job = c.fetchone()
    if job:
        c.execute("UPDATE jobs SET status = 'PROCESSING' WHERE id = ?", (job[0],))
        conn.commit()
    conn.close()
    return job

def update_job_status(run_id: str, status: str, error: str = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE jobs SET status = ?, finished_at = ?, error_msg = ? WHERE run_id = ?",
              (status, datetime.now().isoformat(), error, run_id))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"[OK] Job Queue Initialized: {DB_PATH}")
