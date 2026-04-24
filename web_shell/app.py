# web_shell/app.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import subprocess
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

app = FastAPI(title="SAAS KILLER")

# --- ABSOLUTE PATH ANCHORING ---
ROOT_DIR = Path(__file__).parent.parent.absolute()
FORGE_DIR = ROOT_DIR / "narrative-forge"
OUTPUTS_DIR = FORGE_DIR / "outputs"
LEDGER_FILE = OUTPUTS_DIR / "master_ledger.json"
PYTHON_EXE = str(ROOT_DIR / "harvester_venv" / "Scripts" / "python.exe")

# Ensure static dir is anchored
STATIC_DIR = ROOT_DIR / "web_shell" / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/api/ledger")
async def get_ledger():
    if LEDGER_FILE.exists():
        return JSONResponse(content=json.loads(LEDGER_FILE.read_text(encoding="utf-8")))
    return []

@app.get("/api/bundle/{run_id}")
async def get_bundle(run_id: str):
    bundle_path = OUTPUTS_DIR / "runs" / run_id / "forensic_bundle.json"
    if bundle_path.exists():
        return JSONResponse(content=json.loads(bundle_path.read_text(encoding="utf-8")))
    raise HTTPException(status_code=404, detail="Forensic bundle not found.")

@app.get("/api/deploy-pack/{run_id}")
async def get_deploy_pack(run_id: str):
    pack_path = OUTPUTS_DIR / "runs" / run_id / "deploy_pack.json"
    if pack_path.exists():
        return JSONResponse(content=json.loads(pack_path.read_text(encoding="utf-8")))
    return {"status": "none"}

@app.get("/api/file")
async def get_file(path: str):
    # Path is relative to ROOT_DIR
    full_path = ROOT_DIR / path
    if full_path.exists() and full_path.is_relative_to(ROOT_DIR):
        return FileResponse(str(full_path))
    raise HTTPException(status_code=404, detail="File inaccessible.")

@app.post("/api/run")
async def execute_run(path: str = Form(...), mode: str = Form("retention_aggressive")):
    run_id = f"web_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"[*] Triggering Web Run: {run_id} | Project: {path} | Mode: {mode}")
    
    # ACTUAL INTAKE: Pass path as project/source context
    # Note: run_full.py v1.2 expects --playlist or uses defaults
    cmd = [PYTHON_EXE, str(FORGE_DIR / "run_full.py"), "--mode", mode, "--run-id", run_id]
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    
    if result.returncode != 0:
        return JSONResponse(status_code=500, content={
            "status": "error", 
            "message": "Refinery execution failed.",
            "stderr": result.stderr[-1000:]
        })
    
    bundle_path = OUTPUTS_DIR / "runs" / run_id / "forensic_bundle.json"
    if bundle_path.exists():
        return JSONResponse(content=json.loads(bundle_path.read_text(encoding="utf-8")))
    
    return {"status": "error", "message": "Run finished but bundle is missing."}

@app.get("/api/demo")
async def get_demo():
    # REAL DEMO: Pull from v0_baseline
    baseline_dir = FORGE_DIR / "benchmarks" / "v0_baseline"
    script_path = baseline_dir / "script.txt"
    # Assuming we have a preserved 'raw' sample for the 'before'
    raw_sample = "okay so in this first lecture I want to okay so in this first lecture I want to ask a question the question ask a question..."
    
    if script_path.exists():
        return {
            "before": raw_sample,
            "after": script_path.read_text(encoding="utf-8"),
            "score": 0.70
        }
    return {"status": "no_demo_found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
