# run_resurrection.py
import argparse
import subprocess
import os
import shutil
import tempfile
import hashlib
from pathlib import Path

# --- CONFIG ---
REPO_URL = "https://github.com/stative85/saas-killer.git"
ORIGINAL_VENV = Path(r"C:\Users\cleve\Downloads\CLI\facebook_reel_harvester\harvester_venv\Scripts\python.exe")

def get_file_hash(path: Path):
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def run_resurrection(mode="retention_aggressive"):
    print(f"\n[🧟] INITIATING RESURRECTION CHAMBER...")
    
    with tempfile.TemporaryDirectory(prefix="saas_resurrection_") as temp_dir:
        temp_path = Path(temp_dir)
        print(f"[*] Chamber Path: {temp_path}")
        
        # 1. CLONE
        print("[*] Cloning fresh main...")
        subprocess.run(["git", "clone", REPO_URL, "."], cwd=temp_path, check=True, capture_output=True)
        
        # 2. RUN FULL LOOP
        run_id = f"resurrection_{mode}_test"
        print(f"[*] Running full pipeline: {run_id}...")
        
        # Use existing venv but code from temp dir
        run_cmd = [
            str(ORIGINAL_VENV), "narrative-forge/run_full.py",
            "--mode", mode,
            "--run-id", run_id
        ]
        
        result = subprocess.run(run_cmd, cwd=temp_path, capture_output=True, text=True, encoding="utf-8")
        
        # 3. VERIFY ARTIFACTS
        manifest_path = temp_path / "narrative-forge" / "outputs" / "runs" / run_id / "run_manifest.json"
        bundle_path = temp_path / "narrative-forge" / "outputs" / "runs" / run_id / "forensic_bundle.json"
        script_path = temp_path / "narrative-forge" / "outputs" / "scripts" / "best"
        
        best_files = list(script_path.glob("*.txt"))
        
        if manifest_path.exists() and bundle_path.exists() and best_files:
            print("[✅] All artifacts verified in clean room.")
            script_hash = get_file_hash(best_files[0])
            print(f"[✅] Script Hash: {script_hash[:16]}...")
            
            # Print Manifest Summary
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
                print(f"[✅] Run Manifest OK. Stages: {len(manifest['stages'])}")
            
            print("\n[💎] RESURRECTION SUCCESSFUL. THE SPECIES IS STABLE.")
        else:
            print("[🛑] RESURRECTION FAILED. ARTIFACTS MISSING.")
            print(result.stdout)
            print(result.stderr)
            exit(1)

import json
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="retention_aggressive")
    args = parser.parse_args()
    
    run_resurrection(mode=args.mode)
