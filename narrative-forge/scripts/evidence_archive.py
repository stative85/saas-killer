# evidence_archive.py
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# --- CONFIG ---
FORGE_DIR = Path(__file__).parent.parent.absolute()
RUNS_DIR = FORGE_DIR / "outputs" / "runs"
ARCHIVE_BASE = Path(r"D:\WENDIGO_ARCHIVE")

def archive_ingested_runs():
    print(f"[*] Initiating Evidence Retention Cycle...")
    ARCHIVE_BASE.mkdir(parents=True, exist_ok=True)
    
    count = 0
    for run_dir in RUNS_DIR.iterdir():
        if not run_dir.is_dir(): continue
        
        bundle_path = run_dir / "forensic_bundle.json"
        if not bundle_path.exists(): continue
        
        with open(bundle_path, "r") as f:
            bundle = json.load(f)
            
        # Only archive runs that have completed the loop
        if bundle.get("feedback_status") == "ingested":
            print(f"  [>] Archiving Run: {run_dir.name}")
            dest = ARCHIVE_BASE / run_dir.name
            if dest.exists(): shutil.rmtree(dest)
            shutil.move(str(run_dir), str(dest))
            count += 1
            
    print(f"\n[✅] Retention Cycle Complete. {count} runs moved to {ARCHIVE_BASE}")

if __name__ == "__main__":
    archive_ingested_runs()
