import subprocess
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.absolute()
PYTHON = str(ROOT / "harvester_venv" / "Scripts" / "python.exe")

def boot():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    
    print("[*] Igniting API Sentry...")
    api = subprocess.Popen([PYTHON, "web_shell/app.py"], env=env)
    
    print("[*] Igniting Compute Furnace...")
    worker = subprocess.Popen([PYTHON, "web_shell/worker.py"], env=env)
    
    return api, worker

if __name__ == "__main__":
    api, worker = boot()
    try:
        api.wait()
        worker.wait()
    except KeyboardInterrupt:
        api.terminate()
        worker.terminate()
