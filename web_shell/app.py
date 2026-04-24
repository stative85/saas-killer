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
RUNS_DIR = OUTPUTS_DIR / "runs"
PYTHON_EXE = str(ROOT_DIR / "harvester_venv" / "Scripts" / "python.exe")

STATIC_DIR = ROOT_DIR / "web_shell" / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

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

@app.get("/api/deploy-pack/{run_id}")
async def get_deploy_pack(run_id: str):
    path = RUNS_DIR / run_id / "deploy_pack.json"
    if path.exists():
        return JSONResponse(content=json.loads(path.read_text(encoding="utf-8")))
    return {"status": "none"}

@app.get("/api/file")
async def get_file(path: str):
    full_path = (ROOT_DIR / path).resolve()
    if full_path.exists() and str(full_path).startswith(str(ROOT_DIR)):
        return FileResponse(str(full_path))
    raise HTTPException(status_code=404, detail="File inaccessible.")

@app.post("/api/run")
async def execute_run(path: str = Form(...), mode: str = Form("retention_aggressive")):
    run_id = f"web_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"[*] Triggering Web Run: {run_id} | Mode: {mode}")
    
    cmd = [PYTHON_EXE, str(FORGE_DIR / "run_full.py"), "--mode", mode, "--run-id", run_id]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    
    if result.returncode != 0:
        return JSONResponse(status_code=500, content={"status": "error", "message": result.stderr})
    
    manifest_path = RUNS_DIR / run_id / "run_manifest.json"
    if manifest_path.exists():
        # FIXED: Return the MANIFEST, not the missing bundle
        return JSONResponse(content=json.loads(manifest_path.read_text(encoding="utf-8")))
    
    return JSONResponse(status_code=404, content={"status": "error", "message": f"Run {run_id} successful but manifest missing."})

@app.get("/api/demo")
async def get_demo():
    baseline_dir = FORGE_DIR / "benchmarks" / "v0_baseline"
    script_path = baseline_dir / "script.txt"
    if script_path.exists():
        return {
            "before": "okay so in this first lecture I want to ask a question...",
            "after": script_path.read_text(encoding="utf-8"),
            "score": 0.70
        }
    return {"status": "no_demo_found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
