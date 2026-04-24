# web_shell/worker.py
import time
import subprocess
import os
import sqlite3
from pathlib import Path
from datetime import datetime
from web_shell.queue_manager import get_next_job, update_job_status, DB_PATH

ROOT_DIR = Path(__file__).parent.parent.absolute()
FORGE_DIR = ROOT_DIR / "narrative-forge"
PYTHON_EXE = str(ROOT_DIR / "harvester_venv" / "Scripts" / "python.exe")

def run_worker():
    print(f"\n[WORKER] Compute Plane Online. Waiting for jobs...")
    print(f"[*] Queue: {DB_PATH}")
    
    while True:
        job = get_next_job()
        if not job:
            time.sleep(2) # Backoff
            continue
            
        job_id, run_id, mode, project_path = job
        print(f"\n[>] CLAIMED: {run_id} | Mode: {mode}")
        
        # Execute Refinery Loop
        cmd = [PYTHON_EXE, str(FORGE_DIR / "run_full.py"), "--mode", mode, "--run-id", run_id]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            
            if result.returncode == 0:
                print(f"  [OK] Job {run_id} Completed.")
                # We connect again for status update to avoid locking during long runs
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("UPDATE jobs SET status = 'COMPLETED', finished_at = ? WHERE run_id = ?",
                          (datetime.now().isoformat(), run_id))
                conn.commit()
                conn.close()
            else:
                print(f"  [🛑] Job {run_id} Failed.")
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("UPDATE jobs SET status = 'FAILED', finished_at = ?, error_msg = ? WHERE run_id = ?",
                          (datetime.now().isoformat(), result.stderr[-500:], run_id))
                conn.commit()
                conn.close()
                
        except Exception as e:
            print(f"  [!] Worker Critical Error: {e}")
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE jobs SET status = 'FAILED', finished_at = ?, error_msg = ? WHERE run_id = ?",
                      (datetime.now().isoformat(), str(e), run_id))
            conn.commit()
            conn.close()

if __name__ == "__main__":
    run_worker()
