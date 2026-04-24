# web_shell/app.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from web_shell.queue_manager import init_db, add_job

app = FastAPI(title="SAAS KILLER API")

# --- PATHS ---
ROOT_DIR = Path(__file__).parent.parent.absolute()
FORGE_DIR = ROOT_DIR / "narrative-forge"
OUTPUTS_DIR = FORGE_DIR / "outputs"
RUNS_DIR = OUTPUTS_DIR / "runs"

init_db() # Ensure DB exists on boot

STATIC_DIR = ROOT_DIR / "web_shell" / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/api/ledger")
async def get_ledger():
    ledger = []
    if RUNS_DIR.exists():
        for run_dir in sorted(RUNS_DIR.iterdir(), key=os.path.getmtime, reverse=True):
            manifest_path = run_dir / "run_manifest.json"
            if manifest_path.exists():
                try:
                    ledger.append(json.loads(manifest_path.read_text(encoding="utf-8")))
                except: continue
    return JSONResponse(content=ledger[:50])

@app.get("/api/manifest/{run_id}")
async def get_manifest(run_id: str):
    path = RUNS_DIR / run_id / "run_manifest.json"
    if path.exists():
        return JSONResponse(content=json.loads(path.read_text(encoding="utf-8")))
    raise HTTPException(status_code=404, detail="Manifest not found.")

@app.post("/api/run")
async def execute_run(path: str = Form(...), mode: str = Form("retention_aggressive")):
    run_id = f"web_run_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    print(f"[*] Job Received: {run_id} | Mode: {mode}")
    
    # DROP JOB INTO QUEUE
    try:
        add_job(run_id, mode, path)
        return {"status": "queued", "run_id": run_id, "message": "Job accepted by the Compute Plane."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue job: {e}")

@app.get("/api/file")
async def get_file(path: str):
    full_path = (ROOT_DIR / path).resolve()
    if full_path.exists() and str(full_path).startswith(str(ROOT_DIR)):
        return FileResponse(str(full_path))
    raise HTTPException(status_code=404, detail="File inaccessible.")

@app.get("/api/demo")
async def get_demo():
    baseline_dir = FORGE_DIR / "benchmarks" / "v0_baseline"
    script_path = baseline_dir / "script.txt"
    if script_path.exists():
        return {
            "before": "ugly raw text...",
            "after": script_path.read_text(encoding="utf-8"),
            "score": 0.70
        }
    return {"status": "no_demo_found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
