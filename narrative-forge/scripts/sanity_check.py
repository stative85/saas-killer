# sanity_check.py
from pathlib import Path
import os
import sys
from resilience import verify_env

# --- ARCHITECTURE MAP ---
FORGE_ROOT = Path(__file__).parent.parent
ROOT_DIR = FORGE_ROOT.parent

REQUIRED_PATHS = [
    FORGE_ROOT / "configs" / "default.yaml",
    FORGE_ROOT / "scripts" / "resilience.py",
    FORGE_ROOT / "scripts" / "post_harvest_indexer.py",
    ROOT_DIR / "harvester_venv" / "Scripts" / "python.exe",
    Path(r"C:\Users\cleve\OneDrive\Pictures\yt-dlp.exe")
]

REQUIRED_DIRS = [
    FORGE_ROOT / "outputs" / "runs",
    FORGE_ROOT / "outputs" / "best",
    FORGE_ROOT / "outputs" / "logs"
]

def run_sanity():
    print(f"\n🐺 WENDIGO SANITY CHECK - Initiating Perimeter Scan...")
    
    # Check Files
    verify_env(REQUIRED_PATHS, [])
    
    # Ensure Dirs
    for d in REQUIRED_DIRS:
        d.mkdir(parents=True, exist_ok=True)
        
    # Check Secrets (Warning only for local)
    secrets = FORGE_ROOT / "configs" / "client_secrets.json"
    if not secrets.exists():
        print("[WARNING] client_secrets.json missing. Egress plane will be locked.")
    
    print("[✅] PERIMETER SECURE. SYSTEM READY FOR IGNITION.\n")

if __name__ == "__main__":
    run_sanity()
