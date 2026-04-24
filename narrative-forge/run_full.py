# run_full.py
import argparse
import subprocess
import os
import json
import sys
import re
from pathlib import Path
from datetime import datetime

# --- PATHS ---
FORGE_DIR = Path(__file__).parent.absolute()
SCRIPTS_DIR = FORGE_DIR / "scripts"
OUTPUTS_DIR = FORGE_DIR / "outputs"
RUNS_DIR = OUTPUTS_DIR / "runs"
LEDGER_FILE = OUTPUTS_DIR / "master_ledger.json"

# DYNAMIC PYTHON DETECTION
def get_python_exe():
    local_venv = FORGE_DIR.parent / "harvester_venv" / "Scripts" / "python.exe"
    if local_venv.exists(): return str(local_venv)
    original_venv = Path(r"C:\Users\cleve\Downloads\CLI\facebook_reel_harvester\harvester_venv\Scripts\python.exe")
    if original_venv.exists(): return str(original_venv)
    return sys.executable

PYTHON_EXE = get_python_exe()

def run_step(name, cmd):
    print(f"[*] Executing {name}...")
    full_cmd = [str(PYTHON_EXE)] + [str(c) for c in cmd]
    result = subprocess.run(full_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        print(f"[!] Error in {name}: {result.stderr}")
        return False, result.stdout
    return True, result.stdout

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--playlist", help="YouTube Playlist URL")
    parser.add_argument("--mode", default="fracture_aggressive", choices=["fracture_aggressive", "retention_aggressive"])
    parser.add_argument("--run-id", default="auto")
    args = parser.parse_args()

    run_id = args.run_id if args.run_id != "auto" else datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_path = RUNS_DIR / run_id
    run_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🐺 WENDIGO BUNDLER v1.1 - RESURRECTED | RUN: {run_id}")
    print(f"[*] Engine: {PYTHON_EXE}")

    # 1. EVOLVE
    mode_name, style_name = args.mode.split('_')
    chunks_path = Path(r"C:\Users\cleve\OneDrive\Pictures\corpus_run\index\chunks_with_arcs.jsonl")
    if not chunks_path.exists():
        chunks_path = FORGE_DIR / "outputs" / "infowars_corpus_modern_hardened" / "index" / "chunks_with_arcs.jsonl"

    run_step("EVOLVE", [
        SCRIPTS_DIR / "ab_harness.py", 
        "--n", "5", 
        "--mode", mode_name, 
        "--style", style_name,
        "--chunks", str(chunks_path)
    ])

    # 2. FIND ASSETS
    best_scripts = sorted((OUTPUTS_DIR / "scripts" / "best").glob("*.txt"), key=os.path.getmtime)
    if not best_scripts:
        print("[!] No best scripts found.")
        return
    latest_best = best_scripts[-1]
    
    # 3. PREFLIGHT CRITIC
    preflight_json = run_path / "preflight.json"
    run_step("PREFLIGHT", [SCRIPTS_DIR / "local_critic.py", "--script", str(latest_best), "--out", str(preflight_json)])

    # 4. COMPILE FORENSIC BUNDLE
    preflight_data = json.loads(preflight_json.read_text()) if preflight_json.exists() else {}
    
    bundle = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "mode": args.mode,
        "script_path": str(latest_best.relative_to(FORGE_DIR.parent)),
        "status": "VALIDATED" if preflight_data.get("status") == "ok" else "PREFLIGHT_ERROR",
        "predicted_watch_ratio": preflight_data.get("predicted_watch_ratio", 0.0),
        "slop_detected": preflight_data.get("slop_detected", False),
        "critical_flaw": preflight_data.get("critical_flaw", "None"),
        "winning_line": preflight_data.get("winning_line", "None"),
        "deployment_status": "none",
        "feedback_status": "pending"
    }
    
    bundle_path = run_path / "forensic_bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(f"[✅] Forensic Bundle Sealed: {bundle_path.name}")

    # 5. UPDATE MASTER LEDGER
    ledger = []
    if LEDGER_FILE.exists():
        ledger = json.loads(LEDGER_FILE.read_text())
    
    ledger.insert(0, bundle)
    LEDGER_FILE.write_text(json.dumps(ledger[:100], indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
