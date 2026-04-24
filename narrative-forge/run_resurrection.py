# run_resurrection.py
import argparse
import subprocess
import os
import shutil
import tempfile
import json
from pathlib import Path

REPO_URL = "https://github.com/stative85/saas-killer.git"
ORIGINAL_VENV = Path(r"C:\Users\cleve\Downloads\CLI\facebook_reel_harvester\harvester_venv\Scripts\python.exe")

def run_resurrection(mode="retention_aggressive"):
    print(f"\n[RESURRECTION] INITIATING CLEAN ROOM PROOF...")
    
    # We use a static temp path for easier debugging
    temp_path = Path("C:/Users/cleve/Downloads/CLI/resurrection_chamber")
    if temp_path.exists(): shutil.rmtree(temp_path)
    temp_path.mkdir(parents=True)
    
    try:
        print("[*] Cloning fresh main...")
        subprocess.run(["git", "clone", REPO_URL, "."], cwd=temp_path, check=True, capture_output=True)
        
        run_id = f"resurrection_v1_{mode}"
        print(f"[*] Running full pipeline: {run_id}...")
        
        run_cmd = [str(ORIGINAL_VENV), "narrative-forge/run_full.py", "--mode", mode, "--run-id", run_id]
        result = subprocess.run(run_cmd, cwd=temp_path, capture_output=True, text=True, encoding="utf-8")
        
        print("\n--- RESURRECTION DIR TREE ---")
        for p in temp_path.rglob("*"):
            if "outputs" in str(p): print(f"  {p.relative_to(temp_path)}")
        
        run_dir = temp_path / "narrative-forge" / "outputs" / "runs" / run_id
        if (run_dir / "run_manifest.json").exists():
            print("\n[💎] RESURRECTION SUCCESSFUL. EVIDENCE LOCATED.")
        else:
            print("\n[🛑] RESURRECTION FAILED. EVIDENCE MISSING.")
            print(f"Expected: {run_dir}")
            
    finally:
        # We keep the chamber for forensic analysis
        print(f"[*] Forensic Chamber Preserved: {temp_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="retention_aggressive")
    args = parser.parse_args()
    run_resurrection(mode=args.mode)
