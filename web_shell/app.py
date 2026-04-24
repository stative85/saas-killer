# web_shell/app.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import subprocess
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

app = FastAPI(title="SAAS KILLER")

# --- ABSOLUTE PATH ANCHORING ---
ROOT_DIR = Path(__file__).parent.parent.absolute()
FORGE_DIR = ROOT_DIR / "narrative-forge"
OUTPUTS_DIR = FORGE_DIR / "outputs"
RUNS_DIR = OUTPUTS_DIR / "runs"
PYTHON_EXE = str(ROOT_DIR / "harvester_venv" / "Scripts" / "python.exe")

STATIC_DIR = ROOT_DIR / "web_shell" / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# TASK TRACKER (In-memory for MVP)
jobs: Dict[str, str] = {}

def run_refinery_task(run_id: str, mode: str):
    cmd = [PYTHON_EXE, str(FORGE_DIR / "run_full.py"), "--mode", mode, "--run-id", run_id]
    subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    jobs[run_id] = "COMPLETED"

@app.get("/api/ledger")
async def get_ledger():
    ledger = []
    if RUNS_DIR.exists():
        for run_dir in sorted(RUNS_DIR.iterdir(), key=os.path.getmtime, reverse=True):
            manifest_path = run_dir / "run_manifest.json"
            if manifest_path.exists():
                ledger.append(json.loads(manifest_path.read_text(encoding="utf-8")))
    return JSONResponse(content=ledger[:50])

@app.get("/api/manifest/{run_id}")
async def get_manifest(run_id: str):
    path = RUNS_DIR / run_id / "run_manifest.json"
    if path.exists():
        return JSONResponse(content=json.loads(path.read_text(encoding="utf-8")))
    raise HTTPException(status_code=404, detail="Manifest not found.")

@app.post("/api/run")
async def execute_run(background_tasks: BackgroundTasks, mode: str = Form("retention_aggressive")):
    run_id = f"web_run_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    print(f"[*] Task Queued: {run_id} | Mode: {mode}")
    jobs[run_id] = "RUNNING"
    background_tasks.add_task(run_refinery_task, run_id, mode)
    return {"status": "queued", "run_id": run_id}

@app.post("/api/feedback")
async def ingest_feedback(run_id: str = Form(...), views: int = Form(...), watch_ratio: float = Form(...)):
    print(f"[*] Ingesting Metrics for {run_id}: {views} views, {watch_ratio} ratio")
    
    # 1. Create a temporary feedback JSON for the ingestor
    fb_path = OUTPUTS_DIR / "feedback" / f"{run_id}_feedback.json"
    fb_path.parent.mkdir(parents=True, exist_ok=True)
    
    # We need a minimal feedback object that matches our schema
    fb_data = {
        "run_id": run_id,
        "views": views,
        "avg_watch_ratio": watch_ratio,
        "likes": int(views * 0.1), # Simulated
        "hook_used": "Web-Triggered Content",
        "script_path": str(RUNS_DIR / run_id / "best_script.txt") # Placeholder
    }
    fb_path.write_text(json.dumps(fb_data, indent=2))
    
    # 2. Trigger the Ingestor
    cmd = [PYTHON_EXE, str(FORGE_DIR / "scripts" / "feedback_ingest.py"), "--feedback", str(fb_path), "--out-dir", str(OUTPUTS_DIR / "feedback_updates")]
    subprocess.run(cmd, capture_output=True)
    
    return {"status": "ok", "message": "Feedback loop closed."}

@app.get("/api/file")
async def get_file(path: str):
    full_path = (ROOT_DIR / path).resolve()
    if full_path.exists() and str(full_path).startswith(str(ROOT_DIR)):
        return FileResponse(str(full_path))
    raise HTTPException(status_code=404, detail="File inaccessible.")

@app.get("/api/demo")
async def get_demo():
    # Proof baseline
    return {
        "before": "ugly raw text...",
        "after": "apex refined script...",
        "score": 0.70
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
