# run_full.py
import argparse
import subprocess
import os
import json
from pathlib import Path
from datetime import datetime

# --- CONFIG ---
MIN_TOTAL_SCORE = 0.50
SIMILARITY_THRESHOLD = 0.80

# --- PATHS ---
ROOT_DIR = Path(__file__).parent.parent.absolute()
FORGE_DIR = ROOT_DIR / "narrative-forge"
SCRIPTS_DIR = FORGE_DIR / "scripts"
OUTPUTS_DIR = FORGE_DIR / "outputs"
RUNS_DIR = OUTPUTS_DIR / "runs"
LEDGER_FILE = OUTPUTS_DIR / "master_ledger.json"
PYTHON_EXE = str(ROOT_DIR / "harvester_venv" / "Scripts" / "python.exe")

def run_step(name, cmd, cwd=None):
    print(f"[*] Executing {name}...")
    full_cmd = [PYTHON_EXE] + cmd
    result = subprocess.run(full_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)
    if result.returncode != 0:
        print(f"[!] Error in {name}: {result.stderr}")
        return False, result.stdout
    return True, result.stdout

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--playlist", help="YouTube Playlist URL")
    parser.add_argument("--mode", default="fracture_aggressive", choices=["fracture_aggressive", "retention_aggressive"])
    parser.add_argument("--run-id", default="auto")
    parser.add_argument("--hook-text", help="Manual hook override")
    parser.add_argument("--hook-type", default="declarative")
    args = parser.parse_args()

    run_id = args.run_id if args.run_id != "auto" else datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_path = RUNS_DIR / run_id
    run_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🐺 WENDIGO BUNDLER v1 - RUN: {run_id} | MODE: {args.mode}")

    # 1. EVOLVE (Using A/B Harness)
    mode_name, style_name = args.mode.split('_')
    run_step("EVOLVE", [str(SCRIPTS_DIR / "ab_harness.py"), "--n", "5", "--mode", mode_name, "--style", style_name], cwd=FORGE_DIR)

    # 2. FIND ASSETS
    best_scripts = sorted((FORGE_DIR / "outputs/scripts/best").glob("*.txt"), key=os.path.getmtime)
    latest_best = best_scripts[-1] if best_scripts else None
    
    # 3. PREFLIGHT CRITIC
    preflight_json = run_path / "preflight.json"
    run_step("PREFLIGHT", [str(SCRIPTS_DIR / "local_critic.py"), "--script", str(latest_best), "--out", str(preflight_json)], cwd=FORGE_DIR)

    # 4. COMPILE FORENSIC BUNDLE (v1 Standard)
    preflight_data = json.loads(preflight_json.read_text()) if preflight_json.exists() else {}
    
    bundle = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "mode": args.mode,
        "hook_type": args.hook_type,
        "script_path": str(latest_best.relative_to(ROOT_DIR)) if latest_best else "none",
        "render_path": str((run_path / "video.mp4").relative_to(ROOT_DIR)) if (run_path / "video.mp4").exists() else "none",
        "critic_model": preflight_data.get("critic_model", "none"),
        "predicted_watch_ratio": preflight_data.get("predicted_watch_ratio", 0.0),
        "slop_detected": preflight_data.get("slop_detected", False),
        "critical_flaw": preflight_data.get("critical_flaw", "None"),
        "winning_line": preflight_data.get("winning_line", "None"),
        "deployment_status": "none", # To be updated by deploy scripts
        "feedback_status": "pending"
    }
    
    bundle_path = run_path / "forensic_bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(f"[✅] Forensic Bundle Sealed: {bundle_path.name}")

    # 5. UPDATE MASTER LEDGER (Derived Index)
    ledger = []
    if LEDGER_FILE.exists():
        ledger = json.loads(LEDGER_FILE.read_text())
    
    ledger.insert(0, bundle) # Latest first
    LEDGER_FILE.write_text(json.dumps(ledger[:100], indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
