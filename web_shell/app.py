# web_shell/app.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import subprocess
import json
import os
from pathlib import Path
from datetime import datetime

app = FastAPI(title="SAAS KILLER")

# --- PATHS ---
ROOT_DIR = Path(__file__).parent.parent.absolute()
FORGE_DIR = ROOT_DIR / "narrative-forge"
OUTPUTS_DIR = FORGE_DIR / "outputs"
LEDGER_FILE = OUTPUTS_DIR / "master_ledger.json"
PYTHON_EXE = str(ROOT_DIR / "harvester_venv" / "Scripts" / "python.exe")

# Serve Frontend
app.mount("/static", StaticFiles(directory="web_shell/static"), name="static")

@app.get("/")
async def home():
    return JSONResponse({"status": "SAAS KILLER ONLINE", "vision": "Refine the backlogs."})

@app.get("/api/ledger")
async def get_ledger():
    if LEDGER_FILE.exists():
        with open(LEDGER_FILE, "r") as f:
            return json.load(f)
    return []

@app.post("/api/run")
async def execute_run(mode: str = Form("retention_aggressive")):
    run_id = f"web_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"[*] Triggering Web Run: {run_id} | Mode: {mode}")
    
    # Non-blocking trigger of our master orchestrator
    cmd = [PYTHON_EXE, str(FORGE_DIR / "run_full.py"), "--mode", mode, "--run-id", run_id]
    
    # For MVP, we run synchronously to return immediate result
    # Future: move to background tasks + status polling
    subprocess.run(cmd, capture_output=True)
    
    bundle_path = OUTPUTS_DIR / "runs" / run_id / "forensic_bundle.json"
    if bundle_path.exists():
        with open(bundle_path, "r") as f:
            return json.load(f)
    
    return {"status": "error", "message": "Run failed to seal bundle."}

@app.get("/api/demo")
async def get_demo():
    # Return the 'v0_baseline' as the primary proof demo
    demo_path = FORGE_DIR / "benchmarks" / "v0_baseline" / "script.txt"
    if demo_path.exists():
        return {
            "before": "Ugly transcript sludge from Infowars 1997...",
            "after": demo_path.read_text(encoding="utf-8"),
            "score": 0.70
        }
    return {"status": "no_demo_found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
